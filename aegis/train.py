"""Train, calibrate and select the risk model. Test records are never read here.

  python -m aegis.train

  train (seed 1)    fit the models on tier-1 records: features -> tier-1 answer wrong
  calib (seed 4)    Platt-scale every model's scores into probabilities
  val   (seed 3)    compare models end to end and choose the model and its threshold

Models: single-feature heuristics, logistic regression, gradient-boosted trees, and
gradient-boosted trees with feature groups removed (ablations). Cross-noise models are trained
at one p and scored at the others.

Selection is by the end-to-end objective, not by classification accuracy: among all thresholds
whose validation failures do not exceed relay-BP's at any required p, take the one with the
lowest mean decode time (model inference time included).

Writes models/aegis_router.joblib and experiments/reports/training.json.
"""
import argparse
import json
import time

import joblib
import numpy as np

from mgccorrection.paths import ROOT

from . import features
from .collect import RECORDS, TRAIN_RECORDS, load
from .model import calibrate, quality, train
from .policy import frontier, pareto

MODELS = ROOT / "models"
REPORTS = ROOT / "experiments" / "reports"
SWEEP = [0.003, 0.004, 0.005]
THRESHOLDS = np.concatenate([[0.0], np.geomspace(1e-5, 0.5, 60), [0.75, 1.0]])


def read(directory, split, settings, tier="fast"):
    """Stacked (features, labels, setting index) of a split over (p, f) settings and both bases."""
    F, y, where = [], [], []
    for k, (p, f) in enumerate(settings):
        for basis in "XZ":
            name = f"{split}_{basis}_p{p}" + (f"_f{f}" if f else "") + ".npz"
            if not (directory / name).exists():
                continue
            record = load(directory / name)
            F.append(record[tier]["features"])
            y.append(record[tier]["failed"])
            where.append(np.full(len(y[-1]), k))
    return np.concatenate(F), np.concatenate(y), np.concatenate(where)


def inference_seconds(model, F, repeats=2000):
    """Measured time of one per-shot risk call."""
    rows = F[np.random.default_rng(0).integers(0, len(F), repeats)]
    start = time.perf_counter()
    for row in rows:
        model.risk(row)
    return (time.perf_counter() - start) / repeats


def validation_frontiers(model, overhead, tier1="fast", tier2="strong"):
    """Per p: the threshold sweep of the routed decoder on validation records, and relay-BP's failures."""
    out = {}
    for p in SWEEP:
        x, z = load(RECORDS / f"val_X_p{p}.npz"), load(RECORDS / f"val_Z_p{p}.npz")
        points = frontier(x, z, model.risks(x[tier1]["features"]), model.risks(z[tier1]["features"]), THRESHOLDS,
                          tier1, tier2, overhead)
        relay_pair = x["relay"]["failed"] | z["relay"]["failed"]
        out[p] = {"points": points, "relay_failures": int(relay_pair.sum()),
                  "relay_ms": float((x["relay"]["seconds"] + z["relay"]["seconds"]).mean() * 1e3)}
    return out


def choose_threshold(fronts, slack=0):
    """Largest threshold that keeps validation failures within relay-BP's (+ slack) at every p."""
    ok = [k for k in range(len(THRESHOLDS))
          if all(front["points"][k]["failures_pair"] <= front["relay_failures"] + slack for front in fronts.values())]
    return (float(THRESHOLDS[max(ok)]), True) if ok else (0.0, False)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--tier2", default="strong")
    args = parser.parse_args()
    sweep = [(p, 0.0) for p in SWEEP]
    F, y, where = read(TRAIN_RECORDS, "train", sweep)
    Fc, yc, _ = read(TRAIN_RECORDS, "calib", sweep)
    Fv, yv, wv = read(RECORDS, "val", sweep)
    print(f"train {len(y)} shots ({int(y.sum())} wrong), calibration {len(yc)}, validation {len(yv)}")

    candidates = {
        "heuristic: solution weight": dict(kind="heuristic", feature="solution_weight"),
        "heuristic: iterations": dict(kind="heuristic", feature="log_iterations"),
        "heuristic: syndrome weight": dict(kind="heuristic", feature="syndrome_weight"),
        "logistic": dict(kind="logistic"),
        "gbm": dict(kind="gbm"),
        "gbm, no temporal features": dict(kind="gbm", groups=("tier1", "syndrome", "loss")),
        "gbm, no tier-1 diagnostics": dict(kind="gbm", groups=("syndrome", "temporal", "loss")),
        "gbm, tier-1 diagnostics only": dict(kind="gbm", groups=("tier1",)),
    }
    report = {"train_shots": int(len(y)), "train_wrong": int(y.sum()), "features": features.NAMES, "models": {}}
    fitted = {}
    for name, spec in candidates.items():
        model = calibrate(train(F, y, seed=args.seed, **spec), Fc, yc)
        overhead = inference_seconds(model, Fv)
        fronts = validation_frontiers(model, overhead, tier2=args.tier2)
        threshold, feasible = choose_threshold(fronts)
        k = int(np.argmin(np.abs(THRESHOLDS - threshold)))
        entry = {"inference_us": overhead * 1e6, "threshold": threshold, "feasible": feasible,
                 "validation": {str(p): quality(model, Fv[wv == i], yv[wv == i]) for i, p in enumerate(SWEEP)},
                 "validation_all": quality(model, Fv, yv),
                 "at_threshold": {str(p): fronts[p]["points"][k] | {"relay_failures": fronts[p]["relay_failures"],
                                                                     "relay_ms": fronts[p]["relay_ms"]} for p in SWEEP},
                 "frontier": {str(p): pareto(fronts[p]["points"]) for p in SWEEP}}
        entry["objective_ms"] = float(np.mean([entry["at_threshold"][str(p)]["ms_mean"] for p in SWEEP]))
        report["models"][name] = entry
        fitted[name] = model
        q = entry["validation_all"]
        print(f"{name:30s} AUC {q['auc']:.4f}  AP {q['average_precision']:.3f}  ECE {q['ece']:.4f}  "
              f"{entry['inference_us']:6.0f} us  threshold {threshold:.2e}  " +
              "  ".join(f"p={p}: {entry['at_threshold'][str(p)]['failures_pair']}/{entry['at_threshold'][str(p)]['relay_failures']} fail, "
                        f"{entry['at_threshold'][str(p)]['ms_mean']:.0f} ms" for p in SWEEP))

    # Generalization across noise strengths: train at one p, score at each p.
    report["cross_noise_auc"] = {}
    for i, p in enumerate(SWEEP):
        single = calibrate(train(F[where == i], y[where == i], kind="gbm", seed=args.seed), Fc, yc)
        report["cross_noise_auc"][f"trained at {p}"] = {
            str(q): quality(single, Fv[wv == j], yv[wv == j]).get("auc") for j, q in enumerate(SWEEP)}
    report["cross_noise_auc"]["trained at all"] = {
        str(q): report["models"]["gbm"]["validation"][str(q)].get("auc") for q in SWEEP}

    # Final choice among the learned full-feature models: feasible, then lowest mean time.
    learned = ["logistic", "gbm"]
    chosen = min(learned, key=lambda n: (not report["models"][n]["feasible"], report["models"][n]["objective_ms"]))
    model = fitted[chosen]
    model.meta |= {"name": chosen, "threshold": report["models"][chosen]["threshold"], "tier1": "fast", "tier2": args.tier2,
                   "feature_names": features.NAMES, "seed": args.seed}
    report["chosen"], report["threshold"], report["tier2"] = chosen, model.meta["threshold"], args.tier2
    MODELS.mkdir(exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS / "aegis_router.joblib")
    for name, other in fitted.items():
        joblib.dump(other, MODELS / ("candidate_" + name.replace(" ", "_").replace(":", "").replace(",", "") + ".joblib"))
    (REPORTS / "training.json").write_text(json.dumps(report, indent=1))
    print(f"chosen: {chosen}, threshold {model.meta['threshold']:.3e} -> models/aegis_router.joblib")


if __name__ == "__main__":
    main()
