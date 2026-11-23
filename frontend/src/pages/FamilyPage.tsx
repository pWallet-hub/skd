import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { get } from "../api/client";
import type { Child, NotificationItem, SymptomReport } from "../api/types";
import { Badge, Card, ErrorText, Loading } from "../components/ui";
import { ageLabel, formatDate } from "../utils/format";

export default function FamilyPage() {
  const children = useQuery({ queryKey: ["children"], queryFn: () => get<Child[]>("/children") });
  const reports = useQuery({ queryKey: ["reports"], queryFn: () => get<SymptomReport[]>("/reports?limit=10") });
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => get<NotificationItem[]>("/notifications"),
  });
  const nameOf = (id: number) => children.data?.find((c) => c.id === id)?.display_name ?? `#${id}`;

  return (
    <div className="grid">
      <Card title="My children" actions={<Link to="/report" className="button">Report symptoms</Link>}>
        {children.isLoading && <Loading />}
        <ErrorText error={children.error} />
        <div className="children">
          {children.data?.map((c) => (
            <div key={c.id} className="child">
              <div className="avatar">
                {c.photo_url ? <img src={c.photo_url} alt="" /> : c.display_name[0]}
              </div>
              <div>
                <strong>{c.display_name}</strong>
                <div className="muted">{ageLabel(c.age_months)}</div>
                <div className="muted small">{c.learning_interests.join(", ")}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Recent health reports">
        {reports.isLoading && <Loading />}
        {reports.data?.length === 0 && <p className="muted">No reports yet.</p>}
        <table>
          <tbody>
            {reports.data?.map((r) => (
              <tr key={r.id}>
                <td>{formatDate(r.onset_date)}</td>
                <td>{nameOf(r.child_id)}</td>
                <td>{r.symptoms.map((s) => s.name).join(", ")}</td>
                <td>{r.is_ongoing ? <Badge value="ongoing" /> : <Badge value="recovered" />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="Notifications">
        {notifications.data?.length === 0 && <p className="muted">You're all caught up.</p>}
        <ul className="list">
          {notifications.data?.slice(0, 5).map((n) => (
            <li key={n.id} className={n.read_at ? "" : "unread"}>
              <Badge value={n.kind} /> <strong>{n.title}</strong>
              <div className="muted small">{n.body}</div>
            </li>
          ))}
        </ul>
        <Link to="/notifications">All notifications →</Link>
      </Card>
    </div>
  );
}
