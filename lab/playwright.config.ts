import { defineConfig } from "@playwright/test";
import os from "node:os";
import path from "node:path";

// Runs against a production build (`next start`) on its own port. The lab's backends (:8765 QEC-Aegis,
// :8000 MidQwest FastAPI) must already be running. For the parity suite, the two LEGACY dashboards are
// started here from the same code on their own ports (8766, 8001) in their default (page-serving) mode.
const PORT = Number(process.env.LAB_E2E_PORT ?? 3101);
const MIDQWEST = process.env.MIDQWEST_DIR ?? path.join(os.homedir(), "MidQwest");
export const LEGACY_AEGIS = "http://127.0.0.1:8766";
export const LEGACY_SIM = "http://127.0.0.1:8001";
export default defineConfig({
  testDir: "e2e",
  timeout: 180_000,
  expect: { timeout: 60_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: `http://127.0.0.1:${PORT}`, channel: "chrome", headless: true, viewport: { width: 1440, height: 1000 } },
  webServer: [
    { command: `npx next start -H 127.0.0.1 -p ${PORT}`, url: `http://127.0.0.1:${PORT}/`, reuseExistingServer: true, timeout: 120_000 },
    { command: `cd .. && OMP_NUM_THREADS=1 .venv/bin/python dashboard/server.py --port 8766 --no-browser`, url: `${LEGACY_AEGIS}/api/status`, reuseExistingServer: true, timeout: 120_000 },
    { command: `cd ${MIDQWEST} && .venv/bin/python dashboard/serve.py --port 8001 --no-browser`, url: `${LEGACY_SIM}/api/health`, reuseExistingServer: true, timeout: 120_000 },
  ],
});
