"""SQLite persistence for saved, shareable scenario configurations."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO_DB = APP_ROOT / "data" / "private" / "scenarios.sqlite3"
SCENARIO_DB_ENV = "RLE_SCENARIO_DB"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class ScenarioNotFound(LookupError):
    """Raised when a saved scenario id is not present in the SQLite store."""


class ScenarioStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(os.environ.get(SCENARIO_DB_ENV, DEFAULT_SCENARIO_DB))

    @classmethod
    def from_env(cls) -> ScenarioStore:
        return cls()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scenarios (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                version INTEGER NOT NULL,
                name TEXT NOT NULL,
                config_json TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_created_at ON scenarios(created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_parent_id ON scenarios(parent_id)")
        return connection

    def save(self, config: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        scenario_id = uuid.uuid4().hex[:12]
        parent_id = str(config.get("parent_id") or config.get("base_scenario_id") or "").strip() or None
        root_id = parent_id or scenario_id
        name = str(config.get("name") or "Saved scenario").strip() or "Saved scenario"
        created_at = _now()
        summary = result.get("summary", {})
        config_json = json.dumps(result.get("config", config), sort_keys=True)
        summary_json = json.dumps(summary, sort_keys=True)

        with closing(self._connect()) as connection:
            with connection:
                if parent_id:
                    row = connection.execute(
                        "SELECT MAX(version) AS max_version FROM scenarios WHERE id = ? OR parent_id = ?",
                        (parent_id, parent_id),
                    ).fetchone()
                    version = int(row["max_version"] or 1) + 1
                else:
                    version = 1
                connection.execute(
                    """
                    INSERT INTO scenarios (id, parent_id, version, name, config_json, summary_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (scenario_id, parent_id, version, name, config_json, summary_json, created_at),
                )

        return {
            "id": scenario_id,
            "parent_id": parent_id,
            "root_id": root_id,
            "version": version,
            "name": name,
            "created_at": created_at,
            "share_path": f"/api/v1/scenarios/{scenario_id}",
            "config": json.loads(config_json),
            "summary": json.loads(summary_json),
        }

    def list(self, limit: int = 50) -> dict[str, Any]:
        limit = min(max(int(limit), 1), 250)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT id, parent_id, version, name, summary_json, created_at
                FROM scenarios
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        scenarios = [
            {
                "id": row["id"],
                "parent_id": row["parent_id"],
                "version": row["version"],
                "name": row["name"],
                "created_at": row["created_at"],
                "share_path": f"/api/v1/scenarios/{row['id']}",
                "summary": json.loads(row["summary_json"]),
            }
            for row in rows
        ]
        return {"scenarios": scenarios, "returned": len(scenarios), "limit": limit}

    def get(self, scenario_id: str) -> dict[str, Any]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT id, parent_id, version, name, config_json, summary_json, created_at
                FROM scenarios
                WHERE id = ?
                """,
                (scenario_id,),
            ).fetchone()
        if row is None:
            raise ScenarioNotFound(f"Scenario {scenario_id!r} was not found.")
        return {
            "id": row["id"],
            "parent_id": row["parent_id"],
            "version": row["version"],
            "name": row["name"],
            "created_at": row["created_at"],
            "share_path": f"/api/v1/scenarios/{row['id']}",
            "config": json.loads(row["config_json"]),
            "summary": json.loads(row["summary_json"]),
        }
