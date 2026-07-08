/*
 * Active-scenario state shared across the workspace. Three layers:
 *   - baseline: the dashboard's default scenario config (immutable reference).
 *   - active:   the applied scenario (null means "use the baseline"). Drives the
 *               map's selected set, the export menu, and the comparison view.
 *   - draft:    the workbench's in-progress edits, previewed before applying.
 *
 * The backend (backend/scoring.py, backend/models.py) owns all scoring and
 * validation; this context never recomputes selection — it only holds config
 * and dirty/saved bookkeeping and lets components evaluate via useEvaluate.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useDashboard } from "./queries";
import { cloneConfig, configsEqual } from "../lib/scenario";
import type { ScenarioConfig, SavedScenarioMeta } from "../lib/types";

export interface ScenarioContextValue {
  /** The immutable baseline config from the dashboard (null until it loads). */
  baseline: ScenarioConfig | null;
  /** The applied scenario (null = baseline). */
  active: ScenarioConfig | null;
  /** The applied config, resolving null to the baseline. */
  applied: ScenarioConfig | null;
  /** The workbench draft (null until baseline loads). */
  draft: ScenarioConfig | null;
  /** Draft differs from the applied config. */
  dirty: boolean;
  /** Applied scenario differs from the baseline. */
  customized: boolean;
  /** Saved-scenario metadata for the applied scenario, if it came from the store. */
  saved: SavedScenarioMeta | null;
  setDraft: (next: ScenarioConfig) => void;
  patchDraft: (patch: Partial<ScenarioConfig>) => void;
  resetDraftToApplied: () => void;
  resetDraftToBaseline: () => void;
  /** Apply the current draft as the active scenario. */
  applyDraft: () => void;
  /** Revert the applied scenario back to the baseline. */
  clearActive: () => void;
  /** Load a saved/shared scenario: applies it and records its metadata. */
  loadConfig: (config: ScenarioConfig, saved?: SavedScenarioMeta | null) => void;
  /** Record saved metadata after a successful save without changing the config. */
  markSaved: (meta: SavedScenarioMeta) => void;
}

const ScenarioContext = createContext<ScenarioContextValue | null>(null);

export function ScenarioProvider({ children }: { children: ReactNode }) {
  const dashboard = useDashboard();
  const baseline = dashboard.data?.scenario.config ?? null;

  const [draft, setDraftState] = useState<ScenarioConfig | null>(null);
  const [active, setActive] = useState<ScenarioConfig | null>(null);
  const [saved, setSaved] = useState<SavedScenarioMeta | null>(null);

  // Initialize the draft from the baseline exactly once, when it first arrives.
  useEffect(() => {
    if (baseline && draft === null) setDraftState(cloneConfig(baseline));
  }, [baseline, draft]);

  const applied = active ?? baseline;

  const dirty = useMemo(() => {
    if (!draft || !applied) return false;
    return !configsEqual(draft, applied);
  }, [draft, applied]);

  const customized = useMemo(() => {
    if (!active || !baseline) return false;
    return !configsEqual(active, baseline);
  }, [active, baseline]);

  const setDraft = useCallback((next: ScenarioConfig) => setDraftState(cloneConfig(next)), []);
  const patchDraft = useCallback(
    (patch: Partial<ScenarioConfig>) =>
      setDraftState((current) => (current ? { ...cloneConfig(current), ...patch } : current)),
    [],
  );
  const resetDraftToApplied = useCallback(() => {
    if (applied) setDraftState(cloneConfig(applied));
  }, [applied]);
  const resetDraftToBaseline = useCallback(() => {
    if (baseline) setDraftState(cloneConfig(baseline));
  }, [baseline]);
  const applyDraft = useCallback(() => {
    setDraftState((current) => {
      if (current) {
        setActive(cloneConfig(current));
        setSaved(null);
      }
      return current;
    });
  }, []);
  const clearActive = useCallback(() => {
    setActive(null);
    setSaved(null);
  }, []);
  const loadConfig = useCallback((config: ScenarioConfig, savedMeta: SavedScenarioMeta | null = null) => {
    setActive(cloneConfig(config));
    setDraftState(cloneConfig(config));
    setSaved(savedMeta);
  }, []);
  const markSaved = useCallback((meta: SavedScenarioMeta) => setSaved(meta), []);

  const value = useMemo<ScenarioContextValue>(
    () => ({
      baseline,
      active,
      applied,
      draft,
      dirty,
      customized,
      saved,
      setDraft,
      patchDraft,
      resetDraftToApplied,
      resetDraftToBaseline,
      applyDraft,
      clearActive,
      loadConfig,
      markSaved,
    }),
    [
      baseline,
      active,
      applied,
      draft,
      dirty,
      customized,
      saved,
      setDraft,
      patchDraft,
      resetDraftToApplied,
      resetDraftToBaseline,
      applyDraft,
      clearActive,
      loadConfig,
      markSaved,
    ],
  );

  return <ScenarioContext.Provider value={value}>{children}</ScenarioContext.Provider>;
}

export function useScenario(): ScenarioContextValue {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error("useScenario must be used within ScenarioProvider");
  return ctx;
}
