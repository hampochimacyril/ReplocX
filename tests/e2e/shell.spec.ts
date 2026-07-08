import { expect, test } from "@playwright/test";

const SHOTS = "test-results/screenshots";

test.describe("ReplocX map-first workspace (Session 7)", () => {
  test("map workspace renders the map-dominant layout on desktop", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    // Top bar: brand, type-aware search, data-mode badge, scenario chip.
    await expect(page.getByText("ReplocX")).toBeVisible();
    await expect(page.getByRole("search")).toBeVisible();
    await expect(page.getByText("DEMO")).toBeVisible();
    await expect(page.getByText(/Baseline · saved/)).toBeVisible();

    // Icon nav rail with the five primary contexts.
    await expect(page.getByRole("link", { name: "Map workspace" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Methodology & data" })).toBeVisible();

    // Persistent filter/scenario panel.
    await expect(page.getByRole("complementary", { name: /Filters and scenario/i })).toBeVisible();

    // Map dominance: the map container occupies the majority of the viewport width.
    const map = page.locator(".mapwrap");
    await expect(map).toBeVisible();
    const box = await map.boundingBox();
    expect(box!.width).toBeGreaterThan(1440 * 0.5);

    // Map overlays: legend bound to the active layer, layer controls.
    await expect(page.getByLabel("Legend: climate regions").getByText("Climate region", { exact: true })).toBeVisible();
    const layers = page.getByRole("group", { name: "Map layers and symbology" });
    await expect(layers).toBeVisible();
    await expect(layers.getByText("Candidate centroids")).toBeVisible();
    await expect(layers.getByText("Weather stations")).toBeVisible();
    await expect(layers.getByText("Station links")).toBeVisible();
    await expect(page.getByText(/2,959 matching · 20 selected/)).toBeVisible();

    // Coordinated bottom strip: 5×4 coverage matrix + a distribution chart.
    await expect(page.getByRole("table", { name: /Stratum coverage matrix/i })).toBeVisible();
    await expect(page.getByRole("img", { name: /Distribution of scores across 2959 filtered candidates/i })).toBeVisible();

    await page.screenshot({ path: `${SHOTS}/desktop-map-workspace.png` });
  });

  test("selected-status and climate filters synchronize map counts, matrix, and charts", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    const filterPanel = page.getByRole("complementary", { name: /Filters and scenario/i });
    await filterPanel.getByLabel("Selected status").selectOption("selected");
    await expect(page.getByText(/20 of 2,959 candidates/)).toBeVisible();
    await expect(page.getByText(/20 matching · 20 selected/)).toBeVisible();
    await expect(page.getByRole("img", { name: /Distribution of scores across 20 filtered candidates/i })).toBeVisible();

    await filterPanel.getByLabel("Climate region").selectOption("Marine");
    await expect(page.getByText(/4 of 2,959 candidates/)).toBeVisible();
    await expect(page.getByText(/4 matching · 4 selected/)).toBeVisible();
    await expect(page).toHaveURL(/climate=Marine/);
    await expect(page).toHaveURL(/selected=selected/);
  });

  test("selecting a coverage cell opens the details drawer with separated sections", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await page.getByRole("button", { name: /Higher-density urban/i }).first().click();

    const drawer = page.getByRole("dialog");
    await expect(drawer).toBeVisible();
    // Geographic types are labeled distinctly and never conflated.
    for (const heading of [
      "ZIP / ZCTA",
      "Catchment",
      "Weather station",
      "ResStock filter",
      "Score components",
      "Data quality",
      "Provenance",
    ]) {
      await expect(drawer.getByText(heading, { exact: true })).toBeVisible();
    }
    await page.screenshot({ path: `${SHOTS}/desktop-details-drawer.png` });
  });

  test("ZIP search resolves to the ZIP/ZCTA section with crosswalk caveats", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await page.getByRole("searchbox").fill("19104");
    await page.getByRole("searchbox").press("Enter");

    const drawer = page.getByRole("dialog");
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText("ZIP / ZCTA", { exact: true })).toBeVisible();
    await expect(drawer.getByText(/19104/).first()).toBeVisible();
    await expect(drawer.getByText("Nearest stations to the ZIP point")).toBeVisible();
  });

  test("catchment code and station ID search open typed details without ZIP conflation", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");

    await page.getByRole("searchbox").fill("10001");
    await page.getByRole("searchbox").press("Enter");
    const results = page.getByRole("listbox", { name: "Typed search results" });
    await expect(results).toBeVisible();
    await results.getByRole("option").filter({ hasText: "CBSA 10001" }).click();
    let drawer = page.getByRole("dialog");
    await expect(drawer).toBeVisible();
    await expect(drawer.getByText("Catchment", { exact: true })).toBeVisible();
    await expect(drawer.getByText("ZIP / ZCTA", { exact: true })).toBeVisible();
    await expect(drawer.getByText(/Search a ZIP code/)).toBeVisible();
    await drawer.getByRole("button", { name: "Close details" }).click();

    await page.getByRole("searchbox").fill("730001");
    await page.getByRole("searchbox").press("Enter");
    drawer = page.getByRole("dialog");
    await expect(drawer.getByText("Weather station", { exact: true })).toBeVisible();
    await expect(drawer.getByText("730001")).toBeVisible();
  });

  test("methodology context reads provenance", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/");
    await page.getByRole("link", { name: "Methodology & data" }).click();
    await expect(page.getByRole("heading", { name: "Methodology & data" })).toBeVisible();
    await expect(page.getByText(/Boundary rules/)).toBeVisible();
  });

  test("mobile layout is map-first with a bottom tab bar", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    await expect(page.getByRole("search")).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Primary" })).toBeVisible();
    await expect(page.locator(".mapwrap")).toBeVisible();
    await expect(page.getByRole("button", { name: "Toggle filters" })).toBeVisible();

    const viewport = page.viewportSize()!;
    for (const selector of [".topbar", ".mapwrap", ".nav"]) {
      const box = await page.locator(selector).boundingBox();
      expect(box).not.toBeNull();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width + 1);
    }

    await page.screenshot({ path: `${SHOTS}/mobile-map-workspace.png` });
    await page.getByRole("button", { name: "Toggle filters" }).click();
    await expect(page.getByRole("complementary", { name: /Filters and scenario/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "Close filters" }).last()).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/mobile-filters-sheet.png` });
  });
});
