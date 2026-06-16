/* Shared selection + details-drawer state. A selection can originate from the
 * map, a table row, a matrix cell, or a search result; the details drawer reads
 * whatever is selected. */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { CatchmentRow, ZipLookupResponse } from "../lib/types";

export type Selection =
  | { kind: "catchment"; row: CatchmentRow }
  | { kind: "zip"; result: ZipLookupResponse }
  | null;

interface SelectionContextValue {
  selection: Selection;
  selectCatchment: (row: CatchmentRow) => void;
  selectZip: (result: ZipLookupResponse) => void;
  clear: () => void;
}

const SelectionContext = createContext<SelectionContextValue | null>(null);

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selection, setSelection] = useState<Selection>(null);

  const selectCatchment = useCallback((row: CatchmentRow) => setSelection({ kind: "catchment", row }), []);
  const selectZip = useCallback((result: ZipLookupResponse) => setSelection({ kind: "zip", result }), []);
  const clear = useCallback(() => setSelection(null), []);

  const value = useMemo(
    () => ({ selection, selectCatchment, selectZip, clear }),
    [selection, selectCatchment, selectZip, clear],
  );
  return <SelectionContext.Provider value={value}>{children}</SelectionContext.Provider>;
}

export function useSelection(): SelectionContextValue {
  const ctx = useContext(SelectionContext);
  if (!ctx) throw new Error("useSelection must be used within SelectionProvider");
  return ctx;
}
