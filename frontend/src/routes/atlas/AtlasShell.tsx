import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  BookOpen,
  FlaskConical,
  BarChart3,
  ShieldHalf,
  Scale,
  Download,
  MapPinned,
} from "lucide-react";
import { useHealth } from "../../state/queries";
import { LoadingState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { AtlasControlsContext, SCENARIOS, SCENARIO_COLOR, SCENARIO_SHORT, useScenarioDictionary } from "./atlas";
import type { AtlasTier, Scenario } from "../../lib/types";

const SUB_NAV: Array<{ to: string; label: string; Icon: typeof BookOpen; end?: boolean }> = [
  { to: "/atlas", label: "Introduction", Icon: BookOpen, end: true },
  { to: "/atlas/locations", label: "How locations were selected", Icon: MapPinned },
  { to: "/atlas/results", label: "Results A/C/B/D", Icon: BarChart3 },
  { to: "/atlas/sealed-passive", label: "Sealed-passive D contrasts", Icon: ShieldHalf },
  { to: "/atlas/equity", label: "Equity context", Icon: Scale },
  { to: "/atlas/methods", label: "Methods", Icon: FlaskConical },
  { to: "/atlas/exports", label: "Exports/provenance", Icon: Download },
];

/** Segmented control shared by the tier + scenario selectors. */
function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
  color,
}: {
  label: string;
  value: T;
  options: Array<{ value: T; label: string }>;
  onChange: (v: T) => void;
  color?: (v: T) => string;
}) {
  return (
    <div className="atlas-seg" role="group" aria-label={label}>
      <span className="atlas-seg-label">{label}</span>
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            className={`atlas-seg-btn${active ? " active" : ""}`}
            aria-pressed={active}
            onClick={() => onChange(opt.value)}
            style={active && color ? { borderColor: color(opt.value), color: color(opt.value) } : undefined}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

/**
 * ReplocX Research Atlas — a modular sibling to the public selection tool that
 * presents the private, certified ReplocX TMY3 wallfix four-scenario results,
 * sealed-passive contrasts, and equity/degree-day context. Gated behind the
 * backend RLE_ENABLE_ATLAS flag: when off, /api/v1/results/* return 404 and the
 * shell shows a "not enabled" panel so the public demo never hints at the
 * unpublished results.
 */
export function AtlasShell() {
  const health = useHealth();
  const [tier, setTier] = useState<AtlasTier>("annual");
  const [scenario, setScenario] = useState<Scenario>("D");
  const enabled = health.data?.atlas_enabled ?? false;
  const dictionary = useScenarioDictionary(enabled);

  if (health.isLoading) return <LoadingState label="Checking Atlas availability…" />;

  const scenarioLabels = Object.fromEntries(
    SCENARIOS.map((s) => [
      s,
      dictionary.data?.scenarios.find((item) => item.code === s)?.scenario_display_label ?? SCENARIO_SHORT[s],
    ]),
  ) as Record<Scenario, string>;

  return (
    <div className="atlas">
      <aside className="atlas-nav" aria-label="Research Atlas sections">
        <div className="atlas-nav-head">
          <span className="atlas-kicker">ReplocX</span>
          <strong>Research Atlas</strong>
          <Tag tone="info" title="Private, unpublished results tier">
            TMY3 · private
          </Tag>
        </div>
        {SUB_NAV.map(({ to, label, Icon, end }) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? "active" : "")}>
            <Icon size={16} aria-hidden />
            <span>{label}</span>
          </NavLink>
        ))}
      </aside>

      <section className="atlas-main">
        {enabled ? (
          <>
            <div className="atlas-controls">
              <Segmented
                label="Tier"
                value={tier}
                onChange={setTier}
                options={[
                  { value: "annual", label: "Annual" },
                  { value: "seasonal", label: "Cooling season" },
                ]}
              />
              <Segmented
                label="Scenario"
                value={scenario}
                onChange={setScenario}
                color={(v) => SCENARIO_COLOR[v]}
                options={SCENARIOS.map((s) => ({ value: s, label: `${scenarioLabels[s]} (${s})` }))}
              />
            </div>
            <div className="atlas-context">
              <AtlasControlsContext.Provider value={{ tier, scenario, scenarioLabels, setTier, setScenario }}>
                <Outlet />
              </AtlasControlsContext.Provider>
            </div>
          </>
        ) : (
          <div className="doc">
            <h1>Research Atlas — not enabled here</h1>
            <div className="banner" role="note" style={{ marginTop: "var(--space-3)" }}>
              <div>
                <strong>This deployment serves the public location-selection tool only.</strong>
                <div className="muted small" style={{ marginTop: 4 }}>
                  The Atlas presents the private, unpublished ReplocX TMY3 wallfix four-scenario results and
                  equity context. It is served only on an approved private deployment started with{" "}
                  <code>RLE_ENABLE_ATLAS=1</code>. The public demo stays on synthetic selection data.
                </div>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
