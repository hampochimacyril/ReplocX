#!/usr/bin/env python3
"""Phase 2: per-station hourly weather completeness QC (NOAA ISD).

Computes, for each weather station a catchment is assigned to, whether the
station's hourly record for the simulation year is complete enough to drive a
building-energy simulation. This replaces the ``PENDING`` placeholder the
Phase 1 build stage wrote for every site.

Threshold (confirmed for Phase 2)
---------------------------------
A station-year is ``COMPLETE`` when **at least 90 % of the year's hours** have
both a temperature and a humidity (dew-point) observation present; otherwise it
is ``INCOMPLETE``. 90 % is the conventional completeness bar for assembling a
representative weather year (TMY/EnergyPlus-adjacent practice) and is applied
identically to both sources below.

Leap-year handling (Session 3)
------------------------------
The expected hour count is **8,784 for a leap year** and **8,760 otherwise**, so
a leap-year station-year is held to the same 90 % *fraction* rather than being
quietly penalised against a fixed 8,760.

Two sources share one contract, mirroring ``fetch_census``:

* ``--source api``      – real NOAA Integrated Surface Database global-hourly
  files (one per selected station, per year). Six-digit USAF identifiers are
  resolved to the active USAF+WBAN file through NOAA's station-history table.
  Downloads are cached, resumable, and retried with backoff. Per-station fetch
  and parse failures are captured and written to a downloadable error report
  instead of being silently treated as zero coverage.
* ``--source fixture``  – deterministic per-station coverage so the pipeline and
  the test suite run offline. Clearly labelled as a structural stand-in, not a
  measured completeness figure.

Run directly::

    python3 -m pipeline.weather_qc --source fixture --out pipeline/out/station_weather_qc.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import os
from pathlib import Path

from . import config, weather_stations

QC_FIELDS = [
    "station_number",
    "station_name",
    "year",
    "expected_hours",
    "present_hours",
    "coverage_fraction",
    "hourly_weather_qc_status",
    "source",
]

# Columns for the downloadable per-station error report (Session 3).
QC_ERROR_FIELDS = ["station_number", "station_name", "year", "url", "error"]

EXPECTED_HOURS = 8760  # non-leap default; see expected_hours_for() for leap years.
LEAP_HOURS = 8784
COMPLETE_THRESHOLD = 0.90  # >= 90% of the year's hours with temp AND humidity present.
DEFAULT_YEAR = int(os.environ.get("RLE_WEATHER_QC_YEAR", "2023"))

# NOAA ISD global-hourly per-station CSV (verified current, June 2026).
ISD_BASE = "https://www.ncei.noaa.gov/data/global-hourly/access"
ISD_HISTORY_URL = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
WEATHER_CACHE_DIR = config.CACHE_DIR / "weather"
# Sentinels that mark a missing reading in the TMP/DEW value field.
_MISSING_SENTINELS = {"", "+9999", "9999", "-9999"}


def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def expected_hours_for(year: int) -> int:
    """8,784 for a leap year, 8,760 otherwise."""

    return LEAP_HOURS if is_leap_year(year) else EXPECTED_HOURS


def status_for(coverage_fraction: float) -> str:
    return "COMPLETE" if coverage_fraction >= COMPLETE_THRESHOLD else "INCOMPLETE"


# ---------------------------------------------------------------------------
# Offline fixture source
# ---------------------------------------------------------------------------


def _fixture_coverage(station_number: int) -> float:
    """Deterministic synthetic coverage in [0.80, 1.00] keyed by station number.

    Spreads stations across the 90 % threshold so the QC filter is exercised
    (roughly half pass) while staying fully reproducible without network.
    """

    h = (station_number * 1103515245 + 12345) & 0x7FFFFFFF
    return round(0.80 + (h % 21) / 100.0, 4)


def fixture_rows(stations: list[tuple[int, str]], year: int) -> list[dict]:
    expected = expected_hours_for(year)
    rows = []
    for number, name in stations:
        coverage = _fixture_coverage(number)
        rows.append(
            {
                "station_number": str(number),
                "station_name": name,
                "year": year,
                "expected_hours": expected,
                "present_hours": int(round(coverage * expected)),
                "coverage_fraction": coverage,
                "hourly_weather_qc_status": status_for(coverage),
                "source": "fixture",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Live NOAA ISD source (runs on a machine with network)
# ---------------------------------------------------------------------------


def _require(module: str):
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - only hit when deps missing
        raise SystemExit(
            f"--source api needs the '{module}' package. Install it with " f"`pip install {module}` and retry."
        ) from exc


def isd_url(station_id: int | str, year: int) -> str:
    """Per-station ISD global-hourly CSV URL (11-digit USAF+WBAN id)."""

    return f"{ISD_BASE}/{year}/{str(station_id).strip().zfill(11)}.csv"


def _retrying_session(requests):
    """Requests session with bounded retry/backoff for public-data hosts."""

    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def load_station_ids(
    year: int,
    path: Path | None = None,
    session=None,
) -> dict[int, str]:
    """Map six-digit USAF numbers to active 11-digit USAF+WBAN identifiers."""

    history_path = path
    if history_path is None:
        override = os.environ.get("RLE_ISD_HISTORY_FILE")
        history_path = Path(override) if override else WEATHER_CACHE_DIR / "isd-history.csv"

    if not history_path.exists():  # pragma: no cover - network
        if session is None:
            requests = _require("requests")
            session = _retrying_session(requests)
        response = session.get(ISD_HISTORY_URL, timeout=(20, 120))
        response.raise_for_status()
        history_path.parent.mkdir(parents=True, exist_ok=True)
        partial = history_path.with_suffix(history_path.suffix + ".part")
        partial.write_bytes(response.content)
        partial.replace(history_path)

    year_start = year * 10000 + 101
    year_end = year * 10000 + 1231
    selected: dict[int, tuple[tuple[int, int, int], str]] = {}
    with history_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            usaf = str(row.get("USAF", "")).strip().zfill(6)
            wban = str(row.get("WBAN", "")).strip().zfill(5)
            if not usaf.isdigit() or not wban.isdigit():
                continue
            try:
                begin = int(str(row.get("BEGIN", "")).strip() or 0)
                end = int(str(row.get("END", "")).strip() or 99991231)
            except ValueError:
                continue
            if begin > year_end or end < year_start:
                continue
            overlap = min(end, year_end) - max(begin, year_start)
            score = (wban != "99999", overlap, end)
            number = int(usaf)
            current = selected.get(number)
            if current is None or score > current[0]:
                selected[number] = (score, f"{usaf}{wban}")
    return {number: station_id for number, (_, station_id) in selected.items()}


def coverage_from_csv(text: str, year: int) -> float:
    """Fraction of the year's hours with both temperature and dew point present.

    Pure parser (no network) so it can be unit-tested against a recorded ISD
    sample. The TMP and DEW columns carry a comma-separated value/quality pair;
    a sentinel such as ``+9999`` marks a missing reading. Observations are
    de-duplicated to the hour (``YYYY-MM-DDTHH``) to avoid sub-hourly double
    counting, then divided by the year's expected hour count (leap-aware).
    """

    expected = expected_hours_for(year)
    present_hours: set[str] = set()
    reader = csv.DictReader(io.StringIO(text))
    for record in reader:
        date = (record.get("DATE") or "").strip()
        if not date:
            continue
        temp = (record.get("TMP", "") or "").split(",")[0].strip()
        dew = (record.get("DEW", "") or "").split(",")[0].strip()
        if temp in _MISSING_SENTINELS or dew in _MISSING_SENTINELS:
            continue
        present_hours.add(date[:13])  # YYYY-MM-DDTHH -> one slot per hour
    return round(min(len(present_hours), expected) / expected, 4)


def _isd_coverage(session, station_id: str, year: int) -> tuple[float, str | None]:  # pragma: no cover - network
    """Return ``(coverage_fraction, error_message_or_None)`` for a station-year."""

    url = isd_url(station_id, year)
    cache_dir = WEATHER_CACHE_DIR / str(year)
    cached = cache_dir / f"{station_id}.csv"
    if cached.exists():
        try:
            return coverage_from_csv(cached.read_text(encoding="utf-8", errors="replace"), year), None
        except Exception as exc:
            return 0.0, f"cached parse error: {exc}"

    cache_dir.mkdir(parents=True, exist_ok=True)
    partial = cached.with_suffix(".csv.part")
    partial_size = partial.stat().st_size if partial.exists() else 0
    headers = {"Range": f"bytes={partial_size}-"} if partial_size else {}
    try:
        resp = session.get(url, headers=headers, timeout=(20, 120), stream=True)
    except Exception as exc:  # network/transport error
        return 0.0, f"request failed: {exc}"
    if resp.status_code == 404:
        return 0.0, "no ISD global-hourly file for this station-year (HTTP 404)"
    if resp.status_code == 416 and partial.exists():
        partial.replace(cached)
    elif resp.status_code in (200, 206):
        mode = "ab" if resp.status_code == 206 and partial_size else "wb"
        try:
            with partial.open(mode) as handle:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    if chunk:
                        handle.write(chunk)
            partial.replace(cached)
        except Exception as exc:
            return 0.0, f"download failed (partial file retained for resume): {exc}"
    else:
        return 0.0, f"HTTP {resp.status_code}"
    try:
        return coverage_from_csv(cached.read_text(encoding="utf-8", errors="replace"), year), None
    except Exception as exc:  # malformed payload
        return 0.0, f"parse error: {exc}"


def api_rows(
    stations: list[tuple[int, str]],
    year: int,
    errors: list[dict] | None = None,
) -> list[dict]:  # pragma: no cover - needs network
    requests = _require("requests")
    session = _retrying_session(requests)
    station_ids = load_station_ids(year, session=session)
    expected = expected_hours_for(year)
    rows = []
    for number, name in stations:
        station_id = station_ids.get(number)
        if station_id is None:
            coverage = 0.0
            error = f"no active USAF+WBAN mapping in NOAA station history for {year}"
            url = ISD_HISTORY_URL
        else:
            coverage, error = _isd_coverage(session, station_id, year)
            url = isd_url(station_id, year)
        if error is not None and errors is not None:
            errors.append(
                {
                    "station_number": str(number),
                    "station_name": name,
                    "year": year,
                    "url": url,
                    "error": error,
                }
            )
        rows.append(
            {
                "station_number": str(number),
                "station_name": name,
                "year": year,
                "expected_hours": expected,
                "present_hours": int(round(coverage * expected)),
                "coverage_fraction": coverage,
                "hourly_weather_qc_status": status_for(coverage),
                "source": "api",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Public helpers used by build_catchments + entry point
# ---------------------------------------------------------------------------


def compute_rows(
    stations: list[tuple[int, str]],
    source: str,
    year: int = DEFAULT_YEAR,
    errors: list[dict] | None = None,
) -> list[dict]:
    """QC rows for an explicit list of (station_number, station_name).

    Pass an ``errors`` list to capture per-station fetch/parse failures from the
    live source for the downloadable error report; the fixture source never errors.
    """

    unique: dict[int, str] = {}
    for number, name in stations:
        unique.setdefault(int(number), name)
    ordered = sorted(unique.items())
    if source == "api":
        return api_rows(ordered, year, errors)
    return fixture_rows(ordered, year)


def status_map(rows: list[dict]) -> dict[str, str]:
    return {str(row["station_number"]): row["hourly_weather_qc_status"] for row in rows}


def all_station_rows(
    source: str,
    year: int = DEFAULT_YEAR,
    errors: list[dict] | None = None,
) -> list[dict]:
    """QC rows for every station in the ISD master list (CLI convenience)."""

    stations = [(s.number, s.name) for s in weather_stations.load_stations()]
    return compute_rows(stations, source, year, errors)


def selected_stations(path: Path) -> list[tuple[int, str]]:
    """Read the station IDs referenced by a selected-locations CSV."""

    if not path.exists():
        raise SystemExit(f"selected locations file not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    try:
        return [(int(row["selected_station_number"]), row["selected_station_name"]) for row in rows]
    except KeyError as exc:
        raise SystemExit(f"{path} is missing selected-station columns") from exc


def write_rows(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QC_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_error_report(errors: list[dict], out_path: Path) -> None:
    """Write the downloadable per-station QC error report (always written)."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QC_ERROR_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(errors)


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Compute per-station hourly weather QC.")
    parser.add_argument("--source", choices=["fixture", "api"], default="fixture")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--out", type=Path, default=config.OUT_DIR / "station_weather_qc.csv")
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=config.OUT_DIR / "selected_locations.csv",
        help="Selected-locations CSV whose assigned stations should be checked.",
    )
    parser.add_argument(
        "--all-stations",
        action="store_true",
        help="Check the full ISD master list instead of only selected locations (large download).",
    )
    parser.add_argument(
        "--error-report",
        type=Path,
        default=None,
        help="Where to write the per-station error report (default: alongside --out).",
    )
    args = parser.parse_args(argv)

    errors: list[dict] = []
    rows = (
        all_station_rows(args.source, args.year, errors)
        if args.all_stations
        else compute_rows(selected_stations(args.in_path), args.source, args.year, errors)
    )
    write_rows(rows, args.out)
    error_path = args.error_report or args.out.with_name("station_weather_qc_errors.csv")
    write_error_report(errors, error_path)
    complete = sum(r["hourly_weather_qc_status"] == "COMPLETE" for r in rows)
    print(
        f"[weather_qc] source={args.source} year={args.year} "
        f"({expected_hours_for(args.year)} expected hours): "
        f"{complete}/{len(rows)} stations COMPLETE (>= {COMPLETE_THRESHOLD:.0%}); "
        f"{len(errors)} fetch error(s) -> {args.out}"
    )
    return args.out


if __name__ == "__main__":
    main()
