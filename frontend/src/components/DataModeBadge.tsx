import type { HealthResponse } from "../lib/types";

/** Selection-data mode and private Atlas tier status from /api/v1/health. */
export function DataModeBadge({ health }: { health?: HealthResponse }) {
  if (!health) {
    return (
      <span className="badge" title="Checking data mode…">
        …
      </span>
    );
  }
  if (health.status === "degraded" || !health.data_ready) {
    return (
      <span className="badge demo" title={health.detail ?? "Analytical inputs not loaded"}>
        NO DATA
      </span>
    );
  }
  const mode = health.data_mode ?? "production";
  const isDemo = mode === "demo";
  if (health.atlas_enabled) {
    return (
      <span
        className="badge mode-pair"
        title={`Selection data: ${mode} · Atlas tier: certified · ${health.candidate_count ?? "?"} selection candidates`}
      >
        <span>SELECTION {isDemo ? "DEMO" : "PRODUCTION"}</span>
        <span>ATLAS CERTIFIED</span>
      </span>
    );
  }
  return (
    <span
      className={`badge ${isDemo ? "demo" : "prod"}`}
      title={`Data mode from /api/v1/health · ${health.candidate_count ?? "?"} candidates`}
    >
      {isDemo ? "DEMO" : "PRODUCTION"}
    </span>
  );
}
