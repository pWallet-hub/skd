import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { get, post } from "../api/client";
import type { NotificationItem } from "../api/types";
import { Bell, BellRing, BookOpen, Check, Megaphone } from "../components/icons";
import { Badge, Button, Card, EmptyState, Loading, PageHeader } from "../components/ui";
import { formatDateTime } from "../utils/format";

const icon = (kind: string) =>
  kind === "community_alert" ? (
    <div className="list-icon danger"><Megaphone size={18} /></div>
  ) : kind === "guidance" ? (
    <div className="list-icon brand"><BookOpen size={18} /></div>
  ) : (
    <div className="list-icon info"><BellRing size={18} /></div>
  );

export default function NotificationsPage() {
  const qc = useQueryClient();
  const items = useQuery({ queryKey: ["notifications"], queryFn: () => get<NotificationItem[]>("/notifications") });
  const refresh = () => qc.invalidateQueries({ queryKey: ["notifications"] });
  const readAll = useMutation({ mutationFn: () => post("/notifications/read-all"), onSuccess: refresh });
  const readOne = useMutation({ mutationFn: (id: number) => post(`/notifications/${id}/read`), onSuccess: refresh });
  const unread = items.data?.filter((n) => !n.read_at).length ?? 0;

  return (
    <>
      <PageHeader
        title="Notifications"
        subtitle={unread ? `${unread} unread` : "You're all caught up."}
        actions={
          <Button variant="secondary" icon={<Check size={16} />} disabled={!unread} onClick={() => readAll.mutate()}>
            Mark all as read
          </Button>
        }
      />
      <Card flush>
        {items.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
        {items.data?.length === 0 && <EmptyState title="No notifications" icon={<Bell size={22} />} />}
        <ul className="list">
          {items.data?.map((n) => (
            <li key={n.id} className={`list-item ${n.read_at ? "" : "unread"}`}>
              {icon(n.kind)}
              <div className="body">
                <div className="row">
                  <span className="strong">{n.title}</span>
                  <Badge value={n.kind} />
                </div>
                <p style={{ marginTop: 4 }}>{n.body}</p>
                <div className="muted small" style={{ marginTop: 4 }}>{formatDateTime(n.created_at)}</div>
              </div>
              {!n.read_at && (
                <Button variant="ghost" size="sm" onClick={() => readOne.mutate(n.id)}>Mark read</Button>
              )}
            </li>
          ))}
        </ul>
      </Card>
    </>
  );
}
