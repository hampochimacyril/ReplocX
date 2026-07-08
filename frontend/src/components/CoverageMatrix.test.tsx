import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CoverageMatrix } from "./CoverageMatrix";
import { SelectionProvider } from "../state/selection";
import { CLIMATE_REGIONS, TARGET_STRATA } from "../lib/constants";
import { makeRow } from "../test/fixtures";

function renderMatrix() {
  const rows = [
    makeRow({ climate_region: "Cold & Very Cold", urbanicity_short: "HDU", catchment_code: "10000" }),
    makeRow({ climate_region: "Marine", urbanicity_short: "Rural", catchment_code: "99999", catchment_label: "Marine Rural rep" }),
  ];
  return render(
    <MemoryRouter>
      <SelectionProvider>
        <CoverageMatrix rows={rows} />
      </SelectionProvider>
    </MemoryRouter>,
  );
}

describe("CoverageMatrix", () => {
  it("renders a 5×4 grid with all climate-region rows", () => {
    renderMatrix();
    for (const region of CLIMATE_REGIONS) {
      expect(screen.getByText(region.name.replace("Hot-Dry & Mixed Dry", "Hot-Dry"))).toBeInTheDocument();
    }
    // 20 data cells total; the two provided rows are populated, the rest empty.
    const emptyCells = screen.getAllByText("–");
    expect(emptyCells).toHaveLength(TARGET_STRATA - 2);
  });

  it("exposes a clickable representative cell with an accessible name", () => {
    renderMatrix();
    const cell = screen.getByRole("button", { name: /Cold & Very Cold Higher-density urban/i });
    expect(cell).toBeInTheDocument();
  });
});
