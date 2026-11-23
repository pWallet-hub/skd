import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { get, post } from "../api/client";
import type { NotificationItem } from "../api/types";
import { Badge, Card, Loading } from "../components/ui";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const items = useQuery({
    queryKey: ["notifications"],
    queryFn: () => get<NotificationItem[]>("/notifications"),
  });
  const readAll = useMutation({
    mutationFn: () => post("/notifications/read-all"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <Card title="Notifications" actions={<button className="secondary" onClick={() => readAll.mutate()}>Mark all read</button>}>
      {items.isLoading && <Loading />}
      {items.data?.length === 0 && <p className="muted">Nothing here yet.</p>}
      <ul className="list">
        {items.data?.map((n) => (
          <li key={n.id} className={n.read_at ? "" : "unread"}>
            <Badge value={n.kind} /> <strong>{n.title}</strong>
            <span className="muted small"> · {new Date(n.created_at).toLocaleString()}</span>
            <div>{n.body}</div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
