"""National data pipeline for ReplocX.

This package downloads free, public U.S. data and regenerates the analytical
CSVs the application reads (``candidate_scores.csv`` and friends), removing the
dependency on hand-supplied "private" outputs.

Two execution paths share the same ``classify`` and ``build_catchments`` stages:

* ``--source api`` (production): pulls real population/housing from the U.S.
  Census API. Requires a free ``CENSUS_API_KEY`` and outbound network access on
  the machine that runs it.
* ``--source fixture`` (offline/CI): replays a deterministic, clearly-labelled
  bundled dataset so the pipeline, schema validator, and full test suite run
  anywhere without network or a key.

Nothing here is a research result on its own; ``--source fixture`` produces a
reproducible structural stand-in, and ``--source api`` produces a real national
computation from open data that the project still owes methodological review.
"""

__all__ = ["config", "climate", "fetch_census", "classify", "build_catchments", "validate", "pilot"]
