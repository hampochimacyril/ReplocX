"""Shared dispatch for the private Atlas surfaces (``/results`` + ``/equity``).

Both entry points (the dependency-free ``server.py`` and the managed
``fastapi_app.py``) route the Atlas API through this single table so the two
servers stay in lockstep. Paths here use the normalised legacy form
(``/api/results/...``) that both entry points map ``/api/v1/...`` onto.
"""

from __future__ import annotations

from typing import Any

from .atlas_service import get_atlas

ATLAS_PREFIXES = ("/api/results", "/api/equity")


def is_atlas_path(api_path: str) -> bool:
    return any(api_path == p or api_path.startswith(f"{p}/") for p in ATLAS_PREFIXES)


def handle_atlas(api_path: str, params: dict[str, str]) -> dict[str, Any]:
    """Resolve an Atlas GET to its payload.

    Raises :class:`AtlasUnavailableError` when the feature is disabled or the
    data domain is missing (surfaced as HTTP 404 so the public demo never hints
    at the unpublished results), :class:`ValueError` for bad parameters (400),
    and :class:`LookupError` for an unknown Atlas route (404).
    """

    atlas = get_atlas()
    tier = params.get("tier", "annual")
    dimension = params.get("dimension", "climate")

    routes = {
        "/api/results/overview": lambda: atlas.overview(),
        "/api/results/scenario-dictionary": lambda: atlas.scenario_dictionary(),
        "/api/results/scenario-summary": lambda: atlas.scenario_summary(tier),
        "/api/results/by-stratum": lambda: atlas.by_stratum(tier, dimension),
        "/api/results/scenario-c": lambda: atlas.scenario_c(tier),
        "/api/results/d-comparisons": lambda: atlas.d_comparisons(tier),
        "/api/results/differential": lambda: atlas.differential(tier),
        "/api/results/figures": lambda: atlas.figures(),
        "/api/results/figure-source": lambda: atlas.figure_source(params.get("figure_id", "")),
        "/api/results/figure-bundle": lambda: atlas.figure_bundle(params.get("figure_id", "")),
        "/api/results/exports": lambda: atlas.exports_catalog(),
        "/api/results/export-view": lambda: atlas.export_view(
            params.get("view", "scenario-summary"),
            tier,
            dimension,
            params.get("scenario", "D"),
        ),
        "/api/results/cooling-seasons": lambda: atlas.cooling_seasons(),
        "/api/results/sensitivity": lambda: atlas.sensitivity(),
        "/api/results/provenance": lambda: atlas.results_provenance(),
        "/api/equity/profiles": lambda: atlas.equity_profiles(),
        "/api/equity/scenario-cross": lambda: atlas.equity_scenario_cross(params.get("scenario", "D"), dimension),
    }
    handler = routes.get(api_path)
    if handler is None:
        raise LookupError("Atlas route not found.")
    return handler()
