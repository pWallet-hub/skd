import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { get, post } from "../api/client";
import type { Alert, AlertSeverity, School } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, ErrorText, Loading } from "../components/ui";
import { formatDate } from "../utils/format";

export default function AlertsPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const [params] = useSearchParams();
  const signalId = params.get("signal");

  const alerts = useQuery({ queryKey: ["alerts"], queryFn: () => get<Alert[]>("/alerts") });
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => get<School[]>("/geo/schools") });

  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState<AlertSeverity>("advisory");
  const [schoolIds, setSchoolIds] = useState<number[]>([]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["alerts"] });
  const create = useMutation({
    mutationFn: () =>
      post<Alert>("/alerts", {
        title,
        message,
        severity,
        signal_id: signalId ? Number(signalId) : null,
        target_school_ids: schoolIds,
      }),
    onSuccess: () => {
      setTitle("");
      setMessage("");
      setSchoolIds([]);
      invalidate();
    },
  });
  const action = useMutation({
    mutationFn: ({ id, verb }: { id: number; verb: string }) => post<Alert>(`/alerts/${id}/${verb}`),
    onSuccess: () => setTimeout(invalidate, 500), // publish is async (Celery)
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }

  const isReviewer = user?.role === "health_reviewer" || user?.role === "admin";

  return (
    <div className="grid">
      <Card title="Draft a community alert">
        <p className="muted small">
          Alerts need approval by a health reviewer who did not write them before they can be published.
          {signalId && <> Linked to signal #{signalId}.</>}
        </p>
        <form className="form" onSubmit={onSubmit}>
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} />
          </label>
          <label>
            Message
            <textarea rows={4} value={message} onChange={(e) => setMessage(e.target.value)} required minLength={10} />
          </label>
          <label>
            Severity
            <select value={severity} onChange={(e) => setSeverity(e.target.value as AlertSeverity)}>
              <option value="info">Info</option>
              <option value="advisory">Advisory</option>
              <option value="warning">Warning</option>
            </select>
          </label>
          <label>
            Target schools (families with children there)
            <select
              multiple
              value={schoolIds.map(String)}
              onChange={(e) => setSchoolIds(Array.from(e.target.selectedOptions, (o) => Number(o.value)))}
            >
              {schools.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <ErrorText error={create.error} />
          <button disabled={create.isPending}>Save draft</button>
        </form>
      </Card>

      <Card title="Alerts">
        {alerts.isLoading && <Loading />}
        <ErrorText error={action.error} />
        <ul className="list">
          {alerts.data?.map((a) => (
            <li key={a.id}>
              <div className="row">
                <Badge value={a.status} /> <Badge value={a.severity} /> <strong>{a.title}</strong>
              </div>
              <div className="muted small">
                {a.message} · created {formatDate(a.created_at)}
                {a.published_at && <> · published {formatDate(a.published_at)}</>}
              </div>
              <div className="row">
                {a.status === "draft" && (
                  <button onClick={() => action.mutate({ id: a.id, verb: "submit" })}>Submit for approval</button>
                )}
                {a.status === "pending_approval" && isReviewer && (
                  <>
                    <button onClick={() => action.mutate({ id: a.id, verb: "approve" })}>Approve</button>
                    <button className="secondary" onClick={() => action.mutate({ id: a.id, verb: "reject" })}>
                      Send back
                    </button>
                  </>
                )}
                {a.status === "approved" && (
                  <button onClick={() => action.mutate({ id: a.id, verb: "publish" })}>Publish</button>
                )}
                {(a.status === "approved" || a.status === "published") && isReviewer && (
                  <button className="secondary" onClick={() => action.mutate({ id: a.id, verb: "retract" })}>
                    Retract
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
