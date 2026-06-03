import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000
  },
  fullyParallel: false,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:8787",
    trace: "on-first-retry",
    screenshot: "only-on-failure"
  },
  webServer: {
    command: "python3 -m backend.server --host 127.0.0.1 --port 8787",
    url: "http://127.0.0.1:8787/api/health",
    reuseExistingServer: true,
    timeout: 20_000
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});

