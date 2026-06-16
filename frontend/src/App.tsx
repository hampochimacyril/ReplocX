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
          </Routes>
        </main>
      </div>
      <DetailsDrawer />
    </div>
  );
}
