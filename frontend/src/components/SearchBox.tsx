import { useEffect, useRef, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Building2, Filter, Search, Thermometer, X } from "lucide-react";
import { api, ApiError } from "../lib/api";
import { filtersToParams, useFilters } from "../state/filters";
import { useSelection } from "../state/selection";
import type { CatchmentRow, ZipLookupResponse } from "../lib/types";

type SearchChoice =
  | { id: string; kind: "zip"; label: string; meta: string; result: ZipLookupResponse }
  | { id: string; kind: "catchment"; label: string; meta: string; row: CatchmentRow }
  | { id: string; kind: "station"; label: string; meta: string; row: CatchmentRow }
  | { id: string; kind: "filter"; label: string; meta: string };

function includes(value: string | number | undefined, needle: string): boolean {
  return String(value ?? "").toLowerCase().includes(needle);
}

function iconFor(kind: SearchChoice["kind"]) {
  if (kind === "zip") return <span className="search-kind">ZIP</span>;
  if (kind === "catchment") return <Building2 size={14} aria-hidden />;
  if (kind === "station") return <Thermometer size={14} aria-hidden />;
  return <Filter size={14} aria-hidden />;
}

export function SearchBox() {
  const { filters } = useFilters();
  const { selectCatchment, selectZip, clear } = useSelection();
  const navigate = useNavigate();
  const location = useLocation();
  const rootRef = useRef<HTMLFormElement>(null);
  const [value, setValue] = useState("");
  const [choices, setChoices] = useState<SearchChoice[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function choose(choice: SearchChoice) {
    setOpen(false);
    setError(null);
    if (choice.kind === "zip") {
      selectZip(choice.result);
      navigate({ pathname: "/", search: location.search });
      return;
    }
    if (choice.kind === "catchment" || choice.kind === "station") {
      selectCatchment(choice.row);
      navigate({ pathname: "/", search: location.search });
      return;
    }
    clear();
    const params = filtersToParams({ ...filters, search: value.trim() });
    navigate({ pathname: "/", search: params.toString() ? `?${params}` : "" });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const term = value.trim();
    const needle = term.toLowerCase();
    setError(null);
    setChoices([]);
    if (!term) return;

    setBusy(true);
    try {
      const [candidateResult, zipResult] = await Promise.all([
        api.candidates({ search: term, limit: 24 }),
        /^\d{5}$/.test(term)
          ? api.zip(term).catch((err) => {
              if (err instanceof ApiError && err.status === 404) return null;
              throw err;
            })
          : Promise.resolve(null),
      ]);

      const next: SearchChoice[] = [];
      if (zipResult) {
        next.push({
          id: `zip:${zipResult.zip_code}`,
          kind: "zip",
          label: `ZIP ${zipResult.zip_code}`,
          meta: `${zipResult.resolved.zcta ? `ZCTA ${zipResult.resolved.zcta}` : "no ZCTA"} · ${zipResult.resolved.county_label}`,
          result: zipResult,
        });
      }

      for (const row of candidateResult.rows
        .filter((candidate) => includes(candidate.catchment_label, needle) || includes(candidate.catchment_code, needle))
        .slice(0, 6)) {
        next.push({
          id: `catchment:${row.location_uniqueness_key}`,
          kind: "catchment",
          label: row.catchment_label,
          meta: `${row.catchment_type} ${row.catchment_code} · ${row.climate_region} · ${row.urbanicity_short}`,
          row,
        });
      }

      const stations = new Set<string>();
      for (const row of candidateResult.rows) {
        if (!includes(row.selected_station_name, needle) && !includes(row.selected_station_number, needle)) continue;
        const stationId = String(row.selected_station_number);
        if (stations.has(stationId)) continue;
        stations.add(stationId);
        next.push({
          id: `station:${stationId}`,
          kind: "station",
          label: row.selected_station_name,
          meta: `Weather station ${stationId} · assigned to ${row.catchment_label}`,
          row,
        });
        if (stations.size >= 6) break;
      }

      if (candidateResult.total > 0) {
        next.push({
          id: `filter:${term}`,
          kind: "filter",
          label: `Show all ${candidateResult.total.toLocaleString()} matches on the map`,
          meta: "Apply as a shared catchment/station filter",
        });
      }

      const directChoices = next.filter((choice) => choice.kind !== "filter");
      if (directChoices.length === 1) {
        choose(directChoices[0]);
      } else if (next.length) {
        setChoices(next);
        setOpen(true);
      } else {
        setError(`No ZIP, catchment, or station matched “${term}”.`);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      ref={rootRef}
      className="search"
      role="search"
      onSubmit={onSubmit}
      aria-label="Search ZIP, catchment, or station"
    >
      <Search size={16} aria-hidden />
      <input
        type="search"
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
          setOpen(false);
          setError(null);
        }}
        placeholder="Search ZIP, catchment, or weather station…"
        aria-label="Search ZIP, catchment, or station"
        aria-expanded={open}
        aria-controls="global-search-results"
        inputMode="text"
        autoComplete="off"
      />
      {value && !busy && (
        <button
          className="search-clear"
          type="button"
          onClick={() => {
            setValue("");
            setOpen(false);
            setError(null);
          }}
          aria-label="Clear search"
        >
          <X size={14} aria-hidden />
        </button>
      )}
      {busy && <span className="muted small" role="status">Searching…</span>}
      {error && (
        <span className="search-error" role="alert">
          {error}
        </span>
      )}
      {open && (
        <div id="global-search-results" className="search-results" role="listbox" aria-label="Typed search results">
          {choices.map((choice) => (
            <button key={choice.id} type="button" role="option" onClick={() => choose(choice)}>
              <span className="search-result-icon">{iconFor(choice.kind)}</span>
              <span>
                <strong>{choice.label}</strong>
                <small>{choice.meta}</small>
              </span>
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
