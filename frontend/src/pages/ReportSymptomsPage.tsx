import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { get, post } from "../api/client";
import type { Child, Symptom, SymptomReport } from "../api/types";
import { AlertTriangle, Check, ShieldCheck } from "../components/icons";
import { useToast } from "../components/Toast";
import { Avatar, Button, Card, ErrorText, Field, Loading, PageHeader } from "../components/ui";
import { ageLabel } from "../utils/format";

const today = () => new Date().toISOString().slice(0, 10);

export default function ReportSymptomsPage() {
  const qc = useQueryClient();
  const toast = useToast();
  const navigate = useNavigate();
  const children = useQuery({ queryKey: ["children"], queryFn: () => get<Child[]>("/children") });
  const symptoms = useQuery({ queryKey: ["symptoms"], queryFn: () => get<Symptom[]>("/symptoms") });

  const [childId, setChildId] = useState<number | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [onset, setOnset] = useState(today());
  const [visited, setVisited] = useState(false);
  const [consent, setConsent] = useState(true);
  const [notes, setNotes] = useState("");

  const grouped = useMemo(() => {
    const g: Record<string, Symptom[]> = {};
    symptoms.data?.forEach((s) => (g[s.category] ??= []).push(s));
    return g;
  }, [symptoms.data]);

  const submit = useMutation({
    mutationFn: () =>
      post<SymptomReport>("/reports", {
        child_id: childId,
        symptom_ids: selected,
        onset_date: onset,
        visited_facility: visited,
        consent_to_aggregate: consent,
        notes: notes || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports"] });
      toast("Report saved. Thank you for keeping your child's history up to date.");
      navigate("/family");
    },
  });

  const toggle = (id: number) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    submit.mutate();
  }

  if (children.isLoading || symptoms.isLoading) return <Loading rows={6} />;

  return (
    <>
      <PageHeader title="Report a health concern" subtitle="Record what you've noticed. It takes about a minute." />
      <div className="grid grid-main">
        <Card>
          <form className="form" onSubmit={onSubmit}>
            <Field label="Which child?">
              <div className="grid grid-2" style={{ gap: 10 }}>
                {children.data?.map((c) => (
                  <button
                    type="button"
                    key={c.id}
                    className="child-card"
                    style={{
                      cursor: "pointer", background: "var(--surface)", font: "inherit", textAlign: "left",
                      borderColor: childId === c.id ? "var(--brand-500)" : undefined,
                      boxShadow: childId === c.id ? "0 0 0 3px var(--brand-100)" : undefined,
                    }}
                    onClick={() => setChildId(c.id)}
                  >
                    <Avatar name={c.display_name} src={c.photo_url} />
                    <div style={{ flex: 1 }}>
                      <div className="strong">{c.display_name}</div>
                      <div className="muted small">{ageLabel(c.age_months)}</div>
                    </div>
                    {childId === c.id && <Check size={18} color="var(--brand-600)" />}
                  </button>
                ))}
              </div>
            </Field>

            <Field label="What symptoms have you noticed?" hint="Select all that apply.">
              <div className="stack" style={{ gap: 12 }}>
                {Object.entries(grouped).map(([cat, list]) => (
                  <div key={cat}>
                    <div className="small muted" style={{ textTransform: "capitalize", marginBottom: 6 }}>{cat}</div>
                    <div className="chips">
                      {list.map((s) => (
                        <label key={s.id} className={`chip ${selected.includes(s.id) ? "on" : ""}`}>
                          <input type="checkbox" checked={selected.includes(s.id)} onChange={() => toggle(s.id)} />
                          {selected.includes(s.id) && <Check size={14} />}
                          {s.name}
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Field>

            <div className="form-grid">
              <Field label="When did it start?">
                <input className="input" type="date" value={onset} max={today()} onChange={(e) => setOnset(e.target.value)} required />
              </Field>
            </div>

            <label className="check">
              <input type="checkbox" checked={visited} onChange={(e) => setVisited(e.target.checked)} />
              My child has already visited a health facility for this
            </label>

            <Field label="Anything else? (optional)">
              <textarea className="input" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} placeholder="E.g. how much they're eating or drinking, what you've tried…" />
            </Field>

            <label className="check">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
              <span>
                Include this report in <strong>anonymous</strong> community health statistics. Your child's identity is
                never shared.
              </span>
            </label>

            <ErrorText error={submit.error} />
            <div className="row">
              <Button disabled={!childId || selected.length === 0 || submit.isPending}>
                {submit.isPending ? "Saving…" : "Submit report"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => navigate(-1)}>Cancel</Button>
            </div>
          </form>
        </Card>

        <div className="stack">
          <div className="callout warn">
            <AlertTriangle size={20} />
            <div>
              <strong>Seek care now if your child:</strong>
              <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                <li>has difficulty breathing</li>
                <li>is very drowsy or hard to wake</li>
                <li>cannot keep any fluids down</li>
                <li>has a fever with a stiff neck or rash</li>
              </ul>
            </div>
          </div>
          <div className="callout info">
            <ShieldCheck size={20} />
            <div>
              This is an <strong>observation</strong>, not a diagnosis. Only a health professional can confirm a
              condition.
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
