"""Phase 2 regression tests: HUD crosswalk, weather QC, and TIGER geometry.

These run against the offline fixture pipeline output in ``pipeline/out`` (built
with ``python3 -m pipeline.run --source fixture``), keeping the bundled demo as
the default for every other suite.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from backend.data_service import DataService
from pipeline import geometry, validate, weather_qc

APP_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_OUT = Path(os.environ.get("RLE_ANALYSIS_DATA_DIR", APP_ROOT / "pipeline" / "out"))


class WeatherQcUnitTests(unittest.TestCase):
    def test_threshold_is_ninety_percent(self) -> None:
        self.assertEqual(0.90, weather_qc.COMPLETE_THRESHOLD)
        self.assertEqual("COMPLETE", weather_qc.status_for(0.90))
        self.assertEqual("COMPLETE", weather_qc.status_for(0.999))
        self.assertEqual("INCOMPLETE", weather_qc.status_for(0.8999))

    def test_fixture_rows_are_deterministic_and_well_formed(self) -> None:
        a = weather_qc.compute_rows([(722003, "A"), (720283, "B")], "fixture")
        b = weather_qc.compute_rows([(720283, "B"), (722003, "A")], "fixture")
        self.assertEqual(a, b)  # order-independent + reproducible
        for row in a:
            self.assertEqual(8760, row["expected_hours"])
            self.assertEqual(row["hourly_weather_qc_status"], weather_qc.status_for(row["coverage_fraction"]))


class GeometryUnitTests(unittest.TestCase):
    def test_fixture_polygons_are_closed_rings(self) -> None:
        rows = [
            {
                "catchment_type": "CBSA",
                "catchment_code": "37980",
                "centroid_lat": 39.95,
                "centroid_lon": -75.16,
                "catchment_label": "Philly",
                "climate_region": "Mixed-Humid",
                "urbanicity_short": "HDU",
            }
        ]
        fc = geometry.feature_collection(rows, "fixture")
        self.assertEqual("FeatureCollection", fc["type"])
        ring = fc["features"][0]["geometry"]["coordinates"][0]
        self.assertEqual(ring[0], ring[-1])


@unittest.skipUnless(
    (PIPELINE_OUT / "selection_metadata.json").exists(),
    "pipeline/out missing; run `python3 -m pipeline.run --source fixture`",
)
class PipelineOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = DataService(analysis_dir=PIPELINE_OUT)

    def test_validate_passes_on_pipeline_output(self) -> None:
        self.assertEqual([], validate.validate(PIPELINE_OUT))

    def test_weather_qc_replaces_pending(self) -> None:
        statuses = {row["hourly_weather_qc_status"] for row in self.service.site_list}
        self.assertNotIn("PENDING", statuses)
        self.assertTrue(statuses <= {"COMPLETE", "INCOMPLETE"})
        kpis = self.service.dashboard()["kpis"]
        self.assertGreaterEqual(kpis["weather_qc_complete_count"], 0)
        self.assertLessEqual(kpis["weather_qc_complete_count"], 20)

    def test_geometry_matches_selected_catchments(self) -> None:
        geo = self.service.geometry()
        self.assertEqual(20, len(geo["features"]))
        geo_keys = {
            f"{f['properties']['catchment_type']}:{str(f['properties']['catchment_code']).zfill(5)}"
            for f in geo["features"]
        }
        sel_keys = {f"{r['catchment_type']}:{str(r['catchment_code']).zfill(5)}" for r in self.service.selected}
        self.assertEqual(sel_keys, geo_keys)

    def test_crosswalk_from_pipeline_resolves_zip(self) -> None:
        self.assertEqual("HUD-USPS crosswalk (pipeline output)", self.service.provenance()["zip_crosswalk"]["mode"])
        cbsa = self.service.zip_lookup("19104")
        self.assertEqual("CBSA", cbsa["simulation_filter_geography"]["boundary_type"])
        self.assertTrue(cbsa["resolved"]["urbanicity"])
        rural_rows = [row for row in self.service.zip_crosswalk if row["urbanicity"] == "rural"]
        if rural_rows:
            rural_zip = str(rural_rows[0]["zip_code"]).zfill(5)
            rural = self.service.zip_lookup(rural_zip)
            self.assertEqual("County", rural["simulation_filter_geography"]["boundary_type"])
        # Leading zeros preserved through the pipeline crosswalk too.
        self.assertEqual("02108", self.service.zip_lookup("02108")["resolved"]["zcta"])


if __name__ == "__main__":
    unittest.main()
