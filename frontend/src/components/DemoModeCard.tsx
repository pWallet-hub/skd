import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { get, post, put } from "../api/client";
import type { DemoStatus } from "../api/types";
import { Sparkles } from "./icons";
import { useToast } from "./Toast";
import { Button, Card, Switch } from "./ui";
import { timeAgo } from "../utils/format";

/** Admin control for the live demo activity simulator. */
export function DemoModeCard() {
  const toast = useToast();
  const qc = useQueryClient();
  const status = useQuery({ queryKey: ["demo"], queryFn: () => get<DemoStatus>("/admin/demo"), refetchInterval: 30_000 });
  const refreshAll = () => {
    qc.invalidateQueries();
  };
  const toggle = useMutation({
    mutationFn: (enabled: boolean) => put<DemoStatus>("/admin/demo", { enabled }),
    onSuccess: (s) => {
      qc.setQueryData(["demo"], s);
      toast(s.enabled ? "Demo mode on — activity will appear every few minutes" : "Demo mode off");
    },
  });
  const simulate = useMutation({
    mutationFn: () => post<Record<string, number>>("/admin/demo/simulate"),
    onSuccess: (stats) => {
      refreshAll();
      const parts = Object.entries(stats).filter(([, v]) => v).map(([k, v]) => `${v} ${k.replace("_", " ")}`);
      toast(parts.length ? `Generated: ${parts.join(", ")}` : "Nothing new this round — try again");
    },
  });
  const s = status.data;
  const minutes = s ? Math.round(s.interval_seconds / 60) : 3;

  return (
    <Card
      title={<span className="row" style={{ gap: 8 }}><Sparkles size={18} /> Demo mode</span>}
      subtitle="For presentations: the fictional demo families keep using the app — new reports, recoveries, growth checks, vaccinations and new sign-ups."
      flush
    >
      <div className="setting-row">
        <div>
          <div className="strong">Simulate live activity</div>
          <div className="muted small">Runs every {minutes} minutes in the background while on. Only demo accounts (…@example.com) are affected.</div>
          {s?.last_run_at && (
            <div className="default">
              Last run {timeAgo(s.last_run_at)}
              {s.last_run_stats && ": " + Object.entries(s.last_run_stats).filter(([, v]) => v).map(([k, v]) => `${v} ${k.replace("_", " ")}`).join(", ")}
            </div>
          )}
        </div>
        <div className="row" style={{ justifyContent: "flex-end" }}>
          {s && <Switch checked={s.enabled} label="Simulate live activity" onChange={(v) => toggle.mutate(v)} />}
          <span className="small muted">{s?.enabled ? "On" : "Off"}</span>
        </div>
      </div>
      <div className="setting-row">
        <div>
          <div className="strong">Generate activity now</div>
          <div className="muted small">Instantly adds a round of realistic activity — handy right before showing a dashboard.</div>
        </div>
        <div className="row" style={{ justifyContent: "flex-end" }}>
          <Button variant="secondary" icon={<Sparkles size={16} />} onClick={() => simulate.mutate()} disabled={simulate.isPending}>
            {simulate.isPending ? "Generating…" : "Generate"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
