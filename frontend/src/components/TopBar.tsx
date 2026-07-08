import { SlidersHorizontal, Sun, Moon, MonitorSmartphone, RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { SearchBox } from "./SearchBox";
import { DataModeBadge } from "./DataModeBadge";
import { ScenarioChip } from "./ScenarioChip";
import { ExportMenu } from "./ExportMenu";
import { useTheme } from "../state/theme";
import { useScenario } from "../state/scenario";
import type { HealthResponse } from "../lib/types";

const THEME_ICON = { light: Sun, dark: Moon, system: MonitorSmartphone };
const THEME_LABEL = { light: "Light theme", dark: "Dark theme", system: "System theme" };

export function TopBar({ health, onToggleFilters }: { health?: HealthResponse; onToggleFilters?: () => void }) {
  const { mode, cycle } = useTheme();
  const queryClient = useQueryClient();
  const { applied } = useScenario();
  const ThemeIcon = THEME_ICON[mode];

  return (
    <header className="topbar">
      <div className="brand">
        <span className="mark" aria-hidden>
          Rx
        </span>
        <span className="desktop-only">ReplocX</span>
      </div>
      <SearchBox />
      {onToggleFilters && (
        <button className="btn btn-icon filter-toggle" type="button" onClick={onToggleFilters} aria-label="Toggle filters">
          <SlidersHorizontal size={16} aria-hidden />
        </button>
      )}
      <span className="spacer" />
      <DataModeBadge health={health} />
      <span className="desktop-only">
        <ScenarioChip />
      </span>
      <span className="topbar-secondary">
        <ExportMenu config={applied ?? undefined} />
      </span>
      <button
        className="btn btn-icon topbar-secondary"
        type="button"
        onClick={() => queryClient.invalidateQueries()}
        aria-label="Refresh data"
        title="Refresh data"
      >
        <RefreshCw size={16} aria-hidden />
      </button>
      <button className="btn btn-icon topbar-secondary" type="button" onClick={cycle} aria-label={THEME_LABEL[mode]} title={THEME_LABEL[mode]}>
        <ThemeIcon size={16} aria-hidden />
      </button>
    </header>
  );
}
