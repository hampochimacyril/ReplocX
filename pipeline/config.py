"""Shared constants and paths for the national data pipeline.

These mirror the invariants the application and its regression tests depend on
(see ``backend/scoring.py`` and ``backend/models.py``): five climate regions,
four urbanicity classes, the 20 strata they form, and the baseline score
weights. Keep them in sync with the backend if either side changes.
"""

from __future__ import annotations

from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parent
APP_ROOT = PIPELINE_ROOT.parent

# Pipeline working tree. ``out`` is what the app reads via RLE_ANALYSIS_DATA_DIR.
WORK_DIR = PIPELINE_ROOT / "work"
CACHE_DIR = PIPELINE_ROOT / "cache"
OUT_DIR = PIPELINE_ROOT / "out"

RAW_CATCHMENTS = WORK_DIR / "catchments_raw.csv"
CLASSIFIED_CATCHMENTS = WORK_DIR / "catchments_classified.csv"

# --- Tract-level pilot (Session 2) -----------------------------------------
# The pilot is a genuinely tract-derived run over a small set of states. It is
# deliberately kept separate from the national ``OUT_DIR`` because its outputs
# are *partial* (only the strata the pilot states reach) and must never be
# mistaken for a complete national result. Raw downloads cache under
# ``PILOT_CACHE_DIR`` (gitignored); recorded offline fixtures live in
# ``PILOT_DATA_DIR`` (committed).
PILOT_DATA_DIR = PIPELINE_ROOT / "data" / "pilot"
PILOT_CACHE_DIR = CACHE_DIR / "pilot"
PILOT_OUT_DIR = PIPELINE_ROOT / "pilot_out"

# --- Invariants shared with backend/scoring.py -----------------------------
CLIMATE_ORDER = [
    "Cold & Very Cold",
    "Hot-Dry & Mixed Dry",
    "Hot-Humid",
    "Marine",
    "Mixed-Humid",
]

# (long label, short label) preserving the order backend/scoring.py expects.
URBANICITY = [
    ("higher density urban", "HDU"),
    ("lower density urban", "LDU"),
    ("suburban/small town", "Suburban"),
    ("rural", "Rural"),
]
URBANICITY_ORDER = [long for long, _ in URBANICITY]
URBANICITY_SHORT = {long: short for long, short in URBANICITY}

STRATA = [(climate, urb) for climate in CLIMATE_ORDER for urb in URBANICITY_ORDER]

# Baseline composite-score weights (must match backend/models DEFAULT_WEIGHTS
# and sum to 1.0). The pipeline writes the percentile inputs; the backend
# recomputes the score from them at request time.
SCORE_WEIGHTS = {
    "housing_unit_coverage_percentile": 0.45,
    "population_density_percentile": 0.35,
    "population_coverage_percentile": 0.20,
}

# --- Urbanicity classification thresholds ----------------------------------
# Population density (people / sq mi) cut points. Rural catchments are filtered
# by county; all denser classes are filtered within their CBSA (this is the
# County-vs-CBSA rule the ResStock export and tests assert).
URBANICITY_DENSITY_BREAKS = [
    (3000.0, "higher density urban"),
    (1000.0, "lower density urban"),
    (200.0, "suburban/small town"),
    (0.0, "rural"),
]


def catchment_type_for(urbanicity: str) -> str:
    """Rural -> County catchment; everything else -> CBSA catchment."""

    return "County" if urbanicity == "rural" else "CBSA"


def urbanicity_for_density(density_sqmi: float) -> str:
    for threshold, label in URBANICITY_DENSITY_BREAKS:
        if density_sqmi >= threshold:
            return label
    return "rural"
