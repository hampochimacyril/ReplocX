import { defineConfig, devices } from "@playwright/test";

const e2ePort = process.env.RLE_E2E_PORT ?? "8791";
const baseURL = `http://127.0.0.1:${e2ePort}`;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000
  },
  fullyParallel: false,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure"
  },
  webServer: {
    // Serves the built frontend/dist via the dependency-free stdlib server.
    // Run `npm run build` (or scripts/verify_all.sh) first so dist exists.
    command: `python3 -m backend.server --host 127.0.0.1 --port ${e2ePort}`,
    url: `${baseURL}/api/health`,
    reuseExistingServer: true,
    timeout: 30_000
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
