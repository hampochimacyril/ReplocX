import { expect, test } from "@playwright/test";

const SHOTS = "test-results/screenshots";

test.describe("ReplocX Session 8 workflows", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
  });

  test("candidate ranking: sort, compare, column visibility, CSV export", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Catchments" }).click();

    await expect(page.getByRole("heading", { name: "Candidate ranking" })).toBeVisible();
    const tableRegion = page.getByRole("region", { name: "Candidate ranking table" });
    await expect(tableRegion).toBeVisible();
    await expect(page.getByText(/of 2,959 candidates · sorted by/)).toBeVisible();

    // Sorting: activating a column header sets its aria-sort.
    const distanceHeader = page.getByRole("button", { name: /Station dist\./ });
    await distanceHeader.click();
    const th = page.locator("th", { has: distanceHeader });
    await expect(th).toHaveAttribute("aria-sort", /ascending|descending/);

    // Comparison selection from the table feeds the compare tray.
    await page.locator(".dtable tbody tr").first().getByRole("checkbox").check();
    await expect(page.getByText(/1\/4 to compare/)).toBeVisible();

    // Column visibility.
    await page.getByRole("button", { name: "Columns" }).click();
    await expect(page.getByRole("menu", { name: "Toggle columns" })).toBeVisible();

    // CSV export triggers a download with a scoped filename.
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("button", { name: "Export CSV" }).click(),
    ]);
    expect(download.suggestedFilename()).toMatch(/replocx_ranking_.*\.csv/);

    await page.screenshot({ path: `${SHOTS}/desktop-catchments-table.png` });
  });

  test("scenario workbench: validate weights, normalize, preview, apply", async ({ page }) => {
    await page.goto("/scenario");
    await expect(page.getByRole("heading", { name: "Scenario workbench" })).toBeVisible();

    const housing = page.getByLabel("Housing-unit coverage weight");
    await housing.fill("0.9");
    const apply = page.getByRole("button", { name: /Apply to workspace/ });
    await expect(apply).toBeDisabled();
    await expect(page.getByText("1.45", { exact: true })).toBeVisible();

    await page.getByRole("button", { name: /Normalize to 1.00/ }).click();
    await expect(page.getByText("1.00", { exact: true })).toBeVisible();
    await expect(apply).toBeEnabled();

    // Live preview keeps the 20-strata coverage invariant visible.
    await expect(page.getByText("Live preview vs. baseline")).toBeVisible();
    await expect(page.getByText("20 / 20")).toBeVisible();

    await apply.click();
    await expect(page.getByText(/Custom scenario · unsaved/)).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/desktop-scenario-workbench.png` });
  });

  test("scenario save creates a versioned, shareable scenario", async ({ page }) => {
    await page.goto("/scenario");
    await expect(page.getByRole("heading", { name: "Scenario workbench" })).toBeVisible();
    await page.getByLabel("Scenario name").fill("E2E density scenario");
    await page.getByRole("button", { name: /Save scenario/ }).click();
    await expect(page.getByText(/Saved as/)).toBeVisible();
    await expect(page.getByText(/version 1/)).toBeVisible();
    // The saved scenario appears in the version history list.
    await expect(page.getByText("Saved scenarios & versions")).toBeVisible();
    await expect(page.getByText("E2E density scenario").first()).toBeVisible();
  });

  test("compare: allocation deltas and candidate matrix", async ({ page }) => {
    // Seed the comparison tray from the ranking table.
    await page.goto("/catchments");
    await expect(page.getByRole("heading", { name: "Candidate ranking" })).toBeVisible();
    await page.locator(".dtable tbody tr").first().getByRole("checkbox").check();

    await page.getByRole("link", { name: "Compare" }).click();
    await expect(page.getByRole("heading", { name: "Compare" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Allocation summary" })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Per-stratum representatives/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Candidate comparison/ })).toBeVisible();
    // The seeded candidate is present in the comparison matrix.
    await expect(page.getByText(/1 selected/)).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/desktop-compare.png` });
  });

  test("methodology surfaces validation status and data lineage", async ({ page }) => {
    await page.goto("/methodology");
    await expect(page.getByRole("heading", { name: "Methodology & data" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Validation status" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Data lineage" })).toBeVisible();
    await expect(page.getByText("20 strata resolved")).toBeVisible();
    await expect(page.getByText(/Score weights sum to 1.0/)).toBeVisible();
  });
});
