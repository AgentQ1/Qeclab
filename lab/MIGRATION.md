# Migration of the legacy dashboards into the research lab

The research lab (`http://127.0.0.1:3100`) replaces two legacy pages:

- the QEC-Aegis page served by `dashboard/server.py` on :8765 (this repository)
- the MidQwest page served by `dashboard/serve.py` on :8000 (the MidQwest repository)

Both backends keep every API route. With `--api-only` (the default under `make dev`), their `/`
redirects to the lab. The legacy pages are still in the source and come back without the flag:
`make legacy-demo`, or `dashboard/serve.py` in MidQwest. Rolling back means dropping `--api-only`.

## How parity was verified

`lab/e2e/parity.spec.ts` starts both legacy pages from the same code on their own ports (8766, 8001).
For each feature, the legacy page makes a request, the lab replays the same request (same seed), and
the test asserts that the responses are identical and that both pages display the same values.
`lab/e2e/migration.spec.ts` holds a regression test for every migrated feature, and `lab/e2e/lab.spec.ts`
checks every module against its API responses. The pytest suites of both backends cover the new
endpoints (`tests/test_dashboard.py` here, `tests/test_dashboard_api.py` in MidQwest).

## Feature-parity matrix

| Legacy page | Feature | Where in the lab | Verified by | Status |
|---|---|---|---|---|
| :8000 | Experiment choice: code, distance, basis, rounds | Modules 2, 3 | lab.spec M2/M3, parity 1 | PASS |
| :8000 | Inject a known X/Y/Z error on a chosen data qubit and time, run on Aer, decode with PyMatching | Module 2 (repetition), Module 3 (surface) | parity 1 (identical response, same displayed values) | PASS |
| :8000 | Lattice with the checks that fired | Module 3 | lab.spec M3, migration P2 | PASS |
| :8000 | Circuit diagram with the injected error and the fired measurements | Modules 2, 3 (`components/Circuit.tsx`) | parity 1 (identical drawing, error count), migration P2 (column and row of the error, fired-gate count) | PASS |
| :8000 | Circuit size as written and compiled for IBM heavy-hex, routing overhead | Modules 2, 3 (labeled as a local estimate, not an execution) | parity 1 (depth, two-qubit gates, overhead), migration P2 | PASS |
| :8000 | Syndrome by round | Module 2 grid, Module 3 space-time record | lab.spec M2/M3 | PASS |
| :8000 | Result details: fired detectors, errors before and after decoding, Stim cross-check, first-shot raw bits, run id, seed, timing | Modules 2, 3 | parity 1, lab.spec M2 | PASS |
| :8000 | Logical-error-rate sweep: noise model, p range, points, shots, chart and table | Module 6 (B) | lab.spec M6 (every table row equals the response) | PASS |
| :8000 | Stored 2,000,000-shot validation study | Module 3, Fig. 3.1 | lab.spec (renders from /api/reference) | PASS |
| :8000 | Aer against Stim comparison | Module 6 (C) | lab.spec M6 | PASS |
| :8000 | IBM hardware archive: job, checksums, re-decode, tiles, detector rates, records, calibration | Module 8 (adds the SHA-256 values) | parity 4, lab.spec M8 | PASS |
| :8000 | Backend status and versions | sidebar | lab.spec | PASS |
| :8765 | One memory experiment: basis, p, erasure fraction, seed, baselines, next seed | Module 6 (A), Module 5 | parity 2 (identical shot, predictions, iterations, outcomes) | PASS |
| :8765 | Syndrome raster with heralds per round | Module 6 (A), Module 4 overlay | lab.spec M6, M4 | PASS |
| :8765 | Decoder comparison table | Module 6 (A), Module 5 | parity 2 | PASS |
| :8765 | Router decision: path, risk against threshold | Module 5 (risk bar, route, threshold, fallback rule) | parity 2, migration P1 | PASS |
| :8765 | Every feature the risk model read | Module 5, grouped as the model sees them | parity 2 (same count, same values), migration P1 | PASS |
| :8765 | Decoder study: BP-OSD against relay-BP shot by shot | Module 5, Fig. 5.1 | parity 3, migration P1 | PASS |
| :8765 | Tiers, routing rules and perfect-router bounds (legacy showed a subset; the lab shows all) | Module 5, Fig. 5.2 | parity 3, migration P1 | PASS |
| :8765 | Rejected learned predecoder | Module 5, Fig. 5.4 (with the methodology from `aegis/predecoder.py`) | parity 3, migration P1 | PASS |
| :8765 | Frozen-test evaluation tables (sweep, latency, erasure) | Module 7, section 7.0 (pending / running / failed / partial / completed) | migration P0 (all five states; the completed view against a schema-identical fixture) | PASS (feature) |
| :8765 | Final figures from `docs/figures` | Module 7, section 7.0 gallery (proxied from :8765) | code path only: no figure exists yet | PASS (feature), untested with real images |
| :8765 | Starter-kit reference results | Module 7, Fig. 7.1 (hollow reference points, data table) | lab.spec | PASS |
| :8765 | "How it works" schematic | Module 5 (equations 5.1–5.8 and the routing description) | — | PASS |

New in the lab, with no legacy counterpart: router model ranking and chosen thresholds (Fig. 5.3), the
architecture rationale with quoted numbers, live pipeline progress for the frozen evaluation, the
Gross-code Tanner graph and DEM, MWPM visualization, and Modules 1–2.

## Remaining gaps

| Gap | Why | What closes it |
|---|---|---|
| **No frozen-test results exist yet** | The test-set pipeline stopped at `test_Z_p0.004` (87 of 200 chunks). The erasure router is not trained, and the online, timing and evaluate steps have never run. | `make evaluate-frozen` (several hours, resumable). The lab shows its progress and switches to the final view only when `aegis.evaluate` covers every setting. |
| Final-figure gallery not exercised with real images | `aegis.figures` has not run (it needs the evaluation) | Same pipeline: its `figures` step |
| Legacy-mode parity tests start extra servers on 8766 and 8001 | They need the legacy pages, which the default startup no longer serves | Nothing: Playwright starts them automatically |
