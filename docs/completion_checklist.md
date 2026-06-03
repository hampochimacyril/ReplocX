# Completion Checklist

## Confirmed Repository Workflow

- Private repository confirmed: `https://github.com/hampochimacyril/Location-representation-explorer`
- Branch: `feature/location-representation-explorer`
- Draft pull request: `https://github.com/hampochimacyril/Location-representation-explorer/pull/1`
- Commit scope: application source, documentation, tests, Docker configuration, and private PR screenshots only
- Raw analytical datasets, local manifests, credentials, and generated caches are excluded

## Locally Verified Application Behavior

- Local application starts with `python3 -m backend.server`
- Overview dashboard renders all 20 target strata
- ZIP search preserves leading-zero identifiers and explains ZIP/ZCTA/county/CBSA scope
- Scenario scoring is deterministic and exportable as scenario JSON
- Unique-location allocator selects one target catchment per stratum
- Candidate ranking supports filtering, sorting, comparison, and CSV export
- Site-list CSV export returns one row per selected stratum
- Methodology and source pages document the major analytical rules and limitations

## Automated Checks

Run in this environment:

```bash
python3 -m unittest discover -s tests -v
node --check frontend/app.js
python3 -m py_compile backend/*.py scripts/*.py tests/*.py
```

Run in a Node environment with `npm` available:

```bash
npm install
npm run test:e2e
```

The current Codex workspace has Node.js but does not have `npm`, `pnpm`, `yarn`, `npx`, or
`corepack`, so Playwright dependency installation cannot be verified inside this session.

## Remaining Research Data Work

- Replace the demonstration ZIP crosswalk with a documented national HUD-USPS refresh.
- Add hourly weather completeness metrics before simulation handoff.
- Curate exact NREL enumeration mappings for non-baseline scenario alternatives.
- Add full catchment polygons when tract, county, and CBSA geometry files are approved for private use.

