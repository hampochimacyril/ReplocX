import { useState } from "react";
import { Routes, Route, useLocation } from "react-router-dom";
import { NavRail } from "./components/NavRail";
import { TopBar } from "./components/TopBar";
import { DetailsDrawer } from "./components/DetailsDrawer";
import { MapWorkspace } from "./routes/MapWorkspace";
import { Catchments } from "./routes/Catchments";
import { Scenario } from "./routes/Scenario";
import { Compare } from "./routes/Compare";
import { Methodology } from "./routes/Methodology";
import { AtlasShell } from "./routes/atlas/AtlasShell";
import { Introduction } from "./routes/atlas/Introduction";
import { DataMethods } from "./routes/atlas/DataMethods";
import { SimulationResults } from "./routes/atlas/SimulationResults";
import { SealedPassive } from "./routes/atlas/SealedPassive";
import { Equity } from "./routes/atlas/Equity";
import { Methods } from "./routes/atlas/Methods";
import { Exports } from "./routes/atlas/Exports";
import { AtlasSiteDetail } from "./routes/atlas/AtlasSiteDetail";
import { useHealth } from "./state/queries";

/** Routes that own the persistent filter panel, so the top-bar filter toggle is
 * only shown where it does something. */
const FILTER_ROUTES = new Set(["/", "/catchments"]);

export function App() {
  const [filtersOpen, setFiltersOpen] = useState(false);
  const health = useHealth();
  const location = useLocation();
  const hasFilters = FILTER_ROUTES.has(location.pathname);

  return (
    <div className="app">
      <TopBar health={health.data} onToggleFilters={hasFilters ? () => setFiltersOpen((v) => !v) : undefined} />
      <div className="body">
        <NavRail />
        <main className="ctx">
          <Routes>
            <Route path="/" element={<MapWorkspace filtersOpen={filtersOpen} onCloseFilters={() => setFiltersOpen(false)} />} />
            <Route path="/catchments" element={<Catchments filtersOpen={filtersOpen} onCloseFilters={() => setFiltersOpen(false)} />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/scenario" element={<Scenario />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/atlas" element={<AtlasShell />}>
              <Route index element={<Introduction />} />
              <Route path="locations" element={<DataMethods />} />
              <Route path="results" element={<SimulationResults />} />
              <Route path="sealed-passive" element={<SealedPassive />} />
              <Route path="equity" element={<Equity />} />
              <Route path="methods" element={<Methods />} />
              <Route path="exports" element={<Exports />} />
              <Route path="sites/:siteId" element={<AtlasSiteDetail />} />
            </Route>
          </Routes>
        </main>
      </div>
      <DetailsDrawer />
    </div>
  );
}
