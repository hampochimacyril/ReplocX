# Social posts & outreach copy

Live demo: https://representative-location-explorer.onrender.com
Repo: https://github.com/hampochimacyril/Location-representation-explorer

## LinkedIn (use cases + integrations + collaborator call)

> I turned a piece of my PhD into a live web app — and I'm looking for collaborators. 🎓→🛠️
>
> National building-stock and heat-health studies can't simulate every community, so
> researchers must choose a small, *defensible* set of representative U.S. locations.
> Doing it transparently is deceptively hard (a ZIP code is not a county, and the wrong
> simulation filter quietly biases everything downstream).
>
> So I built the **Representative Location Explorer**: it selects 20 representative
> catchments across 5 climate regions × 4 urbanicity classes, resolves any ZIP to its
> real Census geography, lets you tune the method and re-solve instantly, and measures
> every coverage trade-off — deterministic, reproducible, and auditable.
>
> 𝗪𝗵𝗲𝗿𝗲 𝗶𝘁 𝗰𝗮𝗻 𝗯𝗲 𝘂𝘀𝗲𝗱:
> • Selecting simulation sites for NREL ResStock / ComStock building-stock runs
> • Building a reproducible sampling frame for national energy or decarbonization studies
> • Heat-health & climate-vulnerability work (which populations does each site represent?)
> • Designing weatherization / energy-efficiency programs by climate–urbanicity strata
> • Utility, DER, and grid planning that needs representative archetypes
> • Environmental-justice and equity analyses of who is (and isn't) represented
> • Teaching reproducible geospatial method
>
> 𝗜𝗻𝘁𝗲𝗴𝗿𝗮𝘁𝗶𝗼𝗻 (𝗶𝗻𝘁𝗲𝗿𝗼𝗽𝗲𝗿𝗮𝗯𝗶𝗹𝗶𝘁𝘆) 𝗿𝗼𝗮𝗱𝗺𝗮𝗽:
> The app already emits exact ResStock filter fields, so it's designed to pair with
> established tooling — NREL **ResStock/ComStock**, **OpenStudio** + **EnergyPlus**,
> district-scale **URBANopt**, and GIS stacks (QGIS/ArcGIS, GeoPandas) — via a documented
> REST API and exportable scenarios, with co-simulation/coupling as a longer-term goal.
>
> 𝗜'𝗺 𝗹𝗼𝗼𝗸𝗶𝗻𝗴 𝗳𝗼𝗿 𝗰𝗼𝗹𝗹𝗮𝗯𝗼𝗿𝗮𝘁𝗼𝗿𝘀 — building-energy modelers, geospatial/Census data folks,
> heat-health researchers, and software engineers — to make the method more robust and the
> tool genuinely production-grade. If selecting representative locations is a pain point
> for your work, I'd love to talk.
>
> Live demo (synthetic data): https://representative-location-explorer.onrender.com
> Open source + methodology: https://github.com/hampochimacyril/Location-representation-explorer
>
> #BuildingEnergy #ResStock #EnergyPlus #OpenStudio #ClimateResilience #HeatHealth
> #GIS #Python #ResearchSoftware #OpenScience #PhDLife #Decarbonization

## X / Twitter

> Turned part of my PhD into a live app: the Representative Location Explorer.
>
> Picks the 20 U.S. locations that best represent the nation for building-energy &
> heat-health simulations — transparent, reproducible, ZIP-aware. Designed to pair with
> NREL ResStock + OpenStudio/EnergyPlus.
>
> Looking for collaborators 👇
> representative-location-explorer.onrender.com

## Instagram (with the video)

> From dissertation chapter to deployed app. The Representative Location Explorer chooses
> the U.S. locations that best stand in for the whole country in national building-energy
> and heat-health simulations — and shows exactly why each was picked. Built from an idea
> in my PhD into something live you can click. Looking for collaborators. Link in bio.
> #PhDLife #Python #ClimateTech #ResearchSoftware #BuildingScience #ResStock

## Terminology note

- "Pairing with established software" = **integration / interoperability** (general), or
  **coupling / co-simulation** for running models together (often via the **FMI**
  Functional Mock-up Interface standard). Use "integration" for API/data exchange and
  "co-simulation/coupling" when two simulation engines run jointly.
