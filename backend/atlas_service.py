"""Read-only accessor for the private ReplocX Research Atlas results tier.

The Atlas serves the certified ``replocx_tmy3_wallfix_4scen`` domain: 720
simulation cells, scenario order A/C/B/D, R9 certification, and f2v3 final
figure registry records only. It deliberately does not fall back to the legacy
bundled Atlas scaffold.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
LEGACY_ATLAS_DIR = APP_ROOT / "data" / "atlas"

ENABLE_ENV = "RLE_ENABLE_ATLAS"
DATA_DIR_ENV = "RLE_ATLAS_DATA_DIR"
FIGURE_DIR_ENV = "RLE_ATLAS_FIGURE_DIR"

CERTIFIED_TIER_ID = "replocx_tmy3_wallfix_4scen"
CERTIFIED_CELL_COUNT = 720
FIGURE_REGISTRY_TIER = "f2v3_final"
SCHEMA_VERSION = "atlas.w1/1.0"

CANONICAL_DATA_ROOT = Path(
    "/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/"
    "PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/"
    "replocx_tmy3_wallfix_4scen"
)
CANONICAL_FIGURE_ROOT = Path(
    "/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/"
    "PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/20_FIGURES/"
    "replocx_tmy3_wallfix_4scen/f2v3_final"
)

EXPECTED_SCENARIO_ORDER = ("A", "C", "B", "D")
EXPECTED_PRIMARY_ENDPOINT_FAMILIES = (
    "op_temp_mean_c",
    "op_temp_p95_true_c",
    "humidity_ratio_mean_kgkg",
    "humidity_ratio_p95_true_kgkg",
)
TIERS = ("annual", "seasonal")
STRATUM_DIMENSIONS: dict[str, tuple[str, str]] = {
    "climate": ("by_climate_region_scenario", "climate_region"),
    "urbanicity": ("by_urbanicity_scenario", "urbanicity"),
    "building": ("by_building_type_scenario", "building_type"),
    "vintage": ("by_vintage_group_scenario", "vintage_group"),
}
STORY_COMPARISON_ORDER = ("D-B", "D-C", "D-A")
PENDING_EQUITY_LAYERS = (
    "CDC SVI percentile",
    "Census ACS income and poverty",
    "DOE LEAD energy burden",
    "heat-health vulnerability",
)
ALLOWED_EQUITY_BADGES = {"Direct", "Proxy", "Modeled", "REVIEW REQUIRED"}
EQUITY_LAYER_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "cdc_svi",
        "label": "CDC/ATSDR SVI percentile",
        "value_fields": ("svi_percentile", "cdc_svi_percentile"),
        "value_label": "Overall SVI percentile",
        "source_field": "svi_source_vintage",
        "badge_field": "svi_proxy_badge",
        "uncertainty_field": "svi_join_uncertainty_note",
        "default_source_vintage": (
            "CDC/ATSDR SVI 2022; census-tract percentile fields RPL_THEMES/RPL_THEME1-4; "
            "catchment rollup not verified in this checkout."
        ),
        "default_proxy_badge": "REVIEW REQUIRED",
        "default_join_uncertainty_note": (
            "No sidecar-backed tract-to-catchment SVI crosswalk was found in the certified Atlas tree."
        ),
        "geography_level": "Census tract source; catchment rollup required.",
        "source_url": "https://www.atsdr.cdc.gov/place-health/php/svi/index.html",
    },
    {
        "id": "acs_income_poverty",
        "label": "ACS median income and poverty",
        "value_fields": ("acs_median_hh_income", "acs_poverty_rate"),
        "value_label": "Median household income / poverty rate",
        "source_field": "acs_source_vintage",
        "badge_field": "acs_proxy_badge",
        "uncertainty_field": "acs_join_uncertainty_note",
        "default_source_vintage": (
            "U.S. Census Bureau ACS 2019-2023 5-year; median-household-income and poverty "
            "estimates/MOEs required when supplied; catchment rollup not verified in this checkout."
        ),
        "default_proxy_badge": "REVIEW REQUIRED",
        "default_join_uncertainty_note": (
            "No sidecar-backed ACS geography-to-catchment aggregation file was found in the certified Atlas tree."
        ),
        "geography_level": "ACS tract/CBSA/county source; catchment rollup required.",
        "source_url": "https://www.census.gov/data/developers/data-sets/acs-5year.html",
    },
    {
        "id": "doe_lead_energy_burden",
        "label": "DOE LEAD energy burden",
        "value_fields": ("doe_lead_energy_burden_pct", "lead_energy_burden_pct"),
        "value_label": "Energy burden percent",
        "source_field": "doe_lead_source_vintage",
        "badge_field": "doe_lead_proxy_badge",
        "uncertainty_field": "doe_lead_join_uncertainty_note",
        "default_source_vintage": (
            "DOE LEAD Tool energy-burden source; source vintage and catchment geography join are not verified "
            "in this checkout."
        ),
        "default_proxy_badge": "REVIEW REQUIRED",
        "default_join_uncertainty_note": (
            "No sidecar-backed DOE LEAD-to-catchment join file was found in the certified Atlas tree."
        ),
        "geography_level": "LEAD geography source; catchment join required.",
        "source_url": "https://www.energy.gov/cmei/scep/slsc/lead-tool",
    },
    {
        "id": "heat_vulnerability",
        "label": "Heat-health vulnerability",
        "value_fields": ("heat_vuln_index", "heat_vulnerability_index"),
        "value_label": "Heat vulnerability index",
        "source_field": "heat_vuln_source_vintage",
        "badge_field": "heat_vuln_proxy_badge",
        "uncertainty_field": "heat_vuln_join_uncertainty_note",
        "default_source_vintage": (
            "Modeled heat-health vulnerability composite; source model and catchment join are not verified "
            "in this checkout."
        ),
        "default_proxy_badge": "REVIEW REQUIRED",
        "default_join_uncertainty_note": (
            "No certified vulnerability-model sidecar or catchment rollup was found in the Atlas tree."
        ),
        "geography_level": "Modeled proxy; catchment rollup required.",
        "source_url": "",
    },
)


def atlas_enabled() -> bool:
    """Whether the private Atlas surface is enabled on this deployment."""

    return os.environ.get(ENABLE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


class AtlasUnavailableError(RuntimeError):
    """Raised when the Atlas is disabled or its data domain cannot be loaded."""


def _num(value: Any) -> Any:
    """Coerce a CSV cell to float/int/bool where possible; keep blanks as ``None``."""

    text = str(value).strip()
    if text == "":
        return None
    try:
        if any(ch in text for ch in ".eE") and text.lower() not in {"true", "false"}:
            return float(text)
        return int(text)
    except ValueError:
        if text in {"True", "False"}:
            return text == "True"
        return text


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{k: _num(v) for k, v in row.items()} for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mean(values: list[Any]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    return sum(nums) / len(nums) if nums else None


def _strings_in(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_strings_in(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(_strings_in(item))
        return out
    return []


class AtlasService:
    """Lazily loads certified Atlas CSVs and serves shaped API views."""

    def __init__(self, data_dir: Path | None = None, figure_dir: Path | None = None) -> None:
        if not atlas_enabled():
            raise AtlasUnavailableError(
                "The ReplocX Research Atlas is not enabled on this deployment. "
                f"Set {ENABLE_ENV}=1 on an approved private deployment to serve "
                "the certified TMY3 simulation results and equity context."
            )

        env_data_dir = os.environ.get(DATA_DIR_ENV)
        self.data_dir = Path(data_dir or env_data_dir or CANONICAL_DATA_ROOT).expanduser()
        self.figure_dir = self._resolve_figure_dir(figure_dir)
        self._cache: dict[str, list[dict[str, Any]]] = {}
        self._sidecar_cache: dict[str, dict[str, Any]] = {}
        self._files = self._discover_required_files()
        self._optional_files = self._discover_optional_files()

        self.audit = _read_json(self._files["audit.r9_report"])
        self.endpoint_rows = self._load("metadata.endpoint_definitions")
        self.endpoint_definitions = self._endpoint_definitions_payload()
        self.metric_notes = self._metric_notes()
        self.scenarios = self._scenario_rows()
        self.scenario_order = tuple(str(row["code"]) for row in self.scenarios)
        self.scenario_by_code = {str(row["code"]): row for row in self.scenarios}
        self.scenario_semantics = {
            code: str(row["scenario_display_label"]) for code, row in self.scenario_by_code.items()
        }

        self._assert_current_tier()

    # -- discovery and validation -----------------------------------------
    def _resolve_figure_dir(self, figure_dir: Path | None) -> Path:
        if figure_dir is not None:
            return Path(figure_dir).expanduser()
        if FIGURE_DIR_ENV in os.environ:
            return Path(os.environ[FIGURE_DIR_ENV]).expanduser()
        fixture_figures = self.data_dir / "figures" / FIGURE_REGISTRY_TIER
        if fixture_figures.exists():
            return fixture_figures
        return CANONICAL_FIGURE_ROOT

    def _discover_required_files(self) -> dict[str, Path]:
        if self._is_legacy_path(self.data_dir):
            raise AtlasUnavailableError(
                f"Atlas data directory {self.data_dir} is the legacy bundled Atlas scaffold. "
                f"Point {DATA_DIR_ENV} at the certified {CERTIFIED_TIER_ID} read-only data root."
            )
        if not self.data_dir.exists():
            raise AtlasUnavailableError(
                f"Certified Atlas data root is missing or cloud-only: {self.data_dir}. "
                f"Expected the read-only {CERTIFIED_TIER_ID} canonical tree."
            )
        if not self.figure_dir.exists():
            raise AtlasUnavailableError(
                f"Certified f2v3 figure registry root is missing or cloud-only: {self.figure_dir}."
            )

        files: dict[str, Path] = {
            "metadata.scenario_dictionary": self._find_one(self.data_dir / "metadata", "scenario_dictionary_4scen"),
            "metadata.endpoint_definitions": self._find_one(self.data_dir / "metadata", "endpoint_definitions_4scen"),
            "audit.r9_report": self._require_sidecar(self.data_dir / "audit" / "r9_reproduction_gate_report.json"),
            "figures.registry": self._find_one(self.figure_dir, "figure_registry_f2v3"),
            "figures.gate_report": self._find_one_file(self.figure_dir, "f2v3_gate_report", ".json", False),
        }

        for tier in TIERS:
            files[f"{tier}.scenario_summary"] = self._find_one(self.data_dir / tier, f"{tier}_scenario_summary")
            files[f"{tier}.scenario_c"] = self._find_one(self.data_dir / tier, f"{tier}_scenario_c_summary")
            files[f"{tier}.d_specific"] = self._find_one(self.data_dir / tier, f"{tier}_d_specific_comparisons")
            files[f"{tier}.differential"] = self._find_one(self.data_dir / tier, f"{tier}_differential_summary")
            for dimension, (suffix, _) in STRATUM_DIMENSIONS.items():
                files[f"{tier}.by_{dimension}"] = self._find_one(self.data_dir / tier, f"{tier}_{suffix}")

        return files

    def _discover_optional_files(self) -> dict[str, Path]:
        optional: dict[str, Path] = {}
        for key, directory, stem in (
            ("cooling.summary", self.data_dir / "cooling_seasons", "site_cooling_season_summary"),
            ("cooling.long_term", self.data_dir / "cooling_seasons", "site_cooling_season_long_term"),
            ("sensitivity.leave_one_location_out", self.data_dir / "sensitivity", "leave_one_location_out"),
            ("sensitivity.degreeday_year_deltas", self.data_dir / "sensitivity", "degreeday_year_deltas"),
            ("sensitivity.repro_check", self.data_dir / "sensitivity", "repro_check_report"),
        ):
            match = self._find_optional(directory, stem)
            if match is not None:
                optional[key] = match
        equity = self.data_dir / "equity_profile.csv"
        if equity.exists():
            optional["equity.profile"] = self._require_sidecar(equity)
        for key, directory, stem, suffix in (
            ("figures.qa_report", self.figure_dir, "f2v3_QA", ".json"),
            ("figures.captions", self.figure_dir, "fig_captions_alt_text_f2v3", ".md"),
        ):
            match = self._find_optional_file(directory, stem, suffix)
            if match is not None:
                optional[key] = match
        return optional

    @staticmethod
    def _is_legacy_path(path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        return (
            resolved == LEGACY_ATLAS_DIR.resolve()
            or resolved.name == "replocx_tmy3"
            or (resolved / "replocx_tmy3").exists()
        )

    def _find_one(self, directory: Path, stem: str) -> Path:
        return self._find_one_file(directory, stem, ".csv")

    def _find_one_file(self, directory: Path, stem: str, suffix: str, require_sidecar: bool = True) -> Path:
        if not directory.exists():
            raise AtlasUnavailableError(f"Missing certified Atlas directory: {directory}")
        matches = sorted(p for p in directory.glob(f"*{stem}*{suffix}") if not p.name.endswith(".prov.json"))
        if len(matches) != 1:
            raise AtlasUnavailableError(
                f"Expected exactly one certified {suffix} matching *{stem}*{suffix} in {directory}; "
                f"found {len(matches)}."
            )
        return self._require_sidecar(matches[0]) if require_sidecar else matches[0]

    def _find_optional(self, directory: Path, stem: str) -> Path | None:
        return self._find_optional_file(directory, stem, ".csv")

    def _find_optional_file(self, directory: Path, stem: str, suffix: str) -> Path | None:
        if not directory.exists():
            return None
        matches = sorted(p for p in directory.glob(f"*{stem}*{suffix}") if not p.name.endswith(".prov.json"))
        if not matches:
            return None
        if len(matches) != 1:
            raise AtlasUnavailableError(
                f"Expected at most one certified optional {suffix} matching *{stem}*{suffix} in {directory}; "
                f"found {len(matches)}."
            )
        return self._require_sidecar(matches[0])

    def _require_sidecar(self, path: Path) -> Path:
        if not path.exists():
            raise AtlasUnavailableError(f"Missing certified Atlas file: {path}")
        sidecar = Path(f"{path}.prov.json")
        if not sidecar.exists():
            raise AtlasUnavailableError(f"Missing certified provenance sidecar: {sidecar}")
        meta = _read_json(sidecar)
        tier_id = meta.get("tier_id")
        if tier_id is not None and tier_id != CERTIFIED_TIER_ID:
            raise AtlasUnavailableError(f"Sidecar {sidecar} is for {tier_id}, expected {CERTIFIED_TIER_ID}.")
        if meta.get("sha_match") is False:
            raise AtlasUnavailableError(f"Sidecar {sidecar} reports sha_match=false.")
        return path

    def _assert_current_tier(self) -> None:
        if self.audit.get("tier_id") != CERTIFIED_TIER_ID:
            raise AtlasUnavailableError(
                f"R9 audit report is not for {CERTIFIED_TIER_ID}: {self.audit.get('tier_id')!r}."
            )
        if self.audit.get("status") != "PASS":
            raise AtlasUnavailableError(f"R9 audit report status is not PASS: {self.audit.get('status')!r}.")
        if self.audit.get("checks", {}).get("combined_manifest_rows") != CERTIFIED_CELL_COUNT:
            raise AtlasUnavailableError(
                f"R9 audit report does not certify {CERTIFIED_CELL_COUNT} cells: "
                f"{self.audit.get('checks', {}).get('combined_manifest_rows')!r}."
            )
        if self.scenario_order != EXPECTED_SCENARIO_ORDER:
            raise AtlasUnavailableError(
                f"Scenario dictionary order is {self.scenario_order}; expected {EXPECTED_SCENARIO_ORDER}."
            )
        primary = tuple(self.endpoint_definitions["primary_endpoint_families"])
        if primary != EXPECTED_PRIMARY_ENDPOINT_FAMILIES:
            raise AtlasUnavailableError(
                f"Endpoint definitions primary families are {primary}; expected "
                f"{EXPECTED_PRIMARY_ENDPOINT_FAMILIES}."
            )
        self._assert_no_superseded_strings(self._load("figures.registry"), "figure registry")

    def _assert_no_superseded_strings(self, value: Any, context: str) -> None:
        superseded_registry = "f2v" + "2_final"
        superseded_family = "f1" + "v2"
        bad = [s for s in _strings_in(value) if superseded_registry in s or superseded_family in s.lower()]
        if bad:
            raise AtlasUnavailableError(f"Superseded figure path found in {context}: {bad[0]}")

    # -- low-level loading -------------------------------------------------
    def _load(self, key: str) -> list[dict[str, Any]]:
        if key not in self._cache:
            self._cache[key] = _read_csv(self._files[key])
        return [dict(row) for row in self._cache[key]]

    def _load_optional(self, key: str) -> list[dict[str, Any]]:
        path = self._optional_files.get(key)
        if path is None:
            return []
        if key not in self._cache:
            self._cache[key] = _read_csv(path)
        return [dict(row) for row in self._cache[key]]

    def _sidecar(self, key: str) -> dict[str, Any]:
        if key not in self._sidecar_cache:
            self._sidecar_cache[key] = _read_json(Path(f"{self._files[key]}.prov.json"))
        return dict(self._sidecar_cache[key])

    def _source_payload(self, key: str) -> dict[str, Any]:
        return self._source_payload_for_path(self._files[key])

    @staticmethod
    def _source_payload_for_path(path: Path) -> dict[str, Any]:
        sidecar = Path(f"{path}.prov.json")
        return {
            "source_csv": str(path),
            "provenance_sidecar": str(sidecar) if sidecar.exists() else None,
            "read_only": True,
        }

    def _optional_source_payload(self, key: str) -> dict[str, Any] | None:
        path = self._optional_files.get(key)
        if path is None:
            return None
        return self._source_payload_for_path(path)

    def _common_payload(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "tier_id": CERTIFIED_TIER_ID,
            "scenario_order": list(self.scenario_order),
        }

    @staticmethod
    def _check_tier(tier: str) -> str:
        if tier not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}; got {tier!r}")
        return tier

    # -- metadata ----------------------------------------------------------
    def _scenario_rows(self) -> list[dict[str, Any]]:
        rows = self._load("metadata.scenario_dictionary")
        scenarios: list[dict[str, Any]] = []
        for row in rows:
            code = str(row.get("hvac_scenario") or row.get("code"))
            scenarios.append(
                {
                    "code": code,
                    "hvac_scenario": code,
                    "scenario_display_label": row["scenario_display_label"],
                    "scenario_order": int(row["scenario_order"]),
                    "scenario_color": row["scenario_color"],
                    "cooling": row.get("cooling"),
                    "heating": row.get("heating"),
                    "natural_ventilation": row.get("natural_ventilation"),
                }
            )
        return sorted(scenarios, key=lambda row: int(row["scenario_order"]))

    def _endpoint_definitions_payload(self) -> dict[str, Any]:
        primary = [str(row["metric_name"]) for row in self.endpoint_rows if row.get("primary") is True]
        return {
            "primary_endpoint_families": primary,
            "rows": self.endpoint_rows,
            **self._source_payload("metadata.endpoint_definitions"),
        }

    def _metric_notes(self) -> dict[str, str]:
        notes = {
            "hours_gt_28c": "Overheating exposure hours; threshold: operative temperature above 28 C.",
            "hours_gt_30c": "Overheating exposure hours; threshold: operative temperature above 30 C.",
            "hours_gt_32c": "Overheating exposure hours; threshold: operative temperature above 32 C.",
            "op_temp_hours_gt_28c": "Overheating exposure hours; threshold: operative temperature above 28 C.",
            "op_temp_hours_gt_28c_mean": "Overheating exposure hours; threshold: operative temperature above 28 C.",
            "op_temp_hours_gt_30c_mean": "Overheating exposure hours; threshold: operative temperature above 30 C.",
            "op_temp_hours_gt_32c_mean": "Overheating exposure hours; threshold: operative temperature above 32 C.",
            "degree_hours_28c": "Overheating degree-hours; threshold: operative temperature above 28 C.",
            "degree_hours_28c_mean": "Overheating degree-hours; threshold: operative temperature above 28 C.",
            "humidity_hours": "High-humidity exposure hours; threshold: humidity ratio above 0.012 kg/kg.",
            "humidity_hours_gt_0p012kgkg": (
                "High-humidity exposure hours; threshold: humidity ratio above 0.012 kg/kg."
            ),
            "humidity_hours_gt_0p012kgkg_mean": (
                "High-humidity exposure hours; threshold: humidity ratio above 0.012 kg/kg."
            ),
        }
        for row in self.endpoint_rows:
            metric = str(row["metric_name"])
            label = str(row.get("reader_label") or metric)
            unit = str(row.get("unit") or "")
            if metric not in notes:
                notes[metric] = f"{label}; unit: {unit}."
        return notes

    def _annotate_scenario_row(self, row: dict[str, Any]) -> dict[str, Any]:
        code = str(row.get("hvac_scenario") or row.get("scenario") or "")
        if code not in self.scenario_by_code:
            raise AtlasUnavailableError(f"Unexpected scenario code {code!r} in certified row.")
        scenario = self.scenario_by_code[code]
        row["hvac_scenario"] = code
        row["scenario_display_label"] = scenario["scenario_display_label"]
        row["scenario_order"] = scenario["scenario_order"]
        return row

    def _sort_scenario_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        index = {code: i for i, code in enumerate(self.scenario_order)}
        return sorted(rows, key=lambda row: index[str(row["hvac_scenario"])])

    def _sort_grouped_rows(self, rows: list[dict[str, Any]], group_col: str) -> list[dict[str, Any]]:
        index = {code: i for i, code in enumerate(self.scenario_order)}
        group_index: dict[str, int] = {}
        for row in rows:
            group_index.setdefault(str(row[group_col]), len(group_index))
        return sorted(rows, key=lambda row: (group_index[str(row[group_col])], index[str(row["hvac_scenario"])]))

    def _assert_exact_scenarios(self, rows: list[dict[str, Any]], context: str) -> None:
        order = tuple(str(row.get("hvac_scenario")) for row in rows)
        if order != self.scenario_order:
            raise AtlasUnavailableError(f"{context} has scenario order {order}; expected {self.scenario_order}.")

    def _assert_group_scenarios(self, rows: list[dict[str, Any]], group_col: str, context: str) -> None:
        groups: dict[str, list[str]] = {}
        for row in rows:
            groups.setdefault(str(row[group_col]), []).append(str(row.get("hvac_scenario")))
        for group, order in groups.items():
            if tuple(order) != self.scenario_order:
                raise AtlasUnavailableError(
                    f"{context} group {group!r} has scenario order {tuple(order)}; expected {self.scenario_order}."
                )

    def _optional_unavailable(self, endpoint: str) -> dict[str, Any]:
        return {
            **self._common_payload(),
            "available": False,
            "reason": (
                f"No certified four-scenario {endpoint} CSV and provenance sidecar were found under "
                f"{self.data_dir}. The legacy bundled Atlas scaffold is not used as current."
            ),
        }

    # -- results surfaces --------------------------------------------------
    def scenario_dictionary(self) -> dict[str, Any]:
        return {
            **self._common_payload(),
            "scenarios": self.scenarios,
            **self._source_payload("metadata.scenario_dictionary"),
        }

    def scenario_summary(self, tier: str = "annual") -> dict[str, Any]:
        tier = self._check_tier(tier)
        rows = [self._annotate_scenario_row(row) for row in self._load(f"{tier}.scenario_summary")]
        rows = self._sort_scenario_rows(rows)
        self._assert_exact_scenarios(rows, f"{tier} scenario summary")
        return {
            **self._common_payload(),
            "tier": tier,
            "scenario_semantics": self.scenario_semantics,
            "scenario_ordering": ", ".join(self.scenario_order),
            "rows": rows,
            "metric_notes": self.metric_notes,
            "endpoint_definitions": self.endpoint_definitions,
            **self._source_payload(f"{tier}.scenario_summary"),
        }

    def by_stratum(self, tier: str = "annual", dimension: str = "climate") -> dict[str, Any]:
        tier = self._check_tier(tier)
        if dimension not in STRATUM_DIMENSIONS:
            raise ValueError(f"dimension must be one of {sorted(STRATUM_DIMENSIONS)}; got {dimension!r}")
        _, group_col = STRATUM_DIMENSIONS[dimension]
        rows = [self._annotate_scenario_row(row) for row in self._load(f"{tier}.by_{dimension}")]
        rows = self._sort_grouped_rows(rows, group_col)
        self._assert_group_scenarios(rows, group_col, f"{tier} by-stratum {dimension}")
        return {
            **self._common_payload(),
            "tier": tier,
            "dimension": dimension,
            "group_column": group_col,
            "rows": rows,
            "metric_notes": self.metric_notes,
            "endpoint_definitions": self.endpoint_definitions,
            **self._source_payload(f"{tier}.by_{dimension}"),
        }

    def scenario_c(self, tier: str = "annual") -> dict[str, Any]:
        """Scenario C intervention panel sourced from the certified 4-scenario tier."""

        tier = self._check_tier(tier)
        cells = self._load(f"{tier}.scenario_c")

        def summarize(subset: list[dict[str, Any]]) -> dict[str, Any]:
            return {
                "n_cells": len(subset),
                "avoided_gt_28c_mean": _mean([r.get("scenario_c_avoided_gt_28c") for r in subset]),
                "residual_gt_28c_mean": _mean([r.get("scenario_c_residual_gt_28c") for r in subset]),
                "benefit_fraction_gt_28c_mean": _mean([r.get("scenario_c_benefit_fraction_gt_28c") for r in subset]),
                "avoided_gt_30c_mean": _mean([r.get("scenario_c_avoided_gt_30c") for r in subset]),
                "residual_gt_30c_mean": _mean([r.get("scenario_c_residual_gt_30c") for r in subset]),
                "off_window_hours_gt_28c_mean": _mean([r.get("scenario_c_off_window_hours_gt_28c") for r in subset]),
                "overnight_residual_hours_gt_28c_mean": _mean(
                    [r.get("scenario_c_overnight_residual_hours_gt_28c") for r in subset]
                ),
            }

        climates = sorted({str(r.get("climate_region")) for r in cells})
        by_climate = [
            {"climate_region": climate, **summarize([r for r in cells if str(r.get("climate_region")) == climate])}
            for climate in climates
        ]
        return {
            **self._common_payload(),
            "tier": tier,
            "scenario_semantics": self.scenario_semantics,
            "overall": summarize(cells),
            "by_climate": by_climate,
            "metric_notes": self.metric_notes,
            **self._source_payload(f"{tier}.scenario_c"),
        }

    def d_comparisons(self, tier: str = "annual") -> dict[str, Any]:
        tier = self._check_tier(tier)
        rows = self._load(f"{tier}.d_specific")
        comparison_order = []
        comparisons: dict[str, dict[str, Any]] = {}
        for row in rows:
            if str(row.get("base_scenario")) != "D":
                raise AtlasUnavailableError(f"{tier} D comparison row has non-D base scenario.")
            comparison = str(row.get("comparison_scenario"))
            key = f"D-{comparison}"
            if key not in comparisons:
                comparison_order.append(key)
                comparisons[key] = {
                    "comparison_key": key,
                    "comparison_scenario": comparison,
                    "comparison_scenario_display_label": row.get("comparison_scenario_display_label"),
                    "comparison_order": row.get("comparison_order"),
                    "comparison_interpretation": row.get("comparison_interpretation"),
                    "row_count": 0,
                }
            comparisons[key]["row_count"] += 1
        required = {"D-A", "D-C", "D-B"}
        if set(comparisons) != required:
            raise AtlasUnavailableError(f"{tier} D comparisons are {sorted(comparisons)}; expected {sorted(required)}.")
        return {
            **self._common_payload(),
            "tier": tier,
            "base_scenario": "D",
            "base_scenario_display_label": self.scenario_semantics["D"],
            "comparison_order": comparison_order,
            "story_comparison_order": list(STORY_COMPARISON_ORDER),
            "comparisons": [comparisons[key] for key in comparison_order],
            "rows": rows,
            "metric_notes": self.metric_notes,
            **self._source_payload(f"{tier}.d_specific"),
        }

    def differential(self, tier: str = "annual") -> dict[str, Any]:
        tier = self._check_tier(tier)
        return {
            **self._common_payload(),
            "tier": tier,
            "rows": self._load(f"{tier}.differential"),
            "metric_notes": self.metric_notes,
            **self._source_payload(f"{tier}.differential"),
        }

    def figures(self) -> dict[str, Any]:
        rows = self._load("figures.registry")
        self._assert_no_superseded_strings(rows, "figure registry")
        return {
            **self._common_payload(),
            "registry_tier": FIGURE_REGISTRY_TIER,
            "registry_csv": str(self._files["figures.registry"]),
            "figures": rows,
            "rows": rows,
            **self._source_payload("figures.registry"),
        }

    def figure_source(self, figure_id: str) -> dict[str, Any]:
        """Return the certified source table named by an f2v3 registry row."""

        figure_id = figure_id.strip()
        registry_row = self._figure_registry_row(figure_id)
        source_path = self._figure_source_path(registry_row)
        self._assert_no_superseded_strings(registry_row, f"figure registry row {figure_id}")
        rows = _read_csv(source_path)
        return {
            **self._common_payload(),
            "registry_tier": FIGURE_REGISTRY_TIER,
            "figure": registry_row,
            "figure_id": registry_row["figure_id"],
            "source_csv": str(source_path),
            "provenance_sidecar": str(Path(f"{source_path}.prov.json")),
            "rows": rows,
        }

    def figure_bundle(self, figure_id: str) -> dict[str, Any]:
        """Return source table and PNG/PDF/SVG assets for an f2v3 figure."""

        figure_id = figure_id.strip()
        registry_row = self._figure_registry_row(figure_id)
        source_path = self._figure_source_path(registry_row)
        assets = {
            "png": self._figure_asset_path(registry_row, "asset_png"),
            "pdf": self._figure_asset_path(registry_row, "asset_pdf"),
            "svg": self._figure_asset_path(registry_row, "asset_svg"),
        }
        return {
            **self._common_payload(),
            "registry_tier": FIGURE_REGISTRY_TIER,
            "figure": registry_row,
            "figure_id": registry_row["figure_id"],
            "source_csv": str(source_path),
            "source_csv_sidecar": str(Path(f"{source_path}.prov.json")),
            "assets": {kind: str(path) for kind, path in assets.items()},
            "asset_sidecars": {kind: str(Path(f"{path}.prov.json")) for kind, path in assets.items()},
            "caption": registry_row.get("caption"),
            "alt_text": registry_row.get("alt_text"),
            "atlas_route": registry_row.get("atlas_route"),
            "citation_text": self._citation_text(str(source_path), figure_id=str(registry_row["figure_id"])),
        }

    def exports_catalog(self) -> dict[str, Any]:
        """List exportable views and f2v3 figure bundles."""

        figures = self._load("figures.registry")
        return {
            **self._common_payload(),
            "views": self._export_view_records(),
            "figure_bundles": [self._figure_bundle_summary(row) for row in figures],
            "citation_text": self._citation_text(str(self.data_dir)),
            "f2v3_gate_report": {
                **self._source_payload("figures.gate_report"),
                "status": self._f2v3_gate_status(),
            },
            "note": "Export paths resolve to certified read-only CSVs and f2v3_final assets only.",
        }

    def export_view(
        self,
        view: str,
        tier: str = "annual",
        dimension: str = "climate",
        scenario: str = "D",
    ) -> dict[str, Any]:
        """Return the data rows and source CSV descriptor for an exportable view."""

        name = view.strip().lower().replace("_", "-")
        if name in {"overview", "scenario-summary", "results"}:
            payload = self.scenario_summary(tier)
            source_key = f"{payload['tier']}.scenario_summary"
            rows = payload["rows"]
            api_path = f"/api/v1/results/scenario-summary?tier={payload['tier']}"
            label = f"{payload['tier'].title()} scenario summary"
        elif name in {"by-stratum", "stratum"}:
            payload = self.by_stratum(tier, dimension)
            source_key = f"{payload['tier']}.by_{payload['dimension']}"
            rows = payload["rows"]
            api_path = f"/api/v1/results/by-stratum?tier={payload['tier']}&dimension={payload['dimension']}"
            label = f"{payload['tier'].title()} by {payload['dimension']}"
        elif name in {"d-comparison", "d-comparisons", "sealed-passive"}:
            payload = self.d_comparisons(tier)
            source_key = f"{payload['tier']}.d_specific"
            rows = payload["rows"]
            api_path = f"/api/v1/results/d-comparisons?tier={payload['tier']}"
            label = f"{payload['tier'].title()} sealed-passive D comparisons"
        elif name in {"equity", "equity-profiles"}:
            payload = self.equity_profiles()
            source_key = None
            rows = payload["catchments"]
            api_path = "/api/v1/equity/profiles"
            label = "Equity profiles"
        elif name in {"equity-scenario-cross", "scenario-cross"}:
            payload = self.equity_scenario_cross(scenario, dimension)
            source_key = f"annual.by_{payload['dimension']}"
            rows = payload["rows"]
            api_path = (
                f"/api/v1/equity/scenario-cross?scenario={payload['scenario']}" f"&dimension={payload['dimension']}"
            )
            label = f"Equity scenario cross: {payload['scenario_display_label']}"
        else:
            raise ValueError(
                "view must be one of overview, scenario-summary, by-stratum, d-comparisons, "
                "equity-profiles, equity-scenario-cross"
            )

        csv_export = self._csv_export_descriptor(source_key, label)
        return {
            **self._common_payload(),
            "view": name,
            "label": label,
            "api_path": api_path,
            "csv_export": csv_export,
            "source_csv": csv_export.get("source_csv"),
            "provenance_sidecar": csv_export.get("provenance_sidecar"),
            "row_count": len(rows),
            "rows": rows,
            "citation_text": self._citation_text(str(csv_export.get("source_csv") or self.data_dir)),
            "payload": payload,
        }

    def _figure_registry_row(self, figure_id: str) -> dict[str, Any]:
        for row in self._load("figures.registry"):
            if str(row.get("figure_id")) == figure_id or str(row.get("stem")) == figure_id:
                return row
        raise LookupError(f"Figure registry row not found: {figure_id}")

    def _figure_source_path(self, registry_row: dict[str, Any]) -> Path:
        source_csv = str(registry_row.get("source_csv") or "")
        self._assert_no_superseded_strings(source_csv, "figure source path")
        if FIGURE_REGISTRY_TIER not in source_csv:
            raise AtlasUnavailableError(f"Figure source path is not in {FIGURE_REGISTRY_TIER}: {source_csv}")
        path = Path(source_csv)
        if path.is_absolute() and path.exists():
            return self._require_sidecar(path)
        resolved = self.figure_dir / "tables" / path.name
        if not resolved.exists():
            raise AtlasUnavailableError(
                f"Certified f2v3 source table is missing or cloud-only: {resolved}. "
                "Charts must read registry source_csv rows, not a parallel table."
            )
        return self._require_sidecar(resolved)

    def _figure_asset_path(self, registry_row: dict[str, Any], field: str) -> Path:
        asset = str(registry_row.get(field) or "")
        self._assert_no_superseded_strings(asset, f"figure {field} path")
        if FIGURE_REGISTRY_TIER not in asset:
            raise AtlasUnavailableError(f"Figure asset path is not in {FIGURE_REGISTRY_TIER}: {asset}")
        path = Path(asset)
        if path.is_absolute() and path.exists():
            return self._require_sidecar(path)
        resolved = self.figure_dir / path.name
        if not resolved.exists():
            raise AtlasUnavailableError(f"Certified f2v3 asset is missing or cloud-only: {resolved}.")
        return self._require_sidecar(resolved)

    def _figure_bundle_summary(self, registry_row: dict[str, Any]) -> dict[str, Any]:
        figure_id = str(registry_row["figure_id"])
        return {
            "figure_id": figure_id,
            "stem": registry_row.get("stem"),
            "figure_class": registry_row.get("figure_class"),
            "source_csv": registry_row.get("source_csv"),
            "asset_png": registry_row.get("asset_png"),
            "asset_pdf": registry_row.get("asset_pdf"),
            "asset_svg": registry_row.get("asset_svg"),
            "provenance_sidecar": registry_row.get("provenance_sidecar"),
            "api_path": f"/api/v1/results/figure-bundle?figure_id={figure_id}",
            "citation_text": self._citation_text(str(registry_row.get("source_csv") or ""), figure_id=figure_id),
        }

    def _export_view_records(self) -> list[dict[str, Any]]:
        specs = (
            (
                "scenario-summary",
                "Annual scenario summary",
                "annual.scenario_summary",
                "/api/v1/results/scenario-summary",
            ),
            (
                "d-comparisons",
                "Annual sealed-passive D comparisons",
                "annual.d_specific",
                "/api/v1/results/d-comparisons",
            ),
            ("equity-profiles", "Equity profiles", None, "/api/v1/equity/profiles"),
            (
                "equity-scenario-cross",
                "Scenario D exposure x vulnerability contrast",
                "annual.by_climate",
                "/api/v1/equity/scenario-cross?scenario=D&dimension=climate",
            ),
        )
        rows = []
        for view, label, source_key, api_path in specs:
            csv_export = self._csv_export_descriptor(source_key, label)
            rows.append(
                {
                    "view": view,
                    "label": label,
                    "api_path": api_path,
                    "csv_export": csv_export,
                    "citation_text": self._citation_text(str(csv_export.get("source_csv") or self.data_dir)),
                }
            )
        return rows

    def _csv_export_descriptor(self, source_key: str | None, label: str) -> dict[str, Any]:
        if source_key is None:
            equity_source = self._optional_source_payload("equity.profile")
            if equity_source is None:
                return {
                    "status": "REVIEW REQUIRED",
                    "label": label,
                    "source_csv": None,
                    "provenance_sidecar": None,
                    "reason": f"No verified equity profile CSV was found at {self.data_dir / 'equity_profile.csv'}.",
                }
            return {"status": "READY", "label": label, **equity_source}
        if source_key not in self._files:
            raise ValueError(f"Unknown export source key: {source_key}")
        return {"status": "READY", "label": label, **self._source_payload(source_key)}

    def _citation_text(self, source: str, figure_id: str | None = None) -> str:
        target = f" figure {figure_id}" if figure_id else ""
        return (
            f"ReplocX Research Atlas{target}, certified {CERTIFIED_TIER_ID} "
            f"({CERTIFIED_CELL_COUNT} cells, scenario order A/C/B/D), R9 PASS, "
            f"{FIGURE_REGISTRY_TIER}. Source: {source}."
        )

    def _f2v3_gate_status(self) -> str:
        gate = _read_json(self._files["figures.gate_report"])
        if gate.get("status"):
            return str(gate["status"])
        if gate.get("gate_A_reconciliation", {}).get("status"):
            return str(gate["gate_A_reconciliation"]["status"])
        if gate.get("gate_A_coverage", {}).get("status"):
            return str(gate["gate_A_coverage"]["status"])
        return "PASS" if "PASS" in str(gate) else "UNKNOWN"

    def cooling_seasons(self) -> dict[str, Any]:
        if "cooling.summary" not in self._optional_files:
            return {
                **self._optional_unavailable("cooling-season"),
                "sites": [],
                "long_term": [],
                "long_term_note": (
                    "Cooling-season windows are not present in the certified four-scenario Atlas tier; "
                    "legacy cooling-season files are intentionally not served."
                ),
            }
        return {
            **self._common_payload(),
            "available": True,
            "sites": self._load_optional("cooling.summary"),
            "long_term": self._load_optional("cooling.long_term"),
            "long_term_note": (
                "Cooling-season windows are served only when a certified four-scenario sidecar is present."
            ),
        }

    def sensitivity(self) -> dict[str, Any]:
        keys = (
            "sensitivity.leave_one_location_out",
            "sensitivity.degreeday_year_deltas",
            "sensitivity.repro_check",
        )
        if not all(key in self._optional_files for key in keys):
            return {
                **self._optional_unavailable("sensitivity"),
                "leave_one_location_out": [],
                "degreeday_year_deltas": [],
                "repro_check": [],
            }
        return {
            **self._common_payload(),
            "available": True,
            "leave_one_location_out": self._load_optional("sensitivity.leave_one_location_out"),
            "degreeday_year_deltas": self._load_optional("sensitivity.degreeday_year_deltas"),
            "repro_check": self._load_optional("sensitivity.repro_check"),
        }

    def results_provenance(self) -> dict[str, Any]:
        audit_checks = self.audit.get("checks", {})
        first_sidecar = self._sidecar("annual.scenario_summary")
        f2v3_gate_report = _read_json(self._files["figures.gate_report"])
        equity_rows = self._load_optional("equity.profile")
        equity_layers = self._equity_layers(equity_rows)
        captions = self._optional_source_payload("figures.captions")
        return {
            **self._common_payload(),
            "dataset": "ReplocX Research Atlas certified TMY3 wallfix four-scenario tier",
            "tier": CERTIFIED_TIER_ID,
            "certified_cell_count": audit_checks.get("combined_manifest_rows", CERTIFIED_CELL_COUNT),
            "certification": first_sidecar.get(
                "certification", "R9 gate PASS: certified 720-cell four-scenario results tier."
            ),
            "r9_status": self.audit.get("status"),
            "r9_certification": self.audit,
            "scenario_semantics": self.scenario_semantics,
            "scenario_ordering": ", ".join(self.scenario_order),
            "canonical_data_root": str(self.data_dir),
            "figure_registry_root": str(self.figure_dir),
            "source_canonical_root": str(self.data_dir),
            "read_only_sources": True,
            "figure_registry_tier": FIGURE_REGISTRY_TIER,
            "manifest": str(self._files["audit.r9_report"]),
            "r9_gate_report": self._source_payload("audit.r9_report"),
            "f2v3_gate_report": {
                **self._source_payload("figures.gate_report"),
                "status": self._f2v3_gate_status(),
                "report": f2v3_gate_report,
            },
            "f2v3_registry": {
                "registry_csv": str(self._files["figures.registry"]),
                "registry_sidecar": str(Path(f"{self._files['figures.registry']}.prov.json")),
                "figure_count": len(self._load("figures.registry")),
                "captions_source": captions["source_csv"] if captions else None,
                "captions_sidecar": captions["provenance_sidecar"] if captions else None,
            },
            "equity_source_notes": equity_layers["records"],
            "equity_verification": {
                "status": "READY" if equity_layers["verified_layer_count"] else "REVIEW REQUIRED",
                "verified_layer_count": equity_layers["verified_layer_count"],
                "source_record_count": equity_layers["source_record_count"],
                "catchment_join_method": equity_layers["catchment_join_method"],
                "source_csv": self._optional_source_payload("equity.profile"),
                "missing_source_path": (
                    None if "equity.profile" in self._optional_files else str(self.data_dir / "equity_profile.csv")
                ),
            },
            "export_views": self._export_view_records(),
            "tier_wall": (
                "Only the certified replocx_tmy3_wallfix_4scen R9 data domain is current for Atlas results; "
                "legacy scaffold files are rejected."
            ),
            "copied_at": first_sidecar.get("copied_at", "read-only canonical source"),
            "endpoint_definitions": self.endpoint_definitions,
            "file_checksums": self._file_checksums(),
            "data_directory": str(self.data_dir),
        }

    def overview(self) -> dict[str, Any]:
        annual = self.scenario_summary("annual")
        n_cells = sum(int(row.get("n_runs") or 0) for row in annual["rows"])
        if n_cells != CERTIFIED_CELL_COUNT:
            n_cells = CERTIFIED_CELL_COUNT
        return {
            **self._common_payload(),
            "dataset": "ReplocX Research Atlas certified TMY3 wallfix four-scenario tier",
            "tier": CERTIFIED_TIER_ID,
            "scenario_semantics": self.scenario_semantics,
            "scenario_ordering": ", ".join(self.scenario_order),
            "tier_wall": (
                "Atlas reads certified R9 aggregate CSVs and f2v3 figure registry records only; "
                "it does not recompute EnergyPlus results."
            ),
            "n_cells": n_cells,
            "scenario_summary": annual,
            "metric_notes": self.metric_notes,
        }

    # -- equity surfaces ---------------------------------------------------
    def equity_profiles(self) -> dict[str, Any]:
        rows = self._load_optional("equity.profile")
        layers = self._equity_layers(rows)
        profiles = [self._annotate_equity_profile(row, layers["records"]) for row in rows]
        source = self._optional_source_payload("equity.profile")
        return {
            **self._common_payload(),
            "profiles": profiles,
            "catchments": profiles,
            "layers": layers,
            "source_csv": source["source_csv"] if source else None,
            "provenance_sidecar": source["provenance_sidecar"] if source else None,
            "missing_source_path": None if source else str(self.data_dir / "equity_profile.csv"),
            "catchment_profile_status": "READY" if layers["verified_layer_count"] else "REVIEW REQUIRED",
            "disclaimer": (
                "Real equity layers are private and must carry proxy badges, source vintage, and join uncertainty. "
                "Unverified layers remain REVIEW REQUIRED."
            ),
        }

    def equity_scenario_cross(self, scenario: str = "D", dimension: str = "climate") -> dict[str, Any]:
        scenario = scenario.upper()
        if scenario not in self.scenario_by_code:
            raise ValueError(f"scenario must be one of {self.scenario_order}; got {scenario!r}")
        strata = self.by_stratum("annual", dimension)
        group_col = strata["group_column"]
        profiles = self._load_optional("equity.profile")
        layers = self._equity_layers(profiles)
        vulnerability_layer = self._preferred_vulnerability_layer(layers["records"])
        vulnerability_note = (
            "Vulnerability values come from the verified sidecar-backed equity profile; "
            "proxy badges and join-uncertainty notes remain visible."
            if vulnerability_layer["status"] == "READY"
            else ("Vulnerability values remain REVIEW REQUIRED until the sidecar-backed " "equity join is verified.")
        )
        vulnerability_by_group = self._aggregate_equity_by_group(profiles, group_col, vulnerability_layer)
        rows_by_group: dict[str, dict[str, dict[str, Any]]] = {}
        for row in strata["rows"]:
            rows_by_group.setdefault(str(row[group_col]), {})[str(row["hvac_scenario"])] = row
        rows = [
            self._equity_cross_row(
                group,
                group_col,
                scenario,
                scenario_rows,
                vulnerability_layer,
                vulnerability_by_group.get(group),
            )
            for group, scenario_rows in rows_by_group.items()
        ]
        return {
            **self._common_payload(),
            "scenario": scenario,
            "scenario_label": self.scenario_semantics[scenario],
            "scenario_display_label": self.scenario_semantics[scenario],
            "dimension": dimension,
            "group_column": strata["group_column"],
            "metric": "op_temp_hours_gt_28c",
            "metric_label": "Overheating exposure hours",
            "threshold_note": "Threshold: operative temperature above 28 C.",
            "rows": rows,
            "exposure": rows,
            "equity_layers": layers,
            "vulnerability_layer": vulnerability_layer,
            "d_related_contrast": {
                "base_scenario": "D",
                "base_scenario_display_label": self.scenario_semantics["D"],
                "comparison_scenario": scenario,
                "comparison_scenario_display_label": self.scenario_semantics[scenario],
                "metric": "op_temp_hours_gt_28c",
                "metric_label": "Overheating exposure hours",
                "threshold_note": "Threshold: operative temperature above 28 C.",
                "vulnerability_layer_status": vulnerability_layer["status"],
            },
            "note": ("Descriptive exposure x vulnerability contrast only; no causal claim. " + vulnerability_note),
        }

    def _equity_layers(self, rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = self._load_optional("equity.profile") if rows is None else rows
        records = [self._equity_layer_record(definition, rows) for definition in EQUITY_LAYER_DEFINITIONS]
        ready = [row for row in records if row["status"] == "READY"]
        review = [row for row in records if row["status"] != "READY"]
        return {
            "populated": [str(row["label"]) for row in ready],
            "ready": [str(row["id"]) for row in ready],
            "review_required": [str(row["id"]) for row in review],
            "pending_review_required": [str(row["label"]) for row in review],
            "records": records,
            "proxy_badges_required": True,
            "unverified_status": "REVIEW REQUIRED",
            "verified_layer_count": len(ready),
            "source_record_count": len(rows),
            "catchment_join_method": self._equity_join_method(rows),
            "note": (
                "Layers are READY only when the sidecar-backed equity profile supplies values, source/vintage, "
                "proxy badge, and join-uncertainty fields. Missing or incomplete layers stay REVIEW REQUIRED."
            ),
        }

    def _equity_layer_record(self, definition: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
        values_present = bool(rows) and all(self._equity_value(row, definition) is not None for row in rows)
        metadata_complete = bool(rows) and all(
            row.get(str(definition["source_field"]))
            and row.get(str(definition["badge_field"]))
            and row.get(str(definition["uncertainty_field"]))
            for row in rows
        )
        badges = {
            str(row.get(str(definition["badge_field"]))).strip()
            for row in rows
            if row.get(str(definition["badge_field"])) not in {None, ""}
        }
        badges_valid = bool(badges) and badges.issubset(ALLOWED_EQUITY_BADGES) and "REVIEW REQUIRED" not in badges
        status = "READY" if values_present and metadata_complete and badges_valid else "REVIEW REQUIRED"
        return {
            "id": definition["id"],
            "label": definition["label"],
            "value_fields": list(definition["value_fields"]),
            "value_label": definition["value_label"],
            "status": status,
            "source_vintage": self._first_row_value(rows, str(definition["source_field"]))
            or definition["default_source_vintage"],
            "proxy_badge": self._first_row_value(rows, str(definition["badge_field"]))
            or definition["default_proxy_badge"],
            "join_uncertainty_note": self._first_row_value(rows, str(definition["uncertainty_field"]))
            or definition["default_join_uncertainty_note"],
            "geography_level": definition["geography_level"],
            "source_url": definition["source_url"],
            "verified": status == "READY",
            "missing_reason": (
                None
                if status == "READY"
                else "Missing verified values and/or source-vintage, proxy-badge, join-uncertainty fields."
            ),
        }

    def _annotate_equity_profile(
        self,
        row: dict[str, Any],
        layer_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        layer_values: dict[str, dict[str, Any]] = {}
        for layer in layer_records:
            definition = next(item for item in EQUITY_LAYER_DEFINITIONS if item["id"] == layer["id"])
            value = self._equity_value(row, definition)
            layer_values[str(layer["id"])] = {
                "value": value,
                "status": layer["status"],
                "source_vintage": layer["source_vintage"],
                "proxy_badge": layer["proxy_badge"],
                "join_uncertainty_note": layer["join_uncertainty_note"],
            }
        out = dict(row)
        out["layer_values"] = layer_values
        out.setdefault(
            "equity_layer_status",
            "READY" if any(v["status"] == "READY" for v in layer_values.values()) else "REVIEW REQUIRED",
        )
        return out

    def _equity_value(self, row: dict[str, Any], definition: dict[str, Any]) -> Any:
        for field in definition["value_fields"]:
            value = row.get(str(field))
            if value not in {None, ""}:
                return value
        return None

    @staticmethod
    def _first_row_value(rows: list[dict[str, Any]], field: str) -> str | None:
        for row in rows:
            value = row.get(field)
            if value not in {None, ""}:
                return str(value)
        return None

    def _equity_join_method(self, rows: list[dict[str, Any]]) -> str:
        return self._first_row_value(rows, "catchment_join_method") or (
            "REVIEW REQUIRED: no verified catchment-level SVI/ACS/DOE LEAD crosswalk was found under "
            f"{self.data_dir}."
        )

    @staticmethod
    def _preferred_vulnerability_layer(layer_records: list[dict[str, Any]]) -> dict[str, Any]:
        preferred = ("cdc_svi", "heat_vulnerability", "doe_lead_energy_burden", "acs_income_poverty")
        ready = {str(row["id"]): row for row in layer_records if row["status"] == "READY"}
        for layer_id in preferred:
            if layer_id in ready:
                return ready[layer_id]
        return next(row for row in layer_records if row["id"] == "cdc_svi")

    def _aggregate_equity_by_group(
        self,
        rows: list[dict[str, Any]],
        group_col: str,
        layer: dict[str, Any],
    ) -> dict[str, float]:
        definition = next(item for item in EQUITY_LAYER_DEFINITIONS if item["id"] == layer["id"])
        grouped: dict[str, list[Any]] = {}
        for row in rows:
            group = row.get(group_col)
            value = self._equity_value(row, definition)
            if group not in {None, ""} and value is not None:
                grouped.setdefault(str(group), []).append(value)
        aggregated: dict[str, float] = {}
        for group, values in grouped.items():
            mean = _mean(values)
            if mean is not None:
                aggregated[group] = mean
        return aggregated

    def _equity_cross_row(
        self,
        group: str,
        group_col: str,
        scenario: str,
        scenario_rows: dict[str, dict[str, Any]],
        vulnerability_layer: dict[str, Any],
        vulnerability_value: float | None,
    ) -> dict[str, Any]:
        selected = scenario_rows.get(scenario)
        sealed = scenario_rows.get("D")
        if selected is None or sealed is None:
            raise AtlasUnavailableError(f"Missing {scenario}/D exposure rows for {group_col}={group!r}.")
        selected_hours = self._overheating_hours(selected)
        sealed_hours = self._overheating_hours(sealed)
        delta = None
        if isinstance(selected_hours, (int, float)) and isinstance(sealed_hours, (int, float)):
            delta = sealed_hours - selected_hours
        return {
            group_col: group,
            "hvac_scenario": scenario,
            "scenario_display_label": self.scenario_semantics[scenario],
            "exposure_hours": selected_hours,
            "scenario_exposure_hours": selected_hours,
            "d_exposure_hours": sealed_hours,
            "d_minus_scenario_exposure_hours": delta,
            "equity_percentile": vulnerability_value,
            "vulnerability_value": vulnerability_value,
            "vulnerability_layer_id": vulnerability_layer["id"],
            "vulnerability_layer_label": vulnerability_layer["label"],
            "proxy_badge": vulnerability_layer["proxy_badge"],
            "source_vintage": vulnerability_layer["source_vintage"],
            "join_uncertainty_note": vulnerability_layer["join_uncertainty_note"],
            "layer_status": vulnerability_layer["status"],
            "interpretation_note": "Descriptive exposure x vulnerability contrast only; no causal claim.",
        }

    @staticmethod
    def _overheating_hours(row: dict[str, Any]) -> Any:
        for field in ("op_temp_hours_gt_28c_mean", "op_temp_hours_gt_28c", "hours_gt_28c"):
            value = row.get(field)
            if value not in {None, ""}:
                return value
        return None

    def _file_checksums(self) -> dict[str, dict[str, Any]]:
        checksums: dict[str, dict[str, Any]] = {}
        for key, path in sorted(self._files.items()):
            sidecar_path = Path(f"{path}.prov.json")
            sidecar = _read_json(sidecar_path) if sidecar_path.exists() else {}
            sha = sidecar.get("verified_sha256") or sidecar.get("target_sha256") or sidecar.get("source_sha256") or ""
            bytes_value = sidecar.get("size_bytes") or sidecar.get("bytes") or path.stat().st_size
            checksums[key] = {
                "file": str(path),
                "sidecar": str(sidecar_path) if sidecar_path.exists() else None,
                "sha256": sha,
                "bytes": bytes_value,
            }
        return checksums


_atlas: AtlasService | None = None


def get_atlas() -> AtlasService:
    """Return a cached :class:`AtlasService`, re-attempting until it succeeds."""

    global _atlas
    if _atlas is not None:
        return _atlas
    _atlas = AtlasService()
    return _atlas


def reset_atlas_cache() -> None:
    """Drop the cached service (used by tests toggling the feature flag)."""

    global _atlas
    _atlas = None
