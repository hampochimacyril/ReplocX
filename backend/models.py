"""Scenario validation models for the Representative Location Explorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_WEIGHTS = {
    "housing_unit_coverage_percentile": 0.45,
    "population_density_percentile": 0.35,
    "population_coverage_percentile": 0.20,
}


@dataclass(frozen=True)
class Override:
    climate_region: str
    urbanicity: str
    catchment_type: str
    catchment_code: str
    rationale: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Override":
        required = [
            "climate_region",
            "urbanicity",
            "catchment_type",
            "catchment_code",
            "rationale",
        ]
        missing = [name for name in required if not str(payload.get(name, "")).strip()]
        if missing:
            raise ValueError(f"Override is missing: {', '.join(missing)}")
        catchment_type = str(payload["catchment_type"]).strip()
        if catchment_type not in {"CBSA", "County"}:
            raise ValueError("Override catchment_type must be CBSA or County.")
        return cls(
            climate_region=str(payload["climate_region"]).strip(),
            urbanicity=str(payload["urbanicity"]).strip(),
            catchment_type=catchment_type,
            catchment_code=str(payload["catchment_code"]).strip().zfill(5),
            rationale=str(payload["rationale"]).strip(),
        )


# No location is given a research-priority override by default. Overrides remain a
# fully supported, user-supplied feature, but the baseline scenario applies none.


@dataclass(frozen=True)
class ScenarioConfig:
    version: str = "1.0"
    name: str = "Baseline research scenario"
    density_screen_percentile: float = 0.60
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    unique_location_constraint: bool = True
    max_station_distance_miles: float = 250.0
    station_distance_penalty: float = 0.0
    require_weather_qc: bool = False
    overrides: tuple[Override, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "ScenarioConfig":
        payload = payload or {}
        weights = dict(DEFAULT_WEIGHTS)
        weights.update(payload.get("weights", {}))
        weights = {key: float(value) for key, value in weights.items()}
        expected = set(DEFAULT_WEIGHTS)
        if set(weights) != expected:
            raise ValueError(f"Score weights must contain exactly: {', '.join(sorted(expected))}")
        if abs(sum(weights.values()) - 1.0) > 1e-9:
            raise ValueError("Score weights must sum to 1.0.")
        if any(value < 0 for value in weights.values()):
            raise ValueError("Score weights cannot be negative.")

        density = float(payload.get("density_screen_percentile", 0.60))
        if not 0 <= density <= 1:
            raise ValueError("Density-screen percentile must be between 0 and 1.")

        max_distance = float(payload.get("max_station_distance_miles", 250.0))
        if max_distance <= 0:
            raise ValueError("Maximum station distance must be greater than zero.")

        penalty = float(payload.get("station_distance_penalty", 0.0))
        if not 0 <= penalty <= 1:
            raise ValueError("Station-distance penalty must be between 0 and 1.")

        supplied_overrides = payload.get("overrides")
        if supplied_overrides is None:
            overrides = ()
        else:
            overrides = tuple(Override.from_dict(item) for item in supplied_overrides)

        return cls(
            version=str(payload.get("version", "1.0")),
            name=str(payload.get("name", "User-defined scenario")).strip() or "User-defined scenario",
            density_screen_percentile=density,
            weights=weights,
            unique_location_constraint=bool(payload.get("unique_location_constraint", True)),
            max_station_distance_miles=max_distance,
            station_distance_penalty=penalty,
            require_weather_qc=bool(payload.get("require_weather_qc", False)),
            overrides=overrides,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["overrides"] = [asdict(item) for item in self.overrides]
        return payload

