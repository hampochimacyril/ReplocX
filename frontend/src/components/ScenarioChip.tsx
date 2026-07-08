import { Link } from "react-router-dom";
import { useScenario } from "../state/scenario";

/** Active-scenario chip (name + saved/dirty state). Reflects the applied scenario:
 * the baseline reads "Baseline · saved"; an applied-but-unsaved custom scenario
 * reads "… · unsaved" until it is saved to the store. Links to the workbench. */
export function ScenarioChip() {
  const { applied, customized, saved } = useScenario();
  const rawName = applied?.name ?? "Baseline";
  const isDefaultName = !rawName || rawName === "User-defined scenario";
  const name = !customized ? "Baseline" : isDefaultName ? "Custom scenario" : rawName;
  const dirty = customized && !saved;
  return (
    <Link className="chip" to="/scenario" title="Active scenario — open the workbench">
      <span className={`dot ${dirty ? "dirty" : "saved"}`} aria-hidden />
      <span>
        {name} · {dirty ? "unsaved" : "saved"}
      </span>
    </Link>
  );
}
