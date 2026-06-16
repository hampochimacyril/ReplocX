"""Phase 3 regression tests: ResStock enumeration verification, export adapters,
and the stdlib Python client.

The verification + export tests run against the bundled demo dataset (the default
for every suite). The client test spins up the dependency-free ``backend.server``
on an ephemeral port and drives it through the public ``rle_client`` package.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from backend import exports
from backend.data_service import DataService
from pipeline import resstock_dictionary as rd

APP_ROOT = Path(__file__).resolve().parents[1]
CLIENT_SRC = APP_ROOT / "clients" / "python"
if str(CLIENT_SRC) not in sys.path:
    sys.path.insert(0, str(CLIENT_SRC))


class ResStockDictionaryTests(unittest.TestCase):
    def test_fixture_dictionary_verifies_known_and_rejects_unknown(self) -> None:
        enums, label = rd.load_enumerations("fixture")
        self.assertIn("bundled demonstration", label)
        ok, note = rd.verify(rd.CBSA_FIELD, "37980", enums, label)
        self.assertTrue(ok)
        self.assertNotIn("REVIEW REQUIRED", note)
        bad_ok, bad_note = rd.verify(rd.CBSA_FIELD, "99999", enums, label)
        self.assertFalse(bad_ok)
        self.assertIn("REVIEW REQUIRED", bad_note)

    def test_api_without_dictionary_flags_review_required(self) -> None:
        # No RESSTOCK_ENUMERATION_FILE set -> nothing is silently verified.
        enums, label = rd.load_enumerations("api")
        self.assertEqual({}, enums)
        ok, note = rd.verify(rd.CBSA_FIELD, "37980", enums, label)
        self.assertFalse(ok)
        self.assertIn("REVIEW REQUIRED", note)

    def test_demo_verified_codes_are_in_the_dictionary(self) -> None:
        """Honesty tie: any demo code marked verified must exist in the bundled
        enumeration, so 'VERIFIED' in the demo is never an unbacked assertion."""
        enums, _ = rd.load_enumerations("fixture")
        with (APP_ROOT / "data" / "demo" / "resstock_site_list.csv").open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if str(row["nrel_value_verified"]).strip().lower() in {"true", "1"}:
                    field = row["nrel_filter_field"]
                    value = str(row["nrel_filter_value"]).zfill(5)
                    self.assertIn(
                        value,
                        enums.get(field, set()),
                        f"demo code {field}={value} marked verified but not in dictionary",
                    )


class ExportAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = DataService()
        cls.selected = cls.service.evaluate({})["selected"]

    def test_resstock_sampling_csv_shape(self) -> None:
        text = exports.resstock_sampling_csv(self.selected)
        reader = list(csv.DictReader(text.splitlines()))
        self.assertEqual(20, len(reader))
        self.assertEqual(exports.SAMPLING_FIELDS, list(reader[0].keys()))
        for row in reader:
            self.assertIn(row["parameter"], {rd.COUNTY_FIELD, rd.CBSA_FIELD})
            self.assertEqual(5, len(row["option"]))  # zero-padded
            if row["catchment_type"] == "County":
                self.assertEqual(rd.COUNTY_FIELD, row["parameter"])

    def test_downselect_logic_format(self) -> None:
        logic = exports.downselect_logic(self.selected)
        self.assertEqual(20, len(logic))
        for entry in logic:
            self.assertEqual(1, entry.count("|"))

    def test_openstudio_manifest_pairs_sites_with_stations(self) -> None:
        manifest = exports.openstudio_manifest(self.selected, self.service.provenance())
        self.assertEqual("rle.openstudio_manifest/1.0", manifest["schema"])
        self.assertEqual(20, manifest["site_count"])
        self.assertEqual(20, len(manifest["sites"]))
        sel_ids = {f"{r['catchment_type']}:{str(r['catchment_code']).zfill(5)}" for r in self.selected}
        man_ids = {s["id"] for s in manifest["sites"]}
        self.assertEqual(sel_ids, man_ids)
        for site in manifest["sites"]:
            self.assertIn("verification_status", site["resstock_filter"])
            station = site["weather_station"]
            self.assertTrue(station["isd_station_id"])
            self.assertIn("epw_hint", station)
            self.assertIn(station["isd_station_id"], station["epw_hint"])


class _QuietHandler:
    """Mixin to silence per-request stderr logging during tests."""

    def log_message(self, *args, **kwargs):  # noqa: D401, ANN002, ANN003
        return


class PythonClientEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._old_db = os.environ.get("RLE_SCENARIO_DB")
        cls._scenario_db_dir = tempfile.TemporaryDirectory()
        os.environ["RLE_SCENARIO_DB"] = str(Path(cls._scenario_db_dir.name) / "scenarios.sqlite3")
        from backend.server import Handler

        handler = type("TestHandler", (_QuietHandler, Handler), {})
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        from rle_client import RLEClient

        cls.client = RLEClient(f"http://{host}:{port}", timeout=10.0)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls._scenario_db_dir.cleanup()
        if cls._old_db is None:
            os.environ.pop("RLE_SCENARIO_DB", None)
        else:
            os.environ["RLE_SCENARIO_DB"] = cls._old_db

    def test_health_and_selection(self) -> None:
        health = self.client.health()
        self.assertEqual("ok", health["status"])
        self.assertTrue(health["data_ready"])
        self.assertEqual(20, len(self.client.selected_locations()))

    def test_export_adapters_over_http(self) -> None:
        sampling = self.client.resstock_sampling_csv()
        self.assertEqual(20, len(list(csv.DictReader(sampling.splitlines()))))
        manifest = self.client.openstudio_manifest()
        self.assertEqual(20, manifest["site_count"])

    def test_scenario_and_zip_and_errors(self) -> None:
        result = self.client.evaluate({"density_screen_percentile": 0.75})
        self.assertEqual(20, len(result["selected"]))
        self.assertEqual("CBSA", self.client.zip_lookup("19104")["simulation_filter_geography"]["boundary_type"])
        from rle_client import RLEClientError

        with self.assertRaises(RLEClientError) as ctx:
            self.client.zip_lookup("00000")
        self.assertEqual(404, ctx.exception.status)

    def test_save_and_read_scenario_over_http(self) -> None:
        saved = self.client.save_scenario({"name": "Client saved scenario", "density_screen_percentile": 0.7})
        self.assertEqual(1, saved["version"])
        fetched = self.client.scenario(saved["id"])
        self.assertEqual(saved["id"], fetched["id"])
        self.assertEqual("Client saved scenario", fetched["name"])
        self.assertGreaterEqual(self.client.scenarios()["returned"], 1)

    def test_unknown_api_route_returns_json_404(self) -> None:
        # An unknown API path must return a JSON 404, not fall through to the SPA
        # index.html. Non-API deep links still serve the shell so client-side
        # routing keeps working on a hard refresh.
        host, port = self.server.server_address
        base = f"http://{host}:{port}"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"{base}/api/v1/does-not-exist", timeout=10)
        self.assertEqual(404, ctx.exception.code)
        payload = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("error", payload)
        with urllib.request.urlopen(f"{base}/scenario", timeout=10) as response:
            self.assertEqual(200, response.status)
            self.assertIn("text/html", response.headers.get("Content-Type", ""))


if __name__ == "__main__":
    unittest.main()
