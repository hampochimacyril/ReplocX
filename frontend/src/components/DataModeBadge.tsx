import type { HealthResponse } from "../lib/types";

/** DEMO vs PRODUCTION badge driven by /api/v1/health (§2.1, §9 acceptance). */
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
  return (
    <span
      className={`badge ${isDemo ? "demo" : "prod"}`}
      title={`Data mode from /api/v1/health · ${health.candidate_count ?? "?"} candidates`}
    >
      {isDemo ? "DEMO" : "PRODUCTION"}
    </span>
  );
}
