import { expect, test } from "@playwright/test";

test("overview dashboard renders the baseline scenario", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Overview dashboard" })).toBeVisible();
  await expect(page.getByText("Target strata")).toBeVisible();
  await expect(page.getByText("20/20")).toBeVisible();
  await expect(page.getByText("National target catchments and climate stations")).toBeVisible();
});

test("ZIP explorer preserves leading zeros and explains geography scope", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /ZIP code explorer/ }).click();
  await page.getByLabel("ZIP code").fill("02108");
  await page.getByRole("button", { name: "Resolve ZIP" }).click();
  await expect(page.getByText("Resolved geography · 02108")).toBeVisible();
  await expect(page.getByText("ZCTA", { exact: true })).toBeVisible();
  await expect(page.getByText("25025 · Suffolk County")).toBeVisible();
  await expect(page.getByText("ZIP is an entry point.")).toBeVisible();
});

test("scenario builder updates deterministic allocation preview", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Scenario builder/ }).click();
  await expect(page.getByText("Test methodological choices before saving a scenario")).toBeVisible();
  await expect(page.getByText("Distinct catchments")).toBeVisible();
  await page.locator("#unique").uncheck();
  await expect(page.getByText("Changed assignments")).toBeVisible();
});

test("candidate ranking and site-list export are reachable", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Candidate ranking/ }).click();
  await expect(page.getByText("Inspect every scored candidate")).toBeVisible();
  await expect(page.getByText("2,959 candidates")).toBeVisible();

  await page.getByRole("button", { name: /Scenario builder/ }).click();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export site list CSV" }).click();
  const file = await download;
  expect(file.suggestedFilename()).toContain("representative-location-site-list");
});
