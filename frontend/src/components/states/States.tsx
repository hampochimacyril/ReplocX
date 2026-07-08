import type { ReactNode } from "react";
import { AlertTriangle, Inbox, RotateCw, ServerCrash } from "lucide-react";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="statewrap" role="status" aria-live="polite">
      <div className="statecard">
        <div className="spinner" aria-hidden />
        <p className="muted">{label}</p>
      </div>
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="statewrap" role="alert">
      <div className="statecard">
        <ServerCrash size={28} aria-hidden />
        <h3>{title}</h3>
        <p className="muted">{message}</p>
        {onRetry && (
          <button className="btn" type="button" onClick={onRetry}>
            <RotateCw size={14} aria-hidden /> Retry
          </button>
        )}
      </div>
    </div>
  );
}

export function EmptyState({
  title = "No results",
  message,
  action,
}: {
  title?: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div className="statewrap">
      <div className="statecard">
        <Inbox size={28} aria-hidden />
        <h3>{title}</h3>
        <p className="muted">{message}</p>
        {action}
      </div>
    </div>
  );
}

/** Degraded / 503 banner mirroring the backend health remediation guidance. */
export function DegradedBanner({ detail }: { detail?: string }) {
  return (
    <div className="banner danger" role="alert" style={{ margin: "var(--space-4)" }}>
      <AlertTriangle size={18} aria-hidden style={{ flex: "none", marginTop: 1 }} />
      <div>
        <strong>Analytical inputs are not loaded.</strong>
        <div className="muted small" style={{ marginTop: 4 }}>
          {detail ??
            "The service is running but the read-only analysis directory could not be read. Set RLE_ANALYSIS_DATA_DIR to a valid processed-outputs directory, or rely on the bundled demo dataset."}
        </div>
      </div>
    </div>
  );
}

export function Skeleton({ height = 16, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} aria-hidden />;
}
