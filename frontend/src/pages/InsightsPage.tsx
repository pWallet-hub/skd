import { useQuery } from "@tanstack/react-query";
import { get } from "../api/client";
import type { AreaAggregate, CategoryCount, Overview } from "../api/types";
import { Card, Loading, Stat } from "../components/ui";

export default function InsightsPage() {
  const overview = useQuery({ queryKey: ["overview"], queryFn: () => get<Overview>("/analytics/overview") });
  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: () => get<CategoryCount[]>("/analytics/categories?days=30"),
  });
  const areas = useQuery({
    queryKey: ["areas-agg", 30],
    queryFn: () => get<AreaAggregate[]>("/analytics/areas?days=30"),
  });
  const max = Math.max(1, ...(categories.data?.map((c) => c.count) ?? [1]));

  return (
    <div className="grid">
      <Card title="Overview">
        {overview.isLoading && <Loading />}
        {overview.data && (
          <div className="stats">
            <Stat label="Families" value={overview.data.families} />
            <Stat label="Children" value={overview.data.children} />
            <Stat label="Reports (total)" value={overview.data.reports_total} />
            <Stat label="Reports (7 days)" value={overview.data.reports_last_7_days} />
            <Stat label="Open signals" value={overview.data.open_signals} />
            <Stat label="Published alerts" value={overview.data.published_alerts} />
          </div>
        )}
      </Card>

      <Card title="Most reported concerns (30 days)">
        {categories.data?.map((c) => (
          <div key={c.category} className="bar-row">
            <span>{c.category}</span>
            <div className="bar">
              <div style={{ width: `${(c.count / max) * 100}%` }} />
            </div>
            <strong>{c.count}</strong>
          </div>
        ))}
      </Card>

      <Card title="Reports by area (30 days)">
        <table>
          <thead>
            <tr>
              <th>Area</th>
              <th>Reports</th>
              <th>Top concern</th>
            </tr>
          </thead>
          <tbody>
            {areas.data?.map((a) => (
              <tr key={a.area_id}>
                <td>{a.area_name}</td>
                <td>{a.suppressed ? <span className="muted">&lt; min. size</span> : a.report_count}</td>
                <td>{a.top_category ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
