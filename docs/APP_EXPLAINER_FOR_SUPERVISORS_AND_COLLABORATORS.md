# Representative Location Explorer User Guide

## 1. Purpose

The Representative Location Explorer is a decision-support application for selecting,
reviewing, and exporting representative U.S. locations for national building-stock,
building-energy, and heat-health simulation studies.

The app supports a common research problem: national studies often cannot simulate every
community in the United States, but they still need a defensible sample of places that
captures major differences in climate, urban form, housing representation, and simulation
geography.

The app provides:

- a baseline selection of 20 representative catchments;
- transparent scoring and ranking of candidate locations;
- scenario controls for testing alternative assumptions;
- ZIP-to-geography resolution that avoids common boundary mistakes;
- comparison tools for selected locations, runner-up candidates, and user-preferred
  alternatives;
- exportable site lists and scenario definitions for downstream simulation workflows.

The application does not simulate buildings directly. Its role is to help decide where
building-stock or heat-health simulations should be run, and to document why those places
were selected.

## 2. Intended Users

The app is intended for:

- building-energy modelers selecting simulation sites;
- heat-health and climate-risk researchers choosing representative communities;
- PhD supervisors, committee members, and journal reviewers auditing methodology;
- policy and program teams evaluating national coverage across climate and urban form;
- geospatial analysts working with ZIP, ZCTA, county, CBSA, and station data;
- future project contributors who need to reproduce or update the selection method.

Different users may use the app differently. A reviewer may focus on the methodology and
trade-offs. A modeler may focus on the exported site list. A collaborator may compare a
preferred location against the selected representative catchments.

## 3. Core Concept: Representative Catchments

A catchment is the geographic area used as the simulation target. It is the place whose
building stock, population context, and urban form are being represented.

In this app:

- non-rural catchments are represented by CBSAs, meaning metropolitan or micropolitan
  statistical areas;
- rural catchments are represented by counties;
- weather stations are separate points that provide climate context, not the boundary of
  the building-stock geography;
- ZIP codes are lookup entry points, not simulation boundaries.

This distinction is important because building-stock simulation filters must use the
correct geography. Rural selections use county filters. Non-rural selections use metro
or micropolitan filters. Substituting a ZIP code, city, or weather-station location for
the simulation catchment can bias the analysis.

## 4. Why The Baseline Uses 20 Locations

The baseline method selects one catchment for each combination of climate region and
urbanicity class.

Climate regions:

- Cold & Very Cold
- Hot-Dry & Mixed Dry
- Hot-Humid
- Marine
- Mixed-Humid

Urbanicity classes:

- higher density urban
- lower density urban
- suburban / small town
- rural

The structure is:

| Climate Region | Higher Density Urban | Lower Density Urban | Suburban / Small Town | Rural |
|---|---:|---:|---:|---:|
| Cold & Very Cold | 1 | 1 | 1 | 1 |
| Hot-Dry & Mixed Dry | 1 | 1 | 1 | 1 |
| Hot-Humid | 1 | 1 | 1 | 1 |
| Marine | 1 | 1 | 1 | 1 |
| Mixed-Humid | 1 | 1 | 1 | 1 |

This produces 20 selected catchments.

The 20-catchment design is a structured sampling frame. It is not meant to claim that
only 20 places can fully describe the United States. Instead, it creates a compact and
auditable national sample across major climate and urban-form conditions.

## 5. Why The App Is Needed

The app is not only a way to display the final 20 locations. A static table can do that.
The app is useful because it exposes the method behind the selection and allows users to
test whether the selection remains defensible under different assumptions.

The app helps answer questions such as:

- Why was this catchment selected?
- Which candidate almost won?
- What score difference separates the selected location from the runner-up?
- What changes if housing-unit coverage is weighted more heavily?
- What changes if weather-station distance rules are stricter?
- What happens if a research-priority override is removed?
- How does a user-preferred city compare with the selected representative catchment?
- Are rural and non-rural simulation filters being handled correctly?
- Is a ZIP code being confused with a Census or simulation geography?

The baseline 20 catchments are the answer. The app is the audit trail, comparison tool,
and scenario-testing environment.

## 6. Data Modes

The application supports two data modes.

Production mode reads private processed analytical outputs from the research workspace.
This mode is intended for real project use.

Demo mode reads bundled synthetic data from `data/demo/`. This mode is safe for public
demonstration, continuous integration, and reviewer walkthroughs because it does not
publish private analytical data.

Users should always check the data mode before interpreting results. Demo-mode results
illustrate the workflow and interface. Production-mode results are required for real
research conclusions.

## 7. Main Workflow

The typical app workflow is:

1. Open the overview dashboard.
2. Confirm the data mode and baseline scenario.
3. Review the 20 selected catchments.
4. Inspect catchment geography, urbanicity, climate region, and station context.
5. Use ZIP Explorer to connect familiar ZIP codes to the correct analytical geography.
6. Use Scenario Builder to test alternative assumptions.
7. Use Candidate Ranking to inspect selected and non-selected candidates.
8. Use Allocation Comparison to understand substitutions and score trade-offs.
9. Export the selected site list or scenario definition for documentation or simulation.

The user does not need to understand the full algorithm before using the app, but the
methodology page and exported scenario make the selection auditable.

## 8. How Candidate Scoring Works

Each candidate location receives a scenario score. The baseline scoring formula is:

```text
score =
  0.45 x housing-unit coverage percentile
  + 0.35 x population-density percentile
  + 0.20 x population-coverage percentile
```

The score balances three ideas:

- housing-unit coverage: how well the candidate represents housing stock;
- population density: how well the candidate matches the intended urbanicity profile;
- population coverage: how much population representation the candidate contributes.

The scenario builder allows the user to adjust the weights. The weights must sum to 1.0.
This prevents accidental scenarios where the score is mathematically inconsistent.

## 9. Distinct-Location Allocation

The highest-ranked candidate in each stratum is not always the final selected location.
The app can enforce a distinct-location rule so the final set contains 20 distinct
catchments.

This matters because the same catchment may score well in more than one stratum. If the
same location is selected repeatedly, the final set may become less useful as a national
sample.

When the distinct-location rule is enabled, the allocator chooses one catchment per
stratum while maximizing total score and preventing duplicate catchments. If a lower-ranked
candidate is selected to preserve national coverage, the app reports the substitution and
the score loss.

This makes the trade-off visible:

```text
Independent top pick: highest-scoring candidate within a single stratum.
Final allocation: selected set after enforcing national distinctness and overrides.
```

## 10. Page-By-Page Guide

### Overview Dashboard

Use the overview page to see the baseline status of the selection.

This page is useful for:

- confirming whether data are ready;
- seeing whether the app is in demo or production mode;
- reviewing headline metrics such as selected strata and candidate counts;
- scanning the selected catchments and station context;
- communicating the high-level result to supervisors or collaborators.

Recommended use:

1. Start here before changing scenario assumptions.
2. Confirm the app reports the expected data mode.
3. Use the dashboard as the baseline reference when comparing scenarios.

### ZIP Explorer

Use ZIP Explorer when a user starts with a familiar ZIP code.

The ZIP Explorer:

- validates five-digit ZIP codes;
- preserves leading zeros;
- resolves ZIP codes to ZCTA, county, CBSA, state, climate region, and urbanicity context;
- reports uncertainty in the crosswalk when relevant;
- explains whether the simulation catchment is county-based or CBSA-based;
- keeps weather-station context separate from simulation geography.

Recommended use:

1. Enter a ZIP code relevant to a collaborator, stakeholder, or study area.
2. Review the resolved Census geography.
3. Confirm whether the relevant simulation filter is rural county-based or non-rural
   CBSA-based.
4. Compare the local geography against the selected representative catchment.

### Scenario Builder

Use Scenario Builder to test methodological assumptions.

Available scenario controls include:

- density screen percentile;
- scoring weights;
- unique catchment rule;
- maximum station distance;
- optional weather-readiness requirement;
- research-priority override.

Recommended use:

1. Change one assumption at a time.
2. Re-solve the scenario.
3. Compare changed assignments and score losses.
4. Export the scenario if it represents a meaningful alternative.

### Candidate Ranking

Use Candidate Ranking to inspect the candidate pool.

This page is useful for:

- seeing all scored candidates;
- filtering by stratum or location type;
- checking where a preferred location ranks;
- comparing selected and non-selected candidates;
- exporting candidate or site-list outputs.

Recommended use:

1. Search for a candidate of interest.
2. Compare its score and rank against the selected catchment.
3. Use the result to explain why a preferred location was or was not selected.

### Allocation Comparison

Use Allocation Comparison to understand the difference between independent top picks and
the final selected set.

This page is useful for:

- identifying substitutions caused by the distinct-location rule;
- measuring score loss relative to an unconstrained top pick;
- explaining why a lower-ranked candidate was selected;
- communicating national coverage trade-offs.

Recommended use:

1. Start with the baseline allocation.
2. Note any changed assignments.
3. Interpret each substitution as a trade-off between local score and national coverage.

### Methodology Page

Use the methodology page to explain the rules behind the app.

This page is useful for:

- supervisors;
- reviewers;
- collaborators;
- future project handoffs;
- methods-section drafting.

Recommended use:

1. Use it when preparing a presentation, report, or manuscript.
2. Pair it with exported scenarios so reviewers can connect written method to app output.

## 11. Example Use Cases

### Use Case A: Selecting Sites For A Building-Stock Simulation

A building-energy team needs a manageable set of simulation locations for a national
study. The team opens the app, reviews the baseline 20 catchments, confirms the ResStock
filter fields, and exports the site list.

The app helps the team document:

- which catchments were selected;
- what climate-urban stratum each catchment represents;
- whether each filter should use county or CBSA geography;
- what assumptions produced the site list;
- whether any lower-ranked candidates were selected to protect national coverage.

### Use Case B: Testing A Heat-Health Scenario

A heat-health researcher wants to prioritize weather-station proximity. The researcher
opens Scenario Builder, tightens maximum station distance, and compares the new selected
set against the baseline.

The app helps the researcher identify:

- which strata are sensitive to station-distance rules;
- whether closer stations reduce housing or population coverage;
- whether any candidate becomes ineligible;
- which alternate selection should be exported for heat-health analysis.

### Use Case C: Reviewing A Research-Priority Override

No override is applied by default, but a user can add one for a stratum. A supervisor can
then check whether a location was selected because it was objectively top-ranked or because
of a research priority.

The app makes this visible by showing:

- the override's stratum;
- the override rationale;
- the chosen catchment's unconstrained rank;
- the alternative selected location if the override is removed;
- the score difference between the override and the purely score-based selection.

### Use Case D: Comparing A Preferred City

A collaborator prefers Atlanta, Phoenix, Boston, or another familiar city. The user can
search the candidate ranking, identify the relevant stratum, and compare that preferred
location with the selected representative catchment.

The app helps answer:

- Is the preferred city in the same stratum?
- What is its rank?
- What score components are weaker or stronger?
- Would forcing it reduce national coverage?
- Would it duplicate another selected catchment?

### Use Case E: Avoiding ZIP Geography Errors

A stakeholder provides a ZIP code and asks whether it is represented. The user enters the
ZIP into ZIP Explorer. The app resolves it to the correct ZCTA, county, CBSA, climate, and
urbanicity context.

The app helps prevent mistakes such as:

- treating a ZIP code as a county;
- treating a ZIP code as a city;
- using the weather station as the simulation boundary;
- using `in.city` when the correct filter is county or CBSA.

## 12. Potential Research Questions

The app can support questions such as:

- Which 20 catchments provide a defensible national sample for residential simulation?
- How sensitive is the representative set to different score weights?
- Which climate-urban strata are hardest to represent with high-scoring candidates?
- How much score is lost when national distinctness is enforced?
- Which selected locations are stable across multiple scenarios?
- Which selected locations change when weather-station distance is constrained?
- How should rural and non-rural geography be handled in ResStock-style filters?
- How do ZIP-to-ZCTA and ZIP-to-county uncertainties affect local interpretation?
- How do stakeholder-preferred cities compare against method-selected catchments?
- What documentation is needed to make representative-location selection reproducible?

## 13. Gaps The App Addresses

The app addresses several gaps in applied simulation workflows:

- static site lists with limited explanation;
- unclear rationale for representative-location selection;
- lack of sensitivity testing around score weights and eligibility rules;
- hidden trade-offs between local score and national coverage;
- confusion between ZIP, ZCTA, county, CBSA, city, and weather-station geography;
- incorrect rural and non-rural simulation filter fields;
- difficulty comparing a stakeholder-preferred location against the selected set;
- limited reproducibility for supervisors, reviewers, or collaborators without access to
  the full private data environment.

## 14. Outputs

The app can produce:

- selected catchment summaries;
- ranked candidate tables;
- scenario comparison results;
- versioned scenario JSON;
- site-list CSV exports;
- exact simulation filter fields;
- health and data-mode status information.

These outputs can support reports, manuscripts, reviewer responses, simulation setup,
and future data-refresh workflows.

## 15. Limitations

The app should be interpreted with the following limitations:

- The public deployment uses synthetic demonstration data.
- Production conclusions require real analytical outputs.
- ZIP search currently uses a demonstration crosswalk subset.
- Weather-readiness metrics require additional production-quality data.
- The app selects simulation locations; it does not perform building or heat-health
  simulations itself.
- The 20-catchment baseline is a defensible sampling frame, not a claim that 20 places
  perfectly represent every U.S. community.

## 16. Practical Interpretation

Use the app to move from an unsupported statement:

```text
We selected these locations because they are representative.
```

to a defensible statement:

```text
We selected one catchment for each climate-region x urbanicity stratum using a
documented density screen, weighted scoring rule, and distinct-location allocation. We
tested alternative assumptions, reported substitutions and score losses, preserved
correct Census and ResStock geography, and exported a reproducible scenario definition.
```

That is the main contribution of the app: it turns location selection from a static list
into a transparent, reviewable, and reusable research workflow.

