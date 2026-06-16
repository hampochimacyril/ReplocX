"""Session 2 regression tests: the tract-level pilot pipeline.

These exercise the genuinely tract-derived pilot over the recorded offline
fixtures for the three pilot states (Pennsylvania, Arizona, Minnesota). They
assert the tract→county/CBSA aggregation, that join losses and unresolved
classifications are reported (not silently dropped), deterministic reruns, and
that the pilot stays partial and schema-compatible without claiming to be a
complete national result. They never touch the network and never overwrite the
national ``pipeline/out`` dataset.
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline import config, pilot, validate

ANALYTICAL_FILES = [
    "candidate_scores.csv",
    "selected_locations.csv",
    "resstock_site_list.csv",
    "stratum_status.csv",
    "station_weather_qc.csv",
    "selected_geometry.json",
    "pilot_report.json",  # deterministic in fixture mode (no timestamp/manifest)
]


def _read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class PilotAggregationTests(unittest.TestCase):
    """Unit-level checks on the tract→catchment aggregation itself."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tracts = pilot.load_tracts_fixture(sorted(pilot.PILOT_STATES))
        cls.delineation = pilot.load_delineation_fixture()
        cls.agg = pilot.aggregate(cls.tracts, cls.delineation)
        cls.catchments = {f"{c['catchment_type']}:{c['catchment_code']}": c for c in cls.agg["catchments"]}
        cls.report = cls.agg["report"]

    def test_catchments_are_aggregated_from_tracts(self) -> None:
        # Every catchment is built from >= 1 tract, and is genuinely an aggregate
        # (the fixture has multi-tract catchments).
        self.assertTrue(self.catchments)
        self.assertTrue(all(c["tract_count"] >= 1 for c in self.catchments.values()))
        self.assertTrue(any(c["tract_count"] > 1 for c in self.catchments.values()))

    def test_cbsa_population_equals_sum_of_its_nonrural_tracts(self) -> None:
        # Philadelphia CBSA 37980 is built only from its member counties'
        # non-rural tracts; its population must equal that exact sum.
        member_counties = {county for county, m in self.delineation.items() if m["cbsa_code"] == "37980"}
        expected_pop = 0
        for t in self.tracts:
            if t["county_geoid"] in member_counties:
                density = t["population"] / t["land_area_sqmi"]
                if config.urbanicity_for_density(density) != "rural":
                    expected_pop += t["population"]
        self.assertEqual(expected_pop, self.catchments["CBSA:37980"]["population"])
        self.assertEqual("higher density urban", self.catchments["CBSA:37980"]["urbanicity"])

    def test_rural_tracts_roll_up_to_county_catchments(self) -> None:
        # St. Louis County, MN (27137) has rural tracts -> a County catchment,
        # even though the county also contributes non-rural tracts to a CBSA.
        self.assertIn("County:27137", self.catchments)
        self.assertEqual("rural", self.catchments["County:27137"]["urbanicity"])
        self.assertEqual("Cold & Very Cold", self.catchments["County:27137"]["climate_region"])

    def test_county_cbsa_type_rule(self) -> None:
        for key, c in self.catchments.items():
            if c["urbanicity"] == "rural":
                self.assertEqual("County", c["catchment_type"], key)
            else:
                self.assertEqual("CBSA", c["catchment_type"], key)

    def test_join_losses_reported_not_dropped(self) -> None:
        # Two non-rural tracts sit in Non-core counties (no CBSA) in the fixture.
        self.assertEqual(2, self.report["join_loss_count"])
        lost = {row["tract_geoid"] for row in self.report["join_losses"]}
        self.assertEqual({"04001000204", "42023000204"}, lost)

    def test_every_tract_is_accounted_for(self) -> None:
        # Nothing is silently discarded: each tract lands in a catchment or is
        # explicitly reported as a join loss / unresolved classification.
        in_catchments = sum(c["tract_count"] for c in self.catchments.values())
        reported_out = self.report["join_loss_count"]
        # unresolved CBSAs would also remove tracts; sum their members too.
        self.assertEqual(len(self.tracts), in_catchments + reported_out)

    def test_identifiers_preserved_as_strings_with_leading_zeros(self) -> None:
        # Arizona county 04021 and its 11-digit tract GEOIDs keep leading zeros.
        self.assertIn("County:04021", self.catchments)
        self.assertTrue(all(len(t["tract_geoid"]) == 11 for t in self.tracts))
        self.assertTrue(any(t["county_geoid"].startswith("04") for t in self.tracts))

    def test_state_tract_cache_manifest_redacts_census_key(self) -> None:
        payload = b'[["NAME","B01003_001E","B25001_001E","state","county","tract"]]'

        class Response:
            content = payload

            def raise_for_status(self) -> None:
                return None

        class Session:
            params: list[tuple[str, str]] = []

            def get(self, _url: str, **kwargs) -> Response:
                self.params = kwargs["params"]
                return Response()

        with tempfile.TemporaryDirectory() as tmp:
            session = Session()
            manifest: list[dict] = []
            with (
                patch.object(config, "PILOT_CACHE_DIR", Path(tmp)),
                patch.object(config, "APP_ROOT", Path(tmp)),
            ):
                rows = pilot._load_state_tract_payload(
                    session,
                    "https://api.census.gov/data/2023/acs/acs5",
                    "42",
                    "secret-key",
                    manifest,
                )
        self.assertEqual("NAME", rows[0][0])
        self.assertIn(("key", "secret-key"), session.params)
        self.assertNotIn("secret-key", json.dumps(manifest))


class PilotOutputTests(unittest.TestCase):
    """End-to-end pilot run into a temp dir, then schema/invariant checks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name) / "pilot_out"
        cls.outputs = pilot.build_outputs("fixture")
        pilot.write_outputs(cls.outputs, cls.out, "fixture")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_pilot_validation_passes(self) -> None:
        self.assertEqual([], pilot.validate_pilot(self.out))

    def test_outputs_are_schema_compatible(self) -> None:
        from pipeline.build_catchments import CANDIDATE_FIELDS, SITE_FIELDS, STRATUM_FIELDS

        with (self.out / "candidate_scores.csv").open(encoding="utf-8-sig") as h:
            self.assertEqual(CANDIDATE_FIELDS, next(csv.reader(h)))
        with (self.out / "selected_locations.csv").open(encoding="utf-8-sig") as h:
            self.assertEqual(CANDIDATE_FIELDS, next(csv.reader(h)))
        with (self.out / "resstock_site_list.csv").open(encoding="utf-8-sig") as h:
            self.assertEqual(SITE_FIELDS, next(csv.reader(h)))
        with (self.out / "stratum_status.csv").open(encoding="utf-8-sig") as h:
            self.assertEqual(STRATUM_FIELDS, next(csv.reader(h)))

    def test_pilot_is_partial_not_national(self) -> None:
        report = self.outputs["report"]
        self.assertLess(report["strata_present"], len(config.STRATA))
        self.assertEqual(20, report["national_strata_total"])
        meta = json.loads((self.out / "selection_metadata.json").read_text(encoding="utf-8"))
        self.assertIs(True, meta["is_partial_result"])
        dictionary = meta["provenance"]["resstock_dictionary"]
        self.assertTrue(dictionary["loaded"])
        self.assertEqual(64, len(dictionary["sha256"]))
        # The strict national validator must reject the partial pilot output
        # (proving the pilot is not masquerading as a complete national result).
        self.assertNotEqual([], validate.validate(self.out))

    def test_three_distinct_climate_regions_and_full_urbanicity_spread(self) -> None:
        selected = _read(self.out / "selected_locations.csv")
        climates = {r["climate_region"] for r in selected}
        urbanicities = {r["urbanicity"] for r in selected}
        self.assertEqual({"Mixed-Humid", "Hot-Dry & Mixed Dry", "Cold & Very Cold"}, climates)
        self.assertEqual(set(config.URBANICITY_ORDER), urbanicities)
        self.assertIn("Mixed-Humid", climates)  # Pennsylvania is required in the pilot

    def test_row_counts_match_report(self) -> None:
        report = self.outputs["report"]
        candidates = _read(self.out / "candidate_scores.csv")
        selected = _read(self.out / "selected_locations.csv")
        stratum = _read(self.out / "stratum_status.csv")
        self.assertEqual(report["candidate_count"], len(candidates))
        self.assertEqual(report["selected_count"], len(selected))
        self.assertEqual(report["strata_present"], len(stratum))
        resolved = [r for r in stratum if r["status"] == "RESOLVED"]
        self.assertEqual(len(resolved), len(selected))

    def test_one_distinct_selection_per_resolved_stratum(self) -> None:
        selected = _read(self.out / "selected_locations.csv")
        strata = [(r["climate_region"], r["urbanicity"]) for r in selected]
        keys = [f"{r['catchment_type']}:{r['catchment_code']}" for r in selected]
        self.assertEqual(len(strata), len(set(strata)))
        self.assertEqual(len(keys), len(set(keys)))

    def test_county_cbsa_and_resstock_field_rules(self) -> None:
        for r in _read(self.out / "selected_locations.csv"):
            if r["urbanicity"] == "rural":
                self.assertEqual("County", r["catchment_type"])
            else:
                self.assertEqual("CBSA", r["catchment_type"])
        for r in _read(self.out / "resstock_site_list.csv"):
            if r["target_catchment_type"] == "County":
                self.assertEqual("in.county", r["nrel_filter_field"])
            else:
                self.assertEqual("in.metropolitan_and_micropolitan_statistical_area", r["nrel_filter_field"])

    def test_does_not_overwrite_national_outputs(self) -> None:
        self.assertNotEqual(config.OUT_DIR.resolve(), self.out.resolve())


class PilotDeterminismTests(unittest.TestCase):
    def test_repeated_runs_produce_identical_analytical_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            dir_a, dir_b = Path(a), Path(b)
            pilot.write_outputs(pilot.build_outputs("fixture"), dir_a, "fixture")
            pilot.write_outputs(pilot.build_outputs("fixture"), dir_b, "fixture")
            for name in ANALYTICAL_FILES:
                self.assertEqual(
                    (dir_a / name).read_bytes(),
                    (dir_b / name).read_bytes(),
                    f"{name} is not reproducible across runs",
                )


if __name__ == "__main__":
    unittest.main()
