import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { type Map as MlMap, type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Crosshair, ImageDown, Layers, Maximize2, Minus, Plus } from "lucide-react";
import { CLIMATE_REGIONS, climateHex } from "../lib/constants";
import { matchesFilters, isRepresentative, rowKey } from "../lib/selectors";
import { downloadDataUrl, dateStamp } from "../lib/exports";
import { formatMiles, formatPercentile } from "../lib/format";
import { readVar } from "../lib/css";
import { useFilters } from "../state/filters";
import { useSelection } from "../state/selection";
import type { CatchmentRow, GeometryResponse } from "../lib/types";

const SRC_CATCHMENTS = "catchments";
const SRC_CANDIDATES = "candidates";
const SRC_STATIONS = "stations";
const SRC_LINKS = "links";
const SRC_SEARCH = "search";

const SCORE_STOPS = [
  { value: 0, color: "#440154", label: "0.00" },
  { value: 0.25, color: "#3b528b", label: "0.25" },
  { value: 0.5, color: "#21918c", label: "0.50" },
  { value: 0.75, color: "#5ec962", label: "0.75" },
  { value: 1, color: "#fde725", label: "1.00" },
];

type Bounds = [number, number, number, number];
type ThematicMode = "climate" | "score";

function featureKey(type: string, code: string | number): string {
  return `${type}:${String(code).padStart(5, "0")}`;
}

function geometryBounds(geometry: GeometryResponse): Bounds {
  let minX = 180;
  let minY = 90;
  let maxX = -180;
  let maxY = -90;
  const visit = (coords: number[][]) => {
    for (const [x, y] of coords) {
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
  };
  for (const feature of geometry.features) {
    const shape = feature.geometry;
    if (shape.type === "Polygon") (shape.coordinates as number[][][]).forEach(visit);
    else (shape.coordinates as number[][][][]).forEach((polygon) => polygon.forEach(visit));
  }
  return minX > maxX ? [-125, 24, -66, 50] : [minX, minY, maxX, maxY];
}

function rowBounds(rows: CatchmentRow[]): Bounds | null {
  const points = rows
    .map((row) => [Number(row.centroid_lon), Number(row.centroid_lat)] as const)
    .filter(([lon, lat]) => Number.isFinite(lon) && Number.isFinite(lat));
  if (!points.length) return null;
  const xs = points.map(([lon]) => lon);
  const ys = points.map(([, lat]) => lat);
  let minX = Math.min(...xs);
  let maxX = Math.max(...xs);
  let minY = Math.min(...ys);
  let maxY = Math.max(...ys);
  if (minX === maxX) {
    minX -= 0.5;
    maxX += 0.5;
  }
  if (minY === maxY) {
    minY -= 0.5;
    maxY += 0.5;
  }
  return [minX, minY, maxX, maxY];
}

function climateExpression(): unknown {
  const expression: unknown[] = ["match", ["get", "climate_region"]];
  for (const region of CLIMATE_REGIONS) expression.push(region.name, region.hex);
  expression.push("#9aa4b1");
  return expression;
}

function scoreExpression(): unknown {
  const expression: unknown[] = ["interpolate", ["linear"], ["to-number", ["get", "score"], 0]];
  for (const stop of SCORE_STOPS) expression.push(stop.value, stop.color);
  return expression;
}

function motionDuration(): number {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 300;
}

function popupNode(kind: string, row: CatchmentRow): HTMLElement {
  const node = document.createElement("div");
  node.className = "map-popup";
  const kicker = document.createElement("div");
  kicker.className = "kicker";
  kicker.textContent = kind;
  const title = document.createElement("strong");
  title.textContent = row.catchment_label;
  const detail = document.createElement("div");
  detail.className = "muted small";
  detail.textContent = `${row.climate_region} · ${row.urbanicity_short} · score ${formatPercentile(
    row.scenario_score ?? row.location_score,
  )} · station ${formatMiles(row.station_distance_miles)}`;
  node.append(kicker, title, detail);
  return node;
}

export function MapCanvas({ geometry, rows }: { geometry: GeometryResponse; rows: CatchmentRow[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const rowByKeyRef = useRef(new Map<string, CatchmentRow>());
  const previousSelectedRef = useRef<string | null>(null);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [thematic, setThematic] = useState<ThematicMode>("climate");
  const [layers, setLayers] = useState({
    catchments: true,
    candidates: true,
    stations: true,
    links: true,
  });
  const { filters, reset } = useFilters();
  const { selectCatchment, selection } = useSelection();

  const rowByKey = useMemo(() => new Map(rows.map((row) => [rowKey(row), row])), [rows]);
  rowByKeyRef.current = rowByKey;

  const filteredRows = useMemo(() => rows.filter((row) => matchesFilters(row, filters)), [rows, filters]);
  const candidateRows = useMemo(
    () => filteredRows.filter((row) => !isRepresentative(row)),
    [filteredRows],
  );
  const representativeRows = useMemo(
    () => filteredRows.filter((row) => isRepresentative(row)),
    [filteredRows],
  );

  const geometryFc = useMemo(
    () => ({
      ...geometry,
      features: geometry.features.map((feature) => {
        const key = featureKey(feature.properties.catchment_type, feature.properties.catchment_code);
        const row = rowByKey.get(key);
        return {
          ...feature,
          properties: {
            ...feature.properties,
            feature_key: key,
            score: row?.scenario_score ?? row?.location_score ?? 0,
          },
        };
      }),
    }),
    [geometry, rowByKey],
  );

  const candidatesFc = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: candidateRows
        .filter((row) => Number.isFinite(row.centroid_lon) && Number.isFinite(row.centroid_lat))
        .map((row) => ({
          type: "Feature" as const,
          id: rowKey(row),
          properties: {
            key: rowKey(row),
            catchment_code: row.catchment_code,
            catchment_label: row.catchment_label,
            climate_region: row.climate_region,
            urbanicity_short: row.urbanicity_short,
            score: row.scenario_score ?? row.location_score,
          },
          geometry: { type: "Point" as const, coordinates: [row.centroid_lon, row.centroid_lat] },
        })),
    }),
    [candidateRows],
  );

  const stationsFc = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: representativeRows
        .filter((row) => Number.isFinite(row.selected_station_lon) && Number.isFinite(row.selected_station_lat))
        .map((row) => ({
          type: "Feature" as const,
          id: rowKey(row),
          properties: { key: rowKey(row), station: row.selected_station_name },
          geometry: { type: "Point" as const, coordinates: [row.selected_station_lon, row.selected_station_lat] },
        })),
    }),
    [representativeRows],
  );

  const linksFc = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: representativeRows
        .filter((row) => Number.isFinite(row.centroid_lon) && Number.isFinite(row.selected_station_lon))
        .map((row) => ({
          type: "Feature" as const,
          properties: { key: rowKey(row) },
          geometry: {
            type: "LineString" as const,
            coordinates: [
              [row.centroid_lon, row.centroid_lat],
              [row.selected_station_lon, row.selected_station_lat],
            ],
          },
        })),
    }),
    [representativeRows],
  );

  const searchFc = useMemo(() => {
    if (selection?.kind !== "zip") return { type: "FeatureCollection" as const, features: [] };
    const { longitude, latitude, zip_code } = selection.result.resolved;
    if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
      return { type: "FeatureCollection" as const, features: [] };
    }
    return {
      type: "FeatureCollection" as const,
      features: [
        {
          type: "Feature" as const,
          properties: { label: `ZIP ${zip_code}` },
          geometry: { type: "Point" as const, coordinates: [longitude, latitude] },
        },
      ],
    };
  }, [selection]);

  const selectedRow =
    selection?.kind === "catchment"
      ? selection.row
      : selection?.kind === "zip"
        ? selection.result.candidate ?? selection.result.selected_representative
        : null;
  const selectedKey = selectedRow ? rowKey(selectedRow) : null;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const style: StyleSpecification = {
      version: 8,
      sources: {},
      layers: [{ id: "bg", type: "background", paint: { "background-color": readVar("--surface-2", "#eef1f4") } }],
    };
    let map: MlMap;
    try {
      map = new maplibregl.Map({
        container: containerRef.current,
        style,
        center: [-96, 38],
        zoom: 3,
        attributionControl: false,
        dragRotate: false,
        maxZoom: 12,
        // Required so getCanvas().toDataURL() captures a rendered frame for the
        // map-image export below.
        preserveDrawingBuffer: true,
      });
    } catch {
      setFailed(true);
      return;
    }
    mapRef.current = map;
    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(containerRef.current);
    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: "Catchments: U.S. Census TIGER/Line · stations: NOAA ISD",
      }),
      "bottom-right",
    );
    map.on("error", (event) => {
      if (event?.error?.message?.includes("WebGL")) setFailed(true);
    });
    map.on("load", () => {
      map.addSource(SRC_CATCHMENTS, {
        type: "geojson",
        data: geometryFc as never,
        promoteId: "feature_key",
        attribution: "U.S. Census TIGER/Line",
      });
      map.addSource(SRC_CANDIDATES, {
        type: "geojson",
        data: candidatesFc as never,
        promoteId: "key",
      });
      map.addSource(SRC_STATIONS, { type: "geojson", data: stationsFc as never, promoteId: "key" });
      map.addSource(SRC_LINKS, { type: "geojson", data: linksFc as never });
      map.addSource(SRC_SEARCH, { type: "geojson", data: searchFc as never });

      map.addLayer({
        id: "candidate-pt",
        type: "circle",
        source: SRC_CANDIDATES,
        paint: {
          "circle-radius": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            7,
            ["boolean", ["feature-state", "hover"], false],
            5.5,
            3.2,
          ] as never,
          "circle-color": climateExpression() as never,
          "circle-opacity": 0.72,
          "circle-stroke-color": readVar("--bg", "#fff"),
          "circle-stroke-width": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            2.4,
            0.8,
          ] as never,
        },
      });
      map.addLayer({
        id: "catchment-fill",
        type: "fill",
        source: SRC_CATCHMENTS,
        paint: {
          "fill-color": climateExpression() as never,
          "fill-opacity": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            0.82,
            ["boolean", ["feature-state", "hover"], false],
            0.72,
            ["boolean", ["feature-state", "dim"], false],
            0.08,
            0.52,
          ] as never,
        },
      });
      map.addLayer({
        id: "catchment-line",
        type: "line",
        source: SRC_CATCHMENTS,
        paint: {
          "line-color": readVar("--text", "#11161c"),
          "line-width": [
            "case",
            ["boolean", ["feature-state", "selected"], false],
            3,
            ["boolean", ["feature-state", "hover"], false],
            2,
            0.7,
          ] as never,
          "line-opacity": ["case", ["boolean", ["feature-state", "dim"], false], 0.18, 0.9] as never,
        },
      });
      map.addLayer({
        id: "link-line",
        type: "line",
        source: SRC_LINKS,
        paint: { "line-color": readVar("--info", "#2563a8"), "line-width": 0.9, "line-dasharray": [2, 2] },
      });
      map.addLayer({
        id: "station-pt",
        type: "circle",
        source: SRC_STATIONS,
        paint: {
          "circle-radius": 4,
          "circle-color": readVar("--bg", "#fff"),
          "circle-stroke-color": readVar("--info", "#2563a8"),
          "circle-stroke-width": 1.7,
        },
      });
      map.addLayer({
        id: "search-point",
        type: "circle",
        source: SRC_SEARCH,
        paint: {
          "circle-radius": 7,
          "circle-color": readVar("--accent", "#1f6feb"),
          "circle-stroke-color": readVar("--bg", "#fff"),
          "circle-stroke-width": 2.5,
        },
      });
      map.moveLayer("candidate-pt", "link-line");

      let hovered: { source: string; id: string | number } | null = null;
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 });
      popupRef.current = popup;
      const clearHover = () => {
        if (hovered) map.setFeatureState({ source: hovered.source, id: hovered.id }, { hover: false });
        hovered = null;
        popup.remove();
        map.getCanvas().style.cursor = "";
      };
      const bindRowLayer = (layer: string, source: string, kind: string, property: string) => {
        map.on("mousemove", layer, (event) => {
          const feature = event.features?.[0];
          const key = feature?.properties?.[property] as string | undefined;
          if (!feature || feature.id === undefined || !key) return;
          if (hovered && (hovered.source !== source || hovered.id !== feature.id)) {
            map.setFeatureState({ source: hovered.source, id: hovered.id }, { hover: false });
          }
          hovered = { source, id: feature.id };
          map.setFeatureState({ source, id: feature.id }, { hover: true });
          map.getCanvas().style.cursor = "pointer";
          const row = rowByKeyRef.current.get(key);
          if (row) popup.setLngLat(event.lngLat).setDOMContent(popupNode(kind, row)).addTo(map);
        });
        map.on("mouseleave", layer, clearHover);
        map.on("click", layer, (event) => {
          const key = event.features?.[0]?.properties?.[property] as string | undefined;
          const row = key ? rowByKeyRef.current.get(key) : undefined;
          if (row) selectCatchment(row);
        });
      };
      bindRowLayer("catchment-fill", SRC_CATCHMENTS, "Selected representative", "feature_key");
      bindRowLayer("candidate-pt", SRC_CANDIDATES, "Candidate catchment", "key");
      bindRowLayer("station-pt", SRC_STATIONS, "Assigned weather station", "key");

      map.fitBounds(geometryBounds(geometry), { padding: 36, duration: 0, maxZoom: 7 });
      setReady(true);
    });
    return () => {
      resizeObserver.disconnect();
      popupRef.current?.remove();
      popupRef.current = null;
      map.remove();
      mapRef.current = null;
    };
    // Map lifecycle is intentionally one-time; source effects below keep data current.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    (map.getSource(SRC_CATCHMENTS) as maplibregl.GeoJSONSource | undefined)?.setData(geometryFc as never);
    (map.getSource(SRC_CANDIDATES) as maplibregl.GeoJSONSource | undefined)?.setData(candidatesFc as never);
    (map.getSource(SRC_STATIONS) as maplibregl.GeoJSONSource | undefined)?.setData(stationsFc as never);
    (map.getSource(SRC_LINKS) as maplibregl.GeoJSONSource | undefined)?.setData(linksFc as never);
    (map.getSource(SRC_SEARCH) as maplibregl.GeoJSONSource | undefined)?.setData(searchFc as never);
  }, [geometryFc, candidatesFc, stationsFc, linksFc, searchFc, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    for (const feature of geometryFc.features) {
      const key = String(feature.properties.feature_key);
      const row = rowByKey.get(key);
      map.setFeatureState({ source: SRC_CATCHMENTS, id: key }, { dim: !row || !matchesFilters(row, filters) });
    }
  }, [filters, geometryFc.features, rowByKey, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const previous = previousSelectedRef.current;
    if (previous && previous !== selectedKey) {
      map.setFeatureState({ source: SRC_CATCHMENTS, id: previous }, { selected: false });
      map.setFeatureState({ source: SRC_CANDIDATES, id: previous }, { selected: false });
    }
    if (selectedKey) {
      map.setFeatureState({ source: SRC_CATCHMENTS, id: selectedKey }, { selected: true });
      map.setFeatureState({ source: SRC_CANDIDATES, id: selectedKey }, { selected: true });
    }
    previousSelectedRef.current = selectedKey;
  }, [selectedKey, candidatesFc, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !selection) return;
    if (selection.kind === "zip") {
      const { longitude, latitude } = selection.result.resolved;
      if (Number.isFinite(longitude) && Number.isFinite(latitude)) {
        map.flyTo({ center: [longitude, latitude], zoom: 7, duration: motionDuration() });
      }
      return;
    }
    const key = rowKey(selection.row);
    const polygon = geometryFc.features.find((feature) => feature.properties.feature_key === key);
    if (polygon) {
      map.fitBounds(geometryBounds({ ...geometry, features: [polygon] }), {
        padding: 110,
        maxZoom: 8,
        duration: motionDuration(),
      });
    } else if (Number.isFinite(selection.row.centroid_lon) && Number.isFinite(selection.row.centroid_lat)) {
      map.flyTo({
        center: [selection.row.centroid_lon, selection.row.centroid_lat],
        zoom: 7,
        duration: motionDuration(),
      });
    }
  }, [selection, geometry, geometryFc.features, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const color = thematic === "climate" ? climateExpression() : scoreExpression();
    map.setPaintProperty("catchment-fill", "fill-color", color as never);
    map.setPaintProperty("candidate-pt", "circle-color", color as never);
  }, [thematic, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    const setVisibility = (id: string, visible: boolean) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
    };
    setVisibility("catchment-fill", layers.catchments);
    setVisibility("catchment-line", layers.catchments);
    setVisibility("candidate-pt", layers.candidates);
    setVisibility("station-pt", layers.stations);
    setVisibility("link-line", layers.links);
  }, [layers, ready]);

  const zoom = (delta: number) => {
    const map = mapRef.current;
    if (map) map.zoomTo(map.getZoom() + delta, { duration: motionDuration() });
  };
  const zoomToVisible = () => {
    const map = mapRef.current;
    if (!map) return;
    map.fitBounds(rowBounds(filteredRows) ?? geometryBounds(geometry), {
      padding: 42,
      maxZoom: 8,
      duration: motionDuration(),
    });
  };
  const exportImage = () => {
    const map = mapRef.current;
    if (!map) return;
    map.once("render", () => {
      try {
        downloadDataUrl(`replocx_map_${dateStamp()}.png`, map.getCanvas().toDataURL("image/png"));
      } catch {
        /* toDataURL can throw if the GL context is lost; ignore and leave the UI intact. */
      }
    });
    map.triggerRepaint();
  };
  const zoomToSelection = () => {
    const map = mapRef.current;
    if (!map || !selectedRow) return;
    const key = rowKey(selectedRow);
    const polygon = geometryFc.features.find((feature) => feature.properties.feature_key === key);
    if (polygon) {
      map.fitBounds(geometryBounds({ ...geometry, features: [polygon] }), {
        padding: 110,
        maxZoom: 8,
        duration: motionDuration(),
      });
    } else {
      map.flyTo({
        center: [selectedRow.centroid_lon, selectedRow.centroid_lat],
        zoom: 7,
        duration: motionDuration(),
      });
    }
  };

  return (
    <div className="mapwrap">
      <div
        ref={containerRef}
        className="map-canvas"
        aria-label={`Interactive map with ${representativeRows.length} selected representatives and ${candidateRows.length} filtered candidates`}
      />
      <p className="sr-only" aria-live="polite">
        Showing {candidateRows.length} non-selected candidate catchments and {representativeRows.length} selected representatives.
        Use search or the coverage matrix for keyboard selection.
      </p>
      {failed && (
        <div className="map-fallback">
          <div>
            <strong>Map rendering unavailable</strong>
            <p className="muted small">
              WebGL could not initialize in this browser. Filters, the coverage matrix, charts, search, and details remain usable.
            </p>
          </div>
        </div>
      )}
      {!failed && filteredRows.length === 0 && (
        <div className="map-empty" role="status">
          <strong>No catchments match these filters</strong>
          <span className="muted small">Reset filters or broaden the score/station-distance ranges.</span>
          <button className="btn" type="button" onClick={reset}>
            Reset filters
          </button>
        </div>
      )}

      <div className="map-overlay layers" role="group" aria-label="Map layers and symbology">
        <div className="layer-title">
          <Layers size={13} aria-hidden /> Layers
        </div>
        <label className="check">
          <input
            type="checkbox"
            checked={layers.catchments}
            onChange={(event) => setLayers((value) => ({ ...value, catchments: event.target.checked }))}
          />
          Selected polygons
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={layers.candidates}
            onChange={(event) => setLayers((value) => ({ ...value, candidates: event.target.checked }))}
          />
          Candidate centroids
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={layers.stations}
            onChange={(event) => setLayers((value) => ({ ...value, stations: event.target.checked }))}
          />
          Weather stations
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={layers.links}
            onChange={(event) => setLayers((value) => ({ ...value, links: event.target.checked }))}
          />
          Station links
        </label>
        <label className="layer-select">
          <span>Color by</span>
          <select value={thematic} onChange={(event) => setThematic(event.target.value as ThematicMode)}>
            <option value="climate">Climate region</option>
            <option value="score">Composite score</option>
          </select>
        </label>
      </div>

      <div className="map-overlay map-ctrls" role="group" aria-label="Map zoom controls">
        <button className="btn" type="button" onClick={() => zoom(1)} aria-label="Zoom in">
          <Plus size={16} aria-hidden />
        </button>
        <button className="btn" type="button" onClick={() => zoom(-1)} aria-label="Zoom out">
          <Minus size={16} aria-hidden />
        </button>
        <button className="btn" type="button" onClick={zoomToVisible} aria-label="Fit all filtered results">
          <Maximize2 size={16} aria-hidden />
        </button>
        <button
          className="btn"
          type="button"
          onClick={zoomToSelection}
          disabled={!selectedRow}
          aria-label="Zoom to current selection"
        >
          <Crosshair size={16} aria-hidden />
        </button>
        <button className="btn" type="button" onClick={exportImage} aria-label="Export map as PNG" title="Export map as PNG">
          <ImageDown size={16} aria-hidden />
        </button>
      </div>

      <div className="map-overlay map-count num" aria-live="polite">
        {filteredRows.length.toLocaleString()} matching · {representativeRows.length} selected
      </div>

      <div className="map-overlay legend" aria-label={`Legend: ${thematic === "climate" ? "climate regions" : "composite score"}`}>
        <div className="legend-title">{thematic === "climate" ? "Climate region" : "Composite score"}</div>
        {thematic === "climate"
          ? CLIMATE_REGIONS.map((region) => (
              <div className="row" key={region.name}>
                <span className="swatch" style={{ background: climateHex(region.name) }}>
                  {region.pattern}
                </span>
                {region.name}
              </div>
            ))
          : SCORE_STOPS.map((stop) => (
              <div className="row" key={stop.value}>
                <span className="swatch" style={{ background: stop.color }} aria-hidden />
                {stop.label}
              </div>
            ))}
        <div className="legend-symbols">
          <span><i className="polygon-symbol" /> selected polygon</span>
          <span><i className="point-symbol" /> candidate centroid</span>
        </div>
      </div>
    </div>
  );
}
