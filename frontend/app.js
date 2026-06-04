const pages = [
  ["overview", "Overview dashboard", "⌂", "National decision support"],
  ["zip", "ZIP code explorer", "⌕", "Transparent geography resolution"],
  ["scenario", "Scenario builder", "◈", "Reproducible configuration"],
  ["ranking", "Candidate ranking", "≡", "Inspectable candidate universe"],
  ["allocation", "Allocation comparison", "⇄", "Coverage and score tradeoffs"],
  ["methodology", "Methodology & sources", "§", "Academic methods appendix"],
];

const climateColors = {
  "Cold & Very Cold": "#3977a8",
  "Hot-Dry & Mixed Dry": "#c99a38",
  "Hot-Humid": "#0a9690",
  Marine: "#786ba8",
  "Mixed-Humid": "#b7594d",
};
const app = {
  page: "overview",
  dashboard: null,
  zip: null,
  zipHistory: ["19104", "02108", "98290"],
  scenario: null,
  candidates: null,
  compare: [],
  mapLayers: { stations: true, lines: true, catchments: true },
  tableSort: ["location_score", "desc"],
};

const $ = (selector) => document.querySelector(selector);
const workspace = $("#workspace");
const esc = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
const num = (value, digits = 0) =>
  Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
const pct = (value, digits = 0) => `${num(Number(value || 0) * 100, digits)}%`;
const score = (value) => Number(value || 0).toFixed(3);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const type = response.headers.get("content-type") || "";
  if (!response.ok) {
    const payload = type.includes("json") ? await response.json() : { error: await response.text() };
    throw new Error(payload.error || "Request failed.");
  }
  return type.includes("json") ? response.json() : response.text();
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.classList.remove("show"), 3200);
}

function setScenarioPill(name = "Baseline research scenario") {
  document.querySelector(".scenario-pill").innerHTML = `<i></i> ${esc(name)}`;
}

function setHeader(page) {
  const meta = pages.find(([id]) => id === page);
  $("#page-title").textContent = meta[1];
  $("#page-kicker").textContent = meta[3];
  document.title = `${meta[1]} · Representative Location Explorer`;
}

function closeSidebar() {
  document.querySelector(".sidebar").classList.remove("open");
  const backdrop = $("#sidebar-backdrop");
  if (backdrop) backdrop.hidden = true;
  const menu = $("#mobile-menu");
  if (menu) menu.setAttribute("aria-expanded", "false");
}

function openSidebar() {
  document.querySelector(".sidebar").classList.add("open");
  const backdrop = $("#sidebar-backdrop");
  if (backdrop) backdrop.hidden = false;
  $("#mobile-menu").setAttribute("aria-expanded", "true");
}

function renderNav() {
  $("#primary-nav").innerHTML = pages
    .map(
      ([id, label, icon]) => `
        <button class="nav-item ${id === app.page ? "active" : ""}" data-page="${id}"${id === app.page ? ' aria-current="page"' : ""}>
          <span class="nav-icon" aria-hidden="true">${icon}</span><span>${label}</span>
        </button>`,
    )
    .join("");
  document.querySelectorAll(".nav-item").forEach((button) =>
    button.addEventListener("click", () => {
      app.page = button.dataset.page;
      closeSidebar();
      setHeader(app.page);
      renderNav();
      render();
    }),
  );
}

function intro(title, copy, actions = "") {
  return `<div class="page-intro"><div><p class="eyebrow">Representative Location Explorer</p><h3>${title}</h3><p>${copy}</p></div>${actions ? `<div class="actions">${actions}</div>` : ""}</div>`;
}

function kpi(label, value, note, tone = "", tip = "") {
  return `<article class="kpi ${tone}" title="${esc(tip || note)}"><p class="kpi-label">${label} <span aria-hidden="true">ⓘ</span></p><p class="kpi-value">${value}</p><p class="kpi-note">${note}</p></article>`;
}

function badge(text, tone = "") {
  return `<span class="badge ${tone}">${esc(text)}</span>`;
}

function project(lon, lat) {
  return [((Number(lon) + 126) / 60) * 840, ((50.5 - Number(lat)) / 27) * 430 + 12];
}

function mapSvg(rows, options = {}) {
  const layers = app.mapLayers;
  const uniqueRows = rows.filter((row) => Number.isFinite(Number(row.centroid_lon)) && Number.isFinite(Number(row.centroid_lat)));
  const lines = layers.lines
    ? uniqueRows
        .map((row) => {
          const [x1, y1] = project(row.centroid_lon, row.centroid_lat);
          const [x2, y2] = project(row.selected_station_lon, row.selected_station_lat);
          return `<line class="station-line" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;
        })
        .join("")
    : "";
  const stations = layers.stations
    ? uniqueRows
        .map((row) => {
          const [x, y] = project(row.selected_station_lon, row.selected_station_lat);
          return `<circle class="station" cx="${x}" cy="${y}" r="3.3"><title>${esc(row.selected_station_name)} · ${num(row.station_distance_miles, 1)} mi from target centroid</title></circle>`;
        })
        .join("")
    : "";
  const catches = layers.catchments
    ? uniqueRows
        .map((row) => {
          const [x, y] = project(row.centroid_lon, row.centroid_lat);
          const fill = climateColors[row.climate_region] || "#0a9690";
          return `<circle class="catchment" cx="${x}" cy="${y}" r="${options.highlight === row.location_uniqueness_key ? 8 : 5.5}" fill="${fill}"><title>${esc(row.catchment_label)} · ${esc(row.urbanicity_short)} · score ${score(row.scenario_score ?? row.location_score)}</title></circle>`;
        })
        .join("")
    : "";
  let zip = "";
  if (options.zip) {
    const [x, y] = project(options.zip.longitude, options.zip.latitude);
    zip = `<circle class="zip" cx="${x}" cy="${y}" r="7"><title>ZIP ${esc(options.zip.zip_code)}</title></circle>`;
  }
  return `
    <div class="layer-toggles" role="group" aria-label="Map layers">
      ${Object.entries({ catchments: "Target catchments", stations: "Weather stations", lines: "Station-distance lines" })
        .map(([key, label]) => `<label><input type="checkbox" data-layer="${key}" ${layers[key] ? "checked" : ""}> ${label}</label>`)
        .join("")}
    </div>
    <div class="map-wrap">
      <svg class="map" viewBox="0 0 840 460" role="img" aria-label="Selected target catchments and weather stations across the contiguous United States">
        <path class="us-outline" d="M44 83 L103 61 L174 63 L211 81 L262 80 L305 93 L355 102 L403 88 L463 101 L512 82 L579 85 L632 104 L697 91 L758 122 L797 183 L771 223 L744 245 L730 301 L690 318 L665 345 L629 336 L602 287 L568 276 L541 251 L507 267 L474 255 L446 277 L415 252 L380 271 L347 260 L310 282 L274 262 L247 273 L222 238 L188 238 L163 214 L133 206 L116 173 L72 163 Z"></path>
        <path class="us-outline" d="M657 350 L679 361 L690 394 L681 430 L667 416 L658 385 Z"></path>
        ${lines}${stations}${catches}${zip}
      </svg>
      <div class="map-legend">
        ${Object.entries(climateColors).map(([name, color]) => `<div class="legend-row"><span class="legend-dot" style="background:${color}"></span>${esc(name)}</div>`).join("")}
        <div class="legend-row"><span class="legend-dot" style="background:#17364a"></span>Weather station</div>
      </div>
    </div>`;
}

function bindMapLayers(rerender) {
  document.querySelectorAll("[data-layer]").forEach((input) =>
    input.addEventListener("change", () => {
      app.mapLayers[input.dataset.layer] = input.checked;
      rerender();
    }),
  );
}

function barChart(data, tone = "") {
  const max = Math.max(...Object.values(data), 1);
  return `<div class="bar-chart">${Object.entries(data)
    .map(
      ([label, value]) => `
        <div class="bar-row"><span>${esc(label)}</span><div class="bar-track"><div class="bar-fill ${tone}" style="width:${(value / max) * 100}%"></div></div><strong>${value}</strong></div>`,
    )
    .join("")}</div>`;
}

function histogram(data, ariaLabel = "Selected location score distribution") {
  const max = Math.max(...data.map((item) => item.count), 1);
  return `<svg class="chart-svg" viewBox="0 0 500 170" role="img" aria-label="${esc(ariaLabel)}">
    <line class="chart-axis" x1="34" y1="140" x2="484" y2="140"/>
    ${data
      .map((item, index) => {
        const height = (item.count / max) * 105;
        const x = 54 + index * 86;
        return `<rect x="${x}" y="${140 - height}" width="52" height="${height}" rx="4" fill="#0a9690"><title>${item.label}: ${item.count} locations</title></rect>
          <text class="chart-label" x="${x + 26}" y="157" text-anchor="middle">${item.label}</text><text class="chart-label" x="${x + 26}" y="${132 - height}" text-anchor="middle">${item.count}</text>`;
      })
      .join("")}
  </svg>`;
}

function distanceChart(rows) {
  const bins = [0, 0, 0, 0, 0];
  rows.forEach((row) => bins[Math.min(Math.floor(Number(row.station_distance_miles) / 10), 4)]++);
  return histogram(bins.map((count, index) => ({ label: index === 4 ? "40+" : `${index * 10}-${(index + 1) * 10}`, count })), "Selected weather-station distance distribution");
}

function scoreBars(row) {
  const metrics = [
    ["Housing-unit coverage", row.housing_unit_coverage_percentile, "45% baseline weight"],
    ["Population density", row.population_density_percentile, "35% baseline weight"],
    ["Population coverage", row.population_coverage_percentile, "20% baseline weight"],
  ];
  return `<div class="bar-chart">${metrics
    .map(
      ([label, value, weight]) => `<div class="bar-row"><span title="${weight}">${label}</span><div class="bar-track"><div class="bar-fill" style="width:${Number(value) * 100}%"></div></div><strong>${pct(value)}</strong></div>`,
    )
    .join("")}</div>`;
}

function overview() {
  const { kpis, scenario, climate_distribution, urbanicity_distribution, score_distribution } = app.dashboard;
  const selected = scenario.selected;
  workspace.innerHTML = `
    ${intro("A reproducible national location strategy", "Explore how 20 representative target catchments are selected across five climate regions and four urbanicity categories. Building-stock geography, ZIP entry points, and weather stations stay deliberately separate.")}
    <div class="info-banner"><strong>Current scenario.</strong><span>Density-screened candidates at or above the 60th percentile are scored with the baseline 45 / 35 / 20 formula. Distinct target catchments are maximized, with a documented Philadelphia research-priority override for Mixed-Humid HDU.</span></div>
    <section class="kpi-grid">
      ${kpi("Target strata", kpis.target_strata, "5 climate regions × 4 urbanicity categories", "teal")}
      ${kpi("Distinct locations", kpis.distinct_locations, "Represented target catchments", "teal")}
      ${kpi("Candidate universe", num(kpis.candidate_count), "Inspectable scored catchments")}
      ${kpi("Verified filters", `${kpis.verified_filter_count}/20`, "Exact ResStock enumeration values", "teal")}
      ${kpi("Weather QC complete", `${kpis.weather_qc_complete_count}/20`, "Hourly completeness remains pre-simulation QC", "gold")}
    </section>
    <section class="grid two">
      <article class="card">
        <div class="card-header"><div><h4>National target catchments and climate stations</h4><p class="card-subtitle">Target markers use climate-region color. Dark station markers remain separate climate-source locations.</p></div>${badge("20 selected", "teal")}</div>
        ${mapSvg(selected)}
      </article>
      <div class="stack">
        <article class="card"><div class="card-header"><div><h4>Selected sites by climate region</h4><p class="card-subtitle">Balanced representation across the five climate regions.</p></div></div>${barChart(climate_distribution)}</article>
        <article class="card"><div class="card-header"><div><h4>Urbanicity mix</h4><p class="card-subtitle">Each climate region contributes one site per urbanicity stratum.</p></div></div>${barChart(urbanicity_distribution, "blue")}</article>
      </div>
    </section>
    <section class="grid equal" style="margin-top:16px">
      <article class="card"><div class="card-header"><div><h4>Composite-score distribution</h4><p class="card-subtitle">Selected-site scores after the density screen.</p></div></div>${histogram(score_distribution)}</article>
      <article class="card"><div class="card-header"><div><h4>Station-distance distribution</h4><p class="card-subtitle">Miles between target catchment centroids and selected climate stations.</p></div>${badge("QC pending", "gold")}</div>${distanceChart(selected)}</article>
    </section>
    <section class="card" style="margin-top:16px">
      <div class="card-header"><div><h4>Research-priority overrides</h4><p class="card-subtitle">Overrides are explicit, removable, and retained in the scenario audit trail.</p></div>${badge("1 active", "gold")}</div>
      <div class="priority-card"><div class="badge-row">${badge("Mixed-Humid", "navy")}${badge("HDU")}${badge("Research priority", "gold")}</div><p><strong>Philadelphia-Camden-Wilmington, PA-NJ-DE-MD</strong><br>Unconstrained rank 2 · score ${score(selected.find(row => row.catchment_code === "37980")?.scenario_score)} · selected because the team has stronger local heat-health data coverage in Philadelphia.</p></div>
    </section>`;
  bindMapLayers(overview);
}

function zipExplorer() {
  workspace.innerHTML = `
    ${intro("Resolve a ZIP code without blurring geographic boundaries", "A USPS ZIP code begins the search. The explorer documents the linked Census-compatible geography, analytical catchment, uncertainty, and weather-station context before any simulation filter is proposed.")}
    <article class="card">
      <div class="card-header"><div><h4>ZIP code search</h4><p class="card-subtitle">Try demonstration records: 19104, 02108, 10001, 33130, 90012, 95501, or rural 98290.</p></div>${badge("Leading zeros preserved", "teal")}</div>
      <form id="zip-form" class="search-panel">
        <input class="text-input" id="zip-input" inputmode="numeric" maxlength="5" pattern="[0-9]{5}" placeholder="19104" aria-label="ZIP code" required>
        <button class="button" type="submit">Resolve ZIP</button>
      </form>
      <div class="history"><span>Recent:</span>${app.zipHistory.map(zip => `<button type="button" data-zip="${zip}">${zip}</button>`).join("")}</div>
    </article>
    <div id="zip-result" style="margin-top:16px">${app.zip ? renderZipResult(app.zip) : `<div class="empty-state card"><div><h4>Start with a five-digit ZIP code</h4><p>Resolution details and score context will appear here.</p></div></div>`}</div>`;
  $("#zip-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    resolveZip($("#zip-input").value);
  });
  document.querySelectorAll("[data-zip]").forEach((button) => button.addEventListener("click", () => resolveZip(button.dataset.zip)));
  if (app.zip) bindMapLayers(zipExplorer);
}

async function resolveZip(zip) {
  const input = String(zip).trim();
  if (!/^\d{5}$/.test(input)) return toast("Enter a five-digit ZIP code. Leading zeros are preserved.");
  $("#zip-result").innerHTML = `<div class="loading-state card"><div class="spinner"></div><p>Resolving ${esc(input)}…</p></div>`;
  try {
    app.zip = await api(`/api/zip/${input}`);
    app.zipHistory = [input, ...app.zipHistory.filter((item) => item !== input)].slice(0, 5);
    zipExplorer();
  } catch (error) {
    $("#zip-result").innerHTML = `<div class="info-banner coral"><strong>ZIP not resolved.</strong><span>${esc(error.message)}</span></div>`;
  }
}

function renderZipResult(result) {
  const r = result.resolved;
  const candidate = result.candidate;
  const selected = result.selected_representative;
  const rows = candidate ? [{ ...candidate, location_uniqueness_key: `${candidate.catchment_type}:${candidate.catchment_code}` }] : [];
  return `
    <div class="info-banner gold"><strong>ZIP is an entry point.</strong><span>${esc(result.simulation_filter_geography.explanation)}</span></div>
    <section class="grid two">
      <div class="stack">
        <article class="card">
          <div class="card-header"><div><h4>Resolved geography · ${esc(result.zip_code)}</h4><p class="card-subtitle">${esc(r.source_version)}</p></div>${badge(r.match_type, "teal")}</div>
          <div class="badge-row">${badge(r.climate_region, "navy")}${badge(r.urbanicity_short, "teal")}${badge(`${num(r.allocation_ratio * 100)}% allocation`, "gold")}</div>
          <div class="details-grid" style="margin-top:10px">
            <div class="metric"><span>ZCTA</span><strong>${esc(r.zcta)}</strong></div><div class="metric"><span>State</span><strong>${esc(r.state)}</strong></div>
            <div class="metric"><span>County</span><strong>${esc(r.county_geoid)} · ${esc(r.county_label)}</strong></div><div class="metric"><span>CBSA</span><strong>${esc(r.cbsa_code || "Outside CBSA")}</strong></div>
            <div class="metric"><span>Target boundary</span><strong>${esc(result.simulation_filter_geography.boundary_type)} ${esc(result.simulation_filter_geography.boundary_code)}</strong></div><div class="metric"><span>Crosswalk matches</span><strong>${result.crosswalk_matches.length}</strong></div>
          </div>
          <details open><summary>Crosswalk uncertainty and limitations</summary><p>${esc(r.uncertainty_note)} The bundled subset is for demonstration; use a documented quarterly HUD-USPS refresh for national ZIP search.</p></details>
        </article>
        <article class="card">
          <div class="card-header"><div><h4>Analytical catchment score</h4><p class="card-subtitle">${candidate ? esc(candidate.catchment_label) : "The resolved search geography is not represented in the analytical candidate table."}</p></div>${candidate ? badge(`Score ${score(candidate.location_score)}`, "teal") : badge("No candidate", "coral")}</div>
          ${candidate ? `${scoreBars(candidate)}<details><summary>Why this score?</summary><p>The score combines housing-unit coverage percentile (45%), within-stratum population-density percentile (35%), and population-coverage percentile (20%). The ZIP does not receive a score directly; the candidate target catchment does.</p></details>` : `<p class="card-subtitle">Candidate scores are computed at CBSA urban/suburban or county rural catchment scope.</p>`}
        </article>
        <article class="card">
          <div class="card-header"><div><h4>Selected representative comparison</h4><p class="card-subtitle">${esc(r.climate_region)} · ${esc(r.urbanicity_short)}</p></div></div>
          <div class="metric"><span>Current representative</span><strong>${esc(selected?.catchment_label || "Unavailable")}</strong></div>
          <div class="metric"><span>Composite score</span><strong>${score(selected?.location_score)}</strong></div>
          <div class="metric"><span>Weather station</span><strong>${esc(selected?.selected_station_name || "Unavailable")}</strong></div>
          <div class="metric"><span>Relationship</span><strong>${candidate && selected && candidate.catchment_code === selected.catchment_code ? "Resolved catchment is selected" : "Compare against selected alternative"}</strong></div>
        </article>
      </div>
      <div class="stack">
        <article class="card"><div class="card-header"><div><h4>Resolved-area map</h4><p class="card-subtitle">Gold shows the ZIP entry point. Catchment and station remain separate.</p></div></div>${mapSvg(rows.length ? rows : selected ? [{ ...selected, location_uniqueness_key: `${selected.catchment_type}:${selected.catchment_code}` }] : [], { zip: { ...r, zip_code: result.zip_code } })}</article>
        <article class="card"><div class="card-header"><div><h4>Nearby weather stations</h4><p class="card-subtitle">Climate-source context only. Hourly completeness remains a separate QC step.</p></div>${badge("QC pending", "gold")}</div><div class="station-list">${result.nearby_weather_stations.map((station) => `<div class="station-item"><div><p>${esc(station.station_name)}</p><small>Station ${esc(station.station_number)}</small></div><div>${badge(`${num(station.distance_from_zip_miles, 1)} mi`)} ${badge(station.weather_qc_status, "gold")}</div></div>`).join("")}</div></article>
      </div>
    </section>`;
}

function scenarioBuilder() {
  const result = app.scenario || app.dashboard.scenario;
  const config = result.config;
  const overrides = config.overrides || [];
  workspace.innerHTML = `
    ${intro("Test methodological choices before saving a scenario", "Adjust the density screen, scoring weights, uniqueness constraint, weather-distance rules, and research priorities. Every result is deterministic and exportable as a versioned scenario.", `<button class="button secondary" id="export-scenario">Export scenario JSON</button><button class="button" id="export-sites">Export site list CSV</button>`)}
    <section class="grid two">
      <div class="stack">
        <article class="card">
          <div class="card-header"><div><h4>Screening and score formula</h4><p class="card-subtitle">Weights must sum to 100%. Live results refresh after changes.</p></div><div style="display:flex;gap:8px;align-items:center"><button type="button" class="normalize-button" id="normalize-weights" hidden>Normalize to 100%</button><span id="weight-badge">${badge("100% allocated", "teal")}</span></div></div>
          <div class="form-grid">
            <div class="form-group"><label>Density-screen percentile <output id="density-output">${pct(config.density_screen_percentile)}</output></label><input id="density" type="range" min="0" max="0.95" step="0.05" value="${config.density_screen_percentile}"></div>
            <div class="form-group"><label>Maximum station distance <output id="distance-output">${num(config.max_station_distance_miles)} mi</output></label><input id="max-distance" type="range" min="25" max="500" step="25" value="${config.max_station_distance_miles}"></div>
            <div class="form-group"><label>Housing-unit coverage <output id="housing-output">${pct(config.weights.housing_unit_coverage_percentile)}</output></label><input id="housing" type="range" min="0" max="1" step="0.05" value="${config.weights.housing_unit_coverage_percentile}"></div>
            <div class="form-group"><label>Population density <output id="population-density-output">${pct(config.weights.population_density_percentile)}</output></label><input id="population-density" type="range" min="0" max="1" step="0.05" value="${config.weights.population_density_percentile}"></div>
            <div class="form-group"><label>Population coverage <output id="population-output">${pct(config.weights.population_coverage_percentile)}</output></label><input id="population" type="range" min="0" max="1" step="0.05" value="${config.weights.population_coverage_percentile}"></div>
            <div class="form-group"><label>Station-distance penalty <output id="penalty-output">${pct(config.station_distance_penalty)}</output></label><input id="penalty" type="range" min="0" max="0.25" step="0.01" value="${config.station_distance_penalty}"></div>
          </div>
          <div class="weight-warning" id="weight-warning" role="status" hidden></div>
        </article>
        <article class="card">
          <div class="card-header"><div><h4>Allocation and weather rules</h4><p class="card-subtitle">Weather eligibility is deliberately separate from catchment scoring.</p></div></div>
          <label class="check-line"><input id="unique" type="checkbox" ${config.unique_location_constraint ? "checked" : ""}><span><strong>Require distinct target catchments</strong><br>Maximize national representation while retaining the strongest feasible combined score.</span></label>
          <label class="check-line"><input id="qc" type="checkbox" ${config.require_weather_qc ? "checked" : ""}><span><strong>Require complete hourly weather QC</strong><br>Disabled by default because the current source workbook does not contain hourly completeness metrics.</span></label>
        </article>
        <article class="card">
          <div class="card-header"><div><h4>Research-priority override</h4><p class="card-subtitle">The initial scenario documents Philadelphia. Clear the checkbox to remove it.</p></div>${badge("Audit trail", "gold")}</div>
          <label class="check-line"><input id="override-enabled" type="checkbox" ${overrides.length ? "checked" : ""}><span><strong>Apply Mixed-Humid HDU research priority</strong><br>Seed Philadelphia-Camden-Wilmington because local heat-health data coverage is stronger.</span></label>
          <div class="override-editor">
            <label class="field-label">Climate region<input class="text-input" value="Mixed-Humid" disabled></label>
            <label class="field-label">Urbanicity<input class="text-input" value="higher density urban" disabled></label>
            <label class="field-label">CBSA code<input class="text-input" id="override-code" value="${esc(overrides[0]?.catchment_code || "37980")}" maxlength="5"></label>
            <span>${badge("Editable", "gold")}</span>
          </div>
        </article>
      </div>
      <div class="stack" id="scenario-live">${renderScenarioLive(result)}</div>
    </section>`;
  bindScenarioEvents();
  $("#export-scenario").addEventListener("click", () => download("representative-location-scenario.json", JSON.stringify((app.scenario || app.dashboard.scenario).config, null, 2), "application/json"));
  $("#export-sites").addEventListener("click", exportSites);
}

function scenarioPayload() {
  const enabled = $("#override-enabled").checked;
  return {
    version: "1.0",
    name: "User-defined scenario",
    density_screen_percentile: Number($("#density").value),
    max_station_distance_miles: Number($("#max-distance").value),
    station_distance_penalty: Number($("#penalty").value),
    unique_location_constraint: $("#unique").checked,
    require_weather_qc: $("#qc").checked,
    weights: {
      housing_unit_coverage_percentile: Number($("#housing").value),
      population_density_percentile: Number($("#population-density").value),
      population_coverage_percentile: Number($("#population").value),
    },
    overrides: enabled
      ? [{
          climate_region: "Mixed-Humid",
          urbanicity: "higher density urban",
          catchment_type: "CBSA",
          catchment_code: $("#override-code").value,
          rationale: "Research-priority override: Philadelphia has stronger local heat-health data coverage for the project team.",
        }]
      : [],
  };
}

function refreshWeightState() {
  $("#density-output").textContent = pct($("#density").value);
  $("#distance-output").textContent = `${num($("#max-distance").value)} mi`;
  $("#housing-output").textContent = pct($("#housing").value);
  $("#population-density-output").textContent = pct($("#population-density").value);
  $("#population-output").textContent = pct($("#population").value);
  $("#penalty-output").textContent = pct($("#penalty").value);
  const total = Number($("#housing").value) + Number($("#population-density").value) + Number($("#population").value);
  const balanced = Math.abs(total - 1) < 0.001;
  $("#weight-badge").innerHTML = balanced ? badge("100% allocated", "teal") : badge(`${pct(total)} allocated`, "coral");
  const normalize = $("#normalize-weights");
  const warning = $("#weight-warning");
  if (normalize) normalize.hidden = balanced;
  if (warning) {
    warning.hidden = balanced;
    warning.textContent = balanced ? "" : "Score weights must total 100% before the scenario can be evaluated. Use “Normalize to 100%”, or adjust the three weight sliders.";
  }
  return balanced;
}

function bindScenarioEvents() {
  let timer;
  document.querySelectorAll("#density,#max-distance,#housing,#population-density,#population,#penalty,#unique,#qc,#override-enabled,#override-code").forEach((input) =>
    input.addEventListener("input", () => {
      const balanced = refreshWeightState();
      clearTimeout(timer);
      if (balanced) timer = setTimeout(evaluateScenario, 300);
    }),
  );
  $("#normalize-weights")?.addEventListener("click", () => {
    const ids = ["#housing", "#population-density", "#population"];
    const total = ids.reduce((sum, id) => sum + Number($(id).value), 0);
    if (total <= 0) {
      ids.forEach((id) => ($(id).value = 1 / 3));
    } else {
      ids.forEach((id) => ($(id).value = Number($(id).value) / total));
    }
    if (refreshWeightState()) evaluateScenario();
  });
}

async function evaluateScenario() {
  $("#scenario-live").innerHTML = `<article class="card loading-state"><div class="spinner"></div><p>Evaluating scenario…</p></article>`;
  try {
    app.scenario = await api("/api/scenarios/evaluate", { method: "POST", body: JSON.stringify(scenarioPayload()) });
    setScenarioPill("User-defined scenario");
    $("#scenario-live").innerHTML = renderScenarioLive(app.scenario);
  } catch (error) {
    $("#scenario-live").innerHTML = `<div class="info-banner coral"><strong>Scenario cannot be evaluated.</strong><span>${esc(error.message)}</span></div>`;
  }
}

function renderScenarioLive(result) {
  const s = result.summary;
  return `
    <article class="card">
      <div class="card-header"><div><h4>Live allocation result</h4><p class="card-subtitle">Deterministic preview before scenario export.</p></div>${badge(`${s.strata_count} strata`, "teal")}</div>
      <section class="grid equal">
        ${kpi("Distinct catchments", s.represented_location_count, "Target locations represented", "teal")}
        ${kpi("Eligible candidates", num(s.eligible_candidate_count), "After scenario screening")}
        ${kpi("Combined score", num(s.combined_score, 3), "Across 20 assignments")}
        ${kpi("Changed assignments", s.changed_assignment_count, "Versus independent tops", "gold")}
      </section>
    </article>
    <article class="card">
      <div class="card-header"><div><h4>Scenario cautions</h4><p class="card-subtitle">A simulation export is not a weather-QC clearance.</p></div></div>
      <div class="info-banner gold"><strong>${result.selected.filter(row => !row.nrel_value_verified).length} filter mapping(s) require review.</strong><span>Any new scenario alternative without a curated enumeration mapping stays visibly blocked for simulation handoff.</span></div>
      <div class="metric"><span>Hourly weather completeness</span><strong>Separate pre-simulation QC</strong></div>
      <div class="metric"><span>Scenario version</span><strong>${esc(result.config.version)}</strong></div>
      <div class="metric"><span>Score difference vs independent top</span><strong>${num(s.score_difference, 3)}</strong></div>
    </article>
    <article class="card"><div class="card-header"><div><h4>Assignment changes</h4><p class="card-subtitle">Transparent substitutions from independent top-ranked candidates.</p></div></div>
      <div class="change-list">${result.changes.length ? result.changes.map(change => `<div class="change-item"><h5>${esc(change.climate_region)} · ${esc(change.urbanicity_short)}</h5><p>${esc(change.from_label)} → <strong>${esc(change.to_label)}</strong><br>Score difference: −${num(change.score_loss, 3)}. ${esc(change.reason)}</p></div>`).join("") : `<p class="card-subtitle">No assignments differ from independent top-ranked candidates.</p>`}</div>
    </article>`;
}

function sortableTh(label, key) {
  const [column, direction] = app.tableSort;
  const ariaSort = column === key ? (direction === "asc" ? "ascending" : "descending") : "none";
  return `<th scope="col" data-sort="${key}" role="columnheader" aria-sort="${ariaSort}" tabindex="0" title="Sort by ${esc(label)}">${esc(label)}<span class="sort-caret" aria-hidden="true"></span></th>`;
}

function applySortIndicators() {
  const [column, direction] = app.tableSort;
  document.querySelectorAll("th[data-sort]").forEach((header) =>
    header.setAttribute("aria-sort", header.dataset.sort === column ? (direction === "asc" ? "ascending" : "descending") : "none"),
  );
}

async function loadCandidates() {
  workspace.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading candidate table…</p></div>`;
  app.candidates = await api("/api/candidates?limit=3000");
  candidateRanking();
}

function candidateRanking() {
  if (!app.candidates) return loadCandidates();
  const rows = sortedCandidates(app.candidates.rows);
  workspace.innerHTML = `
    ${intro("Inspect every scored candidate", "Search, sort, filter, export, and compare target catchments. Exact ResStock values remain visibly verified only where an enumeration mapping has been curated.", `<button class="button secondary" id="export-ranking">Export visible CSV</button>`)}
    <section class="card">
      <div class="table-toolbar">
        <input id="rank-search" class="text-input" placeholder="Search catchment, code, or station">
        <select id="rank-climate"><option value="">All climate regions</option>${Object.keys(climateColors).map(value => `<option>${esc(value)}</option>`).join("")}</select>
        <select id="rank-urbanicity"><option value="">All urbanicity categories</option>${["HDU", "LDU", "Suburban", "Rural"].map(value => `<option>${value}</option>`).join("")}</select>
        <select id="rank-selected"><option value="">All candidates</option><option value="selected">Selected only</option><option value="verified">Verified filter only</option></select>
        <span>${badge(`${num(rows.length)} candidates`, "teal")}</span>
      </div>
      <div class="table-wrap"><table><thead><tr>
        <th scope="col">Compare</th>${sortableTh("Climate", "climate_region")}${sortableTh("Urbanicity", "urbanicity_short")}${sortableTh("Candidate catchment", "catchment_label")}<th scope="col">Boundary</th>${sortableTh("Population", "population_2010")}${sortableTh("Housing units", "housing_units_2010")}${sortableTh("Pop. density", "population_density_sqmi")}${sortableTh("HU density", "housing_unit_density_sqmi")}${sortableTh("Score", "location_score")}${sortableTh("Rank", "selection_rank")}<th scope="col">Selected</th><th scope="col">Weather station</th>${sortableTh("Station mi", "station_distance_miles")}<th scope="col">NREL filter</th><th scope="col">Verified</th>
      </tr></thead><tbody id="ranking-body">${rankingRows(rows.slice(0, 700))}</tbody></table></div>
      <p class="card-subtitle" id="ranking-note">Showing ${num(Math.min(rows.length, 700))} of ${num(rows.length)} locally loaded candidates.</p>
    </section>
    <section class="grid equal" style="margin-top:16px">
      <article class="card"><div class="card-header"><div><h4>Candidate density and score scatter</h4><p class="card-subtitle">Population density on the x-axis; composite score on the y-axis. Showing the filtered view.</p></div></div><div id="scatter">${scatter(rows.slice(0, 700))}</div></article>
      <article class="card"><div class="card-header"><div><h4>Side-by-side comparison</h4><p class="card-subtitle">Select up to two table rows.</p></div>${badge(`${app.compare.length}/2 selected`)}</div><div id="candidate-compare">${renderCandidateCompare()}</div></article>
    </section>`;
  bindRankingEvents();
}

function rankingRows(rows) {
  return rows
    .map(
      (row) => `<tr class="${row.baseline_selected ? "selected-row" : ""}">
      <td><input type="checkbox" aria-label="Compare ${esc(row.catchment_label)}" data-compare="${esc(row.location_uniqueness_key)}|${esc(row.climate_region)}|${esc(row.urbanicity)}" ${app.compare.some(item => item.location_uniqueness_key === row.location_uniqueness_key && item.climate_region === row.climate_region && item.urbanicity === row.urbanicity) ? "checked" : ""}></td>
      <td>${esc(row.climate_region)}</td><td>${badge(row.urbanicity_short)}</td><td title="${esc(row.catchment_label)}">${esc(row.catchment_label)}</td><td>${esc(row.catchment_type)} ${esc(row.catchment_code)}</td>
      <td>${num(row.population_2010)}</td><td>${num(row.housing_units_2010)}</td><td>${num(row.population_density_sqmi, 1)}</td><td>${num(row.housing_unit_density_sqmi, 1)}</td><td>${score(row.location_score)}</td><td>${row.selection_rank || "—"}</td>
      <td>${row.baseline_selected ? badge("Selected", "teal") : "—"}</td><td title="${esc(row.selected_station_name)}">${esc(row.selected_station_name)}</td><td>${num(row.station_distance_miles, 1)}</td><td title="${esc(row.nrel_filter_value || "Mapping required")}">${esc(row.nrel_filter_field)}</td><td>${row.nrel_value_verified ? badge("Verified", "teal") : badge("Review", "gold")}</td>
    </tr>`,
    )
    .join("");
}

function sortedCandidates(rows) {
  const [column, direction] = app.tableSort;
  return [...rows].sort((a, b) => {
    const av = a[column] ?? "";
    const bv = b[column] ?? "";
    const result = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv), undefined, { numeric: true });
    return direction === "asc" ? result : -result;
  });
}

function filteredCandidates() {
  const query = ($("#rank-search")?.value || "").toLowerCase();
  const climate = $("#rank-climate")?.value || "";
  const urbanicity = $("#rank-urbanicity")?.value || "";
  const selected = $("#rank-selected")?.value || "";
  return sortedCandidates(app.candidates.rows.filter((row) => {
    if (query && !`${row.catchment_label} ${row.catchment_code} ${row.selected_station_name}`.toLowerCase().includes(query)) return false;
    if (climate && row.climate_region !== climate) return false;
    if (urbanicity && row.urbanicity_short !== urbanicity) return false;
    if (selected === "selected" && !row.baseline_selected) return false;
    if (selected === "verified" && !row.nrel_value_verified) return false;
    return true;
  }));
}

function refreshRankingBody() {
  const rows = filteredCandidates();
  $("#ranking-body").innerHTML = rankingRows(rows.slice(0, 700));
  $("#ranking-note").textContent = `Showing ${num(Math.min(rows.length, 700))} of ${num(rows.length)} filtered candidates.`;
  $("#scatter").innerHTML = scatter(rows.slice(0, 700));
  applySortIndicators();
  bindCompareInputs();
}

function sortByColumn(column) {
  app.tableSort = [column, app.tableSort[0] === column && app.tableSort[1] === "desc" ? "asc" : "desc"];
  refreshRankingBody();
}

function bindRankingEvents() {
  ["#rank-search", "#rank-climate", "#rank-urbanicity", "#rank-selected"].forEach((selector) => $(selector).addEventListener("input", refreshRankingBody));
  document.querySelectorAll("[data-sort]").forEach((header) => {
    header.addEventListener("click", () => sortByColumn(header.dataset.sort));
    header.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        sortByColumn(header.dataset.sort);
      }
    });
  });
  $("#export-ranking").addEventListener("click", () => downloadCsv("candidate-ranking.csv", filteredCandidates()));
  bindCompareInputs();
}

function bindCompareInputs() {
  document.querySelectorAll("[data-compare]").forEach((checkbox) =>
    checkbox.addEventListener("change", () => {
      const [key, climate, urbanicity] = checkbox.dataset.compare.split("|");
      const row = app.candidates.rows.find(item => item.location_uniqueness_key === key && item.climate_region === climate && item.urbanicity === urbanicity);
      app.compare = checkbox.checked ? [...app.compare.filter(item => item !== row), row].slice(-2) : app.compare.filter(item => item !== row);
      $("#candidate-compare").innerHTML = renderCandidateCompare();
      refreshRankingBody();
    }),
  );
}

function renderCandidateCompare() {
  if (!app.compare.length) return `<div class="empty-state" style="min-height:210px"><p>Choose one or two candidate rows to compare.</p></div>`;
  return `<div class="comparison-grid">${app.compare.map(row => `<div class="compare-card"><h5>${esc(row.catchment_label)}</h5><div class="badge-row">${badge(row.climate_region, "navy")}${badge(row.urbanicity_short, "teal")}</div><p><strong>Composite score:</strong> ${score(row.location_score)}</p><p><strong>Density:</strong> ${num(row.population_density_sqmi, 1)} people / sq mi</p><p><strong>Housing units:</strong> ${num(row.housing_units_2010)}</p><p><strong>Station:</strong> ${esc(row.selected_station_name)} · ${num(row.station_distance_miles, 1)} mi</p><p><strong>ResStock:</strong> ${row.nrel_value_verified ? "Verified" : "Review required"}</p></div>`).join("")}</div>`;
}

function scatter(rows) {
  const maxX = Math.max(...rows.map(row => Number(row.population_density_sqmi)), 1);
  return `<svg class="chart-svg" viewBox="0 0 520 210" role="img" aria-label="Population density versus composite score scatter plot">
    <line class="chart-axis" x1="36" y1="178" x2="505" y2="178"/><line class="chart-axis" x1="36" y1="18" x2="36" y2="178"/>
    ${rows.map(row => {
      const x = 40 + Math.sqrt(Number(row.population_density_sqmi) / maxX) * 455;
      const y = 174 - Number(row.location_score) * 150;
      return `<circle cx="${x}" cy="${y}" r="${row.baseline_selected ? 4 : 2.2}" fill="${climateColors[row.climate_region]}" opacity="${row.baseline_selected ? 1 : .6}"><title>${esc(row.catchment_label)} · ${score(row.location_score)}</title></circle>`;
    }).join("")}
    <text class="chart-label" x="265" y="204" text-anchor="middle">Population density (square-root scale)</text>
    <text class="chart-label" x="8" y="102" transform="rotate(-90 8 102)" text-anchor="middle">Composite score</text>
  </svg>`;
}

function allocationComparison() {
  const result = app.scenario || app.dashboard.scenario;
  const s = result.summary;
  workspace.innerHTML = `
    ${intro("See what changes when representation is protected", "Compare unconstrained top-ranked candidates, global distinct-location allocation, and the active user-defined scenario. Every substitution includes its score difference and rationale.")}
    <section class="grid equal">
      <article class="card">
        <div class="card-header"><div><h4>Coverage tradeoff</h4><p class="card-subtitle">Target-catchment representation before and after scenario rules.</p></div></div>
        <div class="tradeoff"><div class="tradeoff-stat"><strong>${s.independent_location_count}</strong><span>Independent locations</span></div><div class="tradeoff-arrow">→</div><div class="tradeoff-stat"><strong>${s.represented_location_count}</strong><span>Scenario locations</span></div></div>
        <div class="metric" style="margin-top:10px"><span>Distinct-location allocation</span><strong>${s.distinct_location_count} locations</strong></div>
        <div class="metric"><span>Scenario combined score</span><strong>${num(s.combined_score, 3)}</strong></div>
        <div class="metric"><span>Score difference vs independent tops</span><strong>${num(s.score_difference, 3)}</strong></div>
        <div class="metric" title="Share of the unconstrained per-stratum composite score retained after distinct-coverage rules. 100% means representation is free of score cost."><span>Coverage efficiency</span><strong>${s.coverage_efficiency != null ? pct(s.coverage_efficiency, 1) : "—"}</strong></div>
        <div class="metric"><span>Median selected score</span><strong>${s.median_scenario_score != null ? score(s.median_scenario_score) : "—"}</strong></div>
        <div class="metric"><span>Mean station distance</span><strong>${s.mean_station_distance_miles != null ? `${num(s.mean_station_distance_miles, 1)} mi` : "—"}</strong></div>
      </article>
      <article class="card"><div class="card-header"><div><h4>Assignment substitutions</h4><p class="card-subtitle">Slope-style trace from independent candidates to active scenario assignments.</p></div></div>${slopeChart(result)}</article>
    </section>
    <section class="grid two" style="margin-top:16px">
      <article class="card"><div class="card-header"><div><h4>Active scenario map</h4><p class="card-subtitle">Selected target catchments and separate weather stations.</p></div>${badge(`${s.represented_location_count} represented`, "teal")}</div>${mapSvg(result.selected)}</article>
      <article class="card"><div class="card-header"><div><h4>Changed assignments</h4><p class="card-subtitle">Reasons for score-lowering substitutions and explicit priorities.</p></div>${badge(`${result.changes.length} changes`, "gold")}</div><div class="change-list">${result.changes.length ? result.changes.map(change => `<div class="change-item"><h5>${esc(change.climate_region)} · ${esc(change.urbanicity_short)}</h5><p><strong>${esc(change.from_label)}</strong><br>↓ ${esc(change.to_label)}<br>Score difference: −${num(change.score_loss, 3)} · ${esc(change.reason)}</p></div>`).join("") : `<p class="card-subtitle">The active scenario matches all independent top-ranked candidates.</p>`}</div></article>
    </section>`;
  bindMapLayers(allocationComparison);
}

function slopeChart(result) {
  const changes = result.changes;
  if (!changes.length) return `<div class="empty-state" style="min-height:170px"><p>No substitutions in the active scenario.</p></div>`;
  return `<svg class="chart-svg" viewBox="0 0 560 ${Math.max(150, changes.length * 52 + 24)}" role="img" aria-label="Substitutions caused by allocation rules">
    ${changes.map((change, index) => {
      const y = 30 + index * 52;
      return `<text class="chart-label" x="8" y="${y}">${esc(change.urbanicity_short)}</text><line x1="130" y1="${y - 4}" x2="430" y2="${y + 13}" stroke="#c99a38" stroke-width="2"/><circle cx="130" cy="${y - 4}" r="4" fill="#3977a8"/><circle cx="430" cy="${y + 13}" r="4" fill="#0a9690"/><text class="chart-label" x="138" y="${y - 10}">${esc(change.from_label).slice(0, 30)}</text><text class="chart-label" x="438" y="${y + 18}">${esc(change.to_label).slice(0, 22)}</text>`;
    }).join("")}
  </svg>`;
}

function methodology() {
  const provenance = app.dashboard.provenance;
  workspace.innerHTML = `
    ${intro("Methodology and source notes", "This page is written as an inspectable methods appendix. It states the baseline choices, their reasons, and the limitations that remain before simulation.")}
    <article class="card method-copy">
      <section><h4>Purpose and analytical unit</h4><p>The explorer identifies one representative building-stock target catchment for every combination of five climate regions and four urbanicity categories. Weather stations are climate sources, not proxies for the socioeconomic or building-stock characteristics of the communities being simulated.</p></section>
      <section><h4>ZIP codes are search entry points</h4><p>A USPS ZIP code is not silently treated as a Census ZCTA, place, county, CBSA, or weather-station location. ZIP search resolves a documented crosswalk record, displays one-to-many uncertainty when present, and then proposes the analytical catchment appropriate to the stratum. Leading zeros remain intact.</p></section>
      <section><h4>Catchment boundary rules</h4><p>Higher-density urban, lower-density urban, and suburban / small-town tracts are aggregated within a CBSA. Rural tracts are aggregated within a county. The associated ResStock filters are exact and deliberately different:</p><div class="formula">Non-rural: in.metropolitan_and_micropolitan_statistical_area<br>Rural:     in.county<br><br>Do not substitute in.city for rural selections.</div></section>
      <section><h4>Density screen and score</h4><p>Candidates at or above the configurable within-stratum population-density percentile are retained. The baseline threshold is 60%.</p><div class="formula">score = 0.45 × housing-unit coverage percentile<br>      + 0.35 × population-density percentile<br>      + 0.20 × population-coverage percentile</div></section>
      <section><h4>Unique-location optimization</h4><p>The baseline global allocation selects one candidate per stratum while maximizing the total score and preserving distinct represented catchments. If that rule selects a lower-ranked alternative, the explorer reports the score difference and substitution rationale. The rule can be disabled for sensitivity analysis.</p></section>
      <section><h4>Research-priority override</h4><p>Philadelphia-Camden-Wilmington is seeded as the preferred Mixed-Humid HDU catchment because the project team has stronger local heat-health data coverage in Philadelphia. The candidate has unconstrained rank 2. The override is labeled, editable, removable, and preserved in exported scenario JSON.</p></section>
      <section><h4>Data sources</h4><ul>${provenance.sources.map(source => `<li><strong>${esc(source.name)}.</strong> ${esc(source.role)} ${source.url ? `<a href="${esc(source.url)}" rel="noreferrer">${esc(source.url)}</a>` : esc(source.file || "")}</li>`).join("")}</ul><p><strong>Boundary system:</strong> ${esc(provenance.boundary_system)} · <strong>Method version:</strong> ${esc(provenance.method_version)}.</p></section>
      <section><h4>Known limitations and pre-simulation QC</h4><ul>${provenance.limitations.map(item => `<li>${esc(item)}</li>`).join("")}<li>${esc(provenance.zip_crosswalk.limitation)}</li><li>Hourly temperature and humidity completeness, station distance, elevation, and coastal context require review before simulation.</li></ul></section>
    </article>`;
}

function download(filename, content, mime = "text/plain") {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
  toast(`Exported ${filename}`);
}

function downloadCsv(filename, rows) {
  if (!rows.length) return toast("No rows to export.");
  const fields = ["climate_region", "urbanicity_short", "catchment_type", "catchment_code", "catchment_label", "population_2010", "housing_units_2010", "population_density_sqmi", "housing_unit_density_sqmi", "location_score", "selection_rank", "selected_station_name", "station_distance_miles", "nrel_filter_field", "nrel_filter_value", "nrel_verification_status"];
  const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  download(filename, [fields.join(","), ...rows.map(row => fields.map(field => quote(row[field])).join(","))].join("\n"), "text/csv");
}

async function exportSites() {
  try {
    const content = await api("/api/exports/site-list.csv", { method: "POST", body: JSON.stringify((app.scenario || app.dashboard.scenario).config) });
    download("representative-location-site-list.csv", content, "text/csv");
  } catch (error) {
    toast(error.message);
  }
}

function render() {
  if (!app.dashboard) return;
  ({ overview, zip: zipExplorer, scenario: scenarioBuilder, ranking: candidateRanking, allocation: allocationComparison, methodology }[app.page] || overview)();
}

async function start() {
  renderNav();
  setHeader(app.page);
  $("#mobile-menu").addEventListener("click", () =>
    document.querySelector(".sidebar").classList.contains("open") ? closeSidebar() : openSidebar(),
  );
  $("#sidebar-backdrop")?.addEventListener("click", closeSidebar);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeSidebar();
  });
  $("#refresh-view").addEventListener("click", async () => {
    try {
      app.dashboard = await api("/api/dashboard");
      app.scenario = null;
      setScenarioPill();
      render();
      toast("Read-only analytical inputs refreshed.");
    } catch (error) {
      toast(error.message);
    }
  });
  try {
    app.dashboard = await api("/api/dashboard");
    if (app.dashboard?.provenance?.data_mode === "demo") {
      const status = $("#data-status");
      if (status) status.innerHTML = `<span style="background:#c99a38;box-shadow:0 0 0 3px rgba(201,154,56,.18)"></span> Demonstration dataset`;
      setScenarioPill("Baseline scenario · demo data");
    }
    render();
  } catch (error) {
    workspace.innerHTML = `<div class="info-banner coral"><strong>Application could not load.</strong><span>${esc(error.message)} The analytical inputs may be unavailable — check the server log and <code>/api/health</code>.</span></div>`;
    const status = $("#data-status");
    if (status) status.innerHTML = `<span style="background:#d98b6a;box-shadow:0 0 0 3px rgba(217,139,106,.18)"></span> Inputs unavailable`;
  }
}

start();
