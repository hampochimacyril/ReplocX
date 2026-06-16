from __future__ import annotations

import unittest
from pathlib import Path

from backend.data_service import DataService, _external_data_root


class DataServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = DataService()

    def test_dashboard_kpis(self) -> None:
        kpis = self.service.dashboard()["kpis"]
        self.assertEqual(20, kpis["target_strata"])
        self.assertEqual(20, kpis["distinct_locations"])
        self.assertEqual(2959, kpis["candidate_count"])
        self.assertEqual(20, kpis["verified_filter_count"])

    def test_zip_lookup_explains_simulation_scope(self) -> None:
        result = self.service.zip_lookup("19104")
        self.assertEqual("CBSA", result["simulation_filter_geography"]["boundary_type"])
        self.assertIn("ZIP is only a search entry point", result["simulation_filter_geography"]["explanation"])

    def test_rural_zip_uses_county_scope(self) -> None:
        result = self.service.zip_lookup("98290")
        self.assertEqual("County", result["simulation_filter_geography"]["boundary_type"])

    def test_unknown_zip_has_transparent_error(self) -> None:
        with self.assertRaisesRegex(LookupError, "demonstration crosswalk"):
            self.service.zip_lookup("00000")

    def test_external_data_root_handles_shallow_container_path(self) -> None:
        self.assertEqual(Path("/"), _external_data_root(Path("/app")))
        self.assertEqual(Path("/Users"), _external_data_root(Path("/Users/example/Developer")))


if __name__ == "__main__":
    unittest.main()
