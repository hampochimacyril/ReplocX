"""Climate-region classification from county FIPS.

Maps each U.S. county to one of the project's five climate regions, derived from
the DOE Building America / IECC climate-zone framework. The backbone is a
state-level assignment (usable nationally out of the box); ``COUNTY_OVERRIDES``
refine states that span more than one Building America region.

This is an approximate, transparent classifier intended to be tightened over
time (Phase 2 can swap in a full county-level IECC table from PNNL/NREL). It is
deterministic and offline: no network required.
"""

from __future__ import annotations

# Postal code -> climate region. Choices follow the dominant Building America
# zone for each state's population. Split states are refined below.
STATE_CLIMATE = {
    # Cold & Very Cold (northern tier + interior mountain/high-plains)
    "AK": "Cold & Very Cold",
    "CT": "Cold & Very Cold",
    "CO": "Cold & Very Cold",
    "IA": "Cold & Very Cold",
    "ID": "Cold & Very Cold",
    "IL": "Cold & Very Cold",
    "IN": "Cold & Very Cold",
    "MA": "Cold & Very Cold",
    "ME": "Cold & Very Cold",
    "MI": "Cold & Very Cold",
    "MN": "Cold & Very Cold",
    "MT": "Cold & Very Cold",
    "ND": "Cold & Very Cold",
    "NE": "Cold & Very Cold",
    "NH": "Cold & Very Cold",
    "NY": "Cold & Very Cold",
    "OH": "Cold & Very Cold",
    "RI": "Cold & Very Cold",
    "SD": "Cold & Very Cold",
    "UT": "Cold & Very Cold",
    "VT": "Cold & Very Cold",
    "WI": "Cold & Very Cold",
    "WY": "Cold & Very Cold",
    # Hot-Dry & Mixed Dry (desert southwest + most of California)
    "AZ": "Hot-Dry & Mixed Dry",
    "CA": "Hot-Dry & Mixed Dry",
    "NM": "Hot-Dry & Mixed Dry",
    "NV": "Hot-Dry & Mixed Dry",
    # Hot-Humid (gulf + deep south + south Atlantic + tropical)
    "AL": "Hot-Humid",
    "FL": "Hot-Humid",
    "GA": "Hot-Humid",
    "HI": "Hot-Humid",
    "LA": "Hot-Humid",
    "MS": "Hot-Humid",
    "SC": "Hot-Humid",
    "TX": "Hot-Humid",
    # Marine (Pacific Northwest west of the Cascades dominates state pop centers)
    "OR": "Marine",
    "WA": "Marine",
    # Mixed-Humid (mid-Atlantic, upper south, lower midwest)
    "AR": "Mixed-Humid",
    "DC": "Mixed-Humid",
    "DE": "Mixed-Humid",
    "KS": "Mixed-Humid",
    "KY": "Mixed-Humid",
    "MD": "Mixed-Humid",
    "MO": "Mixed-Humid",
    "NC": "Mixed-Humid",
    "NJ": "Mixed-Humid",
    "OK": "Mixed-Humid",
    "PA": "Mixed-Humid",
    "TN": "Mixed-Humid",
    "VA": "Mixed-Humid",
    "WV": "Mixed-Humid",
}

# Numeric state FIPS -> postal code (used when only the GEOID is available).
STATE_FIPS_TO_POSTAL = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
}

# County GEOID (state+county, 5 digits) -> climate region. Refines split states.
# A representative, non-exhaustive set; extend as the classifier is hardened.
COUNTY_OVERRIDES = {
    # Coastal/NW California is Marine even though the state defaults Hot-Dry.
    "06075": "Marine",  # San Francisco
    "06081": "Marine",  # San Mateo
    "06001": "Marine",  # Alameda
    "06013": "Marine",  # Contra Costa
    # Texas hill country / west Texas trends Hot-Dry & Mixed Dry.
    "48141": "Hot-Dry & Mixed Dry",  # El Paso
    # Upstate South Carolina / north Georgia uplands are Mixed-Humid.
    "45045": "Mixed-Humid",  # Greenville, SC
    "13089": "Mixed-Humid",  # DeKalb, GA (Atlanta)
    "13121": "Mixed-Humid",  # Fulton, GA (Atlanta)
    # Southern Florida is the project's clearest Hot-Humid anchor (kept explicit).
    "12086": "Hot-Humid",  # Miami-Dade
}


def climate_for_county(county_geoid: str) -> str:
    """Return the climate region for a 5-digit county GEOID.

    Precedence: explicit county override -> state-level default. Raises if the
    state FIPS is unrecognized so a bad GEOID fails loudly rather than silently
    landing in the wrong stratum.
    """

    geoid = str(county_geoid).strip().zfill(5)
    if geoid in COUNTY_OVERRIDES:
        return COUNTY_OVERRIDES[geoid]
    postal = STATE_FIPS_TO_POSTAL.get(geoid[:2])
    if postal is None:
        raise ValueError(f"Unrecognized state FIPS in county GEOID: {county_geoid!r}")
    return STATE_CLIMATE[postal]
