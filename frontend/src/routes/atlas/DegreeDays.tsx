import { LoadingState, ErrorState } from "../../components/states/States";
import { Tag } from "../../components/ui/Tag";
import { useCoolingSeasons, fmt } from "./atlas";

/** Monthly HDD/CDD context: per-site cooling-season windows derived from NOAA
 * long-term (1970–2019) degree-day climatology. */
export function DegreeDays() {
  const { data, isLoading, isError, error, refetch } = useCoolingSeasons();
  if (isLoading) return <LoadingState label="Loading cooling-season windows…" />;
  if (isError || !data) return <ErrorState message={(error as Error)?.message ?? "Failed."} onRetry={refetch} />;

  return (
    <div className="doc">
      <h1>Monthly HDD / CDD</h1>
      <p className="muted">{data.long_term_note}</p>

      <p>
        Each selected site's cooling season is the set of months whose degree-day climatology crosses the
        cooling threshold. Non-rural sites use their CBSA station; rural sites use the county station. Sites
        that never clear the threshold fall back to the peak-CDD month and are flagged.
      </p>

      <div className="tablewrap" style={{ maxHeight: 420 }}>
        <table className="dtable">
          <thead>
            <tr>
              <th>Climate</th>
              <th>Urbanicity</th>
              <th>Station</th>
              <th>Cooling months</th>
              <th className="num">Length</th>
              <th>Contiguous</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {data.sites.map((r, i) => (
              <tr key={i}>
                <td>{String(r.climate_region)}</td>
                <td>{String(r.urbanicity_short)}</td>
                <td>
                  <span className="cell-label" title={String(r.selected_station_name)}>
                    {String(r.selected_station_name)}
                  </span>
                </td>
                <td>{String(r.season_month_set)}</td>
                <td className="num">{fmt(r.season_length_months, 0)}</td>
                <td>{String(r.season_contiguous) === "True" ? "yes" : "no"}</td>
                <td>
                  {String(r.fallback_peak_cdd_used) === "True" && (
                    <Tag tone="warn" title="Peak-CDD fallback used">
                      peak-CDD fallback
                    </Tag>
                  )}
                  {String(r.low_cooling_need_flag) === "True" && (
                    <Tag tone="info" title="Low cooling need">
                      low cooling need
                    </Tag>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
