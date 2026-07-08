import { useEffect, useRef, useState } from "react";
import { Download, FileJson, FileSpreadsheet, Braces } from "lucide-react";
import { EXPORTS, downloadExport, downloadScenarioJson, type ExportSpec } from "../lib/exports";
import type { ScenarioConfig } from "../lib/types";

const ICON_FOR: Record<string, typeof FileJson> = {
  "site-list": FileSpreadsheet,
  resstock: FileSpreadsheet,
  openstudio: FileJson,
};

export function ExportMenu({ config }: { config?: Partial<ScenarioConfig> }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function run(spec: ExportSpec) {
    setBusy(spec.id);
    setError(null);
    try {
      await downloadExport(spec, config ?? {});
      setOpen(false);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="menu" ref={ref}>
      <button
        className="btn"
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Download size={14} aria-hidden /> Export
      </button>
      {open && (
        <div className="menu-list" role="menu" aria-label="Export options">
          {EXPORTS.map((spec) => {
            const Icon = ICON_FOR[spec.id] ?? FileSpreadsheet;
            return (
              <button key={spec.id} type="button" role="menuitem" onClick={() => run(spec)} disabled={busy !== null}>
                <Icon size={14} aria-hidden />
                <span style={{ flex: 1 }}>{spec.label}</span>
                <span className="muted small">{busy === spec.id ? "…" : spec.path.replace("/exports/", "")}</span>
              </button>
            );
          })}
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              downloadScenarioJson(config ?? {});
              setOpen(false);
            }}
            disabled={busy !== null}
          >
            <Braces size={14} aria-hidden />
            <span style={{ flex: 1 }}>Scenario config JSON</span>
            <span className="muted small">local</span>
          </button>
          {error && (
            <div className="note" role="alert" style={{ color: "var(--danger)" }}>
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
