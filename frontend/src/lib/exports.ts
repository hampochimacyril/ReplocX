/* Client helpers that POST a scenario config to the backend export endpoints and
 * stream the response to a download. The backend builds every export; the client
 * only triggers and names the file. */
import { API_BASE } from "./api";
import { authHeaders, promptForToken } from "./auth";
import { downloadText, triggerDownload } from "./csv";
import type { ScenarioConfig } from "./types";

/** Short UTC date stamp (YYYYMMDD) for export filenames. */
export function dateStamp(date = new Date()): string {
  return date.toISOString().slice(0, 10).replace(/-/g, "");
}

export interface ExportSpec {
  id: string;
  label: string;
  path: string;
  filename: string;
}

export const EXPORTS: ExportSpec[] = [
  { id: "site-list", label: "Site-list CSV", path: "/exports/site-list.csv", filename: "replocx_site_list.csv" },
  {
    id: "resstock",
    label: "ResStock sampling CSV",
    path: "/exports/resstock-sampling.csv",
    filename: "replocx_resstock_sampling.csv",
  },
  {
    id: "openstudio",
    label: "OpenStudio manifest JSON",
    path: "/exports/openstudio-manifest.json",
    filename: "replocx_openstudio_manifest.json",
  },
];

export async function downloadExport(spec: ExportSpec, config: Partial<ScenarioConfig>): Promise<void> {
  // Like the JSON client, retry once after prompting for a token on a 401 so
  // exports work on an authenticated private deployment.
  for (;;) {
    const res = await fetch(`${API_BASE}${spec.path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "*/*", ...authHeaders() },
      body: JSON.stringify(config ?? {}),
    });
    if (res.status === 401) {
      const token = await promptForToken();
      if (token) continue;
    }
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Export failed (${res.status}): ${detail.slice(0, 200)}`);
    }
    const blob = await res.blob();
    triggerDownload(spec.filename, blob);
    return;
  }
}

/** Export the active scenario configuration as a reusable JSON file (client-side;
 * the same shape the /scenarios endpoints accept). */
export function downloadScenarioJson(config: Partial<ScenarioConfig>, name?: string): void {
  const safeName = (name ?? config.name ?? "scenario")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48) || "scenario";
  const payload = {
    schema: "rle.scenario_config/1.0",
    exported_at: new Date().toISOString(),
    config,
  };
  downloadText(`replocx_${safeName}_${dateStamp()}.json`, JSON.stringify(payload, null, 2), "application/json");
}

/** Save a map snapshot (data URL → PNG file). The map canvas must be created with
 * preserveDrawingBuffer so toDataURL captures the rendered frame. */
export function downloadDataUrl(filename: string, dataUrl: string): void {
  const anchor = document.createElement("a");
  anchor.href = dataUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}
