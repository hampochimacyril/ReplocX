import { expect, test } from "@playwright/test";

const SHOTS = "test-results/screenshots";
const atlasEnabled = /^(1|true|yes|on)$/i.test(process.env.RLE_ENABLE_ATLAS ?? "");

test.describe("Research Atlas gated modes", () => {
  test("disabled public-demo mode hides the private Atlas", async ({ page }) => {
    test.skip(atlasEnabled, "Disabled-mode check runs without RLE_ENABLE_ATLAS.");
    await page.goto("/atlas");
    await expect(page.getByRole("heading", { name: /not enabled here/i })).toBeVisible();
    await expect(page.getByText("RLE_ENABLE_ATLAS=1")).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/atlas-disabled-public-demo.png` });
  });

  test("enabled private mode renders A/C/B/D story spine and responsive screenshots", async ({ page }) => {
    test.skip(!atlasEnabled, "Enabled-mode check runs with RLE_ENABLE_ATLAS=1.");

    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/atlas");
    await expect(page.getByRole("heading", { name: "National pivot" })).toBeVisible();
    await expect(page.getByText("SELECTION DEMO")).toBeVisible();
    await expect(page.getByText("ATLAS CERTIFIED", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "AC 2-8pm + NV other hours (C)" })).toBeVisible();
    await expect(page.getByRole("button", { name: "No AC or NV (D)" })).toBeVisible();
    await expect(page.getByRole("img", { name: /Fig02 source values/i })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/atlas-enabled-desktop-overview.png`, fullPage: true });

    await page.setViewportSize({ width: 900, height: 1100 });
    await page.goto("/atlas/results");
    await expect(page.getByRole("heading", { name: "Results A/C/B/D" })).toBeVisible();
    await expect(page.getByRole("button", { name: ">28 C" })).toBeVisible();
    await expect(page.getByText(/Overheating exposure hours/).first()).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/atlas-enabled-tablet-results.png`, fullPage: true });

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
