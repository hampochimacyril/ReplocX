from __future__ import annotations

import re
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]


class ProjectContractTests(unittest.TestCase):
    def test_required_product_pages_are_present(self) -> None:
        app_js = (APP_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
        for label in [
            "Overview dashboard",
            "ZIP code explorer",
            "Scenario builder",
            "Candidate ranking",
            "Allocation comparison",
            "Methodology & sources",
        ]:
            self.assertIn(label, app_js)

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
        for path in APP_ROOT.rglob("*"):
            if ".git" in path.parts or path.is_dir() or path.suffix not in text_suffixes:
                continue
            content = path.read_text(encoding="utf-8")
            self.assertIsNone(secret_pattern.search(content), f"Potential credential in {path.relative_to(APP_ROOT)}")


if __name__ == "__main__":
    unittest.main()

