import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { get, post } from "../api/client";
import type { Signal, SignalStatus } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { MapPin, Radar, RefreshCw, School } from "../components/icons";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, Loading, PageHeader, Tabs } from "../components/ui";
import { formatDate } from "../utils/format";

type Filter = "open" | SignalStatus | "all";
const OPEN: SignalStatus[] = ["detected", "under_review", "confirmed"];

export default function SignalsPage() {
  const { user } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [filter, setFilter] = useState<Filter>("open");
  const signals = useQuery({ queryKey: ["signals"], queryFn: () => get<Signal[]>("/signals") });
  const detect = useMutation({
    mutationFn: () => post<{ created: number; updated: number }>("/signals/detect"),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["signals"] });
      toast(`Detection finished: ${r.created} new, ${r.updated} updated`);
    },
    onError: (e) => toast(e.message, "error"),
  });
  const canDetect = !!user && ["analyst", "health_reviewer", "admin"].includes(user.role);

  const list = signals.data?.filter((s) =>
    filter === "all" ? true : filter === "open" ? OPEN.includes(s.status) : s.status === filter,
  );
  const count = (f: Filter) =>
    signals.data?.filter((s) => (f === "all" ? true : f === "open" ? OPEN.includes(s.status) : s.status === f)).length ?? 0;

  return (
    <>
      <PageHeader
        title="Community health signals"
        subtitle="Unusual increases in similar reports. A signal is a prompt for human review — never a confirmed outbreak."
        actions={
          canDetect && (
            <Button icon={<RefreshCw size={16} />} onClick={() => detect.mutate()} disabled={detect.isPending}>
              {detect.isPending ? "Running…" : "Run detection now"}
            </Button>
          )
        }
      />
      <Tabs<Filter>
        value={filter}
        onChange={setFilter}
        tabs={[
          { value: "open", label: `Open (${count("open")})` },
          { value: "dismissed", label: `Dismissed (${count("dismissed")})` },
          { value: "resolved", label: `Resolved (${count("resolved")})` },
          { value: "all", label: `All (${count("all")})` },
        ]}
      />
      <Card flush>
        {signals.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
        {list?.length === 0 && <EmptyState title="No signals here" message="Detection runs every hour." icon={<Radar size={22} />} />}
        {!!list?.length && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Signal</th><th>Where</th><th className="num">Reports</th><th className="num">Expected</th><th className="num">Ratio</th><th>Window</th><th>Status</th></tr>
              </thead>
              <tbody>
                {list.map((s) => (
                  <tr key={s.id} className="clickable" onClick={() => navigate(`/signals/${s.id}`)}>
                    <td>
                      <div className="strong" style={{ textTransform: "capitalize" }}>{s.symptom_category}</div>
                      <div className="muted small">#{s.id}</div>
                    </td>
                    <td>
                      <span className="row" style={{ gap: 6, flexWrap: "nowrap" }}>
                        {s.school ? <School size={16} color="var(--text-3)" /> : <MapPin size={16} color="var(--text-3)" />}
                        {s.school?.name ?? s.area?.name}
                      </span>
                    </td>
                    <td className="num strong">{s.report_count}</td>
                    <td className="num">{s.baseline_count}</td>
                    <td className="num">×{s.score}</td>
                    <td className="small">{formatDate(s.window_start)} – {formatDate(s.window_end)}</td>
                    <td><Badge value={s.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
