import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, post } from "../api/client";
import type { Signal, SignalStatus } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, ErrorText, Loading } from "../components/ui";
import { formatDate } from "../utils/format";

const NEXT: Record<SignalStatus, SignalStatus[]> = {
  detected: ["under_review", "dismissed"],
  under_review: ["confirmed", "dismissed"],
  confirmed: ["resolved"],
  dismissed: ["under_review"],
  resolved: [],
};

export default function SignalDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
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
    onSuccess: refresh,
  });
  const addNote = useMutation({
    mutationFn: () => post(`/signals/${id}/notes`, { body: note }),
    onSuccess: refresh,
  });

  if (signal.isLoading) return <Loading />;
  const s = signal.data;
  if (!s) return <ErrorText error={signal.error} />;
  const canAct = user && ["analyst", "health_reviewer", "admin"].includes(user.role);

  return (
    <div className="grid">
      <Card title={`Signal #${s.id} — ${s.symptom_category}`} actions={<Badge value={s.status} />}>
        <dl className="facts">
          <dt>Where</dt>
          <dd>{s.school?.name ?? s.area?.name}</dd>
          <dt>Window</dt>
          <dd>
            {formatDate(s.window_start)} – {formatDate(s.window_end)}
          </dd>
          <dt>Reports</dt>
          <dd>
            {s.report_count} (expected ~{s.baseline_count}, ×{s.score})
          </dd>
          <dt>Findings</dt>
          <dd>{s.findings ?? "—"}</dd>
        </dl>
        <Link to="/map">View on map →</Link>
      </Card>

      <Card title="Investigation log">
        <ul className="list">
          {s.notes?.map((n) => (
            <li key={n.id}>
              <span className="muted small">{new Date(n.created_at).toLocaleString()}</span>
              {n.status_change && <Badge value={n.status_change.split("->")[1]} />}
              <div>{n.body}</div>
            </li>
          ))}
          {s.notes?.length === 0 && <li className="muted">No notes yet.</li>}
        </ul>
        {canAct && (
          <div className="form">
            <textarea
              rows={3}
              placeholder="Note (required for status changes)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <div className="row">
              <button className="secondary" disabled={!note || addNote.isPending} onClick={() => addNote.mutate()}>
                Add note
              </button>
              {NEXT[s.status].map((st) => (
                <button key={st} disabled={note.length < 3 || transition.isPending} onClick={() => transition.mutate(st)}>
                  Move to {st.replace("_", " ")}
                </button>
              ))}
            </div>
            <ErrorText error={transition.error ?? addNote.error} />
          </div>
        )}
        {canAct && s.status === "confirmed" && (
          <Link to={`/alerts?signal=${s.id}`} className="button">
            Draft community alert
          </Link>
        )}
      </Card>
    </div>
  );
}
