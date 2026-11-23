import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { get, post } from "../api/client";
import type { Alert, AlertSeverity, School } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Megaphone, Plus, ShieldCheck } from "../components/icons";
import { Modal } from "../components/Modal";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, ErrorText, Field, Loading, PageHeader } from "../components/ui";
import { formatDateTime } from "../utils/format";

const STEPS = ["draft", "pending_approval", "approved", "published"];

function Progress({ status }: { status: string }) {
  const idx = STEPS.indexOf(status);
  return (
    <div className="row" style={{ gap: 4 }} aria-label={`Status: ${status}`}>
      {STEPS.map((s, i) => (
        <span key={s} title={s.replace("_", " ")} style={{ width: 28, height: 4, borderRadius: 4, background: idx >= i ? "var(--brand-500)" : "var(--border)" }} />
      ))}
    </div>
  );
}

export default function AlertsPage() {
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const signalId = params.get("signal");
  const [creating, setCreating] = useState(!!signalId);

  const alerts = useQuery({ queryKey: ["alerts"], queryFn: () => get<Alert[]>("/alerts") });
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => get<School[]>("/geo/schools") });
  const schoolName = (id: number) => schools.data?.find((s) => s.id === id)?.name ?? `#${id}`;

  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [severity, setSeverity] = useState<AlertSeverity>("advisory");
  const [schoolIds, setSchoolIds] = useState<number[]>([]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["alerts"] });
  const create = useMutation({
    mutationFn: () =>
      post<Alert>("/alerts", { title, message, severity, signal_id: signalId ? Number(signalId) : null, target_school_ids: schoolIds }),
    onSuccess: () => {
      setTitle(""); setMessage(""); setSchoolIds([]); setCreating(false); setParams({});
      invalidate();
      toast("Draft saved");
    },
  });
  const action = useMutation({
    mutationFn: ({ id, verb }: { id: number; verb: string }) => post<Alert>(`/alerts/${id}/${verb}`),
    onSuccess: (_, { verb }) => {
      toast(verb === "publish" ? "Publishing to families…" : `Alert ${verb === "submit" ? "submitted for approval" : verb + "d"}`);
      setTimeout(invalidate, verb === "publish" ? 1200 : 0);
    },
    onError: (e) => toast(e.message, "error"),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    create.mutate();
  }
  const isReviewer = user?.role === "health_reviewer" || user?.role === "admin";

  return (
    <>
      <PageHeader
        title="Community alerts"
        subtitle="Draft → approval by a different health reviewer → publish to targeted families."
        actions={<Button icon={<Plus size={16} />} onClick={() => setCreating(true)}>New alert</Button>}
      />
      <div className="callout info" style={{ marginBottom: 18 }}>
        <ShieldCheck size={20} />
        <div>Four-eyes rule: an alert can only be approved by a health reviewer who did not write it. Every step is recorded in the audit log.</div>
      </div>

      <Card flush>
        {alerts.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
        {alerts.data?.length === 0 && <EmptyState title="No alerts yet" icon={<Megaphone size={22} />} action={<Button onClick={() => setCreating(true)}>Draft the first alert</Button>} />}
        <ul className="list">
          {alerts.data?.map((a) => (
            <li key={a.id} className="list-item">
              <div className={`list-icon ${a.severity === "warning" ? "danger" : "info"}`}><Megaphone size={18} /></div>
              <div className="body">
                <div className="row">
                  <span className="strong">{a.title}</span>
                  <Badge value={a.severity} />
                  <Badge value={a.status} />
                </div>
                <p className="small" style={{ margin: "4px 0", color: "var(--text-2)" }}>{a.message}</p>
                <div className="row muted small">
                  <Progress status={a.status} />
                  <span>Created {formatDateTime(a.created_at)}</span>
                  {a.published_at && <span>· Published {formatDateTime(a.published_at)}</span>}
                  {a.target_school_ids.length > 0 && <span>· {a.target_school_ids.map(schoolName).join(", ")}</span>}
                </div>
              </div>
              <div className="row" style={{ flexWrap: "nowrap" }}>
                {a.status === "draft" && <Button size="sm" onClick={() => action.mutate({ id: a.id, verb: "submit" })}>Submit</Button>}
                {a.status === "pending_approval" && isReviewer && (
                  <>
                    <Button size="sm" onClick={() => action.mutate({ id: a.id, verb: "approve" })}>Approve</Button>
                    <Button size="sm" variant="secondary" onClick={() => action.mutate({ id: a.id, verb: "reject" })}>Send back</Button>
                  </>
                )}
                {a.status === "approved" && <Button size="sm" onClick={() => action.mutate({ id: a.id, verb: "publish" })}>Publish</Button>}
                {(a.status === "approved" || a.status === "published") && isReviewer && (
                  <Button size="sm" variant="ghost" onClick={() => action.mutate({ id: a.id, verb: "retract" })}>Retract</Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </Card>

      {creating && (
        <Modal
          title="Draft a community alert"
          onClose={() => { setCreating(false); setParams({}); }}
          footer={
            <>
              <Button variant="ghost" onClick={() => setCreating(false)}>Cancel</Button>
              <Button form="alert-form" disabled={create.isPending}>Save draft</Button>
            </>
          }
        >
          <form id="alert-form" className="form" onSubmit={onSubmit}>
            {signalId && <div className="callout info">Linked to signal #{signalId}.</div>}
            <Field label="Title">
              <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} placeholder="E.g. Hygiene advice for families at …" />
            </Field>
            <Field label="Message to families" hint="Plain language. State what is known, what to do, and where to get help.">
              <textarea className="input" rows={5} value={message} onChange={(e) => setMessage(e.target.value)} required minLength={10} />
            </Field>
            <div className="form-grid">
              <Field label="Severity">
                <select className="input" value={severity} onChange={(e) => setSeverity(e.target.value as AlertSeverity)}>
                  <option value="info">Info</option>
                  <option value="advisory">Advisory</option>
                  <option value="warning">Warning</option>
                </select>
              </Field>
            </div>
            <Field label="Who should receive it?" hint="Families with a child at the selected schools.">
              <div className="chips">
                {schools.data?.map((s) => (
                  <label key={s.id} className={`chip ${schoolIds.includes(s.id) ? "on" : ""}`}>
                    <input type="checkbox" checked={schoolIds.includes(s.id)} onChange={() => setSchoolIds((ids) => (ids.includes(s.id) ? ids.filter((x) => x !== s.id) : [...ids, s.id]))} />
                    {s.name}
                  </label>
                ))}
              </div>
            </Field>
            <ErrorText error={create.error} />
          </form>
        </Modal>
      )}
    </>
  );
}
