import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { get, post } from "../api/client";
import type { Signal } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Badge, Card, ErrorText, Loading } from "../components/ui";
import { formatDate } from "../utils/format";

export default function SignalsPage() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const signals = useQuery({ queryKey: ["signals"], queryFn: () => get<Signal[]>("/signals") });
  const detect = useMutation({
    mutationFn: () => post<{ created: number; updated: number }>("/signals/detect"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["signals"] }),
  });
  const canDetect = user && ["analyst", "health_reviewer", "admin"].includes(user.role);

  return (
    <Card
      title="Community health signals"
      actions={
        canDetect && (
          <button onClick={() => detect.mutate()} disabled={detect.isPending}>
            {detect.isPending ? "Running…" : "Run detection now"}
          </button>
        )
      }
    >
      <p className="muted small">
        A signal is an unusual increase in similar reports. It is a prompt for human review — never a
        confirmed outbreak or a cause.
      </p>
      {detect.data && (
        <p className="notice">
          Detection finished: {detect.data.created} new, {detect.data.updated} updated.
        </p>
      )}
      <ErrorText error={detect.error} />
      {signals.isLoading && <Loading />}
      {signals.data?.length === 0 && <p className="muted">No signals.</p>}
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Concern</th>
            <th>Where</th>
            <th>Reports / expected</th>
            <th>Window</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {signals.data?.map((s) => (
            <tr key={s.id}>
              <td>
                <Link to={`/signals/${s.id}`}>{s.id}</Link>
              </td>
              <td>{s.symptom_category}</td>
              <td>{s.school ? `🏫 ${s.school.name}` : `📍 ${s.area?.name}`}</td>
              <td>
                {s.report_count} / {s.baseline_count} <span className="muted">(×{s.score})</span>
              </td>
              <td>
                {formatDate(s.window_start)} – {formatDate(s.window_end)}
              </td>
              <td>
                <Badge value={s.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
