import { NavLink } from "react-router-dom";
import { Map as MapIcon, Table2, GitCompareArrows, SlidersHorizontal, BookText } from "lucide-react";

interface NavItem {
  to: string;
  label: string;
  Icon: typeof MapIcon;
  end?: boolean;
}

const ITEMS: NavItem[] = [
  { to: "/", label: "Map workspace", Icon: MapIcon, end: true },
  { to: "/catchments", label: "Catchments", Icon: Table2 },
  { to: "/compare", label: "Compare", Icon: GitCompareArrows },
  { to: "/scenario", label: "Scenario", Icon: SlidersHorizontal },
  { to: "/methodology", label: "Methodology & data", Icon: BookText },
];

export function NavRail() {
  return (
    <nav className="nav" aria-label="Primary">
      {ITEMS.map(({ to, label, Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? "active" : "")} title={label}>
          <Icon size={20} aria-hidden />
          <span className="sr-only">{label}</span>
          <span className="tip" aria-hidden>
            {label}
          </span>
        </NavLink>
      ))}
      <span className="nav-spacer" />
    </nav>
  );
}
