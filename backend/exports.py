"""Export adapters (Phase 3, task 9).

Turn a selected-site set (the ``selected`` list of a scenario ``evaluate()``
result) into artifacts a building-stock modeler can use directly:

* :func:`resstock_sampling_csv` — a ResStock **and** ComStock downselect input.
  Both tools downselect their sample with ``parameter=option`` pairs over the
  same spatial enumeration fields (``in.county`` /
  ``in.metropolitan_and_micropolitan_statistical_area``), so one adapter serves
  both. Each row is one selected catchment's ``parameter,option`` plus context.

* :func:`openstudio_manifest` — a JSON manifest pairing every selected site with
  its representative NOAA ISD weather station and ResStock filter, shaped for an
  OpenStudio/EnergyPlus workflow.

Both are pure functions over plain dicts (no FastAPI, no I/O), so the
dependency-free ``server.py`` and the managed ``fastapi_app.py`` can share them.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Any

SAMPLING_FIELDS = [
    "parameter",
    "option",
    "catchment_type",
    "catchment_code",
    "catchment_label",
    "climate_region",
    "urbanicity",
    "weather_station_id",
    "hourly_weather_qc_status",
    "nrel_verification_status",
]


def _station_id(row: dict[str, Any]) -> str:
    raw = str(row.get("selected_station_number", "")).strip()
    return raw.zfill(6) if raw.isdigit() else raw


def resstock_sampling_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One ResStock/ComStock downselect row per selected catchment."""

    rows: list[dict[str, Any]] = []
    for site in selected:
        rows.append(
            {
                "parameter": site["nrel_filter_field"],
                "option": str(site["nrel_filter_value"]).zfill(5),
                "catchment_type": site["catchment_type"],
                "catchment_code": str(site["catchment_code"]).zfill(5),
                "catchment_label": site["catchment_label"],
                "climate_region": site["climate_region"],
                "urbanicity": site["urbanicity_short"],
                "weather_station_id": _station_id(site),
                "hourly_weather_qc_status": site["hourly_weather_qc_status"],
                "nrel_verification_status": site["nrel_verification_status"],
            }
        )
    return rows


def resstock_sampling_csv(selected: list[dict[str, Any]]) -> str:
    """ResStock/ComStock downselect input as CSV text."""

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=SAMPLING_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(resstock_sampling_rows(selected))
    return buffer.getvalue()


def downselect_logic(selected: list[dict[str, Any]]) -> list[str]:
    """ResStock ``downselect_logic`` strings (``parameter|option``) for a YAML spec."""

    return [f"{site['nrel_filter_field']}|{str(site['nrel_filter_value']).zfill(5)}" for site in selected]


def openstudio_manifest(selected: list[dict[str, Any]], provenance: dict[str, Any] | None = None) -> dict[str, Any]:
    """OpenStudio/EnergyPlus-ready manifest of selected sites.

    Pairs each site with its representative ISD station and ResStock filter. The
    actual EPW/TMY weather file is *not* bundled — only the ISD station identity
    is known — so each site carries an explicit ``epw_hint`` telling the modeler
    where to obtain the weather file for that station.
    """

    provenance = provenance or {}
    sites: list[dict[str, Any]] = []
    for site in selected:
        station_id = _station_id(site)
        sites.append(
            {
                "id": site.get("location_uniqueness_key")
                or f"{site['catchment_type']}:{str(site['catchment_code']).zfill(5)}",
                "catchment_type": site["catchment_type"],
                "catchment_code": str(site["catchment_code"]).zfill(5),
                "catchment_label": site["catchment_label"],
                "climate_region": site["climate_region"],
                "urbanicity": site["urbanicity"],
                "urbanicity_short": site["urbanicity_short"],
                "resstock_filter": {
                    "parameter": site["nrel_filter_field"],
                    "option": str(site["nrel_filter_value"]).zfill(5),
                    "verification_status": site["nrel_verification_status"],
                },
                "centroid": {
                    "lat": site.get("centroid_lat"),
                    "lon": site.get("centroid_lon"),
                },
                "weather_station": {
                    "name": site.get("selected_station_name"),
                    "isd_station_id": station_id,
                    "lat": site.get("selected_station_lat"),
                    "lon": site.get("selected_station_lon"),
                    "distance_miles": site.get("station_distance_miles"),
                    "hourly_weather_qc_status": site["hourly_weather_qc_status"],
                    "epw_hint": (
                        f"Obtain a TMY3/EPW weather file for NOAA ISD station {station_id} "
                        "(e.g. EnergyPlus weather data or NREL NSRDB) before simulation."
                    ),
                },
                "scenario_rank": site.get("scenario_rank"),
                "scenario_score": site.get("scenario_score"),
            }
        )
    return {
        "schema": "rle.openstudio_manifest/1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "method_version": provenance.get("method_version"),
        "data_mode": provenance.get("data_mode"),
        "boundary_system": provenance.get("boundary_system"),
        "site_count": len(sites),
        "weather_note": (
            "Weather files are not bundled. Each site names its representative NOAA ISD "
            "station; obtain the matching TMY3/EPW file (free) before running OpenStudio/EnergyPlus."
        ),
        "source_attribution": provenance.get("sources", []),
        "sites": sites,
    }
