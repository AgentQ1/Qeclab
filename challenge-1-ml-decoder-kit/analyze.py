"""Turn cached run_job.py results into the comparison table and plots. Runs in seconds.

  python analyze.py --dir results

File names it expects (from run_job.py):
  train_{X,Z}_p{p}.npz        decoders: bp                 (seed 1)  router training data
  test_{X,Z}_p{p}.npz         decoders: bp relay [bposd]   (seed 2)  required sweep
  erase_{X,Z}_p{p}_f{f}.npz   decoders: bposd bposd_flags  (seed 2)  erasure experiment

Hybrid decoders are computed from the cache, shot by shot:
  hybrid_rule  run fast BP; if it converged keep its answer, else run relay-BP (time = BP + relay)
  hybrid_ml    the router reads the alarms first; "easy" shots follow hybrid_rule,
               "hard" shots go straight to relay-BP (time = router + relay)
A shot pair (X shot k, Z shot k) fails if either fails; its time is the sum of the two.
"""
import argparse
import csv
import glob
import os
import re
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from decoders import per_cycle_rate

CYCLES = 12


def load(path):
    return dict(np.load(path))


def features(d):
    return np.column_stack([d["round_weights"], d["round_weights"].sum(1), d["n_flags"]])


def train_router(dirname, p):
    files = [f"{dirname}/train_{b}_p{p}.npz" for b in "XZ"]
    if not all(os.path.exists(f) for f in files):
        return None
    data = [load(f) for f in files]
    X = np.vstack([features(d) for d in data])
    y = np.concatenate([d["conv_bp"] for d in data])
    return HistGradientBoostingClassifier(max_iter=200).fit(X, y)


def policies(d, router):
    """(fail, time) per shot for each decoder and hybrid available in one test file."""
    out = {n: (d[f"fail_{n}"], d[f"time_{n}"]) for n in ("relay", "bposd", "bp", "bposd_flags") if f"fail_{n}" in d}
    if "fail_bp" in d and "fail_relay" in d:
        conv = d["conv_bp"]
        rule_fail = np.where(conv, d["fail_bp"], d["fail_relay"])
        rule_time = d["time_bp"] + np.where(conv, 0, d["time_relay"])
        out["hybrid_rule"] = (rule_fail, rule_time)
        if router is not None:
            X = features(d)
            t = time.perf_counter()
            easy = router.predict(X).astype(bool)
            per_shot = (time.perf_counter() - t) / len(X)
            out["hybrid_ml"] = (np.where(easy, rule_fail, d["fail_relay"]),
                                per_shot + np.where(easy, rule_time, d["time_relay"]))
            out["_router_acc"] = (easy == conv).mean()
            out["_baseline_acc"] = max(conv.mean(), 1 - conv.mean())
            out["_escalated_ml"] = (~easy | ~conv).mean()
        out["_escalated_rule"] = (~conv).mean()
    return out


def paired(px, pz, name):
    fx, tx = px[name]
    fz, tz = pz[name]
    rate, err = per_cycle_rate(fx | fz, CYCLES)
    ms = (tx + tz) * 1e3
    return rate, err, ms.mean(), np.percentile(ms, 99)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dir", default="results")
    args = a.parse_args()
    rows = []
    ps = sorted({re.search(r"_p([\d.]+)\.npz", f).group(1) for f in glob.glob(f"{args.dir}/test_X_p*.npz")})
    for p in ps:
        router = train_router(args.dir, p)
        px = policies(load(f"{args.dir}/test_X_p{p}.npz"), router)
        pz = policies(load(f"{args.dir}/test_Z_p{p}.npz"), router)
        for name in [n for n in px if not n.startswith("_") and n in pz]:
            rate, err, mean_ms, p99 = paired(px, pz, name)
            esc = {"hybrid_rule": px.get("_escalated_rule"), "hybrid_ml": px.get("_escalated_ml")}.get(name)
            rows.append({"experiment": "sweep", "p": p, "f": 0, "decoder": name, "rate_per_cycle": rate,
                         "err": err, "mean_ms": mean_ms, "p99_ms": p99, "escalated_X": esc})
        if "_router_acc" in px:
            print(f"p={p} router accuracy {px['_router_acc']:.3f} vs always-guess-majority {px['_baseline_acc']:.3f}")
    for fx in sorted(glob.glob(f"{args.dir}/erase_X_p*_f*.npz")):
        p, f = re.search(r"_p([\d.]+)_f([\d.]+)\.npz", fx).groups()
        fz = fx.replace("erase_X", "erase_Z")
        if not os.path.exists(fz):
            continue
        px, pz = policies(load(fx), None), policies(load(fz), None)
        for name in [n for n in px if not n.startswith("_") and n in pz]:
            rate, err, mean_ms, p99 = paired(px, pz, name)
            rows.append({"experiment": "erasure", "p": p, "f": f, "decoder": name, "rate_per_cycle": rate,
                         "err": err, "mean_ms": mean_ms, "p99_ms": p99, "escalated_X": None})
    if not rows:
        print("no result files found")
        return
    with open(f"{args.dir}/results.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        esc = "" if r["escalated_X"] is None else f"  escalated {r['escalated_X']:.0%}"
        print(f"{r['experiment']:8s} p={r['p']} f={r['f']}  {r['decoder']:12s} rate {r['rate_per_cycle']:.2e} "
              f"+- {r['err']:.1e}  mean {r['mean_ms']:.0f} ms  p99 {r['p99_ms']:.0f} ms{esc}")
    plot(rows, args.dir)


def plot(rows, dirname):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    sweep = [r for r in rows if r["experiment"] == "sweep"]
    for name in sorted({r["decoder"] for r in sweep}):
        rs = sorted([r for r in sweep if r["decoder"] == name], key=lambda r: float(r["p"]))
        x = [float(r["p"]) for r in rs]
        ax[0].errorbar(x, [r["rate_per_cycle"] for r in rs], [r["err"] for r in rs], marker="o", label=name)
        ax[1].plot(x, [r["mean_ms"] for r in rs], marker="o", label=f"{name} mean")
        ax[1].plot(x, [r["p99_ms"] for r in rs], ls="--", marker="x", label=f"{name} p99")
    ax[0].set(xlabel="physical error rate p", ylabel="logical error rate per cycle", yscale="log", title="Accuracy")
    ax[1].set(xlabel="physical error rate p", ylabel="decode time per shot pair (ms)", yscale="log", title="Speed")
    erase = [r for r in rows if r["experiment"] == "erasure"]
    for name in sorted({r["decoder"] for r in erase}):
        rs = sorted([r for r in erase if r["decoder"] == name], key=lambda r: float(r["f"]))
        ax[2].errorbar([float(r["f"]) for r in rs], [r["rate_per_cycle"] for r in rs], [r["err"] for r in rs],
                       marker="o", label=name)
    ax[2].set(xlabel="fraction of noise converted to flagged erasure", ylabel="logical error rate per cycle",
              yscale="log", title="Using erasure flags")
    for x in ax:
        x.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(f"{dirname}/results.png", dpi=150)
    print(f"saved {dirname}/results.csv and {dirname}/results.png")


if __name__ == "__main__":
    main()
