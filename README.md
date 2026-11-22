# QEC Lab: QEC-Aegis and the Error Correction Research Laboratory

ML-assisted decoding of IBM's `[[144,12,12]]` Gross code, built for MidQWest 2026 (Infleqtion Challenge 1:
ML-assisted QEC decoding), together with a local, interactive laboratory that runs from single-qubit physics up to
the decoder itself.

Everything runs on one laptop, offline. Nothing in this repository submits work to quantum hardware.

## QEC-Aegis

A learned router in front of relay-BP:

1. A fast early-stopping relay-BP decodes every shot.
2. A gradient-boosted risk model reads features of that decode and predicts whether its answer is wrong.
3. Only risky or unconverged shots are escalated to full relay-BP.

The model, its threshold and the tier pair were chosen on validation data and frozen before any test shot was
decoded with them. Their hashes are in [experiments/reports/frozen_models.json](experiments/reports/frozen_models.json).
QEC-Aegis is compared against BP-OSD, relay-BP, early-stop relay-BP, a no-ML rule, a hand-picked heuristic, and an
oracle router that knows the true answer (an unattainable bound).

The frozen-test evaluation covers physical error rates p = 0.003, 0.004 and 0.005 (X and Z), erasure fractions
f = 0.25, 0.5 and 0.75, and a single-worker latency benchmark. Final tables are generated into
[docs/RESULTS.md](docs/RESULTS.md) by `python -m aegis.report`. No result is typed by hand.

## Quick start

Requires Python 3.12 and Node.js.

```bash
make setup        # create .venv from requirements.lock, run diagnostics and tests
make dev          # start the research lab at http://127.0.0.1:3100/  (make dev-stop to stop)
make test         # Python test suite (about 2 minutes)
```

Reproducing the evaluation:

```bash
make data             # decode training, calibration and validation shots (~2.5 h on 8 cores, resumable)
make train            # train, calibrate and select the risk model (~2 min)
make evaluate-frozen  # frozen test records, online run, timing, evaluate, figures (hours, resumable)
make evaluate         # recompute all tables from cached records (seconds)
make figures          # redraw docs/figures from the stored evaluation
```

Run `make help` for the full list.

## The research laboratory

Eight modules, served by a Next.js app on port 3100:

| # | Page | Content |
|---|---|---|
| 1 | `/foundations` | Qubit states, Bloch sphere, Pauli operators, measurement, Bell states, noise channels |
| 2 | `/error-correction` | Repetition code, stabilizers, syndromes, distance, logical operators |
| 3 | `/surface-code` | Rotated surface code at d = 3 and 5, space-time detectors, minimum-weight matching |
| 4 | `/gross-code` | Bivariate bicycle construction, check matrices, GF(2) ranks, Tanner graph, memory circuit |
| 5 | `/decoders` | BP, BP-OSD, relay-BP and the QEC-Aegis router, with the design studies |
| 6 | `/experiments` | Bounded live simulations on the real backends |
| 7 | `/results` | Frozen-test evaluation: LER per cycle with 95% intervals, paired comparisons, latency, erasure |
| 8 | `/hardware` | Read-only IBM Quantum account status and an archived, checksum-verified hardware job |

Every number on screen is labelled with its source: exact theory, live simulation, stored measurement, published
reference, IBM account check, or archived hardware.

| Service | Port | Code |
|---|---|---|
| Research lab (Next.js) | 3100 | [lab/](lab/) |
| QEC-Aegis API | 8765 | [dashboard/](dashboard/) |
| Simulation API (FastAPI) | 8000 | companion repository |

## Repository layout

| Path | Contents |
|---|---|
| [aegis/](aegis/) | Decoder tiers, features, risk model, routing policy, training, evaluation, figures, report |
| [dashboard/](dashboard/) | QEC-Aegis API used by the lab |
| [lab/](lab/) | Research laboratory frontend |
| [experiments/](experiments/) | Experiment manifest, decoded shot records, evaluation reports |
| [models/](models/) | Frozen router models |
| [scripts/](scripts/) | Environment setup, experiment runners, dev server control |
| [tests/](tests/) | Python tests, including independent checks of the Gross code |
| [challenge-1-ml-decoder-kit/](challenge-1-ml-decoder-kit/) | The challenge's baseline decoder kit |
| [docs/](docs/) | Architecture, results, setup, demo runbook, IBM connection notes |

## Documents

- [ERROR_CORRECTION_RESEARCH_LABORATORY.md](ERROR_CORRECTION_RESEARCH_LABORATORY.md): laboratory overview and status
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how the pieces fit together
- [docs/RESULTS.md](docs/RESULTS.md): generated results tables
- [docs/SETUP.md](docs/SETUP.md): environment setup
- [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md): setup checklist and the three-minute demonstration
- [docs/IBM_CONNECTION_STATUS.md](docs/IBM_CONNECTION_STATUS.md): read-only IBM check and its safety design
- [docs/CHALLENGE.md](docs/CHALLENGE.md): the original Infleqtion challenge statement
