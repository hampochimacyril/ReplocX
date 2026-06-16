import { useEffect, useMemo, useRef, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
  type VisibilityState,
} from "@tanstack/react-table";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Columns3,
  Download,
  GitCompareArrows,
} from "lucide-react";
import { useActiveRows } from "../state/rows";
import { useFilters } from "../state/filters";
import { useSelection } from "../state/selection";
import { useCompare, COMPARE_LIMIT } from "../state/compare";
import { matchesFilters, isRepresentative, rowKey } from "../lib/selectors";
import { toCsv, downloadText, type CsvColumn } from "../lib/csv";
import { dateStamp } from "../lib/exports";
import { formatMiles, formatScore } from "../lib/format";
import { VerificationTag, WeatherQcTag } from "../components/ui/Tag";
import { LoadingState, ErrorState, EmptyState } from "../components/states/States";
import { FilterPanel } from "../components/FilterPanel";
import { useScenario } from "../state/scenario";
import type { CatchmentRow } from "../lib/types";

const column = createColumnHelper<CatchmentRow>();

function scoreOf(row: CatchmentRow): number {
  return row.scenario_score ?? row.location_score;
}
function rankOf(row: CatchmentRow): number {
  return row.scenario_rank ?? row.selection_rank;
}

const CSV_COLUMNS: CsvColumn<CatchmentRow>[] = [
  { header: "rank", value: rankOf },
  { header: "selected", value: (r) => (isRepresentative(r) ? "yes" : "no") },
  { header: "catchment_label", value: (r) => r.catchment_label },
  { header: "catchment_type", value: (r) => r.catchment_type },
  { header: "catchment_code", value: (r) => r.catchment_code },
  { header: "climate_region", value: (r) => r.climate_region },
  { header: "urbanicity", value: (r) => r.urbanicity_short },
  { header: "composite_score", value: (r) => scoreOf(r).toFixed(3) },
  { header: "station_distance_miles", value: (r) => r.station_distance_miles },
  { header: "weather_qc_status", value: (r) => r.hourly_weather_qc_status },
  { header: "nrel_verification_status", value: (r) => r.nrel_verification_status ?? "" },
];

export function Catchments({ filtersOpen, onCloseFilters }: { filtersOpen: boolean; onCloseFilters: () => void }) {
  const { rows, isLoading, isError, error, refetch } = useActiveRows();
  const { filters } = useFilters();
  const { selectCatchment, selection } = useSelection();
  const compare = useCompare();
  const { applied } = useScenario();
  const [sorting, setSorting] = useState<SortingState>([{ id: "score", desc: true }]);
  const [visibility, setVisibility] = useState<VisibilityState>({});
  const [colMenuOpen, setColMenuOpen] = useState(false);
  const colMenuRef = useRef<HTMLDivElement>(null);

  const filteredRows = useMemo(() => rows.filter((r) => matchesFilters(r, filters)), [rows, filters]);
  const selectedKey = selection?.kind === "catchment" ? rowKey(selection.row) : null;

  const columns = useMemo(
    () => [
      column.display({
        id: "compare",
        header: () => <span className="sr-only">Add to comparison</span>,
        cell: ({ row }) => {
          const r = row.original;
          const checked = compare.has(r);
          return (
            <input
              type="checkbox"
              aria-label={`Compare ${r.catchment_label}`}
              checked={checked}
              disabled={!checked && compare.atLimit}
              onClick={(e) => e.stopPropagation()}
              onChange={() => compare.toggle(r)}
            />
          );
        },
        enableSorting: false,
      }),
      column.accessor(rankOf, {
        id: "rank",
        header: "Rank",
        cell: (info) => <span className="num">{info.getValue()}</span>,
        sortingFn: "basic",
      }),
      column.accessor((r) => r.catchment_label, {
        id: "label",
        header: "Catchment",
        cell: (info) => <span className="cell-label">{info.getValue()}</span>,
      }),
      column.accessor((r) => r.catchment_type, { id: "type", header: "Type" }),
      column.accessor((r) => r.catchment_code, {
        id: "code",
        header: "Code",
        cell: (info) => <span className="num">{info.getValue()}</span>,
      }),
      column.accessor((r) => r.climate_region, { id: "climate", header: "Climate" }),
      column.accessor((r) => r.urbanicity_short, { id: "urbanicity", header: "Urb." }),
      column.accessor(scoreOf, {
        id: "score",
        header: "Score",
        cell: (info) => <span className="num">{formatScore(info.getValue())}</span>,
        sortingFn: "basic",
      }),
      column.accessor((r) => r.station_distance_miles, {
        id: "distance",
        header: "Station dist.",
        cell: (info) => <span className="num">{formatMiles(info.getValue())}</span>,
        sortingFn: "basic",
      }),
      column.accessor((r) => r.hourly_weather_qc_status, {
        id: "qc",
        header: "Weather QC",
        cell: (info) => <WeatherQcTag status={info.getValue()} />,
      }),
      column.accessor((r) => r.nrel_verification_status ?? "", {
        id: "verification",
        header: "ResStock",
        cell: (info) => <VerificationTag status={info.getValue() || undefined} />,
      }),
      column.accessor((r) => (isRepresentative(r) ? 1 : 0), {
        id: "selected",
        header: "Selected",
        cell: (info) =>
          info.getValue() ? <span className="tag ok">Representative</span> : <span className="muted small">candidate</span>,
        sortingFn: "basic",
      }),
    ],
    [compare],
  );

  const table = useReactTable({
    data: filteredRows,
    columns,
    state: { sorting, columnVisibility: visibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setVisibility,
    getRowId: (row) => rowKey(row),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 50 } },
  });

  useEffect(() => {
    if (!colMenuOpen) return;
    const onDoc = (e: MouseEvent) => {
      if (colMenuRef.current && !colMenuRef.current.contains(e.target as Node)) setColMenuOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [colMenuOpen]);

  if (isLoading) return <LoadingState label="Loading candidate ranking…" />;
  if (isError) return <ErrorState message={error?.message ?? "Failed to load candidates."} onRetry={refetch} />;

  const exportCsv = () => {
    const ordered = table.getSortedRowModel().rows.map((r) => r.original);
    const scenarioTag = applied?.name === "User-defined scenario" ? "baseline" : "scenario";
    downloadText(`replocx_ranking_${scenarioTag}_${dateStamp()}.csv`, toCsv(ordered, CSV_COLUMNS));
  };

  const pageStart = table.getState().pagination.pageIndex * table.getState().pagination.pageSize;
  const pageRows = table.getRowModel().rows;

  return (
    <div className="ws ws-table">
      <FilterPanel
        scenario={applied ?? undefined}
        open={filtersOpen}
        resultCount={filteredRows.length}
        totalCount={rows.length}
        onClose={onCloseFilters}
      />
      <div className="tablestage">
        <div className="table-toolbar">
          <div>
            <h2 className="table-title">Candidate ranking</h2>
            <p className="muted small num" aria-live="polite">
              {filteredRows.length.toLocaleString()} of {rows.length.toLocaleString()} candidates · sorted by{" "}
              {sorting[0]?.id ?? "rank"}
            </p>
          </div>
          <span style={{ flex: 1 }} />
          {compare.rows.length > 0 && (
            <span className="chip" title="Selected for comparison">
              <GitCompareArrows size={13} aria-hidden /> {compare.rows.length}/{COMPARE_LIMIT} to compare
            </span>
          )}
          <div className="menu" ref={colMenuRef}>
            <button
              className="btn"
              type="button"
              aria-haspopup="menu"
              aria-expanded={colMenuOpen}
              onClick={() => setColMenuOpen((v) => !v)}
            >
              <Columns3 size={14} aria-hidden /> Columns
            </button>
            {colMenuOpen && (
              <div className="menu-list" role="menu" aria-label="Toggle columns">
                {table
                  .getAllLeafColumns()
                  .filter((col) => col.id !== "compare" && col.getCanHide())
                  .map((col) => (
                    <label key={col.id} className="check" style={{ padding: "6px 10px" }}>
                      <input type="checkbox" checked={col.getIsVisible()} onChange={col.getToggleVisibilityHandler()} />
                      {String(col.columnDef.header)}
                    </label>
                  ))}
              </div>
            )}
          </div>
          <button className="btn" type="button" onClick={exportCsv} disabled={filteredRows.length === 0}>
            <Download size={14} aria-hidden /> Export CSV
          </button>
        </div>

        {filteredRows.length === 0 ? (
          <EmptyState
            title="No candidates match these filters"
            message="Broaden the climate, urbanicity, score, or station-distance filters to see candidates."
          />
        ) : (
          <div className="tablewrap" role="region" aria-label="Candidate ranking table" tabIndex={0}>
            <table className="dtable">
              <thead>
                {table.getHeaderGroups().map((hg) => (
                  <tr key={hg.id}>
                    {hg.headers.map((header) => {
                      const sortable = header.column.getCanSort();
                      const sorted = header.column.getIsSorted();
                      return (
                        <th
                          key={header.id}
                          aria-sort={sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : "none"}
                          className={header.column.id === "compare" ? "col-compare" : undefined}
                        >
                          {header.isPlaceholder ? null : sortable ? (
                            <button type="button" className="th-sort" onClick={header.column.getToggleSortingHandler()}>
                              {flexRender(header.column.columnDef.header, header.getContext())}
                              {sorted === "asc" ? (
                                <ArrowUp size={12} aria-hidden />
                              ) : sorted === "desc" ? (
                                <ArrowDown size={12} aria-hidden />
                              ) : (
                                <ArrowUpDown size={12} aria-hidden className="muted" />
                              )}
                            </button>
                          ) : (
                            flexRender(header.column.columnDef.header, header.getContext())
                          )}
                        </th>
                      );
                    })}
                  </tr>
                ))}
              </thead>
              <tbody>
                {pageRows.map((row) => {
                  const isSel = rowKey(row.original) === selectedKey;
                  return (
                    <tr
                      key={row.id}
                      className={isSel ? "row-selected" : undefined}
                      onClick={() => selectCatchment(row.original)}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          selectCatchment(row.original);
                        }
                      }}
                    >
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className={cell.column.id === "compare" ? "col-compare" : undefined}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {filteredRows.length > 0 && (
          <div className="table-pager">
            <span className="muted small num">
              Showing {pageStart + 1}–{Math.min(pageStart + pageRows.length, filteredRows.length)} of{" "}
              {filteredRows.length.toLocaleString()}
            </span>
            <span style={{ flex: 1 }} />
            <label className="muted small" style={{ display: "flex", gap: 6, alignItems: "center" }}>
              Rows
              <select
                className="select"
                style={{ width: "auto" }}
                value={table.getState().pagination.pageSize}
                onChange={(e) => table.setPageSize(Number(e.target.value))}
              >
                {[25, 50, 100, 250].map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="btn btn-icon"
              type="button"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              aria-label="Previous page"
            >
              <ChevronLeft size={16} aria-hidden />
            </button>
            <span className="muted small num">
              {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
            </span>
            <button
              className="btn btn-icon"
              type="button"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              aria-label="Next page"
            >
              <ChevronRight size={16} aria-hidden />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
