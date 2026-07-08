import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DataModeBadge } from "./DataModeBadge";
import type { HealthResponse } from "../lib/types";

const base: HealthResponse = {
  status: "ok",
  service: "ReplocX",
  version: "1.2.0",
  api_version: "v1",
  data_ready: true,
  auth: { required: false, configured: false, token_env: "RLE_PRIVATE_AUTH_TOKEN" },
  scenario_store: { database_env: "RLE_SCENARIO_DB", default_path: "/tmp/s.sqlite3" },
};

describe("DataModeBadge", () => {
  it("shows DEMO for the bundled dataset", () => {
    render(<DataModeBadge health={{ ...base, data_mode: "demo", candidate_count: 2959 }} />);
    expect(screen.getByText("DEMO")).toBeInTheDocument();
  });

  it("shows PRODUCTION for real analytical data", () => {
    render(<DataModeBadge health={{ ...base, data_mode: "production" }} />);
    expect(screen.getByText("PRODUCTION")).toBeInTheDocument();
  });

  it("distinguishes demo selection data from the certified private Atlas", () => {
    render(
      <DataModeBadge
        health={{ ...base, data_mode: "demo", atlas_enabled: true, candidate_count: 2959 }}
      />,
    );
    expect(screen.getByText("SELECTION DEMO")).toBeInTheDocument();
    expect(screen.getByText("ATLAS CERTIFIED")).toBeInTheDocument();
    expect(screen.queryByText("DEMO")).not.toBeInTheDocument();
  });

  it("shows NO DATA when the service is degraded", () => {
    render(<DataModeBadge health={{ ...base, status: "degraded", data_ready: false, detail: "no inputs" }} />);
    expect(screen.getByText("NO DATA")).toBeInTheDocument();
  });
});
