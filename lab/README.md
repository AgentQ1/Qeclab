# QEC Research Laboratory (frontend)

A Next.js + TypeScript + Tailwind interface that teaches quantum error correction from first principles
up to decoding the [[144,12,12]] Gross code. It has **no simulation code of its own**: every
scientific value comes from one of two existing local backends, or from closed-form mathematics
evaluated in the browser, and every value is labeled with where it came from.

| Port | Service | Repository | What it computes |
|---|---|---|---|
| 3100 | this lab (`next start`) | MidQWest-2026/lab | exact theory, illustrations, the UI |
| 8765 | QEC-Aegis server (stdlib `http.server`) | MidQWest-2026 `dashboard/server.py` | Gross-code circuits (Stim), BP-OSD (ldpc), relay-BP, QEC-Aegis router, stored records |
| 8000 | MidQwest FastAPI server | MidQwest `dashboard/server.py` | repetition and surface codes d = 3, 5 (Stim, Qiskit Aer, PyMatching), the ibm_kingston archive |

The browser only ever talks to the lab. `next.config.ts` proxies `/api/aegis/*` to :8765 and
`/api/sim/*` to :8000 (override with `AEGIS_API` and `SIM_API`). Neither backend has a path to
IBM Quantum hardware.

## Run

```bash
# backends (each in its own terminal)
.venv/bin/python dashboard/server.py --port 8765 --no-browser                  # in MidQWest-2026
.venv/bin/python dashboard/serve.py --port 8000 --no-browser                   # in MidQwest

# lab
cd lab && npm ci && npm run build && npm start                                  # http://127.0.0.1:3100
```

## Modules

| # | Route | Source of its numbers |
|---|---|---|
| 1 | `/foundations` | exact state-vector and Bloch-vector algebra (`lib/quantum.ts`) |
| 2 | `/error-correction` | exact parity algebra; `POST /api/sim/simulate/injection` (Aer + PyMatching) |
| 3 | `/surface-code` | `/api/sim/circuit`, `/simulate/injection`, `/matching-graph`, `/decode-syndrome`, `/reference` |
| 4 | `/gross-code` | `/api/aegis/gross/structure` (computed from the kit's `make_circuit.py`), `/api/aegis/decode` |
| 5 | `/decoders` | in-browser BP / OSD-0 / relay illustration (`lib/bp.ts`, labeled); live `/api/aegis/decode` |
| 6 | `/experiments` | `/api/aegis/decode`, `/api/sim/simulate/rates`, `/api/sim/simulate/compare` |
| 7 | `/results` | `/api/aegis/records` (per-shot records → `aegis.policy.summarize`), `/training`, `/calibration`, `/manifest`, `/reference` |
| 8 | `/hardware` | `/api/sim/hardware` (checksums recomputed, archive re-decoded; read-only) |

## Tests

```bash
npx tsc --noEmit        # types
npx vitest run          # exact-math libraries against known results (Born rule, Bell stabilizers, binomial sums, Wilson = aegis.policy.wilson, GF(2), BP/OSD)
npx playwright test     # browser E2E on a production build: each test captures the real API response and checks the page shows the same values
```

The E2E suite needs both backends running and uses the installed Chrome (`channel: "chrome"`).
