"""Research Atlas tests: gating and W1 four-scenario backend contracts."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from backend import atlas_service
from backend.api import normalize_api_path
from backend.atlas_routes import handle_atlas, is_atlas_path
from backend.atlas_service import AtlasService, AtlasUnavailableError, atlas_enabled, get_atlas, reset_atlas_cache

EXPECTED_ORDER = ["A", "C", "B", "D"]
PRIMARY_FAMILIES = [
    "op_temp_mean_c",
    "op_temp_p95_true_c",
    "humidity_ratio_mean_kgkg",
    "humidity_ratio_p95_true_kgkg",
]
CLIMATES = [label for label, _ in atlas_service.CLIMATE_STRATA]
URBANICITIES = list(atlas_service.URBANICITY_STRATA)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    sidecar = Path(f"{path}.prov.json")
    sidecar.write_text(
        json.dumps(
            {
                "tier_id": atlas_service.CERTIFIED_TIER_ID,
                "verified_sha256": "fixture-sha256",
                "size_bytes": len(text.encode("utf-8")),
                "sha_match": True,
                "certification": "R9 gate PASS: 720 rows/tier, 180 cells/scenario, all four complete, zero fatal cells.",
                "copied_at": "2026-07-07T14:43:17Z",
            }
        ),
        encoding="utf-8",
    )


def _scenario_lines(include_d: bool = True) -> list[str]:
    scenarios = [
        ("A", "AC all day", 1, "#0072B2"),
        ("C", "AC 2-8pm + NV other hours", 2, "#009E73"),
        ("B", "NV only", 3, "#E69F00"),
        ("D", "No AC or NV", 4, "#D55E00"),
    ]
    if not include_d:
        scenarios = scenarios[:3]
    return [
        f"{code},{label},{order},{color},cooling,heating,natural ventilation" for code, label, order, color in scenarios
    ]


def write_atlas_fixture(root: Path, include_d: bool = True, include_equity: bool = True) -> None:
    _write(
        root / "metadata" / "fixture_metadata_scenario_dictionary_4scen_2026-07-07.csv",
        "\n".join(
            [
                "hvac_scenario,scenario_display_label,scenario_order,scenario_color,cooling,heating,natural_ventilation",
                *_scenario_lines(include_d),
                "",
            ]
        ),
    )
    _write(
        root / "metadata" / "fixture_metadata_endpoint_definitions_4scen_2026-07-07.csv",
        "\n".join(
            [
                "metric_name,reader_label,family,unit,primary",
                "op_temp_mean_c,Mean operative temperature,operative temperature,deg C,True",
                "op_temp_p95_true_c,95th-percentile operative temperature,operative temperature,deg C,True",
                "humidity_ratio_mean_kgkg,Mean humidity ratio,humidity ratio,kg/kg,True",
                "humidity_ratio_p95_true_kgkg,95th-percentile humidity ratio,humidity ratio,kg/kg,True",
                "op_temp_hours_gt_28c,Overheating exposure hours,threshold exposure hours,hours above 28 C,False",
                "humidity_hours_gt_0p012kgkg,High-humidity exposure hours,threshold exposure hours,hours above 0.012 kg/kg,False",
                "degree_hours_28c,Overheating degree-hours,intensity-weighted exposure,C-hours above 28 C,False",
                "",
            ]
        ),
    )

    audit = root / "audit" / "r9_reproduction_gate_report.json"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        json.dumps(
            {
                "tier_id": atlas_service.CERTIFIED_TIER_ID,
                "status": "PASS",
                "checks": {
                    "combined_manifest_rows": 720,
                    "combined_manifest_scenario_counts": {"A": 180, "B": 180, "C": 180, "D": 180},
                    "annual": {"primary_endpoint_families_present": True, "pass": True},
                    "seasonal": {"primary_endpoint_families_present": True, "pass": True},
                },
            }
        ),
        encoding="utf-8",
    )
    Path(f"{audit}.prov.json").write_text(json.dumps({"sha_match": True}), encoding="utf-8")

    for tier in ("annual", "seasonal"):
        summary_rows = [
            "hvac_scenario,n_runs,op_temp_mean_c,op_temp_p95_true_c,humidity_ratio_mean_kgkg,humidity_ratio_p95_true_kgkg,hours_gt_28c,hours_gt_30c,hours_gt_32c,degree_hours_28c",
            "A,180,21,24,0.006,0.010,1,0,0,1",
            "C,180,22,27,0.007,0.012,10,3,1,20",
            "B,180,23,29,0.008,0.014,20,8,3,40",
        ]
        if include_d:
            summary_rows.append("D,180,24,33,0.009,0.016,40,20,8,80")
        _write(root / tier / f"fixture_{tier}_scenario_summary_2026-07-07.csv", "\n".join(summary_rows + [""]))

        for stem, group_col, group_value in (
            ("by_climate_region_scenario", "climate_region", "Hot-Humid"),
            ("by_urbanicity_scenario", "urbanicity", "suburban/small town"),
            ("by_building_type_scenario", "building_type", "SF"),
            ("by_vintage_group_scenario", "vintage_group", "post1980"),
        ):
            rows = [
                f"{group_col},hvac_scenario,n_cells,op_temp_mean_c_mean,op_temp_p95_true_c_mean,humidity_ratio_mean_kgkg_mean,humidity_ratio_p95_true_kgkg_mean,op_temp_hours_gt_28c_mean,humidity_hours_gt_0p012kgkg_mean,degree_hours_28c_mean",
                f"{group_value},A,1,21,24,0.006,0.010,1,2,1",
                f"{group_value},C,1,22,27,0.007,0.012,10,20,20",
                f"{group_value},B,1,23,29,0.008,0.014,20,30,40",
            ]
            if include_d:
                rows.append(f"{group_value},D,1,24,33,0.009,0.016,40,50,80")
            _write(root / tier / f"fixture_{tier}_{stem}_2026-07-07.csv", "\n".join(rows + [""]))

        run_rows = [
            (
                "climate_region,urbanicity,hvac_scenario,location_label,"
                "op_temp_mean_c,op_temp_p95_true_c,op_temp_max_c,"
                "op_temp_hours_gt_26c,op_temp_hours_gt_28c,op_temp_hours_gt_30c,"
                "op_temp_hours_gt_32c,degree_hours_28c,humidity_ratio_mean_kgkg,"
                "humidity_ratio_p95_true_kgkg,humidity_hours_gt_0p012kgkg,"
                "joint_hours_gt_28c_0p012kgkg,joint_hours_gt_30c_0p012kgkg"
            )
        ]
        scenario_values = {
            "A": (21, 24, 25, 1, 0, 0, 0, 0, 0.006, 0.010, 2, 0, 0),
            "C": (22, 27, 29, 12, 10, 3, 1, 20, 0.007, 0.012, 20, 2, 1),
            "B": (23, 29, 31, 24, 20, 8, 3, 40, 0.008, 0.014, 30, 8, 3),
            "D": (24, 33, 35, 48, 40, 20, 8, 80, 0.009, 0.016, 50, 20, 8),
        }
        for climate in CLIMATES:
            for urbanicity in URBANICITIES:
                location = f"{climate.replace(' ', '_')}_{urbanicity}"
                for scenario in EXPECTED_ORDER[: 4 if include_d else 3]:
                    values = ",".join(str(value) for value in scenario_values[scenario])
                    run_rows.extend(
                        f"{climate},{urbanicity},{scenario},{location},{values}"
                        for _ in range(atlas_service.CERTIFIED_CELLS_PER_STRATUM_SCENARIO)
                    )
        _write(
            root / tier / f"fixture_{tier}_run_level_metrics_2026-07-07.csv",
            "\n".join(run_rows + [""]),
        )

        _write(
            root / tier / f"fixture_{tier}_scenario_c_summary_2026-07-07.csv",
            "\n".join(
                [
                    "climate_region,scenario_c_avoided_gt_28c,scenario_c_residual_gt_28c,scenario_c_benefit_fraction_gt_28c,scenario_c_avoided_gt_30c,scenario_c_residual_gt_30c,scenario_c_off_window_hours_gt_28c,scenario_c_overnight_residual_hours_gt_28c",
                    "Hot-Humid,10,5,0.67,3,1,4,2",
                    "",
                ]
            ),
        )
        _write(
            root / tier / f"fixture_{tier}_d_specific_comparisons_2026-07-07.csv",
            "\n".join(
                [
                    "base_scenario,base_scenario_display_label,comparison_scenario,comparison_scenario_display_label,comparison_order,comparison_interpretation,op_temp_p95_true_c_reduction_from_D,op_temp_hours_gt_28c_reduction_from_D,degree_hours_28c_reduction_from_D",
                    "D,No AC or NV,A,AC all day,1,Full active-cooling protection relative to sealed passive,9,39,79",
                    "D,No AC or NV,C,AC 2-8pm + NV other hours,2,Peak-window AC plus outside-window NV effect,6,30,60",
                    "D,No AC or NV,B,NV only,3,Natural ventilation effect without AC,4,20,40",
                    "",
                ]
            ),
        )
        _write(
            root / tier / f"fixture_{tier}_differential_summary_2026-07-07.csv",
            "\n".join(
                [
                    "hvac_scenario,metric,value",
                    "A,op_temp_p95_true_c,24",
                    "C,op_temp_p95_true_c,27",
                    "B,op_temp_p95_true_c,29",
                    "D,op_temp_p95_true_c,33",
                    "",
                ]
            ),
        )

    figure_root = root / "figures" / "f2v3_final"
    _write(
        figure_root / "fixture_f2v3_gate_report_2026-07-07.json",
        json.dumps(
            {
                "tier": atlas_service.CERTIFIED_TIER_ID,
                "gate_A_reconciliation": {"status": "PASS", "checks": [{"figure": "F02_summary"}]},
                "gate_A_coverage": {"status": "PASS", "checks": [{"figure": "F02_summary"}]},
            }
        ),
    )
    _write(
        figure_root / "fixture_fig_captions_alt_text_f2v3_2026-07-07.md",
        "# f2v3 captions\n\nFig02. Fixture caption.\n",
    )
    _write(
        figure_root / "fixture_figure_registry_f2v3_2026-07-07.csv",
        "\n".join(
            [
                "figure_id,stem,figure_class,tier_id,source_csv,asset_png,asset_pdf,asset_svg,caption,alt_text,atlas_route,provenance_sidecar",
                "Fig02,F02_summary,results,replocx_tmy3_wallfix_4scen,04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/tables/F02.csv,04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/F02.png,04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/F02.pdf,04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/F02.svg,caption,alt,/results/replocx_tmy3_wallfix_4scen/figures/F02_summary,04_Analysis/_CANONICAL/20_FIGURES/replocx_tmy3_wallfix_4scen/f2v3_final/F02.png.prov.json",
                "",
            ]
        ),
    )
    _write(figure_root / "F02.png", "fixture png")
    _write(figure_root / "F02.pdf", "fixture pdf")
    _write(figure_root / "F02.svg", "<svg />")
    _write(
        figure_root / "tables" / "F02.csv",
        "\n".join(
            [
                "hvac_scenario,scope,op_temp_mean_c,op_temp_p95_true_c,scenario_display_label,scenario_order",
                "A,annual,21,24,AC all day,1",
                "C,annual,22,27,AC 2-8pm + NV other hours,2",
                "B,annual,23,29,NV only,3",
                "D,annual,24,33,No AC or NV,4",
                "",
            ]
        ),
    )
    if include_equity:
        _write(
            root / "equity_profile.csv",
            "\n".join(
                [
                    (
                        "catchment_id,catchment_type,catchment_code,catchment_label,climate_region,urbanicity,"
                        "urbanicity_short,svi_percentile,svi_source_vintage,svi_proxy_badge,"
                        "svi_join_uncertainty_note,acs_median_hh_income,acs_poverty_rate,acs_source_vintage,"
                        "acs_proxy_badge,acs_join_uncertainty_note,doe_lead_energy_burden_pct,"
                        "doe_lead_source_vintage,doe_lead_proxy_badge,doe_lead_join_uncertainty_note,"
                        "heat_vuln_index,heat_vuln_source_vintage,heat_vuln_proxy_badge,"
                        "heat_vuln_join_uncertainty_note,catchment_join_method,equity_layer_status"
                    ),
                    (
                        "CBSA:11184,CBSA,11184,Hot-Humid HDU,Hot-Humid,higher density urban,HDU,"
                        "0.82,CDC/ATSDR SVI 2022 tract RPL_THEMES area-weighted to catchment,Proxy,"
                        "Tract-to-catchment area-weighted proxy; REVIEW SOURCE BEFORE CAUSAL USE,"
                        "42000,0.19,ACS 2019-2023 5-year tract estimates with MOE retained,Direct,"
                        "ACS tract estimates area-weighted to catchment; MOE retained when available,"
                        ",DOE LEAD source not verified,REVIEW REQUIRED,DOE LEAD join not verified,"
                        ",Heat vulnerability source not verified,REVIEW REQUIRED,Heat vulnerability join not verified,"
                        "Tract-to-catchment area-weighted crosswalk over the selected 20 representative locations,"
                        "PARTIAL"
                    ),
                    "",
                ]
            ),
        )


class EnvFixtureMixin:
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture_root = Path(self.tmp.name)
        write_atlas_fixture(self.fixture_root)
        self.old_env = {
            atlas_service.ENABLE_ENV: os.environ.get(atlas_service.ENABLE_ENV),
            atlas_service.DATA_DIR_ENV: os.environ.get(atlas_service.DATA_DIR_ENV),
            atlas_service.FIGURE_DIR_ENV: os.environ.get(atlas_service.FIGURE_DIR_ENV),
            "RLE_PRIVATE_AUTH_TOKEN": os.environ.get("RLE_PRIVATE_AUTH_TOKEN"),
            "RLE_REQUIRE_AUTH": os.environ.get("RLE_REQUIRE_AUTH"),
        }
        os.environ[atlas_service.ENABLE_ENV] = "1"
        os.environ[atlas_service.DATA_DIR_ENV] = str(self.fixture_root)
        os.environ.pop(atlas_service.FIGURE_DIR_ENV, None)
        os.environ.pop("RLE_PRIVATE_AUTH_TOKEN", None)
        os.environ.pop("RLE_REQUIRE_AUTH", None)
        reset_atlas_cache()

    def tearDown(self) -> None:
        for key, value in self.old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_atlas_cache()
        self.tmp.cleanup()


class GatingTests(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        old = os.environ.pop(atlas_service.ENABLE_ENV, None)
        reset_atlas_cache()
        try:
            self.assertFalse(atlas_enabled())
            with self.assertRaises(AtlasUnavailableError):
                get_atlas()
        finally:
            if old is not None:
                os.environ[atlas_service.ENABLE_ENV] = old
            reset_atlas_cache()

    def test_is_atlas_path(self) -> None:
        self.assertTrue(is_atlas_path("/api/results/scenario-summary"))
        self.assertTrue(is_atlas_path("/api/results/scenario-dictionary"))
        self.assertTrue(is_atlas_path("/api/results/d-comparisons"))
        self.assertTrue(is_atlas_path("/api/results/figures"))
        self.assertTrue(is_atlas_path("/api/equity/profiles"))
        self.assertFalse(is_atlas_path("/api/dashboard"))
        self.assertFalse(is_atlas_path("/api/scenarios"))

    def test_normalized_v1_atlas_path_maps_to_shared_dispatch_path(self) -> None:
        self.assertEqual("/api/results/scenario-summary", normalize_api_path("/api/v1/results/scenario-summary"))
        self.assertEqual("/api/equity/scenario-cross", normalize_api_path("/api/v1/equity/scenario-cross"))

    def test_enabled_legacy_bundled_data_fails_loudly(self) -> None:
        old = os.environ.get(atlas_service.ENABLE_ENV)
        old_dir = os.environ.get(atlas_service.DATA_DIR_ENV)
        os.environ[atlas_service.ENABLE_ENV] = "1"
        os.environ[atlas_service.DATA_DIR_ENV] = str(atlas_service.LEGACY_ATLAS_DIR)
        reset_atlas_cache()
        try:
            with self.assertRaisesRegex(AtlasUnavailableError, "legacy bundled Atlas scaffold"):
                get_atlas()
        finally:
            if old is None:
                os.environ.pop(atlas_service.ENABLE_ENV, None)
            else:
                os.environ[atlas_service.ENABLE_ENV] = old
            if old_dir is None:
                os.environ.pop(atlas_service.DATA_DIR_ENV, None)
            else:
                os.environ[atlas_service.DATA_DIR_ENV] = old_dir
            reset_atlas_cache()

    def test_disabled_handle_atlas_still_fails_closed(self) -> None:
        old = os.environ.pop(atlas_service.ENABLE_ENV, None)
        reset_atlas_cache()
        try:
            with self.assertRaises(AtlasUnavailableError):
                handle_atlas("/api/results/scenario-dictionary", {})
        finally:
            if old is not None:
                os.environ[atlas_service.ENABLE_ENV] = old
            reset_atlas_cache()


class ContractConstantTests(unittest.TestCase):
    def test_backend_constants_are_four_scenario_contract(self) -> None:
        self.assertEqual(tuple(EXPECTED_ORDER), atlas_service.EXPECTED_SCENARIO_ORDER)
        self.assertEqual("replocx_tmy3_wallfix_4scen", atlas_service.CERTIFIED_TIER_ID)
        self.assertEqual(720, atlas_service.CERTIFIED_CELL_COUNT)
        self.assertEqual("f2v3_final", atlas_service.FIGURE_REGISTRY_TIER)


class W4DeploymentContractTests(unittest.TestCase):
    def test_public_container_uses_runtime_allowlist(self) -> None:
        dockerfile = (atlas_service.APP_ROOT / "Dockerfile").read_text(encoding="utf-8")
        dockerignore = (atlas_service.APP_ROOT / ".dockerignore").read_text(encoding="utf-8")
        self.assertNotIn("COPY . /app", dockerfile)
        self.assertIn("COPY backend/ /app/backend/", dockerfile)
        for private_path in ("data/atlas/", "pipeline/out/", "tests/fixtures/atlas/"):
            self.assertIn(private_path, dockerignore)

    def test_private_example_has_basic_plus_app_auth_and_read_only_mounts(self) -> None:
        compose = (atlas_service.APP_ROOT / "docker-compose.atlas-private.example.yml").read_text(encoding="utf-8")
        caddy = (atlas_service.APP_ROOT / "deploy" / "atlas-private" / "Caddyfile").read_text(encoding="utf-8")
        self.assertIn('RLE_ENABLE_ATLAS: "1"', compose)
        self.assertIn('RLE_REQUIRE_AUTH: "1"', compose)
        self.assertIn("RLE_PRIVATE_AUTH_TOKEN", compose)
        self.assertGreaterEqual(compose.count(":ro"), 4)
        self.assertIn("basic_auth", caddy)
        self.assertIn('Authorization "Bearer {http.request.header.X-RLE-Auth}"', caddy)
        self.assertIn("header_up -X-RLE-Auth", caddy)


class AtlasW1FixtureTests(EnvFixtureMixin, unittest.TestCase):
    def test_scenario_dictionary_is_loaded_from_certified_metadata(self) -> None:
        payload = handle_atlas("/api/results/scenario-dictionary", {})
        self.assertEqual(EXPECTED_ORDER, payload["scenario_order"])
        self.assertEqual(EXPECTED_ORDER, [row["code"] for row in payload["scenarios"]])
        self.assertEqual("No AC or NV", payload["scenarios"][3]["scenario_display_label"])
        self.assertIn("scenario_dictionary_4scen", payload["source_csv"])

    def test_scenario_summary_returns_acbd_for_annual_and_seasonal(self) -> None:
        for tier in ("annual", "seasonal"):
            payload = handle_atlas("/api/results/scenario-summary", {"tier": tier})
            self.assertEqual(EXPECTED_ORDER, [row["hvac_scenario"] for row in payload["rows"]])
            self.assertEqual(PRIMARY_FAMILIES, payload["endpoint_definitions"]["primary_endpoint_families"])
            self.assertIn("Overheating exposure hours", payload["metric_notes"]["hours_gt_28c"])
            self.assertIn("High-humidity exposure hours", payload["metric_notes"]["humidity_hours"])

    def test_by_stratum_returns_acbd_for_every_dimension_and_tier(self) -> None:
        for tier in ("annual", "seasonal"):
            for dimension in ("climate", "urbanicity", "stratum", "building", "vintage"):
                payload = handle_atlas("/api/results/by-stratum", {"tier": tier, "dimension": dimension})
                group_col = payload["group_column"]
                groups: dict[str, list[str]] = {}
                for row in payload["rows"]:
                    groups.setdefault(str(row[group_col]), []).append(str(row["hvac_scenario"]))
                self.assertTrue(all(order == EXPECTED_ORDER for order in groups.values()))
                first = payload["rows"][0]
                self.assertIn("op_temp_p95_true_c_mean", first)
                self.assertIn("humidity_ratio_mean_kgkg_mean", first)
                self.assertIn("humidity_ratio_p95_true_kgkg_mean", first)
                self.assertIn("op_temp_hours_gt_28c_mean", first)
                self.assertIn("degree_hours_28c_mean", first)

    def test_full_stratum_contract_covers_all_20_combinations(self) -> None:
        for tier in ("annual", "seasonal"):
            payload = handle_atlas("/api/results/by-stratum", {"tier": tier, "dimension": "stratum"})
            self.assertEqual("atlas.strata/1.0", payload["contract_version"])
            self.assertEqual(20, payload["stratum_count"])
            self.assertEqual(["climate_region", "urbanicity"], payload["group_columns"])
            self.assertEqual(EXPECTED_ORDER, payload["scenario_order"])
            self.assertEqual(80, len(payload["rows"]))
            self.assertEqual(
                {(climate, urbanicity) for climate in CLIMATES for urbanicity in URBANICITIES},
                {(row["climate_region"], row["urbanicity"]) for row in payload["strata"]},
            )
            self.assertTrue(
                all(row["n_cells"] == atlas_service.CERTIFIED_CELLS_PER_STRATUM_SCENARIO for row in payload["rows"])
            )
            self.assertEqual("server", payload["aggregation"]["location"])
            self.assertIn("run_level_metrics", payload["source_csv"])
            self.assertTrue(payload["provenance_sidecar"].endswith(".prov.json"))
            self.assertEqual(
                {
                    "tier_id": atlas_service.CERTIFIED_TIER_ID,
                    "r9_status": "PASS",
                    "figure_registry_tier": "f2v3_final",
                    "read_only": True,
                },
                payload["certified_provenance"],
            )

    def test_d_comparisons_include_story_comparisons(self) -> None:
        payload = handle_atlas("/api/results/d-comparisons", {"tier": "annual"})
        self.assertEqual("D", payload["base_scenario"])
        self.assertEqual(["D-B", "D-C", "D-A"], payload["story_comparison_order"])
        self.assertEqual({"D-A", "D-C", "D-B"}, {row["comparison_key"] for row in payload["comparisons"]})
        interpretations = " ".join(str(row["comparison_interpretation"]) for row in payload["comparisons"])
        self.assertIn("Natural ventilation effect", interpretations)
        self.assertIn("Peak-window AC", interpretations)
        self.assertIn("Full active-cooling protection", interpretations)

    def test_provenance_reports_certified_r9_f2v3_domain(self) -> None:
        payload = handle_atlas("/api/results/provenance", {})
        self.assertEqual(atlas_service.CERTIFIED_TIER_ID, payload["tier_id"])
        self.assertEqual(720, payload["certified_cell_count"])
        self.assertEqual("PASS", payload["r9_status"])
        self.assertEqual("f2v3_final", payload["figure_registry_tier"])
        self.assertTrue(payload["read_only_sources"])
        self.assertEqual(PRIMARY_FAMILIES, payload["endpoint_definitions"]["primary_endpoint_families"])
        self.assertIn("figure_registry_f2v3", payload["file_checksums"]["figures.registry"]["file"])

    def test_figure_source_reads_registry_source_csv_rows(self) -> None:
        payload = handle_atlas("/api/results/figure-source", {"figure_id": "Fig02"})
        self.assertEqual("Fig02", payload["figure_id"])
        self.assertEqual("f2v3_final", payload["registry_tier"])
        self.assertIn("/tables/F02.csv", payload["source_csv"])
        self.assertEqual(EXPECTED_ORDER, [row["hvac_scenario"] for row in payload["rows"]])
        self.assertEqual(33, payload["rows"][3]["op_temp_p95_true_c"])

    def test_equity_profiles_verify_layers_and_keep_unverified_review_required(self) -> None:
        payload = handle_atlas("/api/equity/profiles", {})
        self.assertEqual("PARTIAL", payload["catchments"][0]["equity_layer_status"])
        self.assertEqual("READY", payload["catchment_profile_status"])
        layers = {row["id"]: row for row in payload["layers"]["records"]}
        self.assertEqual("READY", layers["cdc_svi"]["status"])
        self.assertEqual("CDC/ATSDR SVI percentile", layers["cdc_svi"]["label"])
        self.assertIn("CDC/ATSDR SVI 2022", layers["cdc_svi"]["source_vintage"])
        self.assertEqual("Proxy", layers["cdc_svi"]["proxy_badge"])
        self.assertIn("area-weighted", layers["cdc_svi"]["join_uncertainty_note"])
        self.assertEqual("READY", layers["acs_income_poverty"]["status"])
        self.assertEqual("Direct", layers["acs_income_poverty"]["proxy_badge"])
        self.assertEqual("REVIEW REQUIRED", layers["doe_lead_energy_burden"]["status"])
        self.assertEqual("REVIEW REQUIRED", layers["heat_vulnerability"]["status"])

    def test_missing_equity_source_keeps_layers_review_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_atlas_fixture(root, include_equity=False)
            payload = AtlasService(root).equity_profiles()
            self.assertEqual([], payload["catchments"])
            self.assertEqual("REVIEW REQUIRED", payload["catchment_profile_status"])
            self.assertIn("equity_profile.csv", payload["missing_source_path"])
            self.assertEqual(0, payload["layers"]["verified_layer_count"])
            self.assertEqual(
                {"cdc_svi", "acs_income_poverty", "doe_lead_energy_burden", "heat_vulnerability"},
                set(payload["layers"]["review_required"]),
            )

    def test_equity_scenario_cross_supports_acbd_and_rejects_invalid_codes(self) -> None:
        for scenario in EXPECTED_ORDER:
            payload = handle_atlas("/api/equity/scenario-cross", {"scenario": scenario, "dimension": "climate"})
            self.assertEqual(scenario, payload["scenario"])
            self.assertEqual("D", payload["d_related_contrast"]["base_scenario"])
            self.assertEqual("Overheating exposure hours", payload["metric_label"])
            self.assertEqual(["Hot-Humid"], [row["climate_region"] for row in payload["rows"]])
            self.assertIn("d_minus_scenario_exposure_hours", payload["rows"][0])
            self.assertIn("verified sidecar-backed equity profile", payload["note"])
            self.assertNotIn("remain REVIEW REQUIRED", payload["note"])
            if scenario == "A":
                self.assertEqual(39, payload["rows"][0]["d_minus_scenario_exposure_hours"])
            if scenario == "D":
                self.assertEqual(0, payload["rows"][0]["d_minus_scenario_exposure_hours"])
        with self.assertRaisesRegex(ValueError, "scenario must be one of"):
            handle_atlas("/api/equity/scenario-cross", {"scenario": "E", "dimension": "climate"})

    def test_exports_smoke_for_results_d_equity_and_figure_bundle(self) -> None:
        results = handle_atlas("/api/results/export-view", {"view": "scenario-summary", "tier": "annual"})
        self.assertEqual("READY", results["csv_export"]["status"])
        self.assertEqual(4, results["row_count"])
        self.assertIn("scenario_summary", results["source_csv"])

        d_compare = handle_atlas("/api/results/export-view", {"view": "d-comparisons", "tier": "annual"})
        self.assertEqual("READY", d_compare["csv_export"]["status"])
        self.assertEqual(3, d_compare["row_count"])
        self.assertIn("d_specific_comparisons", d_compare["source_csv"])

        equity = handle_atlas("/api/results/export-view", {"view": "equity-profiles"})
        self.assertEqual("READY", equity["csv_export"]["status"])
        self.assertEqual(1, equity["row_count"])
        self.assertIn("equity_profile.csv", equity["source_csv"])

        bundle = handle_atlas("/api/results/figure-bundle", {"figure_id": "Fig02"})
        self.assertEqual("f2v3_final", bundle["registry_tier"])
        self.assertIn("/tables/F02.csv", bundle["source_csv"])
        self.assertEqual({"png", "pdf", "svg"}, set(bundle["assets"]))
        for path in [bundle["source_csv"], *bundle["assets"].values()]:
            self.assertIn("f2v3_final", path)
            self.assertNotIn("f2v2_final", path)
            self.assertNotIn("f1v2", path.lower())

        catalog = handle_atlas("/api/results/exports", {})
        self.assertTrue(any(row["view"] == "equity-scenario-cross" for row in catalog["views"]))
        self.assertTrue(any(row["figure_id"] == "Fig02" for row in catalog["figure_bundles"]))

    def test_overview_reports_720_cells_and_embeds_summary_contract(self) -> None:
        payload = handle_atlas("/api/results/overview", {})
        self.assertEqual(720, payload["n_cells"])
        self.assertEqual(EXPECTED_ORDER, payload["scenario_summary"]["scenario_order"])
        self.assertEqual(EXPECTED_ORDER, [row["hvac_scenario"] for row in payload["scenario_summary"]["rows"]])

    def test_optional_cooling_and_sensitivity_do_not_use_legacy_files(self) -> None:
        cooling = handle_atlas("/api/results/cooling-seasons", {})
        sensitivity = handle_atlas("/api/results/sensitivity", {})
        self.assertFalse(cooling["available"])
        self.assertFalse(sensitivity["available"])
        self.assertEqual([], cooling["sites"])
        self.assertEqual([], sensitivity["leave_one_location_out"])
        self.assertIn("legacy bundled Atlas scaffold", cooling["reason"])

    def test_provenance_reports_w3_export_and_equity_fields(self) -> None:
        payload = handle_atlas("/api/results/provenance", {})
        self.assertEqual("PASS", payload["f2v3_gate_report"]["status"])
        self.assertEqual(1, payload["f2v3_registry"]["figure_count"])
        self.assertIn("captions", payload["f2v3_registry"]["captions_source"])
        self.assertEqual("READY", payload["equity_verification"]["status"])
        self.assertTrue(payload["equity_source_notes"])
        self.assertTrue(any(row["view"] == "d-comparisons" for row in payload["export_views"]))

    def test_three_scenario_fixture_fails_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_atlas_fixture(root, include_d=False)
            with self.assertRaisesRegex(AtlasUnavailableError, "Scenario dictionary order"):
                AtlasService(root)


@unittest.skipIf(importlib.util.find_spec("fastapi") is None, "fastapi not installed")
class FastApiAtlasRouteTests(EnvFixtureMixin, unittest.TestCase):
    def test_api_and_v1_result_routes_are_both_mounted_and_dispatch(self) -> None:
        from backend import fastapi_app

        route_paths = {getattr(route, "path", "") for route in fastapi_app.app.routes}
        self.assertIn("/api/results/scenario-summary", route_paths)
        self.assertIn("/api/v1/results/scenario-summary", route_paths)
        self.assertIn("/api/results/export-view", route_paths)
        self.assertIn("/api/v1/results/export-view", route_paths)
        self.assertIn("/api/v1/results/exports", route_paths)
        self.assertIn("/api/v1/results/figure-bundle", route_paths)
        reset_atlas_cache()
        payload = fastapi_app.results_scenario_summary()
        self.assertEqual(EXPECTED_ORDER, [row["hvac_scenario"] for row in payload["rows"]])
        equity_export = fastapi_app.results_export_view(view="equity-profiles")
        self.assertEqual("READY", equity_export["csv_export"]["status"])
        self.assertIn("equity_profile.csv", equity_export["source_csv"])
        catalog = fastapi_app.results_exports()
        self.assertTrue(any(row["view"] == "equity-profiles" for row in catalog["views"]))
        bundle = fastapi_app.results_figure_bundle("Fig02")
        self.assertEqual("f2v3_final", bundle["registry_tier"])

    def test_atlas_disabled_fails_closed_and_public_selection_routes_remain_available(self) -> None:
        from backend import fastapi_app

        os.environ.pop(atlas_service.ENABLE_ENV, None)
        reset_atlas_cache()
        with self.assertRaises(AtlasUnavailableError):
            fastapi_app.results_scenario_summary()
        self.assertEqual("ok", fastapi_app.health()["status"])
        self.assertIn("scenario", fastapi_app.dashboard())


class HealthFlagTests(unittest.TestCase):
    @unittest.skipIf(sys.version_info < (3, 11), "backend.service requires datetime.UTC (Python 3.11+)")
    def test_health_reports_atlas_flag(self) -> None:
        from backend.service import health

        payload = health()
        self.assertIn("atlas_enabled", payload)
        self.assertIsInstance(payload["atlas_enabled"], bool)


if __name__ == "__main__":
    unittest.main()
