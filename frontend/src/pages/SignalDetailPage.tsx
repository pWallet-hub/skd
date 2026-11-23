import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, post } from "../api/client";
import type { Signal, SignalStatus } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ArrowLeft, MapIcon, Megaphone } from "../components/icons";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, ErrorText, Loading, PageHeader, StatCard } from "../components/ui";
import { formatDate, formatDateTime, humanize } from "../utils/format";

const NEXT: Record<SignalStatus, SignalStatus[]> = {
  detected: ["under_review", "dismissed"],
  under_review: ["confirmed", "dismissed"],
  confirmed: ["resolved"],
  dismissed: ["under_review"],
  resolved: [],
};
const ACTION_LABEL: Record<SignalStatus, string> = {
  under_review: "Start review",
  confirmed: "Confirm concern",
  dismissed: "Dismiss",
  resolved: "Mark resolved",
  detected: "Reopen",
};

export default function SignalDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const signal = useQuery({ queryKey: ["signal", id], queryFn: () => get<Signal>(`/signals/${id}`) });

  const refresh = () => {
    setNote("");
    qc.invalidateQueries({ queryKey: ["signal", id] });
    qc.invalidateQueries({ queryKey: ["signals"] });
  };
  const transition = useMutation({
    mutationFn: (status: SignalStatus) => post(`/signals/${id}/transition`, { status, note }),
    onSuccess: (_, status) => {
      refresh();
      toast(`Signal moved to “${humanize(status)}”`);
    },
  });
  const addNote = useMutation({ mutationFn: () => post(`/signals/${id}/notes`, { body: note }), onSuccess: refresh });

  if (signal.isLoading) return <Loading rows={6} />;
  const s = signal.data;
  if (!s) return <ErrorText error={signal.error} />;
  const canAct = !!user && ["analyst", "health_reviewer", "admin"].includes(user.role);

  return (
    <>
      <Link to="/signals" className="small row" style={{ gap: 4, marginTop: 8 }}><ArrowLeft size={14} /> All signals</Link>
      <PageHeader
        title={`${humanize(s.symptom_category)} — ${s.school?.name ?? s.area?.name}`}
        subtitle={<>Signal #{s.id} · detected {formatDateTime(s.detected_at)} · <Badge value={s.status} /></>}
        actions={
          <>
            <Link to="/map" className="btn btn-secondary"><MapIcon size={16} /> View on map</Link>
            {canAct && s.status === "confirmed" && (
              <Link to={`/alerts?signal=${s.id}`} className="btn btn-primary"><Megaphone size={16} /> Draft community alert</Link>
            )}
          </>
        }
      />
      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <StatCard label="Reports in window" value={s.report_count} tone="danger" icon={<strong>#</strong>} sub={`${formatDate(s.window_start)} – ${formatDate(s.window_end)}`} />
        <StatCard label="Expected (baseline)" value={s.baseline_count} tone="info" icon={<strong>≈</strong>} />
        <StatCard label="Ratio to baseline" value={`×${s.score}`} tone="warn" icon={<strong>×</strong>} />
      </div>

      <div className="grid grid-main">
        <Card title="Investigation log" subtitle="Every status change is recorded with a note">
          {s.notes?.length === 0 && <p className="muted">No notes yet.</p>}
          <ol className="timeline">
            {s.notes?.map((n) => (
              <li key={n.id}>
                <div className="row">
                  {n.status_change && <Badge value={n.status_change.split("->")[1]} />}
                  <span className="muted small">{formatDateTime(n.created_at)}</span>
                </div>
                <p style={{ marginTop: 4 }}>{n.body}</p>
              </li>
            ))}
          </ol>
          {canAct && (
            <div className="form" style={{ marginTop: 8 }}>
              <textarea className="input" rows={3} placeholder="Add a note (required for status changes)…" value={note} onChange={(e) => setNote(e.target.value)} />
              <div className="row">
                {NEXT[s.status].map((st) => (
                  <Button key={st} variant={st === "dismissed" ? "secondary" : "primary"} disabled={note.trim().length < 3 || transition.isPending} onClick={() => transition.mutate(st)}>
                    {ACTION_LABEL[st]}
                  </Button>
                ))}
                <Button variant="ghost" disabled={!note.trim() || addNote.isPending} onClick={() => addNote.mutate()}>Add note only</Button>
              </div>
              <ErrorText error={transition.error ?? addNote.error} />
            </div>
          )}
        </Card>
        <Card title="Findings">
          <p className={s.findings ? "" : "muted"}>{s.findings ?? "No findings recorded yet."}</p>
          <div className="callout info" style={{ marginTop: 16 }}>
            Detection compares the last window with the preceding baseline. It cannot tell the cause — verification
            by health professionals is required before any public communication.
          </div>
        </Card>
      </div>
    </>
  );
}
