/*
 * Comparison tray: a small set of candidate rows the user has marked to compare
 * side by side (from the ranking table or the map). Capped so the Compare view
 * stays scannable. Keyed by the stable location-uniqueness key (lib/selectors).
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { rowKey } from "../lib/selectors";
import type { CatchmentRow } from "../lib/types";

export const COMPARE_LIMIT = 4;

interface CompareContextValue {
  rows: CatchmentRow[];
  keys: Set<string>;
  has: (row: CatchmentRow) => boolean;
  toggle: (row: CatchmentRow) => void;
  add: (row: CatchmentRow) => void;
  remove: (key: string) => void;
  clear: () => void;
  atLimit: boolean;
}

const CompareContext = createContext<CompareContextValue | null>(null);

export function CompareProvider({ children }: { children: ReactNode }) {
  const [rows, setRows] = useState<CatchmentRow[]>([]);

  const keys = useMemo(() => new Set(rows.map(rowKey)), [rows]);

  const has = useCallback((row: CatchmentRow) => keys.has(rowKey(row)), [keys]);

  const add = useCallback((row: CatchmentRow) => {
    setRows((current) => {
      const key = rowKey(row);
      if (current.some((r) => rowKey(r) === key) || current.length >= COMPARE_LIMIT) return current;
      return [...current, row];
    });
  }, []);

  const remove = useCallback((key: string) => {
    setRows((current) => current.filter((r) => rowKey(r) !== key));
  }, []);

  const toggle = useCallback((row: CatchmentRow) => {
    setRows((current) => {
      const key = rowKey(row);
      if (current.some((r) => rowKey(r) === key)) return current.filter((r) => rowKey(r) !== key);
      if (current.length >= COMPARE_LIMIT) return current;
      return [...current, row];
    });
  }, []);

  const clear = useCallback(() => setRows([]), []);

  const value = useMemo<CompareContextValue>(
    () => ({ rows, keys, has, toggle, add, remove, clear, atLimit: rows.length >= COMPARE_LIMIT }),
    [rows, keys, has, toggle, add, remove, clear],
  );

  return <CompareContext.Provider value={value}>{children}</CompareContext.Provider>;
}

export function useCompare(): CompareContextValue {
  const ctx = useContext(CompareContext);
  if (!ctx) throw new Error("useCompare must be used within CompareProvider");
  return ctx;
}
