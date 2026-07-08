from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
SECRET_SCAN_EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tools",
    ".venv",
    "blob-report",
    "dist",
    "htmlcov",
    "node_modules",
    "playwright-report",
    "test-results",
}


class ProjectContractTests(unittest.TestCase):
    def test_required_product_contexts_are_present(self) -> None:
        # The redesigned React frontend (Session 6) exposes the same product
        # capabilities through the new map-first information architecture. Assert
        # the five primary contexts and the key analytical surfaces exist in the
        # source rather than string-matching the retired vanilla app.js.
        src = APP_ROOT / "frontend" / "src"
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(src.rglob("*.ts")) if path.is_file()
        ) + "\n".join(path.read_text(encoding="utf-8") for path in sorted(src.rglob("*.tsx")) if path.is_file())
        for label in [
            "Map workspace",
            "Catchments",
            "Compare",
            "Scenario",
            "Methodology & data",
        ]:
            self.assertIn(label, combined, f"Missing primary context: {label}")
        for surface in ["CoverageMatrix", "MapCanvas", "FilterPanel", "DetailsDrawer", "ZIP / ZCTA"]:
            self.assertIn(surface, combined, f"Missing analytical surface: {surface}")

    def test_private_pr_screenshots_exist(self) -> None:
        for name in ["overview.png", "zip-explorer.png", "scenario-builder.png"]:
            path = APP_ROOT / "docs" / "screenshots" / name
            self.assertTrue(path.exists(), f"Missing screenshot: {name}")
            self.assertGreater(path.stat().st_size, 10_000)
            self.assertLess(path.stat().st_size, 1_000_000)

    def test_documentation_set_is_complete(self) -> None:
        for path in [
            "README.md",
            "docs/methodology.md",
            "docs/data_sources.md",
            "docs/privacy_and_repository_rules.md",
            "docs/deployment_options.md",
            "docs/user_guide.md",
            "docs/completion_checklist.md",
        ]:
            self.assertTrue((APP_ROOT / path).exists(), path)

    def test_no_obvious_credentials_are_committed(self) -> None:
        secret_pattern = re.compile(
            r"(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"
        )
        text_suffixes = {".c", ".css", ".csv", ".html", ".js", ".json", ".md", ".py", ".ts", ".tsx", ".txt", ".yml"}
        for dirpath, dirnames, filenames in os.walk(APP_ROOT):
            # Prune excluded directories in place so large generated runtime trees
            # (node_modules, .venv, .tools, .git, tool caches) are never traversed.
            dirnames[:] = [name for name in dirnames if name not in SECRET_SCAN_EXCLUDED_DIRS]
            for filename in filenames:
                path = Path(dirpath) / filename
                if path.suffix not in text_suffixes:
                    continue
                content = path.read_text(encoding="utf-8")
                self.assertIsNone(
                    secret_pattern.search(content),
                    f"Potential credential in {path.relative_to(APP_ROOT)}",
                )


if __name__ == "__main__":
    unittest.main()
