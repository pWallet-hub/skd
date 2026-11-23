import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { get } from "../../api/client";
import type { AuditEntry, Page } from "../../api/types";
import { ClipboardList, Search } from "../../components/icons";
import { Modal } from "../../components/Modal";
import { Card, EmptyState, Loading, PageHeader, Pagination } from "../../components/ui";
import { formatDateTime } from "../../utils/format";

const LIMIT = 25;
const ACTIONS = [
  ["", "All actions"],
  ["auth.", "Sign-ins"],
  ["user.", "User changes"],
  ["alert.", "Alerts"],
  ["signal.", "Signals"],
  ["report.", "Report verification"],
  ["article.", "Content"],
  ["settings.", "Settings"],
  ["school.", "Schools"],
  ["facility.", "Facilities"],
  ["infrastructure.", "Infrastructure"],
];

export default function AuditLogPage() {
  const [action, setAction] = useState("");
  const [actor, setActor] = useState("");
  const [offset, setOffset] = useState(0);
  const [open, setOpen] = useState<AuditEntry | null>(null);
  const qs = new URLSearchParams({ limit: String(LIMIT), offset: String(offset) });
  if (action) qs.set("action", action);
  if (actor) qs.set("actor", actor);
  const logs = useQuery({
    queryKey: ["admin-audit", qs.toString()],
    queryFn: () => get<Page<AuditEntry>>(`/admin/audit-logs?${qs}`),
    placeholderData: keepPreviousData,
  });

  return (
    <>
      <PageHeader title="Audit log" subtitle="Who did what, and when. Entries cannot be edited or deleted." />
      <Card flush>
        <div className="toolbar">
          <div className="input-icon">
            <Search size={16} />
            <input className="input" placeholder="Filter by user email…" value={actor} onChange={(e) => { setActor(e.target.value); setOffset(0); }} aria-label="Filter by user" />
          </div>
          <select className="input" value={action} onChange={(e) => { setAction(e.target.value); setOffset(0); }} aria-label="Filter by action">
            {ACTIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div className="card-body flush">
          {logs.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
          {logs.data?.items.length === 0 && <EmptyState title="No entries" icon={<ClipboardList size={22} />} />}
          {!!logs.data?.items.length && (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>When</th><th>Who</th><th>Action</th><th>Summary</th><th>IP</th></tr></thead>
                <tbody>
                  {logs.data.items.map((e) => (
                    <tr key={e.id} className="clickable" onClick={() => setOpen(e)}>
                      <td className="small" style={{ whiteSpace: "nowrap" }}>{formatDateTime(e.created_at)}</td>
                      <td className="small">{e.actor_email ?? "system"}</td>
                      <td><span className="badge mono" style={{ textTransform: "none" }}>{e.action}</span></td>
                      <td>{e.summary}</td>
                      <td className="mono muted">{e.ip_address ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        {logs.data && <Pagination total={logs.data.total} limit={LIMIT} offset={offset} onChange={setOffset} />}
      </Card>
      {open && (
        <Modal title={`Audit entry #${open.id}`} onClose={() => setOpen(null)}>
          <dl className="stack" style={{ gap: 10, margin: 0 }}>
            {[
              ["When", formatDateTime(open.created_at)],
              ["Who", open.actor_email ?? "system"],
              ["Action", open.action],
              ["Entity", `${open.entity_type}${open.entity_id ? ` #${open.entity_id}` : ""}`],
              ["IP address", open.ip_address ?? "—"],
              ["Summary", open.summary],
            ].map(([k, v]) => (
              <div key={k} className="spread"><dt className="muted">{k}</dt><dd style={{ margin: 0, textAlign: "right" }}>{v}</dd></div>
            ))}
          </dl>
          {Object.keys(open.details).length > 0 && (
            <pre className="mono" style={{ background: "var(--surface-2)", padding: 12, borderRadius: 10, marginTop: 16, overflowX: "auto" }}>
              {JSON.stringify(open.details, null, 2)}
            </pre>
          )}
        </Modal>
      )}
    </>
  );
}
