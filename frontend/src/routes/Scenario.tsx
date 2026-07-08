import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Check,
  Copy,
  FileJson,
  History,
  Plus,
  RotateCcw,
  Save,
  SlidersHorizontal,
  Trash2,
  TriangleAlert,
} from "lucide-react";
import { useScenario } from "../state/scenario";
import { useDashboard, useEvaluate, useSaveScenario, useScenariosList } from "../state/queries";
import { api } from "../lib/api";
import { CLIMATE_REGIONS, URBANICITY } from "../lib/constants";
import {
  DEFAULT_WEIGHTS,
  WEIGHT_KEYS,
  WEIGHT_LABELS,
  normalizeWeights,
  weightSum,
  weightsValid,
} from "../lib/scenario";
import { downloadScenarioJson } from "../lib/exports";
import { formatNumber, formatPercentile, formatScore } from "../lib/format";
import { LoadingState } from "../components/states/States";
import type { ScenarioConfig, ScenarioOverride, ScenarioSummary, ScenarioWeights } from "../lib/types";

const PA_OVERRIDE: ScenarioOverride = {
  climate_region: "Mixed-Humid",
  urbanicity: "higher density urban",
  catchment_type: "CBSA",
  catchment_code: "37980",
  rationale: "Research-priority override: Philadelphia has stronger local heat-health data coverage for the project team.",
};

function isPaOverride(o: ScenarioOverride): boolean {
  return o.catchment_code === "37980" && o.catchment_type === "CBSA";
}

function Delta({ value, digits = 3, invert = false }: { value: number; digits?: number; invert?: boolean }) {
  if (!Number.isFinite(value) || Math.abs(value) < 1e-9) return <span className="muted">±0</span>;
  const positive = value > 0;
  const good = invert ? !positive : positive;
  return (
    <span className="num" style={{ color: good ? "var(--ok)" : "var(--danger)" }}>
      {positive ? "+" : ""}
      {formatNumber(value, digits)}
    </span>
  );
}

export function Scenario() {
  const dashboard = useDashboard();
  const { baseline, draft, applied, dirty, customized, saved, setDraft, patchDraft, applyDraft, resetDraftToApplied, resetDraftToBaseline, loadConfig, markSaved, clearActive } =
    useScenario();
  const [params, setParams] = useSearchParams();
  const [name, setName] = useState("");
  const [copied, setCopied] = useState(false);
  const saveMutation = useSaveScenario();

  // Deep-link load: /scenario?load=<id> fetches and applies a saved scenario.
  const loadId = params.get("load");
  useEffect(() => {
    if (!loadId) return;
    let active = true;
    api.scenarios
      .get(loadId)
      .then((s) => {
        if (!active) return;
        loadConfig(s.config, s);
        setName(s.config.name === "User-defined scenario" ? "" : s.config.name);
      })
      .catch(() => undefined)
      .finally(() => {
        const next = new URLSearchParams(params);
        next.delete("load");
        setParams(next, { replace: true });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadId]);

  const draftEval = useEvaluate(draft);
  const baselineSummary = dashboard.data?.scenario.summary;

  const weights = draft?.weights;
  const sum = weights ? weightSum(weights) : 1;
  const valid = weights ? weightsValid(weights) : false;

  if (!draft || !baseline) return <LoadingState label="Loading scenario workbench…" />;

  const setWeight = (key: keyof ScenarioWeights, value: number) =>
    setDraft({ ...draft, weights: { ...draft.weights, [key]: value } });

  const togglePa = (on: boolean) => {
    const others = (draft.overrides ?? []).filter((o) => !isPaOverride(o));
    patchDraft({ overrides: on ? [...others, PA_OVERRIDE] : others });
  };
  const hasPa = (draft.overrides ?? []).some(isPaOverride);

  const onApply = () => {
    if (valid) applyDraft();
  };

  const onSave = () => {
    if (!valid) return;
    const payload: Partial<ScenarioConfig> & { parent_id?: string | null } = {
      ...draft,
      name: name.trim() || draft.name,
      parent_id: saved?.root_id ?? saved?.id ?? null,
    };
    saveMutation.mutate(payload, {
      onSuccess: (result) => {
        markSaved(result);
        loadConfig(result.config, result);
      },
    });
  };

  const shareUrl = saved ? `${window.location.origin}/scenario?load=${saved.id}` : null;
  const onCopyShare = async () => {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="bench">
      <section className="bench-edit" aria-label="Scenario controls">
        <header className="bench-head">
          <h2>
            <SlidersHorizontal size={16} aria-hidden /> Scenario workbench
          </h2>
          <span className={`chip`} title="Editing state">
            <span className={`dot ${dirty ? "dirty" : "saved"}`} aria-hidden />
            {dirty ? "unsaved edits" : applied && customized ? "applied" : "baseline"}
          </span>
        </header>

        <div className="bench-group">
          <div className="grouphead">Composite weights</div>
          <p className="muted small">Weights must sum to 1.00. Housing-unit coverage, population density, population coverage.</p>
          {WEIGHT_KEYS.map((key) => (
            <div className="field weight-field" key={key}>
              <label htmlFor={`w-${key}`}>{WEIGHT_LABELS[key]}</label>
              <div className="weight-row">
                <input
                  id={`w-${key}`}
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={draft.weights[key]}
                  onChange={(e) => setWeight(key, Number(e.target.value))}
                />
                <input
                  type="number"
                  className="textinput num weight-num"
                  min={0}
                  max={1}
                  step={0.01}
                  value={draft.weights[key]}
                  aria-label={`${WEIGHT_LABELS[key]} weight`}
                  onChange={(e) => setWeight(key, Number(e.target.value))}
                />
              </div>
            </div>
          ))}
          <div className={`weight-sum ${valid ? "ok" : "bad"}`} role="status">
            <span>Σ weights</span>
            <span className="num">{formatNumber(sum, 2)}</span>
            {valid ? <Check size={13} aria-hidden /> : <TriangleAlert size={13} aria-hidden />}
          </div>
          <div className="bench-actions-row">
            <button className="btn" type="button" onClick={() => patchDraft({ weights: normalizeWeights(draft.weights) })} disabled={valid}>
              Normalize to 1.00
            </button>
            <button className="btn" type="button" onClick={() => patchDraft({ weights: { ...DEFAULT_WEIGHTS } })}>
              Default split
            </button>
          </div>
          {!valid && <p className="note" style={{ borderColor: "var(--warn-border)" }}>Weights sum to {formatNumber(sum, 2)}. Normalize before applying or saving.</p>}
        </div>

        <div className="bench-group">
          <div className="grouphead">Eligibility &amp; ranking controls</div>
          <div className="field">
            <label htmlFor="density">Density screen percentile · {formatPercentile(draft.density_screen_percentile)}</label>
            <input
              id="density"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={draft.density_screen_percentile}
              onChange={(e) => patchDraft({ density_screen_percentile: Number(e.target.value) })}
            />
            <p className="muted small">Candidates below this population-density percentile are screened out of non-rural strata.</p>
          </div>
          <div className="field">
            <label htmlFor="maxdist">Max station distance · {Math.round(draft.max_station_distance_miles)} mi</label>
            <input
              id="maxdist"
              type="range"
              min={25}
              max={400}
              step={5}
              value={draft.max_station_distance_miles}
              onChange={(e) => patchDraft({ max_station_distance_miles: Number(e.target.value) })}
            />
          </div>
          <div className="field">
            <label htmlFor="penalty">Station-distance penalty · {formatNumber(draft.station_distance_penalty, 2)}</label>
            <input
              id="penalty"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={draft.station_distance_penalty}
              onChange={(e) => patchDraft({ station_distance_penalty: Number(e.target.value) })}
            />
            <p className="muted small">Down-weights candidates whose centroid is far from their assigned ISD station.</p>
          </div>
          <div className="checks">
            <label className="check">
              <input
                type="checkbox"
                checked={draft.unique_location_constraint}
                onChange={(e) => patchDraft({ unique_location_constraint: e.target.checked })}
              />
              Require 20 distinct catchments (uniqueness constraint)
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={draft.require_weather_qc}
                onChange={(e) => patchDraft({ require_weather_qc: e.target.checked })}
              />
              Require complete hourly weather QC for eligibility
            </label>
          </div>
        </div>

        <div className="bench-group">
          <div className="grouphead">Overrides</div>
          <label className="check">
            <input type="checkbox" checked={hasPa} onChange={(e) => togglePa(e.target.checked)} />
            Philadelphia (PA) research-priority override
          </label>
          <OverridesEditor
            overrides={draft.overrides ?? []}
            onRemove={(idx) => patchDraft({ overrides: (draft.overrides ?? []).filter((_, i) => i !== idx) })}
            onAdd={(o) => patchDraft({ overrides: [...(draft.overrides ?? []), o] })}
          />
        </div>
      </section>

      <section className="bench-preview" aria-label="Scenario preview and actions">
        <PreviewPanel summary={draftEval.data?.summary} baseline={baselineSummary} loading={draftEval.isLoading} valid={valid} />

        {draftEval.data && draftEval.data.changes.length > 0 && (
          <div className="bench-group">
            <div className="grouphead">Override substitutions ({draftEval.data.changes.length})</div>
            {draftEval.data.changes.map((c) => (
              <div className="change-row" key={`${c.climate_region}-${c.urbanicity_short}`}>
                <div className="change-head">
                  <span className="muted small">
                    {c.climate_region} · {c.urbanicity_short}
                  </span>
                  <span className="num" style={{ color: "var(--danger)" }}>−{formatScore(c.score_loss)}</span>
                </div>
                <div className="change-body">
                  <s className="muted">{c.from_label}</s> → <strong>{c.to_label}</strong>
                </div>
                <p className="note">{c.reason}</p>
              </div>
            ))}
          </div>
        )}

        <div className="bench-group">
          <div className="grouphead">Apply &amp; save</div>
          <div className="bench-actions">
            <button className="btn btn-accent" type="button" onClick={onApply} disabled={!valid || !dirty}>
              <Check size={14} aria-hidden /> Apply to workspace
            </button>
            <button className="btn" type="button" onClick={resetDraftToApplied} disabled={!dirty}>
              <RotateCcw size={14} aria-hidden /> Reset edits
            </button>
            <button className="btn" type="button" onClick={resetDraftToBaseline}>
              Reset to baseline
            </button>
            {customized && (
              <button className="btn" type="button" onClick={clearActive}>
                Use baseline scenario
              </button>
            )}
          </div>
          <div className="field" style={{ marginTop: "var(--space-3)" }}>
            <label htmlFor="scenario-name">Scenario name</label>
            <input
              id="scenario-name"
              className="textinput"
              placeholder="e.g. Density-weighted, no PA override"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="bench-actions">
            <button className="btn btn-accent" type="button" onClick={onSave} disabled={!valid || saveMutation.isPending}>
              <Save size={14} aria-hidden /> {saveMutation.isPending ? "Saving…" : saved ? "Save new version" : "Save scenario"}
            </button>
            <button className="btn" type="button" onClick={() => downloadScenarioJson(draft, name || draft.name)}>
              <FileJson size={14} aria-hidden /> Export JSON
            </button>
          </div>
          {saveMutation.isError && (
            <p className="note" role="alert" style={{ color: "var(--danger)", borderColor: "var(--danger-border)" }}>
              {(saveMutation.error as Error).message}
            </p>
          )}
          {saved && (
            <div className="saved-meta">
              <span className="muted small">
                Saved as <strong>{saved.name}</strong> · version {saved.version} · {new Date(saved.created_at).toLocaleString()}
              </span>
              {shareUrl && (
                <button className="btn btn-icon" type="button" onClick={onCopyShare} aria-label="Copy share link" title={shareUrl}>
                  {copied ? <Check size={14} aria-hidden /> : <Copy size={14} aria-hidden />}
                </button>
              )}
            </div>
          )}
        </div>

        <SavedScenarios
          activeId={saved?.id ?? null}
          onLoad={async (id) => {
            const s = await api.scenarios.get(id);
            loadConfig(s.config, s);
            setName(s.config.name === "User-defined scenario" ? "" : s.config.name);
          }}
        />
      </section>
    </div>
  );
}

function PreviewPanel({
  summary,
  baseline,
  loading,
  valid,
}: {
  summary?: ScenarioSummary;
  baseline?: ScenarioSummary;
  loading: boolean;
  valid: boolean;
}) {
  if (!valid) {
    return (
      <div className="bench-group">
        <div className="grouphead">Live preview</div>
        <p className="note" style={{ borderColor: "var(--warn-border)" }}>
          Fix the composite weights to preview this scenario.
        </p>
      </div>
    );
  }
  if (loading || !summary) {
    return (
      <div className="bench-group">
        <div className="grouphead">Live preview</div>
        <p className="muted small">Evaluating scenario…</p>
      </div>
    );
  }
  const d = (key: keyof ScenarioSummary) => summary[key] - (baseline?.[key] ?? summary[key]);
  return (
    <div className="bench-group">
      <div className="grouphead">Live preview vs. baseline</div>
      <table className="preview-table">
        <tbody>
          <tr>
            <th scope="row">Distinct catchments</th>
            <td className="num">{summary.distinct_location_count} / 20</td>
            <td>
              {summary.distinct_location_count === 20 ? (
                <span className="tag ok">complete</span>
              ) : (
                <span className="tag danger">incomplete</span>
              )}
            </td>
          </tr>
          <tr>
            <th scope="row">Combined score</th>
            <td className="num">{formatNumber(summary.combined_score, 3)}</td>
            <td>
              <Delta value={d("combined_score")} />
            </td>
          </tr>
          <tr>
            <th scope="row">Changed assignments</th>
            <td className="num">{summary.changed_assignment_count}</td>
            <td>
              <Delta value={d("changed_assignment_count")} digits={0} invert />
            </td>
          </tr>
          <tr>
            <th scope="row">Eligible candidates</th>
            <td className="num">{summary.eligible_candidate_count.toLocaleString()}</td>
            <td>
              <Delta value={d("eligible_candidate_count")} digits={0} />
            </td>
          </tr>
          <tr>
            <th scope="row">Mean station distance</th>
            <td className="num">{formatNumber(summary.mean_station_distance_miles, 1)} mi</td>
            <td>
              <Delta value={d("mean_station_distance_miles")} digits={1} invert />
            </td>
          </tr>
          <tr>
            <th scope="row">Coverage efficiency</th>
            <td className="num">{formatPercentile(summary.coverage_efficiency)}</td>
            <td>
              <Delta value={d("coverage_efficiency") * 100} digits={1} />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function OverridesEditor({
  overrides,
  onRemove,
  onAdd,
}: {
  overrides: ScenarioOverride[];
  onRemove: (index: number) => void;
  onAdd: (o: ScenarioOverride) => void;
}) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<ScenarioOverride>({
    climate_region: CLIMATE_REGIONS[0].name,
    urbanicity: URBANICITY[0].long,
    catchment_type: "CBSA",
    catchment_code: "",
    rationale: "",
  });
  const canAdd = form.catchment_code.trim().length > 0 && (form.rationale ?? "").trim().length > 0;

  return (
    <div className="overrides">
      {overrides.length === 0 && <p className="muted small">No manual overrides. The deterministic ranking selects every stratum.</p>}
      {overrides.map((o, idx) => (
        <div className="override-row" key={`${o.catchment_type}-${o.catchment_code}-${idx}`}>
          <div>
            <strong className="small">
              {o.catchment_type} {o.catchment_code}
            </strong>
            <div className="muted small">
              {o.climate_region} · {o.urbanicity}
            </div>
            {o.rationale && <div className="muted small">{o.rationale}</div>}
          </div>
          <button className="btn btn-icon" type="button" onClick={() => onRemove(idx)} aria-label={`Remove override ${o.catchment_code}`}>
            <Trash2 size={14} aria-hidden />
          </button>
        </div>
      ))}
      {open ? (
        <div className="override-form">
          <div className="field">
            <label htmlFor="ov-climate">Climate region</label>
            <select id="ov-climate" className="select" value={form.climate_region} onChange={(e) => setForm({ ...form, climate_region: e.target.value })}>
              {CLIMATE_REGIONS.map((r) => (
                <option key={r.name} value={r.name}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="ov-urb">Urbanicity</label>
            <select
              id="ov-urb"
              className="select"
              value={form.urbanicity}
              onChange={(e) => {
                const urb = e.target.value;
                setForm({ ...form, urbanicity: urb, catchment_type: urb === "rural" ? "County" : "CBSA" });
              }}
            >
              {URBANICITY.map((u) => (
                <option key={u.short} value={u.long}>
                  {u.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="ov-code">
              {form.catchment_type} code ({form.urbanicity === "rural" ? "county GEOID" : "CBSA code"})
            </label>
            <input id="ov-code" className="textinput" value={form.catchment_code} onChange={(e) => setForm({ ...form, catchment_code: e.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="ov-why">Rationale</label>
            <input id="ov-why" className="textinput" value={form.rationale} onChange={(e) => setForm({ ...form, rationale: e.target.value })} />
          </div>
          <div className="bench-actions-row">
            <button
              className="btn btn-accent"
              type="button"
              disabled={!canAdd}
              onClick={() => {
                onAdd({ ...form, catchment_code: form.catchment_code.trim() });
                setForm({ ...form, catchment_code: "", rationale: "" });
                setOpen(false);
              }}
            >
              Add override
            </button>
            <button className="btn" type="button" onClick={() => setOpen(false)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button className="btn" type="button" onClick={() => setOpen(true)} style={{ marginTop: "var(--space-2)" }}>
          <Plus size={14} aria-hidden /> Add override
        </button>
      )}
    </div>
  );
}

function SavedScenarios({ activeId, onLoad }: { activeId: string | null; onLoad: (id: string) => void | Promise<void> }) {
  const { data, isLoading } = useScenariosList(100);

  const lineages = useMemo(() => {
    const scenarios = data?.scenarios ?? [];
    const groups = new Map<string, typeof scenarios>();
    for (const s of scenarios) {
      const root = s.parent_id ?? s.id;
      const list = groups.get(root) ?? [];
      list.push(s);
      groups.set(root, list);
    }
    return Array.from(groups.values())
      .map((list) => [...list].sort((a, b) => b.version - a.version))
      .sort((a, b) => (a[0].created_at < b[0].created_at ? 1 : -1));
  }, [data]);

  return (
    <div className="bench-group">
      <div className="grouphead">
        <History size={13} aria-hidden style={{ verticalAlign: "-2px", marginRight: 4 }} /> Saved scenarios &amp; versions
      </div>
      {isLoading && <p className="muted small">Loading saved scenarios…</p>}
      {!isLoading && lineages.length === 0 && <p className="muted small">No saved scenarios yet. Save one above to start a version history.</p>}
      {lineages.map((versions) => (
        <div className="lineage" key={versions[versions.length - 1].id}>
          <div className="lineage-name small">{versions[0].name}</div>
          {versions.map((s) => (
            <div className={`saved-row ${s.id === activeId ? "is-active" : ""}`} key={s.id}>
              <div>
                <span className="num small">v{s.version}</span>{" "}
                <span className="muted small">
                  score {formatNumber(s.summary.combined_score, 2)} · {s.summary.changed_assignment_count} changed ·{" "}
                  {new Date(s.created_at).toLocaleDateString()}
                </span>
              </div>
              <button className="btn" type="button" onClick={() => onLoad(s.id)} disabled={s.id === activeId}>
                {s.id === activeId ? "Loaded" : "Load"}
              </button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
