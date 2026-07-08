"""Phase 4 regression tests: productionization hooks."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from backend.api import API_BASE, normalize_api_path, openapi_schema
from backend.auth import AuthError, require_api_auth
from backend.data_service import DEMO_ANALYSIS_DIR, DataService
from backend.scenario_store import ScenarioStore

# fastapi is an optional dependency: the stdlib backend.server path (and the
# zero-dependency CI "backend" job) run the whole suite without it. Only guard
# the FastAPI-specific routing test behind its presence so module collection
# never fails when fastapi is absent; the quality/e2e/docker jobs install it.
_HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None


class ApiVersioningTests(unittest.TestCase):
    def test_versioned_paths_normalize_to_internal_legacy_routes(self) -> None:
        self.assertEqual("/api/health", normalize_api_path(f"{API_BASE}/health"))
        self.assertEqual("/api/geometry", normalize_api_path(f"{API_BASE}/geometry"))
        self.assertEqual("/api/scenarios", normalize_api_path(f"{API_BASE}/scenarios"))
        self.assertEqual("/api/health", normalize_api_path("/api/health"))

    def test_openapi_documents_phase4_routes(self) -> None:
        schema = openapi_schema()
        self.assertEqual(API_BASE, schema["servers"][0]["url"])
        self.assertIn("/scenarios", schema["paths"])
        self.assertIn("/geometry", schema["paths"])
        parameters = schema["paths"]["/candidates"]["get"]["parameters"]
        self.assertIn("offset", {item["name"] for item in parameters})


class AuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_token = os.environ.get("RLE_PRIVATE_AUTH_TOKEN")
        self._old_required = os.environ.get("RLE_REQUIRE_AUTH")
        os.environ["RLE_PRIVATE_AUTH_TOKEN"] = "test-token"
        os.environ.pop("RLE_REQUIRE_AUTH", None)

    def tearDown(self) -> None:
        if self._old_token is None:
            os.environ.pop("RLE_PRIVATE_AUTH_TOKEN", None)
        else:
            os.environ["RLE_PRIVATE_AUTH_TOKEN"] = self._old_token
        if self._old_required is None:
            os.environ.pop("RLE_REQUIRE_AUTH", None)
        else:
            os.environ["RLE_REQUIRE_AUTH"] = self._old_required

    def test_health_and_openapi_stay_public(self) -> None:
        require_api_auth("/api/health", {})
        require_api_auth("/api/openapi.json", {})

    def test_private_api_requires_bearer_token(self) -> None:
        with self.assertRaises(AuthError):
            require_api_auth("/api/dashboard", {})
        require_api_auth("/api/dashboard", {"Authorization": "Bearer test-token"})
        require_api_auth("/api/dashboard", {"X-RLE-Auth": "test-token"})


@unittest.skipUnless(_HAS_FASTAPI, "fastapi is not installed in this environment")
class FastApiRoutingTests(unittest.TestCase):
    def test_unknown_api_route_returns_json_404_not_spa_shell(self) -> None:
        from fastapi.responses import FileResponse, JSONResponse

        from backend.fastapi_app import static_app

        response = static_app("api/v1/does-not-exist")
        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(404, response.status_code)
        self.assertIn("application/json", response.media_type)
        self.assertIn("error", json.loads(response.body))

        deep_link = static_app("scenario")
        self.assertIsInstance(deep_link, FileResponse)


class ScenarioPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = DataService(analysis_dir=DEMO_ANALYSIS_DIR)

    def test_sqlite_store_saves_lists_and_versions_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ScenarioStore(Path(directory) / "scenarios.sqlite3")
            result = self.service.evaluate({"name": "Phase 4 smoke"})
            saved = store.save(result["config"], result)
            self.assertEqual(1, saved["version"])
            self.assertEqual("Phase 4 smoke", saved["name"])

            fetched = store.get(saved["id"])
            self.assertEqual(saved["id"], fetched["id"])
            self.assertEqual(saved["config"], fetched["config"])

            revision_result = self.service.evaluate(
                {
                    "name": "Phase 4 smoke",
                    "parent_id": saved["id"],
                    "density_screen_percentile": 0.7,
                }
            )
            revision_config = dict(revision_result["config"])
            revision_config["parent_id"] = saved["id"]
            revision = store.save(revision_config, revision_result)
            self.assertEqual(2, revision["version"])
            self.assertEqual(saved["id"], revision["parent_id"])

            listing = store.list()
            self.assertEqual(2, listing["returned"])

    def test_candidate_pagination_metadata(self) -> None:
        first = self.service.candidates_page({"limit": "12", "offset": "0"})
        page = self.service.candidates_page({"limit": "5", "offset": "7"})
        self.assertEqual(5, page["returned"])
        self.assertEqual(7, page["offset"])
        self.assertTrue(page["has_more"])
        self.assertEqual(12, page["next_offset"])
        self.assertEqual(first["rows"][7]["location_uniqueness_key"], page["rows"][0]["location_uniqueness_key"])

    def test_candidate_search_includes_station_number(self) -> None:
        station = str(self.service.candidates[0]["selected_station_number"])
        page = self.service.candidates_page({"search": station, "limit": "10"})
        self.assertGreater(page["returned"], 0)
        self.assertTrue(any(str(row["selected_station_number"]) == station for row in page["rows"]))


if __name__ == "__main__":
    unittest.main()
