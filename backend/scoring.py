"""Deterministic scoring and allocation for representative locations."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import replace
from statistics import median
from typing import Any

from .models import DEFAULT_OVERRIDE, ScenarioConfig

CLIMATE_ORDER = [
    "Cold & Very Cold",
    "Hot-Dry & Mixed Dry",
    "Hot-Humid",
    "Marine",
    "Mixed-Humid",
]
URBANICITY_ORDER = [
    "higher density urban",
    "lower density urban",
    "suburban/small town",
    "rural",
]
STRATA = [(climate, urbanicity) for climate in CLIMATE_ORDER for urbanicity in URBANICITY_ORDER]


def _stratum(row: dict[str, Any]) -> tuple[str, str]:
    return row["climate_region"], row["urbanicity"]


def _key(row: dict[str, Any]) -> str:
    return f"{row['catchment_type']}:{str(row['catchment_code']).zfill(5)}"


def _score(row: dict[str, Any], config: ScenarioConfig) -> float:
    score = sum(float(row[column]) * weight for column, weight in config.weights.items())
    if config.station_distance_penalty:
        distance_ratio = min(float(row["station_distance_miles"]) / config.max_station_distance_miles, 1.0)
        score -= config.station_distance_penalty * distance_ratio
    return round(score, 12)


def _sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -float(row["scenario_score"]),
        -int(row["housing_units_2010"]),
        -float(row["population_density_sqmi"]),
        float(row["station_distance_miles"]),
        row["location_uniqueness_key"],
    )


def _eligible_rows(candidates: Iterable[dict[str, Any]], config: ScenarioConfig) -> list[dict[str, Any]]:
    result = []
    for source in candidates:
        row = deepcopy(source)
        row["location_uniqueness_key"] = _key(row)
        row["scenario_score"] = _score(row, config)
        row["scenario_selected"] = False
        row["scenario_rank"] = None
        row["scenario_note"] = ""
        row["scenario_score_loss_vs_independent_top"] = None
        row["scenario_eligible"] = (
            float(row["population_density_percentile"]) >= config.density_screen_percentile
            and float(row["station_distance_miles"]) <= config.max_station_distance_miles
            and (not config.require_weather_qc or row.get("hourly_weather_qc_status") == "COMPLETE")
        )
        result.append(row)
    return result


def data_compatible_default_config(
    candidates: list[dict[str, Any]],
    config: ScenarioConfig | None = None,
) -> ScenarioConfig:
    """Drop only the implicit Philadelphia default when this dataset cannot use it.

    Recorded/demo data classify Philadelphia in Mixed-Humid HDU, while a live
    tract-derived vintage may classify the same CBSA differently. The baseline
    must not force a geography into the wrong stratum. Explicit user-supplied
    overrides bypass this helper and retain the normal fail-loud behavior.
    """

    candidate_config = config or ScenarioConfig.from_dict(None)
    if candidate_config.overrides != (DEFAULT_OVERRIDE,):
        return candidate_config
    eligible = _eligible_rows(candidates, candidate_config)
    available = any(
        row["scenario_eligible"]
        and row["climate_region"] == DEFAULT_OVERRIDE.climate_region
        and row["urbanicity"] == DEFAULT_OVERRIDE.urbanicity
        and row["catchment_type"] == DEFAULT_OVERRIDE.catchment_type
        and str(row["catchment_code"]).zfill(5) == DEFAULT_OVERRIDE.catchment_code
        for row in eligible
    )
    return candidate_config if available else replace(candidate_config, overrides=())


def _group_rank(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {stratum: [] for stratum in STRATA}
    for row in rows:
        if row["scenario_eligible"]:
            grouped[_stratum(row)].append(row)
    for stratum, subset in grouped.items():
        subset.sort(key=_sort_key)
        for rank, row in enumerate(subset, start=1):
            row["scenario_rank"] = rank
        if not subset:
            raise ValueError(f"No eligible candidates remain for {stratum[0]} / {stratum[1]}.")
    return grouped


def _override_map(config: ScenarioConfig) -> dict[tuple[str, str], Any]:
    result = {}
    for override in config.overrides:
        key = (override.climate_region, override.urbanicity)
        if key not in STRATA:
            raise ValueError(f"Override stratum is not recognized: {key[0]} / {key[1]}.")
        if key in result:
            raise ValueError(f"Only one override is allowed for {key[0]} / {key[1]}.")
        result[key] = override
    return result


def _apply_override(subset: list[dict[str, Any]], override: Any | None) -> list[dict[str, Any]]:
    if override is None:
        return subset
    matches = [
        row
        for row in subset
        if row["catchment_type"] == override.catchment_type
        and str(row["catchment_code"]).zfill(5) == override.catchment_code
    ]
    if not matches:
        raise ValueError(
            f"Override candidate is not eligible for {override.climate_region} / "
            f"{override.urbanicity}: {override.catchment_type} {override.catchment_code}."
        )
    return matches


def independent_selection(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    config: ScenarioConfig,
    apply_overrides: bool = False,
) -> list[dict[str, Any]]:
    override_by_stratum = _override_map(config) if apply_overrides else {}
    selected = []
    for stratum in STRATA:
        subset = _apply_override(grouped[stratum], override_by_stratum.get(stratum))
        selected.append(subset[0])
    return selected


def distinct_selection(
    grouped: dict[tuple[str, str], list[dict[str, Any]]],
    config: ScenarioConfig,
    apply_overrides: bool = True,
) -> list[dict[str, Any]]:
    """Assign one distinct catchment to every stratum with a min-cost flow."""

    overrides = _override_map(config) if apply_overrides else {}
    source = ("source",)
    sink = ("sink",)
    graph: dict[tuple[Any, ...], list[dict[str, Any]]] = {}

    def add_edge(
        start: tuple[Any, ...],
        end: tuple[Any, ...],
        capacity: int,
        cost: float,
        row: dict[str, Any] | None = None,
    ) -> None:
        graph.setdefault(start, [])
        graph.setdefault(end, [])
        graph[start].append({"to": end, "rev": len(graph[end]), "capacity": capacity, "cost": cost, "row": row})
        graph[end].append({"to": start, "rev": len(graph[start]) - 1, "capacity": 0, "cost": -cost, "row": None})

    locations = sorted({row["location_uniqueness_key"] for subset in grouped.values() for row in subset})
    for location in locations:
        add_edge(("location", location), sink, 1, 0.0)

    for stratum in STRATA:
        node = ("stratum", *stratum)
        add_edge(source, node, 1, 0.0)
        subset = _apply_override(grouped[stratum], overrides.get(stratum))
        seen = set()
        for row in subset:
            location = row["location_uniqueness_key"]
            if location in seen:
                continue
            seen.add(location)
            add_edge(node, ("location", location), 1, -float(row["scenario_score"]), row)

    flow = 0
    while flow < len(STRATA):
        distance = {source: 0.0}
        previous: dict[tuple[Any, ...], tuple[tuple[Any, ...], int]] = {}
        queue = deque([source])
        queued = {source}
        while queue:
            current = queue.popleft()
            queued.remove(current)
            for edge_index, edge in enumerate(graph[current]):
                if edge["capacity"] <= 0:
                    continue
                target = edge["to"]
                new_distance = distance[current] + edge["cost"]
                if new_distance < distance.get(target, float("inf")) - 1e-12:
                    distance[target] = new_distance
                    previous[target] = (current, edge_index)
                    if target not in queued:
                        queue.append(target)
                        queued.add(target)
        if sink not in previous:
            raise ValueError("The distinct-location constraint cannot assign all 20 strata.")
        current = sink
        while current != source:
            prior, edge_index = previous[current]
            edge = graph[prior][edge_index]
            edge["capacity"] -= 1
            graph[current][edge["rev"]]["capacity"] += 1
            current = prior
        flow += 1

    selected = []
    for stratum in STRATA:
        node = ("stratum", *stratum)
        matched = [edge["row"] for edge in graph[node] if edge["row"] is not None and edge["capacity"] == 0]
        if len(matched) != 1:
            raise ValueError(f"Allocation returned an invalid assignment for {stratum[0]} / {stratum[1]}.")
        selected.append(matched[0])
    return selected


def _annotate(
    selected: list[dict[str, Any]],
    independent: list[dict[str, Any]],
    config: ScenarioConfig,
) -> list[dict[str, Any]]:
    independent_by_stratum = {_stratum(row): row for row in independent}
    overrides = _override_map(config)
    result = []
    for row in selected:
        item = deepcopy(row)
        top = independent_by_stratum[_stratum(item)]
        loss = round(float(top["scenario_score"]) - float(item["scenario_score"]), 12)
        item["scenario_selected"] = True
        item["scenario_score_loss_vs_independent_top"] = loss
        override = overrides.get(_stratum(item))
        if override:
            item["scenario_note"] = f"{override.rationale} Unconstrained rank: {item['scenario_rank']}."
        elif item["scenario_rank"] == 1:
            item["scenario_note"] = "Top-ranked candidate retained."
        else:
            item["scenario_note"] = (
                "Distinct-location allocation selected this lower-ranked alternative "
                f"to preserve national coverage. Unconstrained rank: {item['scenario_rank']}."
            )
        result.append(item)
    return result


def evaluate(candidates: list[dict[str, Any]], config: ScenarioConfig) -> dict[str, Any]:
    rows = _eligible_rows(candidates, config)
    grouped = _group_rank(rows)
    independent = independent_selection(grouped, config, apply_overrides=False)
    distinct = distinct_selection(grouped, config, apply_overrides=False)
    scenario = (
        distinct_selection(grouped, config, apply_overrides=True)
        if config.unique_location_constraint
        else independent_selection(grouped, config, apply_overrides=True)
    )
    scenario = _annotate(scenario, independent, config)
    independent = _annotate(independent, independent, ScenarioConfig.from_dict({"overrides": []}))
    distinct = _annotate(distinct, independent, ScenarioConfig.from_dict({"overrides": []}))
    independent_keys = {_stratum(row): row["location_uniqueness_key"] for row in independent}
    changes = [
        {
            "climate_region": row["climate_region"],
            "urbanicity": row["urbanicity"],
            "urbanicity_short": row["urbanicity_short"],
            "from_key": independent_keys[_stratum(row)],
            "from_label": next(item["catchment_label"] for item in independent if _stratum(item) == _stratum(row)),
            "to_key": row["location_uniqueness_key"],
            "to_label": row["catchment_label"],
            "score_loss": row["scenario_score_loss_vs_independent_top"],
            "reason": row["scenario_note"],
        }
        for row in scenario
        if independent_keys[_stratum(row)] != row["location_uniqueness_key"]
    ]
    scenario_scores = [float(row["scenario_score"]) for row in scenario]
    scenario_distances = [float(row["station_distance_miles"]) for row in scenario]
    scenario_ranks = [int(row["scenario_rank"]) for row in scenario if row.get("scenario_rank")]
    combined_score = round(sum(scenario_scores), 6)
    independent_combined_score = round(sum(float(row["scenario_score"]) for row in independent), 6)
    # Coverage efficiency expresses how much total composite score the distinct
    # coverage rules retain relative to the unconstrained per-stratum tops
    # (1.0 = no representativeness cost). It is descriptive only and does not
    # influence selection.
    coverage_efficiency = round(combined_score / independent_combined_score, 6) if independent_combined_score else None
    return {
        "config": config.to_dict(),
        "independent": independent,
        "distinct": distinct,
        "selected": scenario,
        "changes": changes,
        "summary": {
            "strata_count": len(scenario),
            "represented_location_count": len({row["location_uniqueness_key"] for row in scenario}),
            "independent_location_count": len({row["location_uniqueness_key"] for row in independent}),
            "distinct_location_count": len({row["location_uniqueness_key"] for row in distinct}),
            "combined_score": combined_score,
            "independent_combined_score": independent_combined_score,
            "score_difference": round(combined_score - independent_combined_score, 6),
            "changed_assignment_count": len(changes),
            "eligible_candidate_count": sum(row["scenario_eligible"] for row in rows),
            # Additive descriptive diagnostics (do not affect selection).
            "coverage_efficiency": coverage_efficiency,
            "min_scenario_score": round(min(scenario_scores), 6) if scenario_scores else None,
            "median_scenario_score": round(median(scenario_scores), 6) if scenario_scores else None,
            "mean_station_distance_miles": (
                round(sum(scenario_distances) / len(scenario_distances), 3) if scenario_distances else None
            ),
            "max_station_distance_miles": round(max(scenario_distances), 3) if scenario_distances else None,
            "mean_unconstrained_rank": (
                round(sum(scenario_ranks) / len(scenario_ranks), 3) if scenario_ranks else None
            ),
        },
    }
