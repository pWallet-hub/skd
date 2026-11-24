import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { get, post } from "../api/client";
import type { ReviewReport } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { CheckCircle2, ClipboardList, HeartPulse } from "../components/icons";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, Loading, PageHeader, Tabs } from "../components/ui";
import { ageLabel, formatDate, timeAgo } from "../utils/format";

type Filter = "parent_observation" | "clinically_confirmed" | "all";

/** Health reviewers check incoming parent reports. Children are shown by age and area, not name. */
export default function ReviewQueuePage() {
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [filter, setFilter] = useState<Filter>("parent_observation");
  const qs = filter === "all" ? "" : `&verification=${filter}`;
  const reports = useQuery({
    queryKey: ["review", filter],
    queryFn: () => get<ReviewReport[]>(`/reports?limit=60${qs}`),
    placeholderData: keepPreviousData,
    refetchInterval: 30_000,
  });
  const verify = useMutation({
    mutationFn: ({ id, verification }: { id: number; verification: string }) => post(`/reports/${id}/verification`, { verification }),
    onSuccess: (_, v) => {
      qc.invalidateQueries({ queryKey: ["review"] });
      toast(v.verification === "clinically_confirmed" ? "Marked clinically confirmed — the parent has been notified" : "Returned to parent observation");
    },
    onError: (e) => toast(e.message, "error"),
  });
  const canVerify = user?.role === "health_reviewer" || user?.role === "admin";

  return (
    <>
      <PageHeader
        title="Report review"
        subtitle="Incoming parent observations. Confirming a report records that a health professional has assessed it, and the parent is notified."
      />
      <Tabs<Filter>
        value={filter}
        onChange={setFilter}
        tabs={[
          { value: "parent_observation", label: "Awaiting review" },
          { value: "clinically_confirmed", label: "Clinically confirmed" },
          { value: "all", label: "All" },
        ]}
      />
      <Card flush>
        {reports.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
        {reports.data?.length === 0 && <EmptyState title="Nothing to review" icon={<ClipboardList size={22} />} />}
        <ul className="list">
          {reports.data?.map((r) => (
            <li key={r.id} className="list-item" style={{ alignItems: "center" }}>
              <div className={`list-icon ${r.is_ongoing ? "danger" : "brand"}`}><HeartPulse size={16} /></div>
              <div className="body">
                <div className="strong">{r.symptoms.map((s) => s.name).join(", ")}</div>
                <div className="muted small">
                  Child aged {r.child_age_months !== null ? ageLabel(r.child_age_months) : "?"} · {r.area_name ?? "unknown area"}
                  {r.school_name && ` · ${r.school_name}`} · started {formatDate(r.onset_date)} · reported {timeAgo(r.created_at)}
                  {r.visited_facility && " · visited a facility"}
                </div>
                {r.notes && <div className="small" style={{ marginTop: 4, color: "var(--text-2)" }}>“{r.notes}”</div>}
              </div>
              <Badge value={r.is_ongoing ? "ongoing" : "recovered"} />
              {canVerify && (r.verification === "parent_observation" ? (
                <Button size="sm" icon={<CheckCircle2 size={14} />} onClick={() => verify.mutate({ id: r.id, verification: "clinically_confirmed" })}>Confirm</Button>
              ) : (
                <Button size="sm" variant="ghost" onClick={() => verify.mutate({ id: r.id, verification: "parent_observation" })}>Undo</Button>
              ))}
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}
