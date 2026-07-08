#!/usr/bin/env python3
"""Phase 2 / Session 3: simplified catchment polygons for the map (TIGER/Line).

Emits a GeoJSON ``FeatureCollection`` with one feature per selected catchment so
the front end can draw real boundaries instead of centroid dots.

Two sources share one contract, mirroring ``fetch_census``:

* ``--source api``     – real Census TIGER/Line cartographic boundaries pulled
  from the TIGERweb REST service per county/CBSA code, then simplified with
  Douglas–Peucker (topology-safe for independently-rendered features) under a
  hard vertex cap. Full **MultiPolygon** support keeps islands and detached
  parts; **Alaska** rings that cross the antimeridian are normalised so they do
  not smear across the map; every feature carries a **geometry-validation**
  result. Requires network access.
* ``--source fixture`` – deterministic synthetic polygons (a small hexagon around
  each catchment centroid, sized by catchment type). Clearly a structural
  stand-in, not a real boundary; always a simple closed ``Polygon``.

Simplification is *topology-safe for this product's rendering model*: each
catchment is fetched and drawn as an independent feature (there is no shared-edge
arc stitching between features), so per-ring Douglas–Peucker preserves each
feature's own closed, non-degenerate topology without creating cross-feature
slivers. Shared-arc preservation across features (a TopoJSON concern) is
deliberately out of scope.

Run directly::

    python3 -m pipeline.geometry --in pipeline/out/selected_locations.csv \
        --source fixture --out pipeline/out/selected_geometry.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

# Fixture polygon radius (degrees) by catchment type. Rural county catchments
# read a touch larger than metro CBSAs so the two are visually distinguishable.
_FIXTURE_RADIUS_DEG = {"County": 0.55, "CBSA": 0.70}
_FIXTURE_VERTICES = 6
MAX_VERTICES = 120  # decimation cap per ring for real TIGER rings.
SIMPLIFY_EPSILON_DEG = 0.01  # Douglas–Peucker tolerance (~1 km at mid-latitudes).

# State FIPS handled specially on the map (non-contiguous / antimeridian).
ALASKA_FIPS = "02"
HAWAII_FIPS = "15"


def _feature(row: dict, geometry: dict, *, geometry_kind: str, extra_props: dict | None = None) -> dict:
    props = {
        "catchment_type": row["catchment_type"],
        "catchment_code": str(row["catchment_code"]).zfill(5),
        "catchment_label": row.get("catchment_label", ""),
        "climate_region": row.get("climate_region", ""),
        "urbanicity_short": row.get("urbanicity_short", ""),
        "geometry_kind": geometry_kind,
    }
    if extra_props:
        props.update(extra_props)
    return {"type": "Feature", "properties": props, "geometry": geometry}


# ---------------------------------------------------------------------------
# Offline fixture polygons
# ---------------------------------------------------------------------------


def _fixture_polygon(row: dict) -> list:
    lon = float(row["centroid_lon"])
    lat = float(row["centroid_lat"])
    radius = _FIXTURE_RADIUS_DEG.get(str(row["catchment_type"]), 0.6)
    # Squash longitude radius by latitude so the shape isn't wildly stretched.
    lon_scale = 1.0 / max(math.cos(math.radians(lat)), 0.2)
    ring = []
    for i in range(_FIXTURE_VERTICES):
        theta = (2 * math.pi * i) / _FIXTURE_VERTICES + math.pi / 6
        ring.append(
            [
                round(lon + radius * lon_scale * math.cos(theta), 5),
                round(lat + radius * math.sin(theta), 5),
            ]
        )
    ring.append(ring[0])  # close the ring
    return [ring]


def fixture_features(rows: list[dict]) -> list[dict]:
    return [
        _feature(
            row,
            {"type": "Polygon", "coordinates": _fixture_polygon(row)},
            geometry_kind="synthetic",
            extra_props={"validation": "ok"},
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Geometry simplification, normalisation, and validation (pure; testable)
# ---------------------------------------------------------------------------


def _perpendicular_distance(point: list, start: list, end: list) -> float:
    """Distance from ``point`` to the segment ``start``–``end`` (degree units)."""

    (x, y), (x1, y1), (x2, y2) = point, start, end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    # Distance from point to the infinite line through start/end.
    return abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.hypot(dx, dy)


def _douglas_peucker(points: list, epsilon: float) -> list:
    """Ramer–Douglas–Peucker line simplification (iterative, no recursion limit)."""

    if len(points) <= 2:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        dmax, index = 0.0, start
        for i in range(start + 1, end):
            d = _perpendicular_distance(points[i], points[start], points[end])
            if d > dmax:
                dmax, index = d, i
        if dmax > epsilon:
            keep[index] = True
            stack.append((start, index))
            stack.append((index, end))
    return [p for p, k in zip(points, keep, strict=True) if k]


def _decimate(ring: list, max_vertices: int) -> list:
    """Hard cap: keep at most ``max_vertices`` points, preserving closure."""

    if len(ring) <= max_vertices:
        return ring
    step = math.ceil(len(ring) / max_vertices)
    thinned = ring[::step]
    if thinned[-1] != ring[-1]:
        thinned.append(ring[-1])
    return thinned


def simplify_ring(ring: list, epsilon: float = SIMPLIFY_EPSILON_DEG, max_vertices: int = MAX_VERTICES) -> list:
    """Topology-preserving per-ring simplification with a hard vertex cap.

    Douglas–Peucker keeps the ring's shape; the cap guards payload size when a
    very intricate boundary survives simplification. The ring is always returned
    closed (first vertex repeated) and with at least 4 points.
    """

    if len(ring) <= 4:
        return ring
    simplified = _douglas_peucker(ring, epsilon)
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    if len(simplified) > max_vertices:
        simplified = _decimate(simplified, max_vertices)
        if simplified[0] != simplified[-1]:
            simplified.append(simplified[0])
    # Guarantee a drawable ring.
    if len(simplified) < 4:
        return ring
    return simplified


def _ring_crosses_antimeridian(ring: list) -> bool:
    lons = [pt[0] for pt in ring]
    return (max(lons) - min(lons)) > 180.0


def normalize_antimeridian(ring: list) -> tuple[list, bool]:
    """Shift western-hemisphere longitudes by +360 when a ring straddles ±180.

    Alaska's Aleutian rings cross the antimeridian; left untouched they render as
    a band spanning the whole map. Returns ``(ring, adjusted)``.
    """

    if not _ring_crosses_antimeridian(ring):
        return ring, False
    shifted = [[lon + 360.0 if lon < 0 else lon, lat] for lon, lat in ring]
    return shifted, True


def validate_geometry(geometry: dict) -> list[str]:
    """Return a list of structural problems with a GeoJSON geometry (empty = ok)."""

    issues: list[str] = []
    gtype = geometry.get("type")
    if gtype not in ("Polygon", "MultiPolygon"):
        return [f"unsupported geometry type: {gtype!r}"]
    polygons = geometry["coordinates"] if gtype == "MultiPolygon" else [geometry["coordinates"]]
    if not polygons:
        return ["geometry has no polygons"]
    for p, polygon in enumerate(polygons):
        if not polygon:
            issues.append(f"polygon {p} has no rings")
            continue
        for r, ring in enumerate(polygon):
            if len(ring) < 4:
                issues.append(f"polygon {p} ring {r} has fewer than 4 vertices")
                continue
            if ring[0] != ring[-1]:
                issues.append(f"polygon {p} ring {r} is not closed")
            for lon, lat in ring:
                if not (math.isfinite(lon) and math.isfinite(lat)):
                    issues.append(f"polygon {p} ring {r} has a non-finite coordinate")
                    break
                if not (-90.0 <= lat <= 90.0):
                    issues.append(f"polygon {p} ring {r} latitude out of range: {lat}")
                    break
                if not (-180.0 <= lon <= 360.0):  # allow +360 antimeridian shift
                    issues.append(f"polygon {p} ring {r} longitude out of range: {lon}")
                    break
    return issues


def geometry_from_tiger(geom: dict, *, epsilon: float = SIMPLIFY_EPSILON_DEG) -> tuple[dict, bool]:
    """Convert a TIGERweb GeoJSON geometry into a simplified, validated geometry.

    Keeps all parts of a MultiPolygon (islands and detached pieces are not
    dropped), simplifies every ring, and normalises antimeridian-crossing rings.
    Returns ``(geometry, antimeridian_adjusted)``.
    """

    gtype = geom.get("type")
    adjusted_any = False

    def _process_polygon(polygon: list) -> list:
        nonlocal adjusted_any
        out_rings = []
        for ring in polygon:
            ring2, adjusted = normalize_antimeridian(ring)
            adjusted_any = adjusted_any or adjusted
            out_rings.append(simplify_ring(ring2, epsilon))
        return out_rings

    if gtype == "Polygon":
        return {"type": "Polygon", "coordinates": _process_polygon(geom["coordinates"])}, adjusted_any
    if gtype == "MultiPolygon":
        polys = [_process_polygon(poly) for poly in geom["coordinates"]]
        # Collapse a single-part MultiPolygon to a Polygon for simplicity.
        if len(polys) == 1:
            return {"type": "Polygon", "coordinates": polys[0]}, adjusted_any
        return {"type": "MultiPolygon", "coordinates": polys}, adjusted_any
    raise ValueError(f"unsupported TIGER geometry type: {gtype!r}")


# ---------------------------------------------------------------------------
# Live TIGER/Line source (runs on a machine with network)
# ---------------------------------------------------------------------------

# TIGERweb cartographic layers: county and CBSA polygons returned as GeoJSON.
TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
_LAYERS = {
    "County": (f"{TIGERWEB}/State_County/MapServer/13/query",),
    # Boundary-consistent Census 2020 CBSA layers: metro + micro. Layer 0 is
    # Combined Statistical Areas (CSA), not individual CBSAs.
    "CBSA": (
        f"{TIGERWEB}/CBSA/MapServer/26/query",
        f"{TIGERWEB}/CBSA/MapServer/27/query",
    ),
}
_CODE_FIELD = {"County": "GEOID", "CBSA": "GEOID"}


def _require(module: str):
    try:
        return __import__(module)
    except ImportError as exc:  # pragma: no cover - only hit when deps missing
        raise SystemExit(
            f"--source api needs the '{module}' package. Install it with " f"`pip install {module}` and retry."
        ) from exc


def _retrying_session(requests):
    """Requests session with bounded retry/backoff for TIGERweb."""

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


def _tiger_geometry(session, catchment_type: str, code: str) -> dict | None:  # pragma: no cover - network
    field = _CODE_FIELD[catchment_type]
    for url in _LAYERS[catchment_type]:
        params = {
            "where": f"{field}='{str(code).zfill(5)}'",
            "outFields": field,
            "returnGeometry": "true",
            "f": "geojson",
            "geometryPrecision": "5",
            "outSR": "4326",
        }
        resp = session.get(url, params=params, timeout=120)
        resp.raise_for_status()
        payload = resp.json()
        features = payload.get("features") or []
        if features:
            return features[0].get("geometry") or None
    return None


def api_features(rows: list[dict]) -> tuple[list[dict], list[dict]]:  # pragma: no cover - needs network
    requests = _require("requests")
    session = _retrying_session(requests)
    features = []
    errors = []
    for row in rows:
        ctype = str(row["catchment_type"])
        code = str(row["catchment_code"]).zfill(5)
        fetch_error = ""
        try:
            raw = _tiger_geometry(session, ctype, code)
        except Exception as exc:
            raw = None
            fetch_error = f"TIGER request failed: {exc}"
        if raw is None:
            # Fall back to a synthetic marker so every selection still maps.
            note = fetch_error or "no TIGER feature found"
            features.append(
                _feature(
                    row,
                    {"type": "Polygon", "coordinates": _fixture_polygon(row)},
                    geometry_kind="synthetic_fallback",
                    extra_props={"validation": "ok", "note": f"{note}; synthetic fallback"},
                )
            )
            errors.append({"catchment_type": ctype, "catchment_code": code, "error": note})
            continue
        geom, adjusted = geometry_from_tiger(raw)
        issues = validate_geometry(geom)
        extra = {
            "validation": "ok" if not issues else "; ".join(issues),
            "antimeridian_adjusted": adjusted,
            "state_fips": code[:2] if ctype == "County" else "",
            "non_contiguous_state": (ctype == "County" and code[:2] in (ALASKA_FIPS, HAWAII_FIPS)),
        }
        features.append(_feature(row, geom, geometry_kind="tiger_cb_simplified", extra_props=extra))
        if issues:
            errors.append({"catchment_type": ctype, "catchment_code": code, "error": "; ".join(issues)})
    return features, errors


# ---------------------------------------------------------------------------
# Public helper used by build_catchments + entry point
# ---------------------------------------------------------------------------


def feature_collection(rows: list[dict], source: str = "fixture") -> dict:
    if source == "api":
        features, errors = api_features(rows)
        note = "Simplified Census TIGER/Line cartographic boundaries (Douglas–Peucker, MultiPolygon-aware)."
        invalid = sum(1 for f in features if f["properties"].get("validation") not in ("ok", None))
        metadata = {
            "source": source,
            "note": note,
            "tigerweb_service": TIGERWEB,
            "simplify_epsilon_deg": SIMPLIFY_EPSILON_DEG,
            "max_vertices_per_ring": MAX_VERTICES,
            "feature_count": len(features),
            "features_with_validation_issues": invalid,
            "fetch_errors": errors,
        }
    else:
        features = fixture_features(rows)
        metadata = {
            "source": source,
            "note": "Synthetic placeholder polygons (offline fixture).",
            "feature_count": len(features),
            "features_with_validation_issues": 0,
        }
    # NOTE: the geometry collection is intentionally timestamp-free so it stays
    # byte-reproducible across runs (provenance timestamps live in
    # selection_metadata.json and the crosswalk/QC sidecars).
    return {"type": "FeatureCollection", "metadata": metadata, "features": features}


def main(argv: list[str] | None = None) -> Path:
    from . import config

    parser = argparse.ArgumentParser(description="Emit simplified catchment polygons (GeoJSON).")
    parser.add_argument("--in", dest="in_path", type=Path, default=config.OUT_DIR / "selected_locations.csv")
    parser.add_argument("--source", choices=["fixture", "api"], default="fixture")
    parser.add_argument("--out", type=Path, default=config.OUT_DIR / "selected_geometry.json")
    args = parser.parse_args(argv)

    with args.in_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    collection = feature_collection(rows, args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"[geometry] source={args.source} wrote {len(collection['features'])} features -> {args.out}")
    return args.out


if __name__ == "__main__":
    main()
