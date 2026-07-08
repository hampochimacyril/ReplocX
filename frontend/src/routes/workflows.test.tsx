import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { ScenarioProvider } from "../state/scenario";
import { CompareProvider } from "../state/compare";
import { SelectionProvider } from "../state/selection";
import { Catchments } from "./Catchments";
import { Scenario } from "./Scenario";
import { DEMO_CONFIG, makeCandidates, makeDashboard, makeScenarioResult } from "../test/apiFixtures";

const save = vi.fn();

vi.mock("../lib/api", () => ({
  API_BASE: "/api/v1",
  ApiError: class extends Error {},
  api: {
    health: vi.fn(),
    dashboard: vi.fn(async () => makeDashboard()),
    provenance: vi.fn(),
    geometry: vi.fn(),
    candidates: vi.fn(),
    allCandidates: vi.fn(async () => makeCandidates()),
    zip: vi.fn(),
    evaluate: vi.fn(async () => makeScenarioResult()),
    scenarios: {
      list: vi.fn(async () => ({ scenarios: [], returned: 0, limit: 100 })),
      get: vi.fn(),
      save: (...args: unknown[]) => {
        save(...args);
        return Promise.resolve({
          id: "abc123",
          parent_id: null,
          root_id: "abc123",
          version: 1,
          name: "My scenario",
          created_at: "2026-06-08T00:00:00Z",
          share_path: "/api/v1/scenarios/abc123",
          config: { ...DEMO_CONFIG, name: "My scenario" },
          summary: makeScenarioResult().summary,
        });
      },
    },
  },
}));

function Providers({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ScenarioProvider>
          <CompareProvider>
            <SelectionProvider>{children}</SelectionProvider>
          </CompareProvider>
        </ScenarioProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  save.mockClear();
});

describe("Catchments ranking table", () => {
  it("renders the candidate universe with selected and candidate rows", async () => {
    render(
      <Providers>
        <Catchments filtersOpen={false} onCloseFilters={() => {}} />
      </Providers>,
    );
    expect(await screen.findByText("Cold HDU rep (demo)")).toBeInTheDocument();
    expect(screen.getByText("Hot-Humid LDU candidate (demo)")).toBeInTheDocument();
    expect(screen.getByText(/of 4 candidates · sorted by/)).toBeInTheDocument();
  });

  it("sorts when a column header is activated", async () => {
    render(
      <Providers>
        <Catchments filtersOpen={false} onCloseFilters={() => {}} />
      </Providers>,
    );
    await screen.findByText("Cold HDU rep (demo)");
    const distanceHeader = screen.getByRole("button", { name: /Station dist\./ });
    fireEvent.click(distanceHeader);
    const th = distanceHeader.closest("th")!;
    expect(["ascending", "descending"]).toContain(th.getAttribute("aria-sort"));
  });

  it("adds a row to the comparison tray", async () => {
    render(
      <Providers>
        <Catchments filtersOpen={false} onCloseFilters={() => {}} />
      </Providers>,
    );
    await screen.findByText("Cold HDU rep (demo)");
    fireEvent.click(screen.getByLabelText("Compare Cold HDU rep (demo)"));
    expect(screen.getByText(/1\/4 to compare/)).toBeInTheDocument();
  });
});

describe("Scenario workbench", () => {
  it("flags invalid weights and normalizes them to 1.00", async () => {
    render(
      <Providers>
        <Scenario />
      </Providers>,
    );
    // Workbench renders once the baseline draft initializes.
    await screen.findByText("Scenario workbench");
    const housing = screen.getByLabelText("Housing-unit coverage weight") as HTMLInputElement;
    fireEvent.change(housing, { target: { value: "0.9" } });

    const apply = screen.getByRole("button", { name: /Apply to workspace/ });
    expect(apply).toBeDisabled();
    expect(screen.getByText("1.45")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Normalize to 1.00/ }));
    expect(screen.getByText("1.00")).toBeInTheDocument();
    expect(apply).toBeEnabled();
  });

  it("previews distinct-catchment coverage against the baseline", async () => {
    render(
      <Providers>
        <Scenario />
      </Providers>,
    );
    await screen.findByText("Scenario workbench");
    expect(await screen.findByText("Live preview vs. baseline")).toBeInTheDocument();
    expect(await screen.findByText("20 / 20")).toBeInTheDocument();
  });

  it("saves a scenario and shows saved metadata", async () => {
    render(
      <Providers>
        <Scenario />
      </Providers>,
    );
    await screen.findByText("Scenario workbench");
    fireEvent.click(screen.getByRole("button", { name: /Save scenario/ }));
    await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/Saved as/)).toBeInTheDocument();
    expect(screen.getByText(/version 1/)).toBeInTheDocument();
  });
});
