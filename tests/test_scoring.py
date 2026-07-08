from __future__ import annotations

import unittest

from backend.data_service import DataService
from backend.models import DEFAULT_OVERRIDE, ScenarioConfig
from backend.scoring import data_compatible_default_config


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

    def test_default_research_override_is_honored(self) -> None:
        # The default scenario applies a research-priority override. The overridden
        # stratum must select the override's catchment regardless of its
        # unconstrained rank, so this holds for both the demo dataset and any real
        # national pipeline output (where the override target need not rank #2).
        overridden = [
            row
            for row in self.result["selected"]
            if row["climate_region"] == DEFAULT_OVERRIDE.climate_region
            and row["urbanicity"] == DEFAULT_OVERRIDE.urbanicity
        ]
        self.assertEqual(1, len(overridden))
        self.assertEqual(DEFAULT_OVERRIDE.catchment_code, str(overridden[0]["catchment_code"]).zfill(5))
        self.assertGreaterEqual(int(overridden[0]["scenario_rank"]), 1)

    def test_implicit_default_override_is_removed_when_dataset_reclassifies_target(self) -> None:
        candidates = [dict(row) for row in self.service.candidates]
        target = next(row for row in candidates if str(row["catchment_code"]).zfill(5) == "37980")
        target["urbanicity"] = "lower density urban"
        target["urbanicity_short"] = "LDU"
        config = data_compatible_default_config(candidates)
        self.assertEqual((), config.overrides)

    def test_leading_zero_geography_identifiers_are_preserved(self) -> None:
        lookup = self.service.zip_lookup("02108")
        self.assertEqual("02108", lookup["zip_code"])
        self.assertEqual("02108", lookup["resolved"]["zcta"])
        self.assertEqual("25025", lookup["resolved"]["county_geoid"])

    def test_weights_must_sum_to_one(self) -> None:
        with self.assertRaisesRegex(ValueError, "sum to 1.0"):
            ScenarioConfig.from_dict(
                {
                    "weights": {
                        "housing_unit_coverage_percentile": 0.5,
                        "population_density_percentile": 0.5,
                        "population_coverage_percentile": 0.5,
                    }
                }
            )


if __name__ == "__main__":
    unittest.main()
