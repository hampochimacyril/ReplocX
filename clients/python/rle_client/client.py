"""Stdlib-only client for the ReplocX REST API.

Deliberately depends on nothing outside the Python standard library so it can be
dropped into a URBANopt, GeoPandas, or ResStock pipeline without dragging in a
transitive dependency tree. GeoPandas is only imported (lazily) if you call
:meth:`RLEClient.to_geodataframe`.

Example
-------
>>> from rle_client import ReplocXClient
>>> rle = ReplocXClient("http://127.0.0.1:8787")
>>> rle.health()["status"]
'ok'
>>> sites = rle.selected_locations()          # baseline 20-site selection
>>> manifest = rle.openstudio_manifest()      # OpenStudio/EnergyPlus manifest
>>> gdf = rle.to_geodataframe()               # needs geopandas installed
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

__all__ = ["RLEClient", "RLEClientError"]


class RLEClientError(RuntimeError):
    """Raised when the API returns a non-2xx response or is unreachable."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class RLEClient:
    """Thin wrapper over the explorer's REST API.

    Parameters
    ----------
    base_url:
        Root URL of a running explorer, e.g. ``http://127.0.0.1:8787``.
    timeout:
        Per-request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8787",
        timeout: float = 30.0,
        api_base: str = "/api/v1",
        auth_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_base = "/" + api_base.strip("/")
        self.auth_token = auth_token

    # -- low-level request helpers -------------------------------------------------
    def _request(
        self, method: str, path: str, *, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None
    ) -> tuple[bytes, str]:
        url = self.base_url + self.api_base + path
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        data = None
        headers = {"Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:  # 4xx / 5xx
            detail = exc.read().decode("utf-8", "replace")
            exc.close()
            try:
                detail = json.loads(detail).get("error", detail)
            except json.JSONDecodeError:
                pass
            raise RLEClientError(f"{exc.code} {exc.reason}: {detail}", status=exc.code) from exc
        except urllib.error.URLError as exc:
            raise RLEClientError(f"Could not reach {url}: {exc.reason}") from exc

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        payload, _ = self._request("GET", path, params=params)
        return json.loads(payload)

    def _post_json(self, path: str, body: dict[str, Any] | None) -> Any:
        payload, _ = self._request("POST", path, body=body or {})
        return json.loads(payload)

    def _post_text(self, path: str, body: dict[str, Any] | None) -> str:
        payload, _ = self._request("POST", path, body=body or {})
        return payload.decode("utf-8")

    # -- read endpoints ------------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self._get_json("/health")

    def dashboard(self) -> dict[str, Any]:
        return self._get_json("/dashboard")

    def provenance(self) -> dict[str, Any]:
        return self._get_json("/provenance")

    def geometry(self) -> dict[str, Any]:
        """Selected-catchment polygons as a GeoJSON FeatureCollection."""
        return self._get_json("/geometry")

    def candidates(
        self,
        search: str = "",
        climate: str = "",
        urbanicity: str = "",
        selected_only: bool = False,
        limit: int = 250,
        offset: int = 0,
    ) -> dict[str, Any]:
        return self._get_json(
            "/candidates",
            {
                "search": search,
                "climate": climate,
                "urbanicity": urbanicity,
                "selected_only": str(selected_only).lower(),
                "limit": limit,
                "offset": offset,
            },
        )

    def zip_lookup(self, zip_code: str) -> dict[str, Any]:
        return self._get_json(f"/zip/{urllib.parse.quote(zip_code)}")

    # -- scenario + selection ------------------------------------------------------
    def evaluate(self, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate a scenario (``None`` / ``{}`` = baseline) and return the full result."""
        return self._post_json("/scenarios/evaluate", scenario)

    def save_scenario(self, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate and persist a scenario in the server-side SQLite store."""
        return self._post_json("/scenarios", scenario)

    def scenarios(self, limit: int = 50) -> dict[str, Any]:
        return self._get_json("/scenarios", {"limit": limit})

    def scenario(self, scenario_id: str) -> dict[str, Any]:
        return self._get_json(f"/scenarios/{urllib.parse.quote(scenario_id)}")

    def selected_locations(self, scenario: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Convenience: just the selected sites for a scenario (baseline by default)."""
        return self.evaluate(scenario)["selected"]

    # -- export adapters (Phase 3) -------------------------------------------------
    def site_list_csv(self, scenario: dict[str, Any] | None = None) -> str:
        return self._post_text("/exports/site-list.csv", scenario)

    def resstock_sampling_csv(self, scenario: dict[str, Any] | None = None) -> str:
        """ResStock/ComStock downselect input as CSV text."""
        return self._post_text("/exports/resstock-sampling.csv", scenario)

    def openstudio_manifest(self, scenario: dict[str, Any] | None = None) -> dict[str, Any]:
        """OpenStudio/EnergyPlus-ready manifest of selected sites."""
        return self._post_json("/exports/openstudio-manifest.json", scenario)

    # -- optional GeoPandas helper -------------------------------------------------
    def to_geodataframe(self):  # type: ignore[no-untyped-def]
        """Return the selected-catchment polygons as a GeoDataFrame.

        Lazily imports GeoPandas; install it (``pip install geopandas``) only if
        you need this. Everything else works with the standard library alone.
        """
        try:
            import geopandas  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RLEClientError(
                "to_geodataframe() requires geopandas. Install it with 'pip install geopandas', "
                "or use geometry() to get the raw GeoJSON."
            ) from exc
        return geopandas.GeoDataFrame.from_features(self.geometry()["features"], crs="EPSG:4326")
