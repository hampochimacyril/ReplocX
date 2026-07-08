"""W0 contract tests for the four-scenario Research Atlas migration."""

from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "atlas" / "schemas" / "w0_contract_bundle.schema.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "atlas" / "w0" / "w0_contract_bundle.golden.json"
EXPECTED_ORDER = ["A", "C", "B", "D"]


class SchemaValidationError(AssertionError):
    """Raised when the small W0 schema validator rejects a fixture."""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaValidationError(f"unsupported external ref: {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        node = node[part]
    if not isinstance(node, dict):
        raise SchemaValidationError(f"ref does not resolve to a schema object: {ref}")
    return node


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaValidationError(f"unsupported schema type: {expected}")


def validate_schema(value: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> None:
    """Validate the JSON Schema subset used by the W0 contract artifact."""

    if "$ref" in schema:
        validate_schema(value, _resolve_ref(root, str(schema["$ref"])), root, path)
        return

    for sub_schema in schema.get("allOf", []):
        validate_schema(value, sub_schema, root, path)

    if "not" in schema:
        try:
            validate_schema(value, schema["not"], root, path)
        except SchemaValidationError:
            pass
        else:
            raise SchemaValidationError(f"{path}: matched forbidden schema")

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}: expected const {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        if not any(_type_matches(value, t) for t in expected_type):
            raise SchemaValidationError(f"{path}: expected type {expected_type!r}, got {type(value).__name__}")
    elif isinstance(expected_type, str) and not _type_matches(value, expected_type):
        raise SchemaValidationError(f"{path}: expected type {expected_type!r}, got {type(value).__name__}")

    if "minimum" in schema and isinstance(value, (int, float)) and value < schema["minimum"]:
        raise SchemaValidationError(f"{path}: expected minimum {schema['minimum']!r}, got {value!r}")

    if "pattern" in schema and isinstance(value, str) and re.search(str(schema["pattern"]), value) is None:
        raise SchemaValidationError(f"{path}: expected pattern {schema['pattern']!r}, got {value!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise SchemaValidationError(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        for key, sub_schema in properties.items():
            if key in value:
                validate_schema(value[key], sub_schema, root, f"{path}.{key}")

        additional = schema.get("additionalProperties", True)
        if additional is False:
            extras = set(value) - set(properties)
            if extras:
                raise SchemaValidationError(f"{path}: unexpected properties {sorted(extras)!r}")
        elif isinstance(additional, dict):
            for key in set(value) - set(properties):
                validate_schema(value[key], additional, root, f"{path}.{key}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            raise SchemaValidationError(f"{path}: expected minItems {min_items}, got {len(value)}")

        max_items = schema.get("maxItems")
        if isinstance(max_items, int) and len(value) > max_items:
            raise SchemaValidationError(f"{path}: expected maxItems {max_items}, got {len(value)}")

        prefix_items = schema.get("prefixItems", [])
        for index, sub_schema in enumerate(prefix_items):
            if index >= len(value):
                raise SchemaValidationError(f"{path}: missing prefix item at index {index}")
            validate_schema(value[index], sub_schema, root, f"{path}[{index}]")

        items = schema.get("items", True)
        if items is False and len(value) > len(prefix_items):
            raise SchemaValidationError(f"{path}: unexpected items after index {len(prefix_items) - 1}")
        if isinstance(items, dict):
            for index, item in enumerate(value[len(prefix_items) :], start=len(prefix_items)):
                validate_schema(item, items, root, f"{path}[{index}]")


def validate_fixture(fixture: dict[str, Any]) -> None:
    schema = _load_json(SCHEMA_PATH)
    validate_schema(fixture, schema, schema)


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_walk_strings(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(_walk_strings(item))
        return out
    return []


class AtlasW0ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _load_json(FIXTURE_PATH)

    def test_golden_contract_fixture_matches_schema(self) -> None:
        validate_fixture(self.fixture)
        self.assertEqual(EXPECTED_ORDER, self.fixture["scenario_dictionary"]["scenario_order"])

    def test_results_fixture_missing_d_fails_schema_validation(self) -> None:
        broken = copy.deepcopy(self.fixture)
        for tier in broken["scenario_summary"]["tiers"]:
            tier["rows"] = [row for row in tier["rows"] if row["hvac_scenario"] != "D"]
        with self.assertRaisesRegex(SchemaValidationError, r"scenario_summary.*rows.*minItems"):
            validate_fixture(broken)

    def test_results_fixture_with_only_abc_fails_schema_validation(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["scenario_dictionary"]["scenario_order"] = ["A", "B", "C"]
        broken["scenario_dictionary"]["scenarios"] = broken["scenario_dictionary"]["scenarios"][:3]
        with self.assertRaisesRegex(SchemaValidationError, r"scenario_order.*expected (const|minItems)"):
            validate_fixture(broken)

    def test_figure_registry_fixture_pointing_to_superseded_folder_fails(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["figures"]["figures"][0]["source_csv"] = broken["figures"]["figures"][0]["source_csv"].replace(
            "f2v3_final", "f2v2_final"
        )
        with self.assertRaisesRegex(SchemaValidationError, r"forbidden schema"):
            validate_fixture(broken)

    def test_scenario_dictionary_out_of_order_fails_schema_validation(self) -> None:
        broken = copy.deepcopy(self.fixture)
        broken["scenario_dictionary"]["scenario_order"] = ["A", "B", "C", "D"]
        broken["scenario_dictionary"]["scenarios"][1], broken["scenario_dictionary"]["scenarios"][2] = (
            broken["scenario_dictionary"]["scenarios"][2],
            broken["scenario_dictionary"]["scenarios"][1],
        )
        with self.assertRaisesRegex(SchemaValidationError, r"scenario_order.*expected const 'C'"):
            validate_fixture(broken)

    def test_contract_fixture_uses_only_current_figure_paths(self) -> None:
        strings = _walk_strings(self.fixture)
        self.assertTrue(any("f2v3_final" in s for s in strings))
        self.assertFalse(any("f2v2_final" in s for s in strings))
        self.assertFalse(any("f1v2" in s.lower() for s in strings))

    def test_primary_endpoint_families_are_frozen(self) -> None:
        families = self.fixture["provenance"]["endpoint_definitions"]["primary_endpoint_families"]
        self.assertEqual(
            [
                "op_temp_mean_c",
                "op_temp_p95_true_c",
                "humidity_ratio_mean_kgkg",
                "humidity_ratio_p95_true_kgkg",
            ],
            families,
        )


if __name__ == "__main__":
    unittest.main()
