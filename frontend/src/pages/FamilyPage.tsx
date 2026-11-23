import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { get } from "../api/client";
import type { Child, NotificationItem, SymptomReport } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ArrowRight, Baby, Bell, BellRing, BookOpen, HeartPulse, Megaphone, Stethoscope } from "../components/icons";
import { Avatar, Badge, Card, EmptyState, ErrorText, Loading, PageHeader, StatCard } from "../components/ui";
import { ageLabel, formatDate, timeAgo } from "../utils/format";

const notifIcon = (kind: string) =>
  kind === "community_alert" ? (
    <div className="list-icon danger"><Megaphone size={18} /></div>
  ) : kind === "guidance" ? (
    <div className="list-icon brand"><BookOpen size={18} /></div>
  ) : (
    <div className="list-icon info"><BellRing size={18} /></div>
  );

export default function FamilyPage() {
  const { user } = useAuth();
  const children = useQuery({ queryKey: ["children"], queryFn: () => get<Child[]>("/children") });
  const reports = useQuery({ queryKey: ["reports"], queryFn: () => get<SymptomReport[]>("/reports?limit=8") });
  const notifications = useQuery({ queryKey: ["notifications"], queryFn: () => get<NotificationItem[]>("/notifications") });

  const nameOf = (id: number) => children.data?.find((c) => c.id === id)?.display_name ?? `#${id}`;
  const ongoing = reports.data?.filter((r) => r.is_ongoing).length ?? 0;
  const unread = notifications.data?.filter((n) => !n.read_at).length ?? 0;
  const firstName = user?.full_name.split(" ")[0];

  return (
    <>
      <PageHeader
        title={`Hello, ${firstName} 👋`}
        subtitle="Here's how your family is doing."
        actions={
          <Link to="/report" className="btn btn-primary">
            <Stethoscope size={16} /> Report a concern
          </Link>
        }
      />

      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <StatCard label="Children" value={children.data?.length ?? "–"} icon={<Baby size={20} />} />
        <StatCard label="Ongoing concerns" value={ongoing} tone={ongoing ? "warn" : "ok"} icon={<HeartPulse size={20} />} />
        <StatCard label="Unread notifications" value={unread} tone="info" icon={<Bell size={20} />} />
      </div>

      <div className="grid grid-main">
        <div className="stack">
          <Card title="My children" subtitle="Profiles you manage">
            {children.isLoading && <Loading />}
            <ErrorText error={children.error} />
            <div className="grid grid-2" style={{ gap: 12 }}>
              {children.data?.map((c) => (
                <div key={c.id} className="child-card">
                  <Avatar name={c.display_name} src={c.photo_url} size="lg" />
                  <div>
                    <div className="strong">{c.display_name}</div>
                    <div className="muted small">{ageLabel(c.age_months)} · born {formatDate(c.date_of_birth)}</div>
                    <div className="tags">
                      {c.learning_interests.map((i) => (
                        <span key={i} className="badge badge-brand">{i}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Recent health reports" subtitle="Your observations — not diagnoses" flush>
            {reports.isLoading && <div style={{ padding: "0 20px" }}><Loading /></div>}
            {reports.data?.length === 0 && (
              <EmptyState title="No reports yet" message="When your child is unwell, record it here to keep a history." icon={<HeartPulse size={22} />} />
            )}
            {!!reports.data?.length && (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr><th>Started</th><th>Child</th><th>Symptoms</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {reports.data.map((r) => (
                      <tr key={r.id}>
                        <td>{formatDate(r.onset_date)}</td>
                        <td className="strong">{nameOf(r.child_id)}</td>
                        <td>{r.symptoms.map((s) => s.name).join(", ")}</td>
                        <td><Badge value={r.is_ongoing ? "ongoing" : "recovered"} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>

        <Card title="Notifications" actions={<Link to="/notifications" className="small">View all <ArrowRight size={14} style={{ verticalAlign: -2 }} /></Link>} flush>
          {notifications.data?.length === 0 && <EmptyState title="All caught up" icon={<Bell size={22} />} />}
          <ul className="list">
            {notifications.data?.slice(0, 6).map((n) => (
              <li key={n.id} className={`list-item ${n.read_at ? "" : "unread"}`}>
                {notifIcon(n.kind)}
                <div className="body">
                  <div className="strong">{n.title}</div>
                  <div className="muted small">{n.body}</div>
                  <div className="muted small" style={{ marginTop: 4 }}>{timeAgo(n.created_at)}</div>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
}
