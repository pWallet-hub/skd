import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { get, post } from "../api/client";
import type { Child, Symptom, SymptomReport } from "../api/types";
import { Card, ErrorText, Loading } from "../components/ui";

const today = () => new Date().toISOString().slice(0, 10);

export default function ReportSymptomsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const children = useQuery({ queryKey: ["children"], queryFn: () => get<Child[]>("/children") });
  const symptoms = useQuery({ queryKey: ["symptoms"], queryFn: () => get<Symptom[]>("/symptoms") });

  const [childId, setChildId] = useState<number | "">("");
  const [selected, setSelected] = useState<number[]>([]);
  const [onset, setOnset] = useState(today());
  const [visited, setVisited] = useState(false);
  const [consent, setConsent] = useState(true);
  const [notes, setNotes] = useState("");

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
      navigate("/family");
    },
  });

  const toggle = (id: number) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    submit.mutate();
  }

  if (children.isLoading || symptoms.isLoading) return <Loading />;

  return (
    <Card title="Report a health concern">
      <p className="notice">
        This is an observation, not a diagnosis. If your child has difficulty breathing, is very
        drowsy, or cannot keep fluids down, go to the nearest health facility now.
      </p>
      <form className="form" onSubmit={onSubmit}>
        <label>
          Child
          <select value={childId} onChange={(e) => setChildId(Number(e.target.value))} required>
            <option value="">Select a child…</option>
            {children.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.display_name}
              </option>
            ))}
          </select>
        </label>

        <fieldset>
          <legend>Symptoms</legend>
          <div className="chips">
            {symptoms.data?.map((s) => (
              <label key={s.id} className={`chip ${selected.includes(s.id) ? "on" : ""}`}>
                <input type="checkbox" checked={selected.includes(s.id)} onChange={() => toggle(s.id)} />
                {s.name}
              </label>
            ))}
          </div>
        </fieldset>

        <label>
          When did it start?
          <input type="date" value={onset} max={today()} onChange={(e) => setOnset(e.target.value)} required />
        </label>
        <label className="inline">
          <input type="checkbox" checked={visited} onChange={(e) => setVisited(e.target.checked)} />
          My child has visited a health facility for this
        </label>
        <label>
          Notes (optional)
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
        </label>
        <label className="inline">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          Include this report, without my child's identity, in community health statistics
        </label>
        <ErrorText error={submit.error} />
        <button disabled={!childId || selected.length === 0 || submit.isPending}>
          {submit.isPending ? "Saving…" : "Submit report"}
        </button>
      </form>
    </Card>
  );
}
