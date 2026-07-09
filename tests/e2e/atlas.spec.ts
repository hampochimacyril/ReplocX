import { expect, test } from "@playwright/test";
import { mkdirSync } from "node:fs";

const SHOTS = "test-results/screenshots";
const N3_SHOTS = "docs/atlas/screenshots/2026-07-08-n3";
const atlasEnabled = /^(1|true|yes|on)$/i.test(process.env.RLE_ENABLE_ATLAS ?? "");

mkdirSync(N3_SHOTS, { recursive: true });

test.describe("Research Atlas gated modes", () => {
  test("disabled public-demo mode hides the private Atlas", async ({ page }) => {
    test.skip(atlasEnabled, "Disabled-mode check runs without RLE_ENABLE_ATLAS.");
    await page.goto("/atlas");
    await expect(page.getByRole("heading", { name: /not enabled here/i })).toBeVisible();
    await expect(page.getByText("RLE_ENABLE_ATLAS=1")).toBeVisible();
    const privateApi = await page.request.get("/api/v1/results/by-stratum?dimension=stratum");
    expect(privateApi.status()).toBe(404);
    await page.screenshot({ path: `${SHOTS}/atlas-disabled-public-demo.png` });
  });

  test("enabled private mode renders A/C/B/D story spine and responsive screenshots", async ({ page }) => {
    test.skip(!atlasEnabled, "Enabled-mode check runs with RLE_ENABLE_ATLAS=1.");

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/atlas?dimension=stratum&tier=annual&scenario=D");
    await expect(page.getByRole("heading", { name: "20-stratum reviewer path" })).toBeVisible();
    await expect(page.getByText("SELECTION DEMO")).toBeVisible();
    await expect(page.getByText("ATLAS CERTIFIED", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "AC 2-8pm + NV other hours (C)" })).toBeVisible();
    await expect(page.getByRole("button", { name: "No AC or NV (D)" })).toBeVisible();
    await expect(page.getByText("20 climate × urbanicity strata")).toBeVisible();
    await expect(page.getByText("Cold & Very Cold · HDU")).toBeVisible();
    await expect(page.getByText("Mixed-Humid · Suburban")).toBeVisible();
    await expect(page.getByRole("img", { name: /Fig02 source values/i })).toBeVisible();
    await page.screenshot({ path: `${N3_SHOTS}/atlas-n3-20-strata.png`, fullPage: true });

    const firstSite = page.locator(".atlas-pivot-table tbody a").first();
    await expect(firstSite).toBeVisible();
    await firstSite.click();
    await expect(page.getByLabel("Reviewer drill path")).toBeVisible();
    await page.screenshot({ path: `${N3_SHOTS}/atlas-n3-site-drill.png`, fullPage: true });
    await page.getByRole("button", { name: "Close details" }).click();
    await page.getByRole("link", { name: "Back to 20-stratum pivot" }).click();

    await page.getByRole("button", { name: /Urbanicity/ }).click();
    await expect(page.getByText("4 urbanicity groups")).toBeVisible();
    await page.screenshot({ path: `${N3_SHOTS}/atlas-n3-urbanicity-pivot.png`, fullPage: true });

    await page.setViewportSize({ width: 900, height: 1100 });
    await page.goto("/atlas/results?dimension=stratum&tier=annual&scenario=D");
    await expect(page.getByRole("heading", { name: "Results A/C/B/D" })).toBeVisible();
    await expect(page.getByRole("button", { name: ">28 C" })).toBeVisible();
    await expect(page.getByText(/Overheating exposure hours/).first()).toBeVisible();
    await expect(page.getByText("20 of 20")).toBeVisible();
    await page.screenshot({ path: `${N3_SHOTS}/atlas-n3-results-strata.png`, fullPage: true });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/atlas/sealed-passive");
    await expect(page.getByRole("heading", { name: "Sealed-passive D contrasts" })).toBeVisible();
    await expect(page.getByRole("tab", { name: /D-B/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /D-C/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /D-A/ })).toBeVisible();
    const mobileDChart = page.getByRole("img", { name: /D-B overheating exposure-hour reduction by climate/i });
    await mobileDChart.scrollIntoViewIfNeeded();
    await expect(mobileDChart).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/atlas-enabled-mobile-d-contrasts.png`, fullPage: true });

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/atlas/equity");
    await expect(page.getByRole("heading", { name: "Equity context" })).toBeVisible();
    await expect(page.getByText(/verified sidecar-backed equity profile/i)).toBeVisible();
    await expect(page.getByText("Equity frame — 20 catchments")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/atlas-w4-equity-ready.png`, fullPage: true });

    await page.goto("/atlas/exports");
    await expect(page.getByRole("heading", { name: "Exports/provenance" })).toBeVisible();
    await expect(page.getByText("f2v3_final").first()).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/atlas-w4-exports-provenance.png`, fullPage: true });
  });
});
