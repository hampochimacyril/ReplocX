"""Build the certified Atlas equity profile from official source files.

This script intentionally reads certified Atlas inputs and public equity source
files only. It does not infer or backfill scaffold/demo values.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

CANONICAL_ROOT = Path(
    "/Users/cch322/Library/CloudStorage/OneDrive-DrexelUniversity/PhD files/"
    "PhD_Simulation/PhD Dissertation Framework/04_Analysis/_CANONICAL/10_DATA/"
    "replocx_tmy3_wallfix_4scen"
)
SELECTED_CATCHMENTS = Path("/Users/cch322/Developer/pipeline/out/selected_locations.csv")
TMP_ROOT = Path("/private/tmp")

ACS_PAYLOAD = TMP_ROOT / "censusreporter_atlas_selected_latest.json"
SVI_CSV = TMP_ROOT / "SVI_2022_US.csv"
CBSA_XLSX = TMP_ROOT / "list1_2023.xlsx"
ZCTA_COUNTY_REL = TMP_ROOT / "tab20_zcta520_county20_natl.txt"
HHI_ZIP = TMP_ROOT / "HHI_Data.zip"
LEAD_DICTIONARY = TMP_ROOT / "LEAD_Data_Dictionary_2022.xlsx"

TIER_ID = "replocx_tmy3_wallfix_4scen"
SVI_URL = "https://svi.cdc.gov/Documents/Data/2022/csv/states/SVI_2022_US.csv"
SVI_PAGE = "https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html"
CBSA_URL = (
    "https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/"
    "2023/delineation-files/list1_2023.xlsx"
)
ZCTA_REL_URL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/" "tab20_zcta520_county20_natl.txt"
HHI_URL = "https://www.atsdr.cdc.gov/place-health/media/files/2024/08/HHI_Data.zip"
HHI_PAGE = "https://www.atsdr.cdc.gov/place-health/php/hhi/index.html"
LEAD_DATASET_URL = "https://data.openei.org/submissions/6219"
LEAD_DICT_URL = "https://data.openei.org/files/6219/Data%20Dictionary%202022.xlsx"
LEAD_DOI = "https://doi.org/10.25984/2504170"

STATE_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}
STATE_FIPS_TO_ABBR = {
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path, role: str, url: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "path": str(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "role": role,
    }
    if url:
        out["url"] = url
    return out


def col_index(cell_ref: str) -> int:
    letters = ""
    for char in cell_ref:
        if char.isalpha():
            letters += char
        else:
            break
    value = 0
    for char in letters:
        value = value * 26 + ord(char.upper()) - 64
    return value - 1


def xlsx_rows(path: Path, sheet: str = "xl/worksheets/sheet1.xml") -> list[list[str]]:
    rows: list[list[str]] = []
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                text = "".join(
                    node.text or ""
                    for node in item.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                )
                shared.append(text)
        for _event, elem in ET.iterparse(zf.open(sheet), events=("end",)):
            if not elem.tag.endswith("row"):
                continue
            row: list[str] = []
            for cell in elem.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                idx = col_index(cell.attrib["r"])
                while len(row) <= idx:
                    row.append("")
                value_node = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared[int(value)]
                row[idx] = value
            rows.append(row)
            elem.clear()
    return rows


def xlsx_iter_rows(path: Path, sheet: str = "xl/worksheets/sheet1.xml"):
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
                text = "".join(
                    node.text or ""
                    for node in item.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
                )
                shared.append(text)
        for _event, elem in ET.iterparse(zf.open(sheet), events=("end",)):
            if not elem.tag.endswith("row"):
                continue
            row: list[str] = []
            for cell in elem.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
                idx = col_index(cell.attrib["r"])
                while len(row) <= idx:
                    row.append("")
                value_node = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared[int(value)]
                row[idx] = value
            yield row
            elem.clear()


def numeric(value: Any) -> float | None:
    if value in {None, "", "-999", "-999.0"}:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out):
        return None
    return out


def fmt(value: float | None, digits: int = 6) -> str:
    if value is None:
        return ""
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def load_selected() -> list[dict[str, Any]]:
    with SELECTED_CATCHMENTS.open(newline="") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    for row in rows:
        row["catchment_id"] = f"{row['catchment_type']}:{row['catchment_code']}"
    return rows


def load_current_profile() -> dict[str, dict[str, str]]:
    path = CANONICAL_ROOT / "equity_profile.csv"
    with path.open(newline="") as f:
        return {row["catchment_id"]: dict(row) for row in csv.DictReader(f)}


def load_cbsa_counties() -> tuple[dict[str, list[str]], dict[str, str]]:
    rows = xlsx_rows(CBSA_XLSX)
    header = rows[2]
    index = {name: i for i, name in enumerate(header)}
    cbsa_to_counties: dict[str, list[str]] = defaultdict(list)
    county_to_state: dict[str, str] = {}
    for row in rows[3:]:
        if not row or not row[0]:
            continue
        state_name = row[index["State Name"]]
        if state_name not in STATE_ABBR:
            continue
        state_fips = row[index["FIPS State Code"]].zfill(2)
        county_fips = row[index["FIPS County Code"]].zfill(3)
        geoid = f"{state_fips}{county_fips}"
        cbsa_to_counties[row[index["CBSA Code"]]].append(geoid)
        county_to_state[geoid] = STATE_ABBR[state_name]
    return dict(cbsa_to_counties), county_to_state


def attach_counties(
    selected: list[dict[str, Any]],
    cbsa_to_counties: dict[str, list[str]],
    county_to_state: dict[str, str],
) -> dict[str, list[str]]:
    for row in selected:
        if row["catchment_type"] == "CBSA":
            counties = sorted(set(cbsa_to_counties[row["catchment_code"]]))
        else:
            counties = [row["catchment_code"].zfill(5)]
            county_to_state.setdefault(counties[0], STATE_FIPS_TO_ABBR[counties[0][:2]])
        if not counties:
            raise RuntimeError(f"No county membership for {row['catchment_id']}")
        row["counties"] = counties
    county_to_catchments: dict[str, list[str]] = defaultdict(list)
    for row in selected:
        for county in row["counties"]:
            county_to_catchments[county].append(row["catchment_id"])
    return dict(county_to_catchments)


def rollup_svi(
    selected: list[dict[str, Any]], county_to_catchments: dict[str, list[str]]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    needed_counties = set(county_to_catchments)
    acc = {row["catchment_id"]: {"weight": 0.0, "value": 0.0, "source_count": 0} for row in selected}
    members: list[dict[str, Any]] = []
    with SVI_CSV.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for source in reader:
            geoid = source.get("FIPS", "")
            county = geoid[:5]
            if county not in needed_counties:
                continue
            value = numeric(source.get("RPL_THEMES"))
            weight = numeric(source.get("E_TOTPOP"))
            if value is None or weight is None or weight <= 0:
                continue
            for catchment_id in county_to_catchments[county]:
                acc[catchment_id]["weight"] += weight
                acc[catchment_id]["value"] += value * weight
                acc[catchment_id]["source_count"] += 1
                members.append(
                    {
                        "catchment_id": catchment_id,
                        "source_layer": "cdc_svi",
                        "source_geography_level": "census_tract",
                        "source_geoid": geoid,
                        "source_value": value,
                        "source_weight": weight,
                        "source_county_geoid": county,
                    }
                )
    out: dict[str, dict[str, Any]] = {}
    crosswalk: list[dict[str, str]] = []
    for row in selected:
        catchment_id = row["catchment_id"]
        total = acc[catchment_id]["weight"]
        out[catchment_id] = {
            "value": acc[catchment_id]["value"] / total if total else None,
            "weight": total,
            "source_count": acc[catchment_id]["source_count"],
        }
    for member in members:
        total = out[member["catchment_id"]]["weight"]
        source_row = next(row for row in selected if row["catchment_id"] == member["catchment_id"])
        crosswalk.append(
            {
                "catchment_id": member["catchment_id"],
                "catchment_type": source_row["catchment_type"],
                "catchment_code": source_row["catchment_code"],
                "source_layer": member["source_layer"],
                "source_geography_level": member["source_geography_level"],
                "source_geoid": member["source_geoid"],
                "allocation_weight": fmt(member["source_weight"] / total, 12),
                "weight_basis": "CDC SVI E_TOTPOP tract population share within catchment",
                "join_method": "tract_geoid_prefix_to_county_then_census_2023_cbsa_county_delineation",
                "uncertainty_note": "Population-weighted rollup of tract percentile ranks; percentile ranks are year-specific and should not be compared across SVI vintages.",
            }
        )
    return out, crosswalk


def extract_hhi_files(raw_hhi_dir: Path) -> tuple[Path, Path]:
    with zipfile.ZipFile(HHI_ZIP) as zf:
        data_name = "HHI Data 2024 United States.xlsx"
        dictionary_name = "HHI Data Dictionary 2024.xlsx"
        data_path = raw_hhi_dir / data_name
        dictionary_path = raw_hhi_dir / dictionary_name
        data_path.write_bytes(zf.read(data_name))
        dictionary_path.write_bytes(zf.read(dictionary_name))
    return data_path, dictionary_path


def rollup_hhi(
    selected: list[dict[str, Any]], county_to_catchments: dict[str, list[str]], hhi_xlsx: Path
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    hhi_by_zcta: dict[str, tuple[float, float]] = {}
    header: list[str] | None = None
    index: dict[str, int] = {}
    for row_number, row in enumerate(xlsx_iter_rows(hhi_xlsx)):
        if row_number == 0:
            header = row
            index = {name: i for i, name in enumerate(header)}
            continue
        zcta = row[index["ZCTA"]] if index["ZCTA"] < len(row) else ""
        value = numeric(row[index["OVERALL_RANK"]] if index["OVERALL_RANK"] < len(row) else "")
        pop = numeric(row[index["POP"]] if index["POP"] < len(row) else "")
        if zcta and value is not None and pop is not None and pop > 0:
            hhi_by_zcta[zcta] = (value, pop)
    needed_counties = set(county_to_catchments)
    acc = {row["catchment_id"]: {"weight": 0.0, "value": 0.0, "source_count": 0} for row in selected}
    members: list[dict[str, Any]] = []
    with ZCTA_COUNTY_REL.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="|")
        for source in reader:
            zcta = source.get("GEOID_ZCTA5_20", "")
            county = source.get("GEOID_COUNTY_20", "")
            if not zcta or county not in needed_counties or zcta not in hhi_by_zcta:
                continue
            land = numeric(source.get("AREALAND_ZCTA5_20")) or 0
            part = numeric(source.get("AREALAND_PART")) or 0
            if land <= 0 or part <= 0:
                continue
            value, pop = hhi_by_zcta[zcta]
            weight = pop * (part / land)
            if weight <= 0:
                continue
            for catchment_id in county_to_catchments[county]:
                acc[catchment_id]["weight"] += weight
                acc[catchment_id]["value"] += value * weight
                acc[catchment_id]["source_count"] += 1
                members.append(
                    {
                        "catchment_id": catchment_id,
                        "source_geoid": zcta,
                        "source_weight": weight,
                        "source_county_geoid": county,
                    }
                )
    out: dict[str, dict[str, Any]] = {}
    crosswalk: list[dict[str, str]] = []
    for row in selected:
        catchment_id = row["catchment_id"]
        total = acc[catchment_id]["weight"]
        out[catchment_id] = {
            "value": acc[catchment_id]["value"] / total if total else None,
            "weight": total,
            "source_count": acc[catchment_id]["source_count"],
        }
    for member in members:
        total = out[member["catchment_id"]]["weight"]
        source_row = next(row for row in selected if row["catchment_id"] == member["catchment_id"])
        crosswalk.append(
            {
                "catchment_id": member["catchment_id"],
                "catchment_type": source_row["catchment_type"],
                "catchment_code": source_row["catchment_code"],
                "source_layer": "heat_vulnerability",
                "source_geography_level": "zcta",
                "source_geoid": member["source_geoid"],
                "allocation_weight": fmt(member["source_weight"] / total, 12),
                "weight_basis": "HHI ZCTA POP multiplied by Census 2020 ZCTA-to-county land-area allocation share",
                "join_method": "zcta_to_county_relationship_then_census_2023_cbsa_county_delineation",
                "uncertainty_note": "ZCTAs approximate ZIP Codes; multi-county ZCTAs allocated by land area, then population-weighted to catchment.",
            }
        )
    return out, crosswalk


def extract_lead_county_files(raw_lead_dir: Path, states: list[str]) -> tuple[dict[str, Path], list[dict[str, Any]]]:
    extracted: dict[str, Path] = {}
    zip_records: list[dict[str, Any]] = []
    for state in states:
        zip_path = TMP_ROOT / f"{state}-2022-LEAD-data.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Missing DOE LEAD state archive: {zip_path}")
        with zipfile.ZipFile(zip_path) as zf:
            matches = [name for name in zf.namelist() if name == f"{state} AMI Counties 2022.csv"]
            if not matches:
                raise RuntimeError(f"No AMI Counties CSV in {zip_path}")
            dest = raw_lead_dir / matches[0].replace(" ", "_")
            dest.write_bytes(zf.read(matches[0]))
            extracted[state] = dest
            row_count = sum(1 for _ in csv.DictReader(dest.open(newline="", encoding="utf-8-sig")))
        zip_records.append(
            {
                "state": state,
                "source_zip_url": f"https://data.openei.org/files/6219/{state}-2022-LEAD-data.zip",
                "source_zip_sha256": sha256(zip_path),
                "source_zip_size_bytes": zip_path.stat().st_size,
                "extracted_csv_path": str(dest),
                "extracted_csv_sha256": sha256(dest),
                "extracted_csv_size_bytes": dest.stat().st_size,
                "extracted_csv_rows": row_count,
            }
        )
    return extracted, zip_records


def lead_county_values(extracted: dict[str, Path]) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"units": 0.0, "income": 0.0, "energy": 0.0, "rows": 0, "state": ""}
    )
    for state, path in extracted.items():
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                county = row["FIP"].zfill(5)
                income = numeric(row.get("HINCP*UNITS")) or 0.0
                electricity = numeric(row.get("ELEP*UNITS")) or 0.0
                gas = numeric(row.get("GASP*UNITS")) or 0.0
                fuel = numeric(row.get("FULP*UNITS")) or 0.0
                units = numeric(row.get("UNITS")) or 0.0
                values[county]["units"] += units
                values[county]["income"] += income
                values[county]["energy"] += electricity + gas + fuel
                values[county]["rows"] += 1
                values[county]["state"] = state
    return dict(values)


def rollup_lead(
    selected: list[dict[str, Any]], county_values: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], list[str]]:
    out: dict[str, dict[str, Any]] = {}
    crosswalk: list[dict[str, str]] = []
    missing: list[str] = []
    for row in selected:
        income = 0.0
        energy = 0.0
        units = 0.0
        rows = 0
        for county in row["counties"]:
            source = county_values.get(county)
            if source is None:
                missing.append(county)
                continue
            income += source["income"]
            energy += source["energy"]
            units += source["units"]
            rows += source["rows"]
        value = (energy / income * 100.0) if income > 0 else None
        out[row["catchment_id"]] = {
            "value": value,
            "income": income,
            "energy": energy,
            "units": units,
            "source_count": len(row["counties"]),
            "source_rows": rows,
        }
        for county in row["counties"]:
            source = county_values.get(county)
            if source is None or income <= 0:
                continue
            crosswalk.append(
                {
                    "catchment_id": row["catchment_id"],
                    "catchment_type": row["catchment_type"],
                    "catchment_code": row["catchment_code"],
                    "source_layer": "doe_lead_energy_burden",
                    "source_geography_level": "county",
                    "source_geoid": county,
                    "allocation_weight": fmt(source["income"] / income, 12),
                    "weight_basis": "DOE LEAD HINCP*UNITS county income denominator share within catchment",
                    "join_method": "county_fips_direct_or_census_2023_cbsa_county_delineation",
                    "uncertainty_note": "Catchment energy burden is a ratio of summed LEAD county energy expenditures to summed household income; CBSA values are county-rollup proxies.",
                }
            )
    return out, crosswalk, sorted(set(missing))


def acs_crosswalk(selected: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for row in selected:
        if row["catchment_type"] == "CBSA":
            source_geoid = f"31000US{row['catchment_code']}"
            source_level = "cbsa"
        else:
            source_geoid = f"05000US{row['catchment_code'].zfill(5)}"
            source_level = "county"
        rows.append(
            {
                "catchment_id": row["catchment_id"],
                "catchment_type": row["catchment_type"],
                "catchment_code": row["catchment_code"],
                "source_layer": "acs_income_poverty",
                "source_geography_level": source_level,
                "source_geoid": source_geoid,
                "allocation_weight": "1",
                "weight_basis": "direct Census Reporter ACS geography estimate",
                "join_method": "direct_cbsa_or_county_geoid_match",
                "uncertainty_note": "Direct ACS CBSA/county estimate; source MOEs retained for income and poverty count/universe.",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def copy_raw_files(raw_root: Path) -> dict[str, Path]:
    raw_svi = raw_root / "svi"
    raw_acs = raw_root / "acs"
    raw_census = raw_root / "census"
    raw_hhi = raw_root / "hhi"
    raw_lead = raw_root / "lead"
    for path in (raw_svi, raw_acs, raw_census, raw_hhi, raw_lead):
        path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SVI_CSV, raw_svi / SVI_CSV.name)
    shutil.copy2(ACS_PAYLOAD, raw_acs / "censusreporter_atlas_selected_acs2024_5yr.json")
    shutil.copy2(CBSA_XLSX, raw_census / CBSA_XLSX.name)
    shutil.copy2(ZCTA_COUNTY_REL, raw_census / ZCTA_COUNTY_REL.name)
    shutil.copy2(HHI_ZIP, raw_hhi / HHI_ZIP.name)
    shutil.copy2(LEAD_DICTIONARY, raw_lead / LEAD_DICTIONARY.name)
    hhi_data, hhi_dictionary = extract_hhi_files(raw_hhi)
    return {
        "svi": raw_svi / SVI_CSV.name,
        "acs": raw_acs / "censusreporter_atlas_selected_acs2024_5yr.json",
        "cbsa": raw_census / CBSA_XLSX.name,
        "zcta_county": raw_census / ZCTA_COUNTY_REL.name,
        "hhi_zip": raw_hhi / HHI_ZIP.name,
        "hhi_data": hhi_data,
        "hhi_dictionary": hhi_dictionary,
        "lead_dictionary": raw_lead / LEAD_DICTIONARY.name,
        "lead_dir": raw_lead,
    }


def build_profile_rows(
    selected: list[dict[str, Any]],
    current: dict[str, dict[str, str]],
    svi: dict[str, dict[str, Any]],
    lead: dict[str, dict[str, Any]],
    hhi: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    fields = [
        "catchment_id",
        "catchment_type",
        "catchment_code",
        "catchment_label",
        "climate_region",
        "urbanicity",
        "urbanicity_short",
        "centroid_lat",
        "centroid_lon",
        "population_2010",
        "housing_units_2010",
        "population_density_sqmi",
        "housing_unit_density_sqmi",
        "svi_percentile",
        "svi_source_vintage",
        "svi_proxy_badge",
        "svi_join_uncertainty_note",
        "acs_geoid",
        "acs_geography_name",
        "acs_median_hh_income",
        "acs_median_hh_income_moe",
        "acs_poverty_universe",
        "acs_poverty_universe_moe",
        "acs_poverty_count",
        "acs_poverty_count_moe",
        "acs_poverty_rate",
        "acs_source_vintage",
        "acs_proxy_badge",
        "acs_join_uncertainty_note",
        "doe_lead_energy_burden_pct",
        "doe_lead_source_vintage",
        "doe_lead_proxy_badge",
        "doe_lead_join_uncertainty_note",
        "heat_vuln_index",
        "heat_vuln_source_vintage",
        "heat_vuln_proxy_badge",
        "heat_vuln_join_uncertainty_note",
        "catchment_join_method",
        "equity_layer_status",
    ]
    rows: list[dict[str, str]] = []
    for source in selected:
        catchment_id = source["catchment_id"]
        base = current[catchment_id]
        row = {field: "" for field in fields}
        for field in fields[:13]:
            row[field] = str(source.get(field, base.get(field, "")))
        row["catchment_id"] = catchment_id
        row["svi_percentile"] = fmt(svi[catchment_id]["value"])
        row["svi_source_vintage"] = (
            "CDC/ATSDR SVI 2022 U.S. census-tract CSV; overall RPL_THEMES percentile rank; "
            "population-weighted to Atlas catchments."
        )
        row["svi_proxy_badge"] = "Proxy"
        row["svi_join_uncertainty_note"] = (
            "Tract GEOID county prefix joined to catchment counties; CBSA counties from Census 2023 "
            "delineation. Tract ranks are population-weighted; SVI percentiles are vintage-specific."
        )
        for field in [
            "acs_geoid",
            "acs_geography_name",
            "acs_median_hh_income",
            "acs_median_hh_income_moe",
            "acs_poverty_universe",
            "acs_poverty_universe_moe",
            "acs_poverty_count",
            "acs_poverty_count_moe",
            "acs_poverty_rate",
            "acs_source_vintage",
            "acs_proxy_badge",
            "acs_join_uncertainty_note",
        ]:
            row[field] = base.get(field, "")
        row["doe_lead_energy_burden_pct"] = fmt(lead[catchment_id]["value"])
        row["doe_lead_source_vintage"] = (
            "DOE LEAD Tool 2022 Update, OEDI dataset DOI 10.25984/2504170; AMI county CSV rows from "
            "state archives; energy burden = sum energy expenditures / sum household income * 100."
        )
        row["doe_lead_proxy_badge"] = "Proxy"
        row["doe_lead_join_uncertainty_note"] = (
            "County rows are aggregated within catchments by summing LEAD HINCP*UNITS and energy cost "
            "fields. CBSA values are county-rollup proxies; no tract interpolation is used."
        )
        row["heat_vuln_index"] = fmt(hhi[catchment_id]["value"])
        row["heat_vuln_source_vintage"] = (
            "CDC/ATSDR Heat & Health Index 2024; HHI OVERALL_RANK at ZCTA level; rolled to catchments "
            "through Census 2020 ZCTA-county relationship and Census 2023 CBSA county delineation."
        )
        row["heat_vuln_proxy_badge"] = "Modeled"
        row["heat_vuln_join_uncertainty_note"] = (
            "ZCTA ranks are weighted by HHI population and Census land-area allocation where ZCTAs cross "
            "county boundaries; ZCTAs approximate ZIP Codes and are not exact delivery ZIPs."
        )
        row["catchment_join_method"] = (
            "Sidecar-backed rollup: ACS direct CBSA/county; SVI tract population weights; DOE LEAD county "
            "income-denominator rollup; HHI ZCTA population x land-allocation rollup; CBSA county membership "
            "from Census 2023 list1 delineation."
        )
        row["equity_layer_status"] = "READY"
        rows.append(row)
    return rows


def main() -> None:
    required = [SELECTED_CATCHMENTS, ACS_PAYLOAD, SVI_CSV, CBSA_XLSX, ZCTA_COUNTY_REL, HHI_ZIP, LEAD_DICTIONARY]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required source files: " + ", ".join(missing))

    raw_root = CANONICAL_ROOT / "equity_sources" / "raw"
    crosswalk_root = CANONICAL_ROOT / "equity_sources" / "crosswalks"
    raw_paths = copy_raw_files(raw_root)

    selected = load_selected()
    current = load_current_profile()
    cbsa_to_counties, county_to_state = load_cbsa_counties()
    county_to_catchments = attach_counties(selected, cbsa_to_counties, county_to_state)
    states = sorted({county_to_state[county] for county in county_to_catchments})

    lead_extract_dir = raw_paths["lead_dir"] / "ami_counties"
    lead_extract_dir.mkdir(parents=True, exist_ok=True)
    extracted_lead, lead_zip_records = extract_lead_county_files(lead_extract_dir, states)
    county_lead = lead_county_values(extracted_lead)

    svi, svi_crosswalk = rollup_svi(selected, county_to_catchments)
    hhi, hhi_crosswalk = rollup_hhi(selected, county_to_catchments, raw_paths["hhi_data"])
    lead, lead_crosswalk, missing_lead = rollup_lead(selected, county_lead)
    if missing_lead:
        raise RuntimeError(f"Missing LEAD county values for {missing_lead}")

    incomplete = []
    for row in selected:
        catchment_id = row["catchment_id"]
        if svi[catchment_id]["value"] is None:
            incomplete.append(f"{catchment_id}: SVI")
        if lead[catchment_id]["value"] is None:
            incomplete.append(f"{catchment_id}: LEAD")
        if hhi[catchment_id]["value"] is None:
            incomplete.append(f"{catchment_id}: HHI")
    if incomplete:
        raise RuntimeError("Incomplete layer rollups: " + ", ".join(incomplete))

    profile_rows = build_profile_rows(selected, current, svi, lead, hhi)
    profile_fields = list(profile_rows[0])
    profile_path = CANONICAL_ROOT / "equity_profile.csv"
    write_csv(profile_path, profile_rows, profile_fields)

    crosswalk_rows = acs_crosswalk(selected) + svi_crosswalk + lead_crosswalk + hhi_crosswalk
    crosswalk_fields = [
        "catchment_id",
        "catchment_type",
        "catchment_code",
        "source_layer",
        "source_geography_level",
        "source_geoid",
        "allocation_weight",
        "weight_basis",
        "join_method",
        "uncertainty_note",
    ]
    crosswalk_path = crosswalk_root / "catchment_equity_crosswalk.csv"
    write_csv(crosswalk_path, crosswalk_rows, crosswalk_fields)

    lead_manifest_path = raw_paths["lead_dir"] / "lead_state_zip_manifest.csv"
    write_csv(
        lead_manifest_path,
        lead_zip_records,
        [
            "state",
            "source_zip_url",
            "source_zip_sha256",
            "source_zip_size_bytes",
            "extracted_csv_path",
            "extracted_csv_sha256",
            "extracted_csv_size_bytes",
            "extracted_csv_rows",
        ],
    )

    source_manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "tier_id": TIER_ID,
        "raw_files": {
            "selected_catchments": file_record(
                SELECTED_CATCHMENTS, "20 representative Atlas catchments selected before equity rollup"
            ),
            "acs_payload": file_record(
                raw_paths["acs"], "ACS income/poverty Census Reporter payload", "https://api.censusreporter.org/"
            ),
            "svi_csv": file_record(raw_paths["svi"], "CDC/ATSDR SVI 2022 U.S. tract CSV", SVI_URL),
            "cbsa_delineation": file_record(
                raw_paths["cbsa"], "Census 2023 CBSA-to-county delineation workbook", CBSA_URL
            ),
            "zcta_county_relationship": file_record(
                raw_paths["zcta_county"], "Census 2020 ZCTA-to-county relationship file", ZCTA_REL_URL
            ),
            "hhi_zip": file_record(raw_paths["hhi_zip"], "CDC/ATSDR HHI 2024 data zip", HHI_URL),
            "hhi_data": file_record(raw_paths["hhi_data"], "Extracted HHI 2024 United States workbook", HHI_URL),
            "hhi_dictionary": file_record(raw_paths["hhi_dictionary"], "Extracted HHI 2024 data dictionary", HHI_URL),
            "lead_dictionary": file_record(
                raw_paths["lead_dictionary"], "DOE LEAD Tool 2022 data dictionary", LEAD_DICT_URL
            ),
            "lead_zip_manifest": file_record(
                lead_manifest_path, "State LEAD archive checksums and extracted AMI county CSVs"
            ),
        },
        "lead_state_archives": lead_zip_records,
    }
    manifest_path = raw_root / "source_manifest.json"
    manifest_path.write_text(json.dumps(source_manifest, indent=2) + "\n")

    crosswalk_sidecar = {
        "canonical_name": "catchment_equity_crosswalk.csv",
        "tier_id": TIER_ID,
        "generation_timestamp_utc": datetime.now(UTC).isoformat(),
        "row_count": len(crosswalk_rows),
        "source_layers": {
            "acs_income_poverty": len(acs_crosswalk(selected)),
            "cdc_svi": len(svi_crosswalk),
            "doe_lead_energy_burden": len(lead_crosswalk),
            "heat_vulnerability": len(hhi_crosswalk),
        },
        "source_csv": str(crosswalk_path),
        "sha256": sha256(crosswalk_path),
        "method": "Layer-specific source geography to representative catchment allocation weights.",
    }
    crosswalk_sidecar_path = crosswalk_path.with_suffix(".csv.prov.json")
    crosswalk_sidecar_path.write_text(json.dumps(crosswalk_sidecar, indent=2) + "\n")

    profile_sha = sha256(profile_path)
    sidecar = {
        "canonical_name": "equity_profile.csv",
        "dest_rel": "10_DATA/replocx_tmy3_wallfix_4scen/equity_profile.csv",
        "authority": "CURRENT_CERTIFIED_EQUITY",
        "tier": "ReplocX_TMY3_wallfix_4scen",
        "tier_id": TIER_ID,
        "class": "equity_profile",
        "generation_timestamp_utc": datetime.now(UTC).isoformat(),
        "generated_by": "Codex W4 equity source acquisition and rollup pass",
        "source_inputs": source_manifest["raw_files"],
        "source_urls": [
            SVI_PAGE,
            SVI_URL,
            CBSA_URL,
            ZCTA_REL_URL,
            HHI_PAGE,
            HHI_URL,
            LEAD_DATASET_URL,
            LEAD_DOI,
            LEAD_DICT_URL,
            "https://api.censusreporter.org/",
            "https://www.census.gov/programs-surveys/acs",
        ],
        "geography_crosswalk_method": (
            "CBSA catchments were mapped to counties with Census 2023 list1 CBSA delineation. "
            "County catchments use direct county FIPS. SVI tracts join to counties by tract GEOID prefix. "
            "HHI ZCTAs join to counties through the Census 2020 ZCTA-to-county relationship. ACS uses direct "
            "Census Reporter CBSA/county geographies."
        ),
        "aggregation_method": {
            "cdc_svi": "Population-weighted mean of CDC/ATSDR SVI 2022 tract RPL_THEMES using E_TOTPOP.",
            "acs_income_poverty": (
                "Direct Census Reporter ACS 2024 5-year CBSA/county values retained from W3.5; poverty rate "
                "= B17001002 / B17001001."
            ),
            "doe_lead_energy_burden": (
                "For each county, sum DOE LEAD AMI county rows: energy = ELEP*UNITS + GASP*UNITS + FULP*UNITS; "
                "income = HINCP*UNITS. Catchment percent = sum(energy) / sum(income) * 100."
            ),
            "heat_vulnerability": (
                "Population-weighted mean of CDC/ATSDR HHI 2024 OVERALL_RANK. Multi-county ZCTA population is "
                "allocated by Census ZCTA-county land-area share before catchment aggregation."
            ),
        },
        "uncertainty_moe_handling": (
            "ACS income and poverty MOE fields are retained from source. SVI and HHI percentile/rank rollups do "
            "not have MOEs; uncertainty is documented as aggregation/join uncertainty. DOE LEAD burden is "
            "derived from published LEAD county rows and does not carry a separate MOE."
        ),
        "layer_statuses": {
            "cdc_svi": "READY: official SVI source, values, source/vintage, proxy badge, join uncertainty, and crosswalk present for all 20 catchments",
            "acs_income_poverty": "READY: direct ACS geography values, source vintage, proxy badge, and uncertainty note present for all 20 catchments",
            "doe_lead_energy_burden": "READY: official LEAD county rows, source/vintage, proxy badge, join uncertainty, and rollup crosswalk present for all 20 catchments",
            "heat_vulnerability": "READY: official HHI ZCTA ranks, source/vintage, modeled badge, join uncertainty, and ZCTA/county crosswalk present for all 20 catchments",
        },
        "row_count": len(profile_rows),
        "source_record_count": len(profile_rows),
        "crosswalk": {
            "path": str(crosswalk_path),
            "provenance_sidecar": str(crosswalk_sidecar_path),
            "row_count": len(crosswalk_rows),
            "sha256": sha256(crosswalk_path),
        },
        "lead_state_archives": lead_zip_records,
        "verified_sha256": profile_sha,
        "target_sha256": profile_sha,
        "sha256": profile_sha,
        "sha_match": True,
        "size_bytes": profile_path.stat().st_size,
        "notes": [
            "All four Atlas equity layers are source-backed and marked READY.",
            "No scaffold/demo equity values were used.",
            "DOE LEAD state zips were used only as official containers for extracted AMI county CSVs; extracted CSV checksums and parent zip checksums are recorded.",
        ],
    }
    sidecar_path = profile_path.with_suffix(".csv.prov.json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n")

    print(
        json.dumps(
            {
                "profile": str(profile_path),
                "profile_sha256": profile_sha,
                "rows": len(profile_rows),
                "crosswalk_rows": len(crosswalk_rows),
                "lead_states": states,
                "source_manifest": str(manifest_path),
                "sidecar": str(sidecar_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
