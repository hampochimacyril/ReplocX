#!/usr/bin/env python3
"""Validate read-only analytical inputs and refresh the application manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_DIR = APP_ROOT.parents[1] / "location_selection" / "data" / "processed"
REQUIRED = [
    "candidate_scores.csv",
    "selected_locations.csv",
    "resstock_site_list.csv",
    "top_alternatives.csv",
    "stratum_status.csv",
    "selection_metadata.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    if path.suffix != ".csv":
        return None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--output", type=Path, default=APP_ROOT / "data" / "analysis_manifest.json")
    args = parser.parse_args()
    missing = [name for name in REQUIRED if not (args.analysis_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing required analytical outputs: {', '.join(missing)}")
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "mode": "read-only analytical input references",
        "analysis_directory": str(args.analysis_dir.resolve()),
        "files": [
            {
                "name": name,
                "sha256": sha256(args.analysis_dir / name),
                "rows": row_count(args.analysis_dir / name),
            }
            for name in REQUIRED
        ],
    }
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest for {len(REQUIRED)} read-only analytical inputs to {args.output}")


if __name__ == "__main__":
    main()
