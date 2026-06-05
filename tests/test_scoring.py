from __future__ import annotations

import unittest

from backend.data_service import DataService
from backend.models import ScenarioConfig


class ScoringRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = DataService()
        cls.result = cls.service.evaluate()

    def test_exactly_twenty_strata_and_one_selection_per_stratum(self) -> None:
        selected = self.result["selected"]
        strata = {(row["climate_region"], row["urbanicity"]) for row in selected}
        self.assertEqual(20, len(selected))
        self.assertEqual(20, len(strata))

    def test_unique_constraint_produces_twenty_distinct_catchments(self) -> None:
        keys = {row["location_uniqueness_key"] for row in self.result["selected"]}
        self.assertEqual(20, len(keys))

    def test_resstock_field_rules_and_enumeration_verification(self) -> None:
        for row in self.result["selected"]:
            if row["urbanicity"] == "rural":
                self.assertEqual("County", row["catchment_type"])
                self.assertEqual("in.county", row["nrel_filter_field"])
            else:
                self.assertEqual("CBSA", row["catchment_type"])
                self.assertEqual("in.metropolitan_and_micropolitan_statistical_area", row["nrel_filter_field"])
            self.assertTrue(row["nrel_value_verified"], row["catchment_label"])

    def test_default_scenario_applies_no_override(self) -> None:
        # No research-priority override is applied by default: every stratum keeps
        # its top-ranked candidate and there are no substitutions.
        self.assertEqual([], self.result["config"]["overrides"])
        self.assertEqual([], self.result["changes"])
        for row in self.result["selected"]:
            self.assertEqual(1, row["scenario_rank"], row["catchment_label"])

    def test_leading_zero_geography_identifiers_are_preserved(self) -> None:
        lookup = self.service.zip_lookup("02108")
        self.assertEqual("02108", lookup["zip_code"])
        self.assertEqual("02108", lookup["resolved"]["zcta"])
        self.assertEqual("25025", lookup["resolved"]["county_geoid"])

    def test_weights_must_sum_to_one(self) -> None:
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            ScenarioConfig.from_dict({"weights": {
                "housing_unit_coverage_percentile": 0.5,
                "population_density_percentile": 0.5,
                "population_coverage_percentile": 0.5,
            }})


if __name__ == "__main__":
    unittest.main()

