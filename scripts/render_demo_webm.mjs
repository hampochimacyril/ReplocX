import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = 8877;
const output = path.join(root, "docs/demo/representative-location-explorer-demo.webm");
let server;

async function main() {
  server = spawn("python3", ["-m", "http.server", String(port), "--bind", "127.0.0.1"], {
    cwd: root,
    stdio: ["ignore", "pipe", "pipe"],
  });
  pipeLogs("http", server);
  await waitFor(`http://127.0.0.1:${port}/docs/demo/render_demo_video.html`);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1320, height: 820 } });
  page.setDefaultTimeout(90_000);
  await page.goto(`http://127.0.0.1:${port}/docs/demo/render_demo_video.html`, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.demoDone === true || window.demoError);

  const error = await page.evaluate(() => window.demoError ?? null);
  if (error) throw new Error(error);

  const parts = await page.evaluate(() => window.demoVideoBase64Parts ?? []);
  const buffers = parts.map((part) => {
    const encoded = String(part).split(",").pop();
    return Buffer.from(encoded, "base64");
  });
  await fs.writeFile(output, Buffer.concat(buffers));
  await browser.close();
  cleanup();
  console.log(`Wrote ${path.relative(root, output)}`);
}

async function waitFor(url) {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Server is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

function pipeLogs(name, child) {
  child.stderr.on("data", (chunk) => {
    const text = String(chunk).trim();
    if (text) console.error(`[${name}] ${text}`);
  });
}

function cleanup() {
  if (server && !server.killed) server.kill("SIGTERM");
}

process.on("exit", cleanup);
process.on("SIGINT", () => {
  cleanup();
  process.exit(130);
});
process.on("SIGTERM", () => {
  cleanup();
  process.exit(143);
});

main().catch((error) => {
  console.error(error);
  cleanup();
  process.exit(1);
});
