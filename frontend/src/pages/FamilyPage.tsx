import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { get } from "../api/client";
import type { CareSummary, Child, NotificationItem, SymptomReport } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ChildForm } from "../components/ChildForm";
import { ArrowRight, Baby, Bell, BellRing, BookOpen, ChevronRight, HeartPulse, Hospital, Megaphone, Plus, ShieldCheck, Stethoscope } from "../components/icons";
import { useToast } from "../components/Toast";
import { Avatar, Badge, Button, Card, EmptyState, ErrorText, Loading, PageHeader, StatCard } from "../components/ui";
import { ageLabel, formatDate, timeAgo } from "../utils/format";

const notifIcon = (kind: string) =>
  kind === "community_alert" ? (
    <div className="list-icon danger"><Megaphone size={18} /></div>
  ) : kind === "guidance" ? (
    <div className="list-icon brand"><BookOpen size={18} /></div>
  ) : (
    <div className="list-icon info"><BellRing size={18} /></div>
  );

function ChildCard({ child }: { child: Child }) {
  const navigate = useNavigate();
  const care = useQuery({ queryKey: ["care", child.id], queryFn: () => get<CareSummary>(`/children/${child.id}/care-summary`) });
  return (
    <button className="child-card clickable" onClick={() => navigate(`/children/${child.id}`)}
      style={{ background: "var(--surface)", font: "inherit", textAlign: "left", width: "100%" }}>
      <Avatar name={child.display_name} src={child.photo_url} size="lg" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="strong">{child.display_name}</div>
        <div className="muted small">{ageLabel(child.age_months)} · born {formatDate(child.date_of_birth)}</div>
        <div className="tags">
          {!!care.data?.vaccines_due && (
            <Badge value={care.data.vaccines_overdue ? "confirmed" : "pending_approval"} icon={<ShieldCheck size={12} />}
              label={`${care.data.vaccines_due} vaccine${care.data.vaccines_due > 1 ? "s" : ""} ${care.data.vaccines_overdue ? "overdue" : "due"}`} />
          )}
          {!!care.data?.milestones_to_check && <Badge value="pending_approval" label="Milestone check-in" />}
          {child.learning_interests.slice(0, 2).map((i) => <span key={i} className="badge badge-brand">{i}</span>)}
        </div>
      </div>
      <ChevronRight size={18} color="var(--text-3)" />
    </button>
  );
}

export default function FamilyPage() {
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
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
          <>
            <Link to="/care" className="btn btn-secondary"><Hospital size={16} /> Find care</Link>
            <Link to="/report" className="btn btn-primary"><Stethoscope size={16} /> Report a concern</Link>
          </>
        }
      />

      <div className="grid grid-3 stat-row" style={{ marginBottom: 18 }}>
        <StatCard label="Children" value={children.data?.length ?? "–"} icon={<Baby size={20} />} />
        <StatCard label="Ongoing concerns" value={ongoing} tone={ongoing ? "warn" : "ok"} icon={<HeartPulse size={20} />} />
        <StatCard label="Unread notifications" value={unread} tone="info" icon={<Bell size={20} />} />
      </div>

      <div className="grid grid-main">
        <div className="stack">
          <Card title="My children" subtitle="Tap a child to see growth, vaccinations and milestones"
            actions={<Button size="sm" variant="secondary" icon={<Plus size={14} />} onClick={() => setAdding(true)}>Add child</Button>}>
            {children.isLoading && <Loading />}
            <ErrorText error={children.error} />
            {children.data?.length === 0 && (
              <EmptyState title="Add your first child" message="Create a profile to track growth, vaccinations and health." icon={<Baby size={22} />}
                action={<Button icon={<Plus size={16} />} onClick={() => setAdding(true)}>Add a child</Button>} />
            )}
            <div className="grid grid-2" style={{ gap: 12 }}>
              {children.data?.map((c) => <ChildCard key={c.id} child={c} />)}
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
      {adding && (
        <ChildForm
          onClose={() => setAdding(false)}
          onSaved={(c) => {
            setAdding(false);
            qc.invalidateQueries({ queryKey: ["children"] });
            toast(`${c.display_name} added to your family`);
            navigate(`/children/${c.id}`);
          }}
        />
      )}
    </>
  );
}
