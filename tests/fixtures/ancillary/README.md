# Recorded ancillary-data fixtures (Session 3)

Small, offline samples whose **shapes mirror the real upstream schemas** so the
live `--source api` code paths can be unit-tested without network access. Values
are minimal and illustrative; these are test fixtures, not analytical data.

| File | Mirrors | Used to test |
| --- | --- | --- |
| `hud_zip_county.json` | HUD-USPS API `type=2` (ZIP-COUNTY) envelope (`data.results[]`) | one-to-many ZIP retention, allocation ratios |
| `hud_zip_cbsa.json` | HUD-USPS API `type=4` (ZIP-CBSA) envelope | per-ZIP primary CBSA selection |
| `zip_to_zcta.csv` | a ZIP→ZCTA relationship file (`RLE_ZIP_ZCTA_FILE`) | ZCTA populated only from a real mapping, never equated to the ZIP |
| `tiger_multipolygon.json` | TIGERweb GeoJSON `geometry` (MultiPolygon) | island/detached parts kept, not dropped |
| `tiger_alaska.json` | TIGERweb GeoJSON `geometry` crossing the antimeridian | Alaska antimeridian normalisation + validation |
| `isd_global_hourly_leap.csv` | NOAA ISD global-hourly per-station CSV (TMP/DEW value,quality pairs, `+9999` sentinel) | leap-year (2024) hour de-dup + coverage |
| `resstock_options_lookup.tsv` | ResStock `options_lookup.tsv` (Parameter/Option) | real-dictionary enumeration parse |
| `resstock_data_dictionary.tsv` | OEDI `data_dictionary.tsv` (delimited allowable enumerations) | packed-list option parse |
| `resstock_enumeration_dictionary.tsv` | OEDI `enumeration_dictionary.tsv` | field/enumeration parse |

The 11-digit ISD station id and geography identifiers are kept as strings with
leading zeros, matching the production invariants.
