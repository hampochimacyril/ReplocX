/*
 * Shared, scenario-aware row set. The map workspace, ranking table, and compare
 * view all read from here so they stay coordinated: candidates merged with the
 * applied scenario's selected representatives. When no custom scenario is applied
 * (`active === null`) this resolves to the dashboard baseline, so behavior is
 * identical to the foundation until the user applies an edited scenario.
 */
import { useMemo } from "react";
import { useAllCandidates, useDashboard, useEvaluate } from "./queries";
import { useScenario } from "./scenario";
import { mergeScenarioSelection } from "../lib/selectors";
import type { CatchmentRow, ScenarioChange, ScenarioSummary } from "../lib/types";

export interface ActiveRows {
  rows: CatchmentRow[];
  selectedRows: CatchmentRow[];
  changes: ScenarioChange[];
  summary: ScenarioSummary | undefined;
  /** True while the applied custom scenario is being evaluated. */
  evaluating: boolean;
  isLoading: boolean;
  isError: boolean;
  error: Error | undefined;
  refetch: () => void;
}

export function useActiveRows(): ActiveRows {
  const dashboard = useDashboard();
  const candidates = useAllCandidates();
  const { active } = useScenario();
  const activeEval = useEvaluate(active);

  const usingActive = active !== null && !!activeEval.data;
  const baseline = dashboard.data?.scenario;
  const selectedRows = useMemo(
    () => (usingActive ? activeEval.data!.selected : baseline?.selected ?? []),
    [usingActive, activeEval.data, baseline],
  );
  const changes = usingActive ? activeEval.data!.changes : baseline?.changes ?? [];
  const summary = usingActive ? activeEval.data!.summary : baseline?.summary;

  const rows = useMemo(
    () => mergeScenarioSelection(candidates.data ?? [], selectedRows),
    [candidates.data, selectedRows],
  );

  return {
    rows,
    selectedRows,
    changes,
    summary,
    evaluating: active !== null && activeEval.isLoading,
    isLoading: dashboard.isLoading || candidates.isLoading,
    isError: dashboard.isError || candidates.isError,
    error: (dashboard.error ?? candidates.error ?? activeEval.error) as Error | undefined,
    refetch: () => {
      dashboard.refetch();
      candidates.refetch();
      if (active) activeEval.refetch();
    },
  };
}
