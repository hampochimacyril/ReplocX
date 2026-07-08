"""Session 3 regression tests: live ancillary-data paths exercised offline.

These drive the *real* ``--source api`` code paths (HUD crosswalk row building,
TIGER geometry transform, NOAA ISD coverage parsing, ResStock real-dictionary
parsing) against small **recorded fixtures derived from the real schemas** in
``tests/fixtures/ancillary/`` — so the network-only wrappers stay thin while the
logic that matters is covered without network access.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline import classify, fetch_census, geometry, provenance, weather_qc
from pipeline import fetch_hud_crosswalk as hud
from pipeline import resstock_dictionary as rd

FIX = Path(__file__).resolve().parent / "fixtures" / "ancillary"


def _hud_results(name: str) -> list[dict]:
    payload = json.loads((FIX / name).read_text(encoding="utf-8"))
    return payload["data"]["results"]


class HudCrosswalkZipZctaTests(unittest.TestCase):
    """One-to-many retention + the 'never equate ZIP and ZCTA' guarantee."""

    def setUp(self) -> None:
        self.county = _hud_results("hud_zip_county.json")
        self.cbsa = _hud_results("hud_zip_cbsa.json")

    def test_one_to_many_zip_rows_are_retained(self) -> None:
        rows = hud.build_api_rows(self.county, self.cbsa, "Q1 2025")
        # 3 county records -> 3 rows (63143 split across two counties is kept).
        self.assertEqual(3, len(rows))
        z63143 = [r for r in rows if r["zip_code"] == "63143"]
        self.assertEqual({"29189", "29510"}, {r["county_geoid"] for r in z63143})
        # Allocation ratios come straight from the residential ratios.
        ratios = {r["county_geoid"]: r["allocation_ratio"] for r in z63143}
        self.assertEqual(0.7, ratios["29189"])
        self.assertEqual(0.3, ratios["29510"])
        # Primary CBSA per ZIP from the ZIP-CBSA file.
        self.assertTrue(all(r["cbsa_code"] == "41180" for r in z63143))

    def test_zcta_is_never_equated_to_zip(self) -> None:
        # No ZIP->ZCTA file: every ZCTA blank, NOT a copy of the ZIP.
        rows = hud.build_api_rows(self.county, self.cbsa, "Q1 2025")
        self.assertTrue(all(r["zcta"] == "" for r in rows))
        self.assertTrue(all(r["zip_code"] != "" for r in rows))
        self.assertIn("NOT interchangeable", rows[0]["uncertainty_note"])

    def test_zcta_comes_only_from_relationship_file(self) -> None:
        mapping = hud.load_zip_zcta(FIX / "zip_to_zcta.csv")  # maps 19104 only
        rows = hud.build_api_rows(self.county, self.cbsa, "Q1 2025", zip_zcta=mapping)
        by_zip = {}
        for r in rows:
            by_zip.setdefault(r["zip_code"], r)
        self.assertEqual("19104", by_zip["19104"]["zcta"])  # from the file
        # 63143 absent from the file -> still blank, never the ZIP itself.
        self.assertEqual("", by_zip["63143"]["zcta"])
        self.assertIn("relationship file", by_zip["19104"]["uncertainty_note"])

    def test_climate_and_state_resolved_for_known_county(self) -> None:
        rows = hud.build_api_rows(self.county, self.cbsa, "Q1 2025")
        phl = next(r for r in rows if r["zip_code"] == "19104")
        self.assertEqual("42101", phl["county_geoid"])
        self.assertEqual("37980", phl["cbsa_code"])
        self.assertEqual("PA", phl["state"])
        self.assertTrue(phl["climate_region"])  # non-empty climate label

    def test_provenance_counts_one_to_many(self) -> None:
        rows = hud.build_api_rows(self.county, self.cbsa, "Q1 2025")
        payload = hud.provenance_payload(rows, "api", "Q1 2025", None)
        self.assertEqual(3, payload["row_count"])
        self.assertEqual(2, payload["distinct_zip_count"])
        self.assertEqual(1, payload["one_to_many_zip_count"])
        self.assertFalse(payload["zcta_resolved"])
        self.assertEqual(hud.HUD_API, payload["api"]["endpoint"])

    def test_output_schema_is_unchanged(self) -> None:
        rows = hud.build_api_rows(self.county, self.cbsa, "Q1 2025")
        self.assertEqual(set(hud.CROSSWALK_FIELDS), set(rows[0].keys()))

    def test_territories_outside_the_climate_scope_are_excluded(self) -> None:
        county = self.county + [{"zip": "00601", "geoid": "72005", "res_ratio": 1.0}]
        rows = hud.build_api_rows(county, self.cbsa, "Q1 2025")
        self.assertNotIn("00601", {row["zip_code"] for row in rows})

    def test_hud_query_uses_documented_type_year_and_quarter(self) -> None:
        class Response:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict:
                return {"data": {"results": [{"zip": "19104"}]}}

        class Session:
            def __init__(self) -> None:
                self.kwargs: dict = {}

            def get(self, _url: str, **kwargs) -> Response:
                self.kwargs = kwargs
                return Response()

        session = Session()
        rows = hud._hud_query(session, {}, hud._HUD_TYPE["cbsa"], 2025, 1)
        self.assertEqual(3, hud._HUD_TYPE["cbsa"])
        self.assertEqual(
            {"type": 3, "query": "All", "year": 2025, "quarter": 1},
            session.kwargs["params"],
        )
        self.assertEqual([{"zip": "19104"}], rows)


class GeometryTigerTests(unittest.TestCase):
    def test_multipolygon_keeps_all_parts(self) -> None:
        raw = json.loads((FIX / "tiger_multipolygon.json").read_text(encoding="utf-8"))
        geom, adjusted = geometry.geometry_from_tiger(raw)
        self.assertEqual("MultiPolygon", geom["type"])
        self.assertEqual(2, len(geom["coordinates"]))  # island not dropped
        self.assertFalse(adjusted)
        self.assertEqual([], geometry.validate_geometry(geom))

    def test_alaska_antimeridian_is_normalised(self) -> None:
        raw = json.loads((FIX / "tiger_alaska.json").read_text(encoding="utf-8"))
        geom, adjusted = geometry.geometry_from_tiger(raw)
        self.assertTrue(adjusted)
        self.assertEqual([], geometry.validate_geometry(geom))
        lons = [pt[0] for ring in geom["coordinates"] for pt in ring]
        self.assertTrue(max(lons) > 180.0)  # western lons shifted by +360

    def test_simplify_ring_reduces_and_closes(self) -> None:
        # A jagged near-straight edge collapses to its endpoints; ring stays closed.
        ring = [[0.0, 0.0]]
        for i in range(1, 50):
            ring.append([i * 0.001, 0.0 + (0.00001 if i % 2 else -0.00001)])
        ring.append([0.05, 0.05])
        ring.append([0.0, 0.05])
        ring.append([0.0, 0.0])
        simplified = geometry.simplify_ring(ring, epsilon=0.01)
        self.assertLess(len(simplified), len(ring))
        self.assertEqual(simplified[0], simplified[-1])

    def test_validate_geometry_flags_bad_rings(self) -> None:
        unclosed = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]]}  # not closed
        self.assertTrue(geometry.validate_geometry(unclosed))
        too_few = {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [0, 0]]]}
        self.assertTrue(geometry.validate_geometry(too_few))
        self.assertIn("unsupported", geometry.validate_geometry({"type": "Point", "coordinates": [0, 0]})[0])

    def test_fixture_collection_remains_simple_polygon(self) -> None:
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
        feat = fc["features"][0]
        self.assertEqual("Polygon", feat["geometry"]["type"])
        ring = feat["geometry"]["coordinates"][0]
        self.assertEqual(ring[0], ring[-1])


class NationalClassificationTests(unittest.TestCase):
    @staticmethod
    def _raw(catchment_type: str, code: str, population: int, area: float, county: str) -> dict:
        return {
            "catchment_type": catchment_type,
            "catchment_code": code,
            "catchment_label": code,
            "primary_county_geoid": county,
            "population": population,
            "housing_units": population // 2,
            "land_area_sqmi": area,
            "centroid_lat": 40.0,
            "centroid_lon": -75.0,
        }

    def test_station_label_supplies_cbsa_climate_but_density_supplies_urbanicity(self) -> None:
        raw = self._raw("CBSA", "37980", 4000, 1.0, "99999")
        labels = {
            "37980": {
                "climate_region": "Mixed-Humid",
                "urbanicity": "rural",
            }
        }
        row = classify._classify_row(raw, labels)
        self.assertEqual("Mixed-Humid", row["climate_region"])
        self.assertEqual("higher density urban", row["urbanicity"])
        self.assertEqual("CBSA", row["catchment_type"])

    def test_incompatible_raw_geography_is_filtered_not_relabelled(self) -> None:
        rows = [
            self._raw("County", "42101", 4000, 1.0, "42101"),
            self._raw("County", "42023", 100, 1.0, "42023"),
            self._raw("CBSA", "37980", 4000, 1.0, "42101"),
            self._raw("CBSA", "12345", 100, 1.0, "42101"),
        ]
        classified = classify.classify_rows(rows)
        self.assertEqual(
            {("County", "42023"), ("CBSA", "37980")},
            {(row["catchment_type"], row["catchment_code"]) for row in classified},
        )

    def test_cbsa_primary_county_prefers_central_and_excludes_territories(self) -> None:
        text = (
            "CBSA Code,FIPS State Code,FIPS County Code,Central/Outlying County\n"
            "12345,01,003,Outlying\n"
            "12345,01,001,Central\n"
            "54321,72,005,Central\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "delineation.csv"
            path.write_text(text, encoding="utf-8")
            with patch.dict(os.environ, {"RLE_CBSA_DELINEATION_FILE": str(path)}):
                mapping = fetch_census._load_cbsa_counties()
        self.assertEqual({"12345": ["01001"]}, mapping)


class WeatherLeapYearTests(unittest.TestCase):
    def test_expected_hours_leap_aware(self) -> None:
        self.assertEqual(8760, weather_qc.expected_hours_for(2023))
        self.assertEqual(8784, weather_qc.expected_hours_for(2024))  # divisible by 4
        self.assertEqual(8784, weather_qc.expected_hours_for(2000))  # divisible by 400
        self.assertEqual(8760, weather_qc.expected_hours_for(1900))  # /100 not /400

    def test_coverage_from_recorded_isd_csv(self) -> None:
        text = (FIX / "isd_global_hourly_leap.csv").read_text(encoding="utf-8")
        coverage = weather_qc.coverage_from_csv(text, 2024)
        # 4 distinct valid hours (the +9999 temp row is dropped; the duplicate
        # 13:00 hour is de-duplicated against its valid sibling).
        self.assertEqual(4, int(round(coverage * weather_qc.expected_hours_for(2024))))
        self.assertEqual("INCOMPLETE", weather_qc.status_for(coverage))

    def test_fixture_rows_use_leap_expected_hours(self) -> None:
        rows = weather_qc.compute_rows([(722003, "A")], "fixture", 2024)
        self.assertEqual(8784, rows[0]["expected_hours"])
        rows_2023 = weather_qc.compute_rows([(722003, "A")], "fixture", 2023)
        self.assertEqual(8760, rows_2023[0]["expected_hours"])

    def test_error_report_roundtrip(self) -> None:
        errors = [{"station_number": "999999", "station_name": "X", "year": 2024, "url": "u", "error": "HTTP 404"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "errs.csv"
            weather_qc.write_error_report(errors, path)
            text = path.read_text(encoding="utf-8")
        self.assertIn("station_number,station_name,year,url,error", text)
        self.assertIn("HTTP 404", text)

    def test_station_history_resolves_usaf_to_active_wban(self) -> None:
        text = (
            '"USAF","WBAN","STATION NAME","BEGIN","END"\n'
            '"722280","99999","OLD","19000101","20221231"\n'
            '"722280","13876","BIRMINGHAM","19420801","20250827"\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "isd-history.csv"
            path.write_text(text, encoding="utf-8")
            mapping = weather_qc.load_station_ids(2023, path)
        self.assertEqual("72228013876", mapping[722280])
        self.assertEqual(
            "https://www.ncei.noaa.gov/data/global-hourly/access/2023/72228013876.csv",
            weather_qc.isd_url(mapping[722280], 2023),
        )


class ResStockRealDictionaryTests(unittest.TestCase):
    def test_options_lookup_tsv(self) -> None:
        enums = rd.load_real_dictionary(FIX / "resstock_options_lookup.tsv")
        self.assertIn("37980", enums[rd.CBSA_FIELD])
        ok, _ = rd.verify(rd.CBSA_FIELD, "37980", enums, "x")
        self.assertTrue(ok)
        bad, note = rd.verify(rd.CBSA_FIELD, "99999", enums, "x")
        self.assertFalse(bad)
        self.assertIn("REVIEW REQUIRED", note)

    def test_data_dictionary_tsv_splits_packed_list(self) -> None:
        enums = rd.load_real_dictionary(FIX / "resstock_data_dictionary.tsv")
        self.assertEqual({"10000", "37980", "41180"}, enums[rd.CBSA_FIELD])
        self.assertEqual({"42101", "29189"}, enums[rd.COUNTY_FIELD])

    def test_enumeration_dictionary_tsv(self) -> None:
        enums = rd.load_real_dictionary(FIX / "resstock_enumeration_dictionary.tsv")
        self.assertIn("42101", enums[rd.COUNTY_FIELD])

    def test_current_oedi_enumeration_dictionary_headers(self) -> None:
        text = (
            "metadata_column\tenumeration\tenumeration_description\n"
            'in.county\t"AZ, Maricopa County"\t"County description"\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "enumeration_dictionary.tsv"
            path.write_text(text, encoding="utf-8")
            enums = rd.load_real_dictionary(path)
        self.assertEqual({"AZ, Maricopa County"}, enums[rd.COUNTY_FIELD])

    def test_resolves_current_nrel_county_and_renamed_cbsa_labels(self) -> None:
        enums = {
            rd.COUNTY_FIELD: {"AZ, Maricopa County"},
            rd.CBSA_FIELD: {"Phoenix-Mesa-Scottsdale, AZ MSA"},
        }
        county = rd.resolve_filter_value(
            rd.COUNTY_FIELD,
            "04013",
            "Census Tract 101.02; Maricopa County; Arizona",
            enums,
        )
        cbsa = rd.resolve_filter_value(
            rd.CBSA_FIELD,
            "38060",
            "Phoenix-Mesa-Chandler, AZ",
            enums,
        )
        self.assertEqual("AZ, Maricopa County", county)
        self.assertEqual("Phoenix-Mesa-Scottsdale, AZ MSA", cbsa)

    def test_resolves_cbsa_when_release_state_footprint_differs(self) -> None:
        enums = {
            rd.CBSA_FIELD: {
                "Chicago-Naperville-Elgin, IL-IN-WI MSA",
                "New York-Newark-Jersey City, NY-NJ-PA MSA",
            }
        }
        self.assertEqual(
            "Chicago-Naperville-Elgin, IL-IN-WI MSA",
            rd.resolve_filter_value(
                rd.CBSA_FIELD,
                "16980",
                "Chicago-Naperville-Elgin, IL-IN",
                enums,
            ),
        )

    def test_api_source_with_real_dictionary_records_provenance(self) -> None:
        import os

        old = os.environ.get("RESSTOCK_ENUMERATION_FILE")
        os.environ["RESSTOCK_ENUMERATION_FILE"] = str(FIX / "resstock_options_lookup.tsv")
        try:
            enums, label, prov = rd.load_enumerations_detailed("api")
        finally:
            if old is None:
                os.environ.pop("RESSTOCK_ENUMERATION_FILE", None)
            else:
                os.environ["RESSTOCK_ENUMERATION_FILE"] = old
        self.assertTrue(prov["loaded"])
        self.assertIn("resstock_options_lookup.tsv", label)
        self.assertEqual(64, len(prov["sha256"]))  # real digest recorded
        ok, _ = rd.verify(rd.CBSA_FIELD, "37980", enums, label)
        self.assertTrue(ok)


class ProvenanceHelperTests(unittest.TestCase):
    def test_sha256_and_records(self) -> None:
        self.assertEqual(64, len(provenance.sha256_bytes(b"abc")))
        rec = provenance.download_record("http://x/y", b"abc", cached_file="y")
        self.assertEqual(3, rec["bytes"])
        self.assertEqual("y", rec["cached_file"])
        self.assertIn("downloaded_at_utc", rec)


if __name__ == "__main__":
    unittest.main()
