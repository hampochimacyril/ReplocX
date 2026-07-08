import { describe, it, expect } from "vitest";
import { formatInt, formatNumber, formatPercentile, formatScore, formatMiles } from "./format";

describe("format helpers", () => {
  it("formats integers with thousands separators", () => {
    expect(formatInt(2180000)).toBe("2,180,000");
    expect(formatInt(0)).toBe("0");
  });

  it("renders an em dash for missing values", () => {
    expect(formatInt(undefined)).toBe("—");
    expect(formatNumber(null)).toBe("—");
    expect(formatScore(NaN)).toBe("—");
  });

  it("scales 0–1 percentiles to a 0–100 score", () => {
    expect(formatPercentile(0.9)).toBe("90");
    expect(formatPercentile(0.2)).toBe("20");
  });

  it("formats scores to three decimals and miles with a unit", () => {
    expect(formatScore(0.9)).toBe("0.900");
    expect(formatMiles(29.5)).toBe("29.5 mi");
  });
});
