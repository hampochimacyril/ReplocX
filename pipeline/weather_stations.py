#!/usr/bin/env python3
"""Real NOAA ISD-2023 weather-station master list and lookups.

Backed by ``pipeline/data/ish2023_stations.csv`` — the project's 2023 Integrated
Surface Hourly (ISH/ISD) stations for the continental U.S., each tagged with a
Koeppen-derived ``climate_region``, a LEAD tract ``urbanicity`` class, and its
CBSA. This replaces the synthetic placeholder stations the build stage used
before and provides authoritative per-CBSA climate labels for the real
``--source api`` run. Urbanicity remains an aggregate-density classification.

Offline and deterministic: no network required.
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from . import config

STATIONS_CSV = config.PIPELINE_ROOT / "data" / "ish2023_stations.csv"


@dataclass(frozen=True)
class Station:
    name: str
    number: int
    lat: float
    lon: float
    climate_region: str
    urbanicity: str
    cbsa_code: str
    cbsa_name: str


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.7613  # miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


@lru_cache(maxsize=1)
def load_stations(path: str | None = None) -> tuple[Station, ...]:
    csv_path = Path(path) if path else STATIONS_CSV
    stations: list[Station] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            stations.append(
                Station(
                    name=row["station_name"],
                    number=int(row["station_number"]),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    climate_region=row["climate_region"],
                    urbanicity=row["urbanicity"],
                    cbsa_code=str(row["cbsa_code"]).strip(),
                    cbsa_name=row.get("cbsa_name", ""),
                )
            )
    if not stations:
        raise ValueError(f"No stations loaded from {csv_path}")
    return tuple(stations)


def nearest_station(lat: float, lon: float, path: str | None = None) -> tuple[Station, float]:
    """Nearest ISD station to a point, with great-circle distance in miles."""

    best: Station | None = None
    best_distance = math.inf
    for station in load_stations(path):
        distance = _haversine(lat, lon, station.lat, station.lon)
        if distance < best_distance:
            best, best_distance = station, distance
    assert best is not None
    return best, round(best_distance, 1)


@lru_cache(maxsize=1)
def cbsa_label_map(path: str | None = None) -> dict[str, dict[str, str]]:
    """Majority-vote ``climate_region`` + diagnostic ``urbanicity`` per CBSA.

    The classifier uses the climate vote for CBSAs the file covers and falls
    back to the primary-county map elsewhere. The urbanicity vote remains
    available for diagnostics; aggregate catchment density drives classification.
    """

    climates: dict[str, Counter] = defaultdict(Counter)
    urbanicities: dict[str, Counter] = defaultdict(Counter)
    for station in load_stations(path):
        if not station.cbsa_code:
            continue
        climates[station.cbsa_code][station.climate_region] += 1
        urbanicities[station.cbsa_code][station.urbanicity] += 1
    result: dict[str, dict[str, str]] = {}
    for cbsa in climates:
        result[cbsa] = {
            "climate_region": climates[cbsa].most_common(1)[0][0],
            "urbanicity": urbanicities[cbsa].most_common(1)[0][0],
        }
    return result
