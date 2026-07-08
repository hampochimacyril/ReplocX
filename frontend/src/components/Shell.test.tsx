import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TopBar } from "./TopBar";
import { NavRail } from "./NavRail";
import { SelectionProvider } from "../state/selection";
import { ScenarioProvider } from "../state/scenario";
import type { HealthResponse } from "../lib/types";

const health: HealthResponse = {
  status: "ok",
  service: "ReplocX",
  version: "1.2.0",
  api_version: "v1",
  data_ready: true,
  data_mode: "demo",
  candidate_count: 2959,
  auth: { required: false, configured: false, token_env: "RLE_PRIVATE_AUTH_TOKEN" },
  scenario_store: { database_env: "RLE_SCENARIO_DB", default_path: "/tmp/s.sqlite3" },
};

function renderShell() {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ScenarioProvider>
          <SelectionProvider>
            <TopBar health={health} onToggleFilters={() => {}} />
            <NavRail />
          </SelectionProvider>
        </ScenarioProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("application shell", () => {
  it("renders brand, search, and the data-mode badge", () => {
    renderShell();
    expect(screen.getByText("ReplocX")).toBeInTheDocument();
    expect(screen.getByRole("search")).toBeInTheDocument();
    expect(screen.getByText("DEMO")).toBeInTheDocument();
  });

  it("exposes the five primary navigation contexts", () => {
    renderShell();
    for (const label of ["Map workspace", "Catchments", "Compare", "Scenario", "Methodology & data"]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }
  });
});
