"""ResStock enumeration verification (Phase 3, task 8; extended Session 3).

Replaces the old hard-coded ``nrel_value_verified = True`` in
``build_catchments`` with a real **membership check** of each selected
catchment's ResStock filter value against a public ResStock data dictionary.

ResStock (and ComStock — it shares the same spatial enumeration fields) downselect
each building-stock sample with a ``parameter=option`` pair. The two fields this
project emits are:

* ``in.county`` — value = county catchment code, and
* ``in.metropolitan_and_micropolitan_statistical_area`` — value = CBSA code.

A value is only safe to hand to a modeler if it is an *enumerated option* in the
ResStock data dictionary; otherwise the run still surfaces it, clearly marked
``REVIEW REQUIRED``.

Dual-source, matching the rest of the pipeline:

* ``--source api`` loads the **real** ResStock enumeration. Point
  ``RESSTOCK_ENUMERATION_FILE`` at any of the public NREL dictionary artifacts
  distributed with each ResStock/ComStock release on the Open Energy Data
  Initiative (OEDI) — this code parses them directly, so a hand-curated reformat
  is no longer required:

  - ``options_lookup.tsv`` (the resstock repo / release): ``Parameter Name`` +
    ``Option Name`` tab-separated columns. The parser accepts it, but current
    repository copies use human-readable geography labels and therefore do not
    verify this pipeline's numeric county/CBSA values;
  - ``enumeration_dictionary.tsv`` (per release on OEDI): one row per
    field/enumeration pair;
  - ``data_dictionary.tsv`` (per release on OEDI): a field column plus an
    enumerations column that may hold a delimited list of allowable options.

  The legacy simple ``nrel_filter_field,nrel_filter_value`` CSV and a
  ``{field: [values...]}`` JSON are still accepted. Anything not present in the
  loaded dictionary becomes ``REVIEW REQUIRED`` — the run never silently pretends
  a synthetic/unknown code is valid.
* ``--source fixture`` loads the bundled demonstration enumeration
  (``pipeline/data/resstock_enumerations.csv``), which lists the deterministic
  fixture and demo codes, so the offline suite stays green and
  ``verified_filter_count == 20``.

Free public source for the real dictionary (cite in downstream use): NREL ResStock
spatial enumerations / data + enumeration dictionaries, distributed with the
public ResStock datasets on the Open Energy Data Initiative (OEDI).
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import os
import re
from pathlib import Path
from typing import Any

from . import climate, config, provenance

# Bundled demonstration enumeration that ships with the repo.
DEMO_ENUMERATION_FILE = config.PIPELINE_ROOT / "data" / "resstock_enumerations.csv"

# The two spatial fields this project emits.
COUNTY_FIELD = "in.county"
CBSA_FIELD = "in.metropolitan_and_micropolitan_statistical_area"

VERIFIED_NOTE = (
    "ResStock filter field + value enumeration-verified against the {dictionary}; "
    "ready for ResStock/ComStock downselect."
)
REVIEW_NOTE = (
    "REVIEW REQUIRED: '{value}' is not an enumerated option for '{field}' in the "
    "{dictionary}. Curate the exact ResStock enumeration before simulation export."
)

# Header names (lower-cased) that identify the field/parameter and the value/option
# columns across the various real NREL dictionary layouts.
_FIELD_COLUMNS = (
    "nrel_filter_field",
    "parameter name",
    "parameter",
    "field_name",
    "field name",
    "field",
    "metadata_column",
    "name",
)
_VALUE_COLUMNS = (
    "nrel_filter_value",
    "option name",
    "option",
    "enumeration",
    "enumerations",
    "allowable_enumerations",
    "allowable enumerations",
    "options",
    "value",
    "field_value",
)
# Delimiters a single data_dictionary cell may use to pack a list of options.
_LIST_DELIMITERS = ("|", ";")


def _normalise(value: object) -> str:
    text = str(value).strip()
    return text.zfill(5) if text.isdigit() else text


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def _pick_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    lowered = {name.lower().strip(): name for name in fieldnames if name}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _split_options(cell: str, *, comma_delimited: bool = False) -> list[str]:
    """Split a possibly-delimited enumerations cell into individual options."""

    text = cell.strip()
    if not text:
        return []
    for delim in _LIST_DELIMITERS:
        if delim in text:
            return [part.strip() for part in text.split(delim) if part.strip()]
    if comma_delimited and "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    return [text]


def _load_csv(path: Path) -> dict[str, set[str]]:
    """Legacy bundled format: ``nrel_filter_field,nrel_filter_value`` rows."""

    enumerations: dict[str, set[str]] = {}
    for row in csv.DictReader(_read_text(path).splitlines()):
        field = str(row["nrel_filter_field"]).strip()
        enumerations.setdefault(field, set()).add(_normalise(row["nrel_filter_value"]))
    return enumerations


def _load_json(path: Path) -> dict[str, set[str]]:
    raw = json.loads(_read_text(path))
    return {str(field): {_normalise(v) for v in values} for field, values in raw.items()}


def _load_delimited_dictionary(path: Path, delimiter: str) -> dict[str, set[str]]:
    """Parse a real NREL dictionary artifact (TSV/CSV) into ``field -> {options}``.

    Auto-detects the field and value columns from the header so the same code
    reads ``options_lookup.tsv``, ``enumeration_dictionary.tsv``, and
    ``data_dictionary.tsv`` without a hand reformat. A value cell that packs a
    delimited list of allowable options (as ``data_dictionary.tsv`` sometimes
    does) is expanded into individual options.
    """

    with io.StringIO(_read_text(path), newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        fieldnames = reader.fieldnames or []
        # The simple bundled CSV is handled by _load_csv; only treat as "real"
        # when it is not that exact 2-column shape.
        field_col = _pick_column(fieldnames, _FIELD_COLUMNS)
        value_col = _pick_column(fieldnames, _VALUE_COLUMNS)
        if field_col is None or value_col is None:
            raise ValueError(
                f"Could not identify field/value columns in {path.name}; "
                f"headers were {fieldnames}. Expected one of {_FIELD_COLUMNS} and {_VALUE_COLUMNS}."
            )
        comma_delimited = value_col.lower().strip() in {
            "enumerations",
            "allowable_enumerations",
            "allowable enumerations",
            "options",
        }
        enumerations: dict[str, set[str]] = {}
        for row in reader:
            field = str(row.get(field_col, "")).strip()
            if not field:
                continue
            for option in _split_options(
                str(row.get(value_col, "")),
                comma_delimited=comma_delimited,
            ):
                enumerations.setdefault(field, set()).add(_normalise(option))
    return enumerations


def _is_legacy_simple_csv(path: Path) -> bool:
    with io.StringIO(_read_text(path), newline="") as handle:
        header = next(csv.reader(handle), [])
    lowered = {h.lower().strip() for h in header}
    return {"nrel_filter_field", "nrel_filter_value"}.issubset(lowered)


def load_real_dictionary(path: Path) -> dict[str, set[str]]:
    """Load enumerations from any supported real dictionary artifact."""

    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json(path)
    if suffix == ".tsv":
        return _load_delimited_dictionary(path, "\t")
    # .csv (or unknown): legacy 2-column form, else generic delimited parse.
    if _is_legacy_simple_csv(path):
        return _load_csv(path)
    return _load_delimited_dictionary(path, ",")


def load_enumerations(source: str) -> tuple[dict[str, set[str]], str]:
    """Return ``(enumerations, dictionary_label)`` for the given pipeline source.

    ``api`` requires a real dictionary via ``RESSTOCK_ENUMERATION_FILE``; if it is
    not set the function returns an empty mapping (so every value is honestly
    flagged ``REVIEW REQUIRED``). ``fixture`` always uses the bundled
    demonstration enumeration.
    """

    enums, label, _ = load_enumerations_detailed(source)
    return enums, label


def load_enumerations_detailed(source: str) -> tuple[dict[str, set[str]], str, dict[str, Any]]:
    """Like :func:`load_enumerations`, plus a provenance dict for the metadata.

    The provenance dict records the dictionary file, its SHA-256, the field count,
    and the per-field option counts so a reviewer can confirm exactly which
    dictionary backed each verification.
    """

    if source == "api":
        override = os.environ.get("RESSTOCK_ENUMERATION_FILE")
        if not override:
            prov = {
                "dictionary": "real ResStock data dictionary (NOT loaded)",
                "loaded": False,
                "note": "Set RESSTOCK_ENUMERATION_FILE to a public NREL dictionary artifact; every value is REVIEW REQUIRED until then.",
            }
            return {}, "real ResStock data dictionary (not loaded — set RESSTOCK_ENUMERATION_FILE)", prov
        path = Path(override)
        label = f"real ResStock data dictionary ({path.name})"
        enums = load_real_dictionary(path)
        prov: dict[str, Any] = {
            "dictionary": label,
            "loaded": True,
            "field_count": len(enums),
            "option_counts": {field: len(values) for field, values in sorted(enums.items())},
        }
        prov.update(provenance.file_record(path))
        return enums, label, prov

    # fixture / default
    enums = _load_csv(DEMO_ENUMERATION_FILE)
    prov = {
        "dictionary": "bundled demonstration enumeration",
        "loaded": True,
        "field_count": len(enums),
        "option_counts": {field: len(values) for field, values in sorted(enums.items())},
    }
    prov.update(provenance.file_record(DEMO_ENUMERATION_FILE))
    return enums, "bundled demonstration enumeration", prov


def verify(field: str, value: object, enumerations: dict[str, set[str]], dictionary: str) -> tuple[bool, str]:
    """Verify one ``field=value`` pair against the loaded enumeration.

    Returns ``(verified, note)``. ``verified`` is True only when the field is
    present in the dictionary and the value is one of its enumerated options.
    """

    code = _normalise(value)
    options = enumerations.get(field)
    if options is not None and code in options:
        return True, VERIFIED_NOTE.format(dictionary=dictionary)
    return False, REVIEW_NOTE.format(value=code, field=field, dictionary=dictionary)


def _normalise_geography_label(value: str) -> str:
    text = value.lower()
    text = re.sub(
        r"\b(metropolitan statistical area|micropolitan statistical area|metro area|micro area|msa|microsa)\b",
        "",
        text,
    )
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _county_name(catchment_label: str) -> str:
    parts = [part.strip() for part in catchment_label.split(";") if part.strip()]
    if len(parts) >= 2:
        return parts[-2]
    return catchment_label.split(",", 1)[0].strip()


def _resolve_county_label(code: str, catchment_label: str, options: set[str]) -> str | None:
    postal = climate.STATE_FIPS_TO_POSTAL.get(code[:2])
    if not postal:
        return None
    candidate = f"{postal}, {_county_name(catchment_label)}"
    if candidate in options:
        return candidate
    target = _normalise_geography_label(candidate)
    state_options = [option for option in options if option.startswith(f"{postal}, ")]
    ranked = sorted(
        (
            difflib.SequenceMatcher(None, target, _normalise_geography_label(option)).ratio(),
            option,
        )
        for option in state_options
    )
    return ranked[-1][1] if ranked and ranked[-1][0] >= 0.88 else None


def _state_signature(value: str) -> set[str]:
    suffix = value.rsplit(",", 1)[-1]
    return {token.lower() for token in re.findall(r"\b[A-Z]{2}\b", suffix)}


def _resolve_cbsa_label(catchment_label: str, options: set[str]) -> str | None:
    target = _normalise_geography_label(catchment_label)
    target_states = _state_signature(catchment_label)
    exact = [option for option in options if _normalise_geography_label(option) == target]
    if len(exact) == 1:
        return exact[0]

    candidates = [
        option
        for option in options
        if not target_states
        or target_states.issubset(_state_signature(option))
        or _state_signature(option).issubset(target_states)
    ]
    ranked = sorted(
        (
            difflib.SequenceMatcher(None, target, _normalise_geography_label(option)).ratio(),
            option,
        )
        for option in candidates
    )
    return ranked[-1][1] if ranked and ranked[-1][0] >= 0.62 else None


def resolve_filter_value(
    field: str,
    catchment_code: object,
    catchment_label: str,
    enumerations: dict[str, set[str]],
) -> str:
    """Resolve a catchment to the exact value expected by a ResStock field.

    Legacy/fixture dictionaries enumerate numeric geography codes, while current
    NREL releases enumerate human-readable county and CBSA labels. Return the
    exact enumerated value when resolvable; otherwise retain the code so normal
    verification emits an explicit REVIEW REQUIRED result.
    """

    code = _normalise(catchment_code)
    options = enumerations.get(field, set())
    if code in options:
        return code
    if field == COUNTY_FIELD:
        return _resolve_county_label(code, catchment_label, options) or code
    if field == CBSA_FIELD:
        return _resolve_cbsa_label(catchment_label, options) or code
    return code
