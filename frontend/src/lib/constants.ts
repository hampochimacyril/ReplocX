/* Domain constants: the fixed 20-strata grid (5 climate regions × 4 urbanicity). */

export interface ClimateRegion {
  /** Canonical region name as returned by the API. */
  name: string;
  /** CSS custom property used for DOM swatches/legend. */
  cssVar: string;
  /** Static hex used by MapLibre paint (WebGL cannot read CSS variables). */
  hex: string;
  /** Non-color cue for the legend (§5.6 — never color alone). */
  pattern: string;
}

export const CLIMATE_REGIONS: ClimateRegion[] = [
  { name: "Cold & Very Cold", cssVar: "--c-cold", hex: "#2c7fb8", pattern: "▲" },
  { name: "Hot-Dry & Mixed Dry", cssVar: "--c-hotdry", hex: "#d95f0e", pattern: "■" },
  { name: "Hot-Humid", cssVar: "--c-hothumid", hex: "#c0392b", pattern: "●" },
  { name: "Marine", cssVar: "--c-marine", hex: "#1f8a53", pattern: "◆" },
  { name: "Mixed-Humid", cssVar: "--c-mixed", hex: "#756bb1", pattern: "✦" },
];

export const CLIMATE_BY_NAME: Record<string, ClimateRegion> = Object.fromEntries(
  CLIMATE_REGIONS.map((r) => [r.name, r]),
);

/** Urbanicity categories in fixed display order, with their short codes. */
export interface Urbanicity {
  long: string;
  short: string;
  label: string;
}

export const URBANICITY: Urbanicity[] = [
  { long: "higher density urban", short: "HDU", label: "Higher-density urban" },
  { long: "lower density urban", short: "LDU", label: "Lower-density urban" },
  { long: "suburban/small town", short: "Suburban", label: "Suburban / small town" },
  { long: "rural", short: "Rural", label: "Rural" },
];

export const URBANICITY_BY_SHORT: Record<string, Urbanicity> = Object.fromEntries(
  URBANICITY.map((u) => [u.short, u]),
);

export const TARGET_STRATA = CLIMATE_REGIONS.length * URBANICITY.length;

export function climateHex(name: string): string {
  return CLIMATE_BY_NAME[name]?.hex ?? "#9aa4b1";
}

export function climateVar(name: string): string {
  return CLIMATE_BY_NAME[name]?.cssVar ?? "--border-strong";
}
