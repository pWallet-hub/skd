import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { del, get, patch, post } from "../api/client";
import type { Child, ImmunizationItem, Measurement, MilestoneItem, SymptomReport } from "../api/types";
import { LineSeries } from "../components/charts";
import { ChildForm } from "../components/ChildForm";
import { HealthCardModal } from "../components/HealthCardModal";
import { ArrowLeft, Check, HeartPulse, Pencil, Plus, QrCode, ShieldCheck, Sparkles, Stethoscope, Trash2, TrendingUp } from "../components/icons";
import { Modal } from "../components/Modal";
import { useToast } from "../components/Toast";
import { Avatar, Badge, Button, Card, EmptyState, ErrorText, Field, Loading, PageHeader, StatCard, Tabs } from "../components/ui";
import { ageLabel, formatDate } from "../utils/format";

type Tab = "overview" | "growth" | "vaccines" | "milestones" | "history";
const today = () => new Date().toISOString().slice(0, 10);

const VACCINE_TONE: Record<string, string> = { given: "resolved", due: "pending_approval", overdue: "confirmed", upcoming: "draft" };
const MILESTONE_TONE: Record<string, string> = { achieved: "resolved", expected: "pending_approval", check: "confirmed", upcoming: "draft" };
const MILESTONE_LABEL: Record<string, string> = { achieved: "Achieved", expected: "Around now", check: "Talk to a health worker", upcoming: "Later" };

export default function ChildPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const [editing, setEditing] = useState(false);
  const [sharing, setSharing] = useState(false);

  const child = useQuery({ queryKey: ["child", id], queryFn: () => get<Child>(`/children/${id}`) });
  const measurements = useQuery({ queryKey: ["measurements", id], queryFn: () => get<Measurement[]>(`/children/${id}/measurements`) });
  const vaccines = useQuery({ queryKey: ["vaccines", id], queryFn: () => get<ImmunizationItem[]>(`/children/${id}/immunizations`) });
  const milestones = useQuery({ queryKey: ["milestones", id], queryFn: () => get<MilestoneItem[]>(`/children/${id}/milestones`) });
  const reports = useQuery({ queryKey: ["reports", "child", id], queryFn: () => get<SymptomReport[]>(`/reports?child_id=${id}&limit=50`) });

  const remove = useMutation({
    mutationFn: () => del(`/children/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["children"] });
      toast("Profile removed");
      navigate("/family");
    },
  });

  if (child.isLoading) return <Loading rows={6} />;
  const c = child.data;
  if (!c) return <ErrorText error={child.error} />;

  const latest = measurements.data?.at(-1);
  const nextVaccine = vaccines.data?.find((v) => v.status !== "given");
  const dueVaccines = vaccines.data?.filter((v) => v.status === "due" || v.status === "overdue") ?? [];
  const achieved = milestones.data?.filter((m) => m.status === "achieved").length ?? 0;
  const ongoing = reports.data?.filter((r) => r.is_ongoing) ?? [];

  return (
    <>
      <Link to="/family" className="small row" style={{ gap: 4, marginTop: 8 }}><ArrowLeft size={14} /> My family</Link>
      <PageHeader
        title={c.display_name}
        subtitle={<>{ageLabel(c.age_months)} · born {formatDate(c.date_of_birth)}</>}
        actions={
          <>
            <Link to={`/report?child=${c.id}`} className="btn btn-primary"><Stethoscope size={16} /> Report a concern</Link>
            <Button variant="secondary" icon={<QrCode size={16} />} onClick={() => setSharing(true)}>Health card (QR)</Button>
            <Button variant="secondary" icon={<Pencil size={16} />} onClick={() => setEditing(true)}>Edit</Button>
            <Button variant="ghost" icon={<Trash2 size={16} />} onClick={() => confirm(`Remove ${c.display_name}'s profile and all their records?`) && remove.mutate()}>Remove</Button>
          </>
        }
      />

      <div className="row" style={{ gap: 16, marginBottom: 18, flexWrap: "nowrap" }}>
        <Avatar name={c.display_name} src={c.photo_url} size="lg" />
        <div className="tags">{c.learning_interests.map((i) => <span key={i} className="badge badge-brand">{i}</span>)}</div>
      </div>

      {dueVaccines.length > 0 && (
        <div className="callout warn" style={{ marginBottom: 18 }}>
          <ShieldCheck size={20} />
          <div>
            <strong>{dueVaccines.map((v) => v.name).join(", ")}</strong> {dueVaccines.length > 1 ? "are" : "is"} due.{" "}
            <button className="btn-link" onClick={() => setTab("vaccines")} style={{ background: "none", border: 0, color: "inherit", textDecoration: "underline", cursor: "pointer", padding: 0, font: "inherit" }}>
              Record a vaccination
            </button>{" "}
            after your visit.
          </div>
        </div>
      )}

      <Tabs<Tab>
        value={tab}
        onChange={setTab}
        tabs={[
          { value: "overview", label: "Overview" },
          { value: "growth", label: "Growth" },
          { value: "vaccines", label: `Vaccinations${dueVaccines.length ? ` (${dueVaccines.length} due)` : ""}` },
          { value: "milestones", label: "Milestones" },
          { value: "history", label: `Health history${ongoing.length ? ` (${ongoing.length} ongoing)` : ""}` },
        ]}
      />

      {tab === "overview" && (
        <div className="grid grid-4">
          <StatCard label="Latest height" value={latest?.height_cm ? `${latest.height_cm} cm` : "—"} icon={<TrendingUp size={20} />} sub={latest ? `measured ${formatDate(latest.measured_on)}` : "no measurements"} />
          <StatCard label="Latest weight" value={latest?.weight_kg ? `${latest.weight_kg} kg` : "—"} tone="info" icon={<TrendingUp size={20} />} />
          <StatCard label="Next vaccination" value={nextVaccine ? nextVaccine.name : "Up to date"} tone={dueVaccines.length ? "warn" : "ok"} icon={<ShieldCheck size={20} />} sub={nextVaccine ? `${nextVaccine.status === "upcoming" ? "due" : nextVaccine.status} · ${formatDate(nextVaccine.due_date)}` : undefined} />
          <StatCard label="Milestones reached" value={`${achieved} / ${milestones.data?.length ?? "–"}`} tone="brand" icon={<Sparkles size={20} />} sub={ongoing.length ? `${ongoing.length} ongoing health concern(s)` : "no ongoing concerns"} />
        </div>
      )}
      {tab === "growth" && <GrowthTab childId={c.id} data={measurements.data ?? []} />}
      {tab === "vaccines" && <VaccinesTab child={c} items={vaccines.data} />}
      {tab === "milestones" && <MilestonesTab child={c} items={milestones.data} />}
      {tab === "history" && <HistoryTab childId={c.id} reports={reports.data} />}

      {sharing && <HealthCardModal child={c} onClose={() => setSharing(false)} />}
      {editing && (
        <ChildForm
          child={c}
          onClose={() => setEditing(false)}
          onSaved={() => {
            setEditing(false);
            qc.invalidateQueries({ queryKey: ["child", id] });
            qc.invalidateQueries({ queryKey: ["children"] });
            toast("Profile updated");
          }}
        />
      )}
    </>
  );
}

function GrowthTab({ childId, data }: { childId: number; data: Measurement[] }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [date, setDate] = useState(today());
  const [h, setH] = useState("");
  const [w, setW] = useState("");
  const add = useMutation({
    mutationFn: () => post(`/children/${childId}/measurements`, { measured_on: date, height_cm: h || null, weight_kg: w || null }),
    onSuccess: () => {
      setOpen(false); setH(""); setW("");
      qc.invalidateQueries({ queryKey: ["measurements", String(childId)] });
      toast("Measurement saved");
    },
  });
  const heights = data.filter((m) => m.height_cm).map((m) => ({ date: m.measured_on, value: Number(m.height_cm) }));
  const weights = data.filter((m) => m.weight_kg).map((m) => ({ date: m.measured_on, value: Number(m.weight_kg) }));
  function submit(e: FormEvent) { e.preventDefault(); add.mutate(); }

  return (
    <>
      <div className="row" style={{ marginBottom: 14 }}><Button icon={<Plus size={16} />} onClick={() => setOpen(true)}>Add measurement</Button></div>
      <div className="grid grid-2">
        <Card title="Height" subtitle="centimetres"><LineSeries data={heights} unit="cm" /></Card>
        <Card title="Weight" subtitle="kilograms"><LineSeries data={weights} unit="kg" /></Card>
      </div>
      <Card title="All measurements" flush className="" >
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Date</th><th className="num">Height (cm)</th><th className="num">Weight (kg)</th></tr></thead>
            <tbody>
              {[...data].reverse().map((m) => (
                <tr key={m.id}><td>{formatDate(m.measured_on)}</td><td className="num">{m.height_cm ?? "—"}</td><td className="num">{m.weight_kg ?? "—"}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {open && (
        <Modal title="Add a measurement" onClose={() => setOpen(false)} footer={<><Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button><Button form="m-form" disabled={add.isPending || (!h && !w)}>Save</Button></>}>
          <form id="m-form" className="form" onSubmit={submit}>
            <Field label="Date"><input className="input" type="date" value={date} max={today()} onChange={(e) => setDate(e.target.value)} required /></Field>
            <div className="form-grid">
              <Field label="Height (cm)"><input className="input" type="number" step="0.1" min="30" max="200" value={h} onChange={(e) => setH(e.target.value)} /></Field>
              <Field label="Weight (kg)"><input className="input" type="number" step="0.01" min="1" max="150" value={w} onChange={(e) => setW(e.target.value)} /></Field>
            </div>
            <ErrorText error={add.error} />
          </form>
        </Modal>
      )}
    </>
  );
}

function VaccinesTab({ child, items }: { child: Child; items?: ImmunizationItem[] }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [recording, setRecording] = useState<ImmunizationItem | null>(null);
  const [date, setDate] = useState(today());
  const refresh = (data: ImmunizationItem[]) => {
    qc.setQueryData(["vaccines", String(child.id)], data);
    qc.invalidateQueries({ queryKey: ["care", child.id] });
  };
  const record = useMutation({
    mutationFn: (v: ImmunizationItem) => post<ImmunizationItem[]>(`/children/${child.id}/immunizations`, { vaccine_code: v.code, given_on: date }),
    onSuccess: (data, v) => { refresh(data); setRecording(null); toast(`${v.name} recorded`); },
  });
  const undo = useMutation({
    mutationFn: (v: ImmunizationItem) => del(`/children/${child.id}/immunizations/${v.record_id}`).then(() => get<ImmunizationItem[]>(`/children/${child.id}/immunizations`)),
    onSuccess: refresh,
  });
  if (!items) return <Loading />;
  return (
    <>
      <div className="callout info" style={{ marginBottom: 14 }}>
        <ShieldCheck size={20} /><div>Example routine schedule for this prototype. Always follow your health centre and the child's vaccination card.</div>
      </div>
      <Card flush>
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Vaccine</th><th>Protects against</th><th>Due</th><th>Status</th><th /></tr></thead>
            <tbody>
              {items.map((v) => (
                <tr key={v.code}>
                  <td className="strong">{v.name}</td>
                  <td className="small">{v.protects_against}</td>
                  <td className="small">{formatDate(v.due_date)}</td>
                  <td><Badge value={VACCINE_TONE[v.status]} label={v.status === "given" ? `Given ${formatDate(v.given_on)}` : v.status} /></td>
                  <td>
                    {v.status === "given" ? (
                      <Button variant="ghost" size="sm" onClick={() => undo.mutate(v)}>Undo</Button>
                    ) : v.status !== "upcoming" ? (
                      <Button size="sm" icon={<Check size={14} />} onClick={() => { setDate(today()); setRecording(v); }}>Mark given</Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {recording && (
        <Modal title={`Record ${recording.name}`} onClose={() => setRecording(null)} footer={<><Button variant="ghost" onClick={() => setRecording(null)}>Cancel</Button><Button onClick={() => record.mutate(recording)} disabled={record.isPending}>Save</Button></>}>
          <Field label="Date given"><input className="input" type="date" value={date} min={child.date_of_birth} max={today()} onChange={(e) => setDate(e.target.value)} /></Field>
          <ErrorText error={record.error} />
        </Modal>
      )}
    </>
  );
}

function MilestonesTab({ child, items }: { child: Child; items?: MilestoneItem[] }) {
  const qc = useQueryClient();
  const toast = useToast();
  const set = (data: MilestoneItem[]) => qc.setQueryData(["milestones", String(child.id)], data);
  const mark = useMutation({
    mutationFn: (m: MilestoneItem) => post<MilestoneItem[]>(`/children/${child.id}/milestones`, { milestone_code: m.code, achieved_on: today() }),
    onSuccess: (data, m) => { set(data); toast(`🎉 ${child.display_name}: ${m.title}`); },
  });
  const undo = useMutation({
    mutationFn: (m: MilestoneItem) => del(`/children/${child.id}/milestones/${m.record_id}`).then(() => get<MilestoneItem[]>(`/children/${child.id}/milestones`)),
    onSuccess: set,
  });
  if (!items) return <Loading />;
  const groups: [string, number, number][] = [["0–12 months", 0, 12], ["1–2 years", 13, 24], ["2–3 years", 25, 36], ["3–5 years", 37, 72]];
  return (
    <>
      <div className="callout info" style={{ marginBottom: 14 }}>
        <Sparkles size={20} /><div>Every child develops at their own pace. “Talk to a health worker” is a gentle prompt to check in, not a diagnosis.</div>
      </div>
      <div className="grid grid-2">
        {groups.map(([label, lo, hi]) => (
          <Card key={label} title={label} flush>
            <ul className="list">
              {items.filter((m) => m.expected_months >= lo && m.expected_months <= hi).map((m) => (
                <li key={m.code} className="list-item" style={{ alignItems: "center" }}>
                  <div className={`list-icon ${m.status === "achieved" ? "brand" : ""}`}>{m.status === "achieved" ? <Check size={16} /> : <Sparkles size={16} />}</div>
                  <div className="body">
                    <div className="strong">{m.title}</div>
                    <div className="muted small" style={{ textTransform: "capitalize" }}>{m.domain} · around {m.expected_months} months{m.achieved_on ? ` · ${formatDate(m.achieved_on)}` : ""}</div>
                  </div>
                  <Badge value={MILESTONE_TONE[m.status]} label={MILESTONE_LABEL[m.status]} />
                  {m.status === "achieved" ? (
                    <Button variant="ghost" size="sm" onClick={() => undo.mutate(m)}>Undo</Button>
                  ) : m.status !== "upcoming" ? (
                    <Button size="sm" variant="secondary" onClick={() => mark.mutate(m)}>Done</Button>
                  ) : null}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </>
  );
}

function HistoryTab({ childId, reports }: { childId: number; reports?: SymptomReport[] }) {
  const qc = useQueryClient();
  const toast = useToast();
  const recover = useMutation({
    mutationFn: (r: SymptomReport) => patch(`/reports/${r.id}`, { is_ongoing: false, recovered_on: today() }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["reports"] }); toast("Glad they're feeling better!"); },
  });
  if (!reports) return <Loading />;
  if (reports.length === 0)
    return <Card><EmptyState title="No health reports" message="When your child is unwell, record it to keep a history." icon={<HeartPulse size={22} />} action={<Link to={`/report?child=${childId}`} className="btn btn-primary">Report a concern</Link>} /></Card>;
  return (
    <Card flush>
      <ul className="list">
        {reports.map((r) => (
          <li key={r.id} className="list-item" style={{ alignItems: "center" }}>
            <div className={`list-icon ${r.is_ongoing ? "danger" : "brand"}`}><HeartPulse size={16} /></div>
            <div className="body">
              <div className="strong">{r.symptoms.map((s) => s.name).join(", ")}</div>
              <div className="muted small">
                Started {formatDate(r.onset_date)}
                {r.recovered_on && ` · recovered ${formatDate(r.recovered_on)}`}
                {r.visited_facility && " · visited a health facility"}
              </div>
            </div>
            {r.verification === "clinically_confirmed" && <Badge value="clinically_confirmed" label="Reviewed by health worker" />}
            <Badge value={r.is_ongoing ? "ongoing" : "recovered"} />
            {r.is_ongoing && <Button size="sm" variant="secondary" onClick={() => recover.mutate(r)}>Mark recovered</Button>}
          </li>
        ))}
      </ul>
    </Card>
  );
}
