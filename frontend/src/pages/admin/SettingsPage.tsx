import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { get, post, put } from "../../api/client";
import type { DetectionSettings } from "../../api/types";
import { Gauge, Radar, RefreshCw, Shield } from "../../components/icons";
import { useToast } from "../../components/Toast";
import { Button, Card, ErrorText, Loading, PageHeader } from "../../components/ui";

const FIELDS: { key: keyof DetectionSettings; label: string; help: string; step?: number; min: number; max: number; unit: string }[] = [
  { key: "signal_window_days", label: "Detection window", help: "Recent period that is checked for an unusual increase.", min: 1, max: 60, unit: "days" },
  { key: "signal_baseline_days", label: "Baseline period", help: "Earlier period used to work out what is “normal”. Must be at least as long as the window.", min: 7, max: 365, unit: "days" },
  { key: "signal_min_reports", label: "Minimum reports", help: "A signal needs at least this many reports in the window — avoids alarms from one or two cases.", min: 2, max: 100, unit: "reports" },
  { key: "signal_ratio_threshold", label: "Increase threshold", help: "How many times above the expected level counts as unusual.", step: 0.1, min: 1, max: 20, unit: "× expected" },
];

export default function SettingsPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const current = useQuery({ queryKey: ["settings"], queryFn: () => get<DetectionSettings>("/admin/settings/detection") });
  const defaults = useQuery({ queryKey: ["settings-defaults"], queryFn: () => get<DetectionSettings>("/admin/settings/detection/defaults") });
  const [form, setForm] = useState<DetectionSettings | null>(null);
  useEffect(() => { if (current.data) setForm(current.data); }, [current.data]);

  const save = useMutation({
    mutationFn: (v: DetectionSettings) => put<DetectionSettings>("/admin/settings/detection", v),
    onSuccess: (v) => { qc.setQueryData(["settings"], v); toast("Settings saved"); },
  });
  const detect = useMutation({
    mutationFn: () => post<{ created: number; updated: number }>("/signals/detect"),
    onSuccess: (r) => { qc.invalidateQueries({ queryKey: ["signals"] }); toast(`Detection run: ${r.created} new, ${r.updated} updated`); },
  });

  if (!form) return <Loading rows={6} />;
  const dirty = JSON.stringify(form) !== JSON.stringify(current.data);
  const set = (k: keyof DetectionSettings, v: number) => setForm({ ...form, [k]: v });

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate(form!);
  }

  return (
    <>
      <PageHeader title="Settings" subtitle="Tune how community signals are detected and how data is protected. Changes are audited." />
      <form onSubmit={submit} className="stack">
        <Card
          title={<span className="row" style={{ gap: 8 }}><Radar size={18} /> Signal detection</span>}
          subtitle="Applied to the next detection run (hourly, or run it now)."
          flush
        >
          {FIELDS.map((f) => (
            <div key={f.key} className="setting-row">
              <div>
                <div className="strong">{f.label}</div>
                <div className="muted small">{f.help}</div>
                {defaults.data && <div className="default">Default: {defaults.data[f.key]} {f.unit}</div>}
              </div>
              <div className="row" style={{ flexWrap: "nowrap" }}>
                <input className="input" type="number" min={f.min} max={f.max} step={f.step ?? 1} value={form[f.key]} onChange={(e) => set(f.key, Number(e.target.value))} required />
                <span className="muted small" style={{ whiteSpace: "nowrap" }}>{f.unit}</span>
              </div>
            </div>
          ))}
        </Card>

        <Card title={<span className="row" style={{ gap: 8 }}><Shield size={18} /> Privacy</span>} flush>
          <div className="setting-row">
            <div>
              <div className="strong">Minimum group size</div>
              <div className="muted small">Areas or schools with fewer reports than this are hidden on the map, in statistics and exports.</div>
              {defaults.data && <div className="default">Default: {defaults.data.aggregate_min_cell_size} reports</div>}
            </div>
            <div className="row" style={{ flexWrap: "nowrap" }}>
              <input className="input" type="number" min={1} max={50} value={form.aggregate_min_cell_size} onChange={(e) => set("aggregate_min_cell_size", Number(e.target.value))} required />
              <span className="muted small">reports</span>
            </div>
          </div>
        </Card>

        <div className="callout info">
          <Gauge size={20} />
          <div>
            With these values, a signal is raised when the last <strong>{form.signal_window_days} days</strong> contain at
            least <strong>{form.signal_min_reports} reports</strong> and are at least <strong>×{form.signal_ratio_threshold}</strong> the
            level expected from the previous <strong>{form.signal_baseline_days} days</strong>.
          </div>
        </div>

        <ErrorText error={save.error ?? detect.error} />
        <div className="row">
          <Button disabled={!dirty || save.isPending}>{save.isPending ? "Saving…" : "Save settings"}</Button>
          <Button type="button" variant="ghost" disabled={!dirty} onClick={() => setForm(current.data!)}>Discard changes</Button>
          {defaults.data && <Button type="button" variant="ghost" onClick={() => setForm(defaults.data!)}>Reset to defaults</Button>}
          <span style={{ flex: 1 }} />
          <Button type="button" variant="secondary" icon={<RefreshCw size={16} />} disabled={detect.isPending || dirty} onClick={() => detect.mutate()}>
            Run detection now
          </Button>
        </div>
      </form>
    </>
  );
}
