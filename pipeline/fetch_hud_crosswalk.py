#!/usr/bin/env python3
"""Phase 2 / Session 3: HUD-USPS ZIP crosswalk for the ZIP-code explorer.

Produces ``zip_crosswalk.csv`` — the ZIP -> ZCTA / county / CBSA mapping (with
allocation ratios) the backend uses to resolve a ZIP search into an analytical
catchment, plus a ``zip_crosswalk_provenance.json`` sidecar.

Output schema (matches the bundled ``data/zip_crosswalk_demo.csv`` so the
backend can read either)::

    zip_code, zcta, county_geoid, county_label, cbsa_code, cbsa_label, state,
    climate_region, urbanicity, urbanicity_short, allocation_ratio, match_type,
    uncertainty_note, source_version, latitude, longitude

Two sources share one contract, mirroring ``fetch_census``:

* ``--source api``     – the live HUD-USPS ZIP crosswalk (ZIP-COUNTY and
  ZIP-CBSA quarterly files) via the HUD USER API. **One row per ZIP×county is
  retained** (one-to-many split ZIPs are preserved, not collapsed), each with its
  residential ``allocation_ratio``. The backend resolves a ZIP by choosing the
  highest-ratio record. Requires a free ``HUD_API_TOKEN``.
* ``--source fixture`` – replays the curated demonstration records so the
  pipeline and tests run offline. Clearly labelled; not national coverage.

ZIP vs ZCTA (Session 3)
-----------------------
HUD's crosswalk maps ZIPs to Census geographies but **does not provide ZCTAs**.
ZIP delivery areas and Census ZCTAs are related but not interchangeable, so this
code **never silently sets ``zcta = zip``**. If a real ZIP→ZCTA relationship file
is supplied via ``RLE_ZIP_ZCTA_FILE`` it is used; otherwise ``zcta`` is left
blank with an explicit uncertainty note.

Refresh::

    HUD_API_TOKEN=... python3 -m pipeline.fetch_hud_crosswalk --source api --quarter 1 --year 2025
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any

from . import climate, config, provenance

CROSSWALK_FIELDS = [
    "zip_code",
    "zcta",
    "county_geoid",
    "county_label",
    "cbsa_code",
    "cbsa_label",
    "state",
    "climate_region",
    "urbanicity",
    "urbanicity_short",
    "allocation_ratio",
    "match_type",
    "uncertainty_note",
    "source_version",
    "latitude",
    "longitude",
]

# Curated demonstration crosswalk lives beside the app and is the fixture's
# source of truth, so the offline pipeline output and the bundled demo agree.
DEMO_CROSSWALK = config.APP_ROOT / "data" / "zip_crosswalk_demo.csv"

_NO_ZCTA_NOTE = (
    "ZIP delivery areas and Census ZCTAs are related but NOT interchangeable; HUD "
    "does not supply ZCTA. ZCTA left blank (set RLE_ZIP_ZCTA_FILE to populate). "
    "CBSA is the ZIP's primary HUD ZIP-CBSA match (highest residential ratio); "
    "confirm county→CBSA membership against the OMB delineation."
)
_WITH_ZCTA_NOTE = (
    "ZCTA from the supplied ZIP→ZCTA relationship file (ZIP and ZCTA remain "
    "distinct geographies). CBSA is the ZIP's primary HUD ZIP-CBSA match; confirm "
    "county→CBSA membership against the OMB delineation."
)


# ---------------------------------------------------------------------------
# Offline fixture source
# ---------------------------------------------------------------------------


def fixture_rows() -> list[dict]:
    """Replay the curated demonstration crosswalk records (offline)."""

    with DEMO_CROSSWALK.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["source_version"] = "HUD-USPS-compatible demonstration subset (pipeline fixture replay)"
    return rows


# ---------------------------------------------------------------------------
# Optional ZIP→ZCTA relationship (Session 3): so ZCTA is real, never equated.
# ---------------------------------------------------------------------------

_ZIP_COLS = ("zip", "zip_code", "zipcode")
_ZCTA_COLS = ("zcta", "zcta5", "zcta_code", "zcta5ce")


def load_zip_zcta(path: Path) -> dict[str, str]:
    """Parse a ZIP→ZCTA relationship CSV (tolerant header detection)."""

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        names = {n.lower().strip(): n for n in (reader.fieldnames or [])}
        zip_col = next((names[c] for c in _ZIP_COLS if c in names), None)
        zcta_col = next((names[c] for c in _ZCTA_COLS if c in names), None)
        if not zip_col or not zcta_col:
            raise ValueError(
                f"ZIP→ZCTA file {path.name} needs a ZIP column ({_ZIP_COLS}) and a ZCTA column ({_ZCTA_COLS}); "
                f"found {reader.fieldnames}."
            )
        mapping: dict[str, str] = {}
        for row in reader:
            zip5 = str(row.get(zip_col, "")).strip().zfill(5)
            zcta = str(row.get(zcta_col, "")).strip().zfill(5)
            if zip5 and zcta:
                mapping[zip5] = zcta
    return mapping


# ---------------------------------------------------------------------------
# Live HUD-USPS source (runs on a machine with network + a free token)
# ---------------------------------------------------------------------------

# HUD USER crosswalk API. type 2 = ZIP-COUNTY, type 3 = ZIP-CBSA.
HUD_API = "https://www.huduser.gov/hudapi/public/usps"
_HUD_TYPE = {"county": 2, "cbsa": 3}


def _require(module: str):
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - only hit when deps missing
        raise SystemExit(
            f"--source api needs the '{module}' package. Install it with " f"`pip install {module}` and retry."
        ) from exc


def _retrying_session(requests):
    """Requests session with bounded retry/backoff for the HUD API."""

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


def _ratio(rec: dict) -> float:
    return float(rec.get("res_ratio") or rec.get("tot_ratio") or 0.0)


def build_api_rows(
    county_results: list[dict],
    cbsa_results: list[dict],
    quarter: str,
    zip_zcta: dict[str, str] | None = None,
) -> list[dict]:
    """Build crosswalk rows from HUD API result lists (pure; no network).

    One row per ZIP×county record is emitted (one-to-many ZIPs retained). Each
    ZIP's primary CBSA is taken from the ZIP-CBSA file (highest residential
    ratio). ZCTA comes only from ``zip_zcta`` — never copied from the ZIP.
    """

    zip_zcta = zip_zcta or {}
    has_zcta = bool(zip_zcta)

    cbsa_by_zip: dict[str, tuple[str, float]] = {}
    for rec in cbsa_results:
        zip5 = str(rec.get("zip", "")).zfill(5)
        code = str(rec.get("geoid") or rec.get("cbsa") or "").zfill(5)
        if code in ("", "99999", "00000"):
            code = ""
        ratio = _ratio(rec)
        best = cbsa_by_zip.get(zip5)
        if best is None or ratio > best[1]:
            cbsa_by_zip[zip5] = (code, ratio)

    rows: list[dict] = []
    for rec in county_results:
        zip5 = str(rec.get("zip", "")).zfill(5)
        county = str(rec.get("geoid") or rec.get("county") or "").zfill(5)
        if not zip5 or not county:
            continue
        # The analytical climate/station framework covers the 50 states + DC.
        # HUD's national response also includes territories, which must not be
        # forced into an unrelated continental climate region.
        if county[:2] not in climate.STATE_FIPS_TO_POSTAL:
            continue
        cbsa_code = cbsa_by_zip.get(zip5, ("", 0.0))[0]
        state_postal = climate.STATE_FIPS_TO_POSTAL.get(county[:2], "")
        rows.append(
            {
                "zip_code": zip5,
                "zcta": zip_zcta.get(zip5, ""),  # never the ZIP itself
                "county_geoid": county,
                "county_label": rec.get("countyname", "") or rec.get("county_name", ""),
                "cbsa_code": cbsa_code,
                "cbsa_label": "",
                "state": rec.get("usps_zip_pref_state", "") or state_postal,
                "climate_region": climate.climate_for_county(county),
                "urbanicity": "",  # resolved authoritatively by the catchment join
                "urbanicity_short": "",
                "allocation_ratio": round(_ratio(rec), 4),
                "match_type": "HUD-USPS ZIP-COUNTY (residential ratio); one row per ZIP×county retained",
                "uncertainty_note": _WITH_ZCTA_NOTE if has_zcta else _NO_ZCTA_NOTE,
                "source_version": f"HUD-USPS ZIP crosswalk {quarter}",
                "latitude": "",
                "longitude": "",
            }
        )
    return rows


def _hud_query(
    session,
    headers: dict,
    xtype: int,
    year: int,
    quarter: int,
) -> list[dict]:  # pragma: no cover - network
    resp = session.get(
        HUD_API,
        headers=headers,
        params={
            "type": xtype,
            "query": "All",
            "year": year,
            "quarter": quarter,
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("results", [])


def api_rows(
    year: int,
    quarter: int,
    zip_zcta: dict[str, str] | None = None,
) -> list[dict]:  # pragma: no cover - network
    requests = _require("requests")
    token = os.environ.get("HUD_API_TOKEN")
    if not token:
        raise SystemExit(
            "--source api needs a free HUD_API_TOKEN " "(https://www.huduser.gov/portal/dataset/uspszip-api.html)."
        )
    session = _retrying_session(requests)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    county_results = _hud_query(session, headers, _HUD_TYPE["county"], year, quarter)
    cbsa_results = _hud_query(session, headers, _HUD_TYPE["cbsa"], year, quarter)
    return build_api_rows(county_results, cbsa_results, f"Q{quarter} {year}", zip_zcta)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def provenance_payload(rows: list[dict], source: str, quarter: str, zcta_file: Path | None) -> dict[str, Any]:
    distinct_zips: dict[str, int] = {}
    for row in rows:
        distinct_zips[row["zip_code"]] = distinct_zips.get(row["zip_code"], 0) + 1
    one_to_many = sum(1 for n in distinct_zips.values() if n > 1)
    payload: dict[str, Any] = {
        "source": source,
        "quarter": quarter,
        "row_count": len(rows),
        "distinct_zip_count": len(distinct_zips),
        "one_to_many_zip_count": one_to_many,
        "zcta_resolved": bool(zcta_file),
        "generated_at_utc": provenance.utc_now_iso(),
    }
    if source == "api":
        payload["api"] = {
            "endpoint": HUD_API,
            "types": _HUD_TYPE,
            "note": "ZIP-COUNTY rows retained one-to-many; primary CBSA from ZIP-CBSA (highest residential ratio).",
            "geographic_scope": "50 states and District of Columbia; U.S. territories excluded.",
        }
    else:
        payload["note"] = "Curated demonstration subset replay (not national coverage)."
    if zcta_file is not None:
        payload["zip_zcta_file"] = provenance.file_record(zcta_file)
    return payload


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def write_rows(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CROSSWALK_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Fetch the HUD-USPS ZIP crosswalk.")
    parser.add_argument("--source", choices=["fixture", "api"], default="fixture")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], default=1)
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Alias for a fresh --source api pull of the given quarter.",
    )
    parser.add_argument("--out", type=Path, default=config.OUT_DIR / "zip_crosswalk.csv")
    args = parser.parse_args(argv)

    source = "api" if args.refresh else args.source
    quarter = f"Q{args.quarter} {args.year}"

    zcta_path_env = os.environ.get("RLE_ZIP_ZCTA_FILE")
    zcta_file = Path(zcta_path_env) if zcta_path_env else None
    zip_zcta = load_zip_zcta(zcta_file) if zcta_file else None

    rows = api_rows(args.year, args.quarter, zip_zcta) if source == "api" else fixture_rows()
    write_rows(rows, args.out)

    sidecar = args.out.with_name("zip_crosswalk_provenance.json")
    provenance.write_sidecar(sidecar, provenance_payload(rows, source, quarter, zcta_file))

    print(f"[fetch_hud_crosswalk] source={source} wrote {len(rows)} ZIP records -> {args.out}")
    return args.out


if __name__ == "__main__":
    main()
