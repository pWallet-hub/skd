import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { get } from "../../api/client";
import type { AdminStats, AuditEntry, Page, SystemStatus } from "../../api/types";
import { DailyBars, HBarList } from "../../components/charts";
import { Activity, ArrowRight, FileText, HardDrive, MapPin, RefreshCw, ServerCog, UserPlus, Users } from "../../components/icons";
import { Button, Card, Loading, PageHeader, StatCard } from "../../components/ui";
import { formatBytes, ROLE_LABEL, timeAgo } from "../../utils/format";

export default function AdminDashboardPage() {
  const stats = useQuery({ queryKey: ["admin-stats"], queryFn: () => get<AdminStats>("/admin/stats"), refetchInterval: 30_000 });
  const system = useQuery({ queryKey: ["admin-system"], queryFn: () => get<SystemStatus>("/admin/system"), refetchInterval: 30_000 });
  const audit = useQuery({ queryKey: ["admin-audit", "recent"], queryFn: () => get<Page<AuditEntry>>("/admin/audit-logs?limit=6"), refetchInterval: 30_000 });
  const s = stats.data;
  const allOk = system.data?.services.every((x) => x.ok);

  return (
    <>
      <PageHeader
        title="Admin dashboard"
        subtitle="Platform health, users and activity at a glance."
        actions={
          <>
            <Link to="/admin/users?new=1" className="btn btn-primary"><UserPlus size={16} /> Add user</Link>
          </>
        }
      />

      <div className="grid grid-4" style={{ marginBottom: 18 }}>
        <StatCard label="Total users" value={s?.total_users ?? "–"} icon={<Users size={20} />} sub={`${s?.new_users_30d ?? "–"} new in 30 days`} />
        <StatCard label="Signed in (7 days)" value={s?.logins_7d ?? "–"} tone="info" icon={<Activity size={20} />} sub={`${s?.inactive_users ?? "–"} deactivated accounts`} />
        <StatCard label="Places" value={s ? s.schools + s.facilities + s.infrastructure : "–"} tone="ok" icon={<MapPin size={20} />} sub={s ? `${s.schools} schools · ${s.facilities} facilities` : undefined} />
        <StatCard label="Published articles" value={s?.articles_published ?? "–"} tone="warn" icon={<FileText size={20} />} sub={`${s?.articles_draft ?? "–"} awaiting review`} />
      </div>

      <div className="grid grid-main" style={{ marginBottom: 18 }}>
        <Card title="Health reports per day" subtitle="Last 30 days, by onset date">
          {stats.isLoading ? <Loading rows={5} /> : <DailyBars data={s?.reports_per_day ?? []} />}
        </Card>
        <Card title="Users by role" actions={<Link to="/admin/users" className="small">Manage <ArrowRight size={14} style={{ verticalAlign: -2 }} /></Link>}>
          {stats.isLoading && <Loading />}
          <HBarList items={(s?.users_by_role ?? []).map((r) => ({ label: ROLE_LABEL[r.role], value: r.count }))} />
        </Card>
      </div>

      <div className="grid grid-2">
        <Card
          title="System status"
          subtitle={system.data ? `v${system.data.version} · ${system.data.environment}` : undefined}
          actions={
            <Button variant="ghost" size="sm" icon={<RefreshCw size={14} />} onClick={() => system.refetch()} disabled={system.isFetching}>
              {system.isFetching ? "Checking…" : "Recheck"}
            </Button>
          }
          flush
        >
          {system.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
          {system.data && (
            <div className={`callout ${allOk ? "ok" : "warn"}`} style={{ margin: "0 20px 8px" }}>
              <ServerCog size={18} /> {allOk ? "All systems operational" : "Some services need attention"}
            </div>
          )}
          {system.data?.services.map((svc) => (
            <div key={svc.name} className="service">
              <span className={`pulse ${svc.ok ? "ok" : "down"}`} aria-label={svc.ok ? "OK" : "Down"} />
              <div className="body">
                <div className="strong">{svc.name}</div>
                <div className="muted small">{svc.detail}</div>
              </div>
              <span className="muted small">{svc.latency_ms !== null ? `${svc.latency_ms} ms` : "—"}</span>
            </div>
          ))}
          {system.data?.storage.map((b) => (
            <div key={b.bucket} className="service">
              <HardDrive size={18} color="var(--text-3)" />
              <div className="body">
                <div className="strong mono">{b.bucket}</div>
                <div className="muted small">SeaweedFS bucket</div>
              </div>
              <span className="muted small">{b.objects} files · {formatBytes(b.size_bytes)}</span>
            </div>
          ))}
        </Card>

        <Card title="Recent activity" actions={<Link to="/admin/audit" className="small">Audit log <ArrowRight size={14} style={{ verticalAlign: -2 }} /></Link>} flush>
          {audit.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
          <ul className="list">
            {audit.data?.items.map((e) => (
              <li key={e.id} className="list-item">
                <div className="list-icon brand"><Activity size={16} /></div>
                <div className="body">
                  <div>{e.summary}</div>
                  <div className="muted small">{e.actor_email ?? "system"} · {timeAgo(e.created_at)}</div>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
}
