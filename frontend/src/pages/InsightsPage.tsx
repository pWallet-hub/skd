import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { download, get } from "../api/client";
import type { AreaAggregate, CategoryCount, Overview, Signal, TrendPoint } from "../api/types";
import { DailyBars, HBarList } from "../components/charts";
import { fillDays } from "../utils/chart";
import { humanize } from "../utils/format";
import { Activity, ArrowRight, Baby, Download, Megaphone, Radar, Users } from "../components/icons";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, Loading, PageHeader, StatCard } from "../components/ui";

const RANGES = [7, 14, 30, 90];
const LIVE = 30_000; // refresh every 30 s so new activity shows up during demos

export default function InsightsPage() {
  const toast = useToast();
  const [days, setDays] = useState(30);
  const overview = useQuery({ queryKey: ["overview"], queryFn: () => get<Overview>("/analytics/overview"), refetchInterval: LIVE });
  const trends = useQuery({ queryKey: ["trends", days], queryFn: () => get<TrendPoint[]>(`/analytics/trends?days=${days}`), refetchInterval: LIVE });
  const categories = useQuery({ queryKey: ["categories", days], queryFn: () => get<CategoryCount[]>(`/analytics/categories?days=${days}`), refetchInterval: LIVE });
  const areas = useQuery({ queryKey: ["areas-agg", days], queryFn: () => get<AreaAggregate[]>(`/analytics/areas?days=${days}`), refetchInterval: LIVE });
  const signals = useQuery({ queryKey: ["signals"], queryFn: () => get<Signal[]>("/signals"), refetchInterval: LIVE });
  const open = signals.data?.filter((s) => ["detected", "under_review", "confirmed"].includes(s.status)) ?? [];
  const o = overview.data;

  async function exportCsv() {
    try {
      await download(`/analytics/export.csv?days=${days}`, `smartkids-aggregates-${days}d.csv`);
    } catch {
      toast("Export failed", "error");
    }
  }

  return (
    <>
      <PageHeader
        title="Community health overview"
        subtitle="Aggregated, de-identified data from voluntary parent reports."
        actions={
          <>
            <select className="input" style={{ width: "auto" }} value={days} onChange={(e) => setDays(Number(e.target.value))} aria-label="Time range">
              {RANGES.map((r) => <option key={r} value={r}>Last {r} days</option>)}
            </select>
            <Button variant="secondary" icon={<Download size={16} />} onClick={exportCsv}>Export CSV</Button>
          </>
        }
      />

      <div className="grid grid-4" style={{ marginBottom: 18 }}>
        <StatCard label="Registered families" value={o?.families ?? "–"} icon={<Users size={20} />} sub={`${o?.children ?? "–"} children`} />
        <StatCard label="Reports (last 7 days)" value={o?.reports_last_7_days ?? "–"} tone="info" icon={<Activity size={20} />} sub={`${o?.reports_total ?? "–"} all time`} />
        <StatCard label="Open signals" value={o?.open_signals ?? "–"} tone={o?.open_signals ? "danger" : "ok"} icon={<Radar size={20} />} sub="awaiting or under review" />
        <StatCard label="Published alerts" value={o?.published_alerts ?? "–"} tone="warn" icon={<Megaphone size={20} />} />
      </div>

      <div className="grid grid-main" style={{ marginBottom: 18 }}>
        <Card title="Reports per day" subtitle={`By symptom onset, last ${days} days`}>
          {trends.isLoading ? <Loading rows={5} /> : <DailyBars data={fillDays(trends.data ?? [], days)} />}
        </Card>
        <Card title="Most reported concerns" subtitle="Reports per symptom category">
          {categories.isLoading && <Loading />}
          {categories.data?.length === 0 && <EmptyState title="No reports in this period" />}
          <HBarList items={(categories.data ?? []).map((c) => ({ label: c.category, value: c.count }))} />
        </Card>
      </div>

      <div className="grid grid-main">
        <Card title="Reports by area" subtitle="Areas below the minimum count are hidden for privacy" flush>
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>Area</th><th className="num">Reports</th><th>Top concern</th></tr></thead>
              <tbody>
                {areas.data?.map((a) => (
                  <tr key={a.area_id}>
                    <td className="strong">{a.area_name}</td>
                    <td className="num">{a.suppressed ? <span className="muted small">hidden</span> : a.report_count}</td>
                    <td>{a.top_category ? <Badge value={a.top_category} /> : <span className="muted">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card title="Open signals" actions={<Link to="/signals" className="small">All signals <ArrowRight size={14} style={{ verticalAlign: -2 }} /></Link>} flush>
          {open.length === 0 && <EmptyState title="No open signals" message="Nothing unusual detected." icon={<Baby size={22} />} />}
          <ul className="list">
            {open.map((s) => (
              <li key={s.id} className="list-item">
                <div className="list-icon danger"><Radar size={18} /></div>
                <div className="body">
                  <Link to={`/signals/${s.id}`} className="strong" style={{ color: "var(--text)" }}>
                    {s.school?.name ?? s.area?.name}
                  </Link>
                  <div className="muted small">
                    {humanize(s.symptom_category)} · {s.report_count} reports (≈{s.baseline_count} expected)
                  </div>
                </div>
                <Badge value={s.status} />
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
}
