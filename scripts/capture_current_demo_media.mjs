import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const nodeBin = process.execPath;
const backendPort = 8787;
const frontendPort = 5173;
const backendUrl = `http://127.0.0.1:${backendPort}`;
const frontendUrl = `http://127.0.0.1:${frontendPort}`;
const sceneDir = path.join(root, "docs/demo/scenes");
const screenshotDir = path.join(root, "docs/screenshots");

const children = [];

async function main() {
  await startServers();

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1425, height: 900 }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(20_000);

  await capture(page, "/", "01-overview.png");
  await captureZip(page);
  await capture(page, "/scenario", "03-scenario-builder.png");
  await capture(page, "/catchments", "04-candidate-ranking.png");
  await capture(page, "/compare", "05-allocation-comparison.png");
  await capture(page, "/methodology", "06-methodology.png");

  await browser.close();

  await copyScene("01-overview.png", "overview.png");
  await copyScene("02-zip-explorer.png", "zip-explorer.png");
  await copyScene("03-scenario-builder.png", "scenario-builder.png");
  cleanup();
}

async function captureZip(page) {
  await page.goto(frontendUrl, { waitUntil: "domcontentloaded" });
  await waitForApp(page);
  const search = page.getByRole("searchbox", { name: "Search ZIP, catchment, or station" });
  await search.fill("19104");
  await search.press("Enter");
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(sceneDir, "02-zip-explorer.png"), animations: "disabled" });
}

async function capture(page, route, filename) {
  await page.goto(`${frontendUrl}${route}`, { waitUntil: "domcontentloaded" });
  await waitForApp(page);
  await page.waitForTimeout(900);
  await page.screenshot({ path: path.join(sceneDir, filename), animations: "disabled" });
}

async function waitForApp(page) {
  await page.waitForSelector(".app");
  await page.waitForLoadState("networkidle");
}

async function copyScene(sceneName, screenshotName) {
  await fs.copyFile(path.join(sceneDir, sceneName), path.join(screenshotDir, screenshotName));
}

async function startServers() {
  const backend = spawn("python3", ["-m", "backend.server", "--host", "127.0.0.1", "--port", String(backendPort)], {
    cwd: root,
    stdio: ["ignore", "pipe", "pipe"],
  });
  children.push(backend);
  pipeLogs("backend", backend);
  await waitFor(`${backendUrl}/api/v1/health`);

  const vite = spawn(nodeBin, ["node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--port", String(frontendPort)], {
    cwd: path.join(root, "frontend"),
    stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, BROWSER: "none" },
  });
  children.push(vite);
  pipeLogs("vite", vite);
  await waitFor(frontendUrl);
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
  child.stdout.on("data", (chunk) => {
    const text = String(chunk).trim();
    if (text) console.log(`[${name}] ${text}`);
  });
  child.stderr.on("data", (chunk) => {
    const text = String(chunk).trim();
    if (text) console.error(`[${name}] ${text}`);
  });
  child.on("exit", (code, signal) => {
    if (code && code !== 0) console.error(`[${name}] exited with code ${code}${signal ? ` (${signal})` : ""}`);
  });
}

function cleanup() {
  for (const child of children.reverse()) {
    if (!child.killed) child.kill("SIGTERM");
  }
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
