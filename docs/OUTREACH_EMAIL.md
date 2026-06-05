# Outreach email — Representative Location Explorer

Adaptable email announcing the app to advisors, collaborators, modeling groups, or
potential sponsors. Replace the bracketed placeholders.

---

**Subject:** A web app from our project — choosing representative U.S. locations for building-stock & heat-health simulations

Dear [Name],

I'm excited to share something that came out of my PhD work on [project / dissertation
focus]. A recurring, under-appreciated problem in national building-stock and heat-health
simulation is **which locations we choose to simulate**: we can't model every community,
so we need a small, *defensible* set of places that represent the country's climate and
urban-form diversity — and the selection has to be transparent enough to defend in review.

To make that selection rigorous and inspectable, I built the **Representative Location
Explorer**, a web application that:

- selects **20 representative "catchments"** — one for each combination of 5 climate
  regions × 4 urbanicity classes — using a transparent density screen, a weighted score,
  and a distinct-location optimization that protects national coverage;
- resolves any **ZIP code** to its correct Census geography (ZCTA, county, metro) without
  the common category errors (a ZIP is not a county), with documented uncertainty;
- lets you **tune the method** (weights, screens, rules) and re-solve instantly, then
  **export** versioned, reproducible scenarios and exact simulation filters;
- measures every **coverage trade-off** (e.g., 99.7% coverage efficiency in the baseline).

The app is useful because the 20 locations are not just a static list; they are the
result of methodological choices. A table can publish the baseline answer, but the app
shows the audit trail: why those places were selected, which candidates were runner-up,
what changes if weights or weather-station rules change, whether an override such as
Philadelphia is still justified, and how a user's preferred location compares against the
recommended representative set. In that sense, the app is both a publication of the
baseline 20 catchments and a way for reviewers, collaborators, and future users to test
whether the selection remains defensible under different research priorities.

It's live as a public demo (synthetic data — no private research data is exposed):
**https://representative-location-explorer.onrender.com**
Source and methodology: **https://github.com/hampochimacyril/Location-representation-explorer**

What started as turning a dissertation idea into a quick prototype became a tested,
continuously-integrated, deployed application. I think it can be genuinely useful beyond
my own work — for modelers selecting simulation sites, for researchers who need to
reproduce a selection, and for program and policy teams who need to know *who and what*
each representative place stands for.

I'd love your thoughts on two things: (1) whether this would be useful to your group or
students, and (2) whether you'd be open to [collaborating on / advising / helping fund]
the next stage — replacing the demo data with the full national datasets and integrating
it with established tools like NREL ResStock and OpenStudio/EnergyPlus.

Happy to give a short live walkthrough whenever suits you.

Best regards,
[Your name]
[Program, Department] · Drexel University
[email] · [phone/links]

---

### Shorter sponsor / partnership variant (paste as needed)

> Subject: Sponsoring the next stage of a deployed research tool
>
> Hi [Name] — I built and deployed a working web app from my PhD that selects
> representative U.S. locations for national building-energy and heat-health simulations
> (live demo: representative-location-explorer.onrender.com). It's tested, open, and
> already useful on demonstration data. The point is not only to publish a final list of
> 20 locations; it is to let reviewers and collaborators inspect why those 20 were chosen,
> compare preferred alternatives, and rerun the selection under different assumptions.
> With modest support I can move it from demo to production: ingest the full national
> datasets, integrate with NREL ResStock / OpenStudio, and add the weather-QC and
> geography layers needed for real studies. I've attached a one-page roadmap
> (PRODUCTION_ROADMAP.md). Could we find 20 minutes to talk?
