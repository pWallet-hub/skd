import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { get, patch, post } from "../../api/client";
import type { AdminUser, Area, Page, UserRole } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";
import { KeyRound, Pencil, Search, UserPlus, Users } from "../../components/icons";
import { Modal } from "../../components/Modal";
import { useToast } from "../../components/Toast";
import { Avatar, Badge, Button, Card, EmptyState, ErrorText, Field, Loading, PageHeader, Pagination, Switch } from "../../components/ui";
import { formatDate, ROLE_LABEL, timeAgo } from "../../utils/format";

const ROLES: UserRole[] = ["parent", "health_reviewer", "analyst", "institution", "admin"];
const LIMIT = 15;

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

export default function UsersPage() {
  const { user: me } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState<"" | UserRole>("");
  const [status, setStatus] = useState<"" | "true" | "false">("");
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [creating, setCreating] = useState(params.get("new") === "1");
  const [secret, setSecret] = useState<{ email: string; password: string } | null>(null);
  const q = useDebounced(search);

  useEffect(() => setOffset(0), [q, role, status]);

  const qs = new URLSearchParams({ limit: String(LIMIT), offset: String(offset) });
  if (q) qs.set("search", q);
  if (role) qs.set("role", role);
  if (status) qs.set("is_active", status);
  const users = useQuery({
    queryKey: ["admin-users", qs.toString()],
    queryFn: () => get<Page<AdminUser>>(`/admin/users?${qs}`),
    placeholderData: keepPreviousData,
  });
  const areas = useQuery({ queryKey: ["areas", "sector"], queryFn: () => get<Area[]>("/geo/areas?level=sector") });
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["admin-users"] });
    qc.invalidateQueries({ queryKey: ["admin-stats"] });
  };

  const toggleActive = useMutation({
    mutationFn: (u: AdminUser) => patch<AdminUser>(`/admin/users/${u.id}`, { is_active: !u.is_active }),
    onSuccess: (u) => { refresh(); toast(`${u.email} ${u.is_active ? "activated" : "deactivated"}`); },
    onError: (e) => toast(e.message, "error"),
  });
  const resetPassword = useMutation({
    mutationFn: (u: AdminUser) => post<{ temporary_password: string }>(`/admin/users/${u.id}/reset-password`),
    onSuccess: (r, u) => setSecret({ email: u.email, password: r.temporary_password }),
    onError: (e) => toast(e.message, "error"),
  });

  return (
    <>
      <PageHeader
        title="Users"
        subtitle="Manage accounts, roles and access."
        actions={<Button icon={<UserPlus size={16} />} onClick={() => setCreating(true)}>Add user</Button>}
      />
      <Card flush>
        <div className="toolbar">
          <div className="input-icon">
            <Search size={16} />
            <input className="input" placeholder="Search name or email…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search users" />
          </div>
          <select className="input" value={role} onChange={(e) => setRole(e.target.value as UserRole | "")} aria-label="Filter by role">
            <option value="">All roles</option>
            {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
          </select>
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value as "" | "true" | "false")} aria-label="Filter by status">
            <option value="">Any status</option>
            <option value="true">Active</option>
            <option value="false">Deactivated</option>
          </select>
        </div>
        <div className="card-body flush">
          {users.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
          {users.data?.items.length === 0 && <EmptyState title="No users match" icon={<Users size={22} />} />}
          {!!users.data?.items.length && (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr><th>User</th><th>Role</th><th className="num">Children</th><th>Last sign-in</th><th>Joined</th><th>Active</th><th /></tr>
                </thead>
                <tbody>
                  {users.data.items.map((u) => (
                    <tr key={u.id} style={{ opacity: u.is_active ? 1 : 0.6 }}>
                      <td>
                        <div className="row" style={{ flexWrap: "nowrap", gap: 10 }}>
                          <Avatar name={u.full_name} />
                          <div>
                            <div className="strong">{u.full_name}</div>
                            <div className="muted small">{u.email}</div>
                          </div>
                        </div>
                      </td>
                      <td><Badge value={u.role} label={ROLE_LABEL[u.role]} /></td>
                      <td className="num">{u.role === "parent" ? u.children_count : "—"}</td>
                      <td className="small">{timeAgo(u.last_login_at)}</td>
                      <td className="small">{formatDate(u.created_at)}</td>
                      <td>
                        <Switch checked={u.is_active} label={u.is_active ? "Deactivate" : "Activate"} onChange={() => u.id !== me?.id && toggleActive.mutate(u)} />
                      </td>
                      <td>
                        <div className="row" style={{ flexWrap: "nowrap", gap: 4 }}>
                          <Button variant="ghost" size="sm" aria-label="Edit" title="Edit" onClick={() => setEditing(u)}><Pencil size={15} /></Button>
                          <Button variant="ghost" size="sm" aria-label="Reset password" title="Reset password" onClick={() => resetPassword.mutate(u)}><KeyRound size={15} /></Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        {users.data && <Pagination total={users.data.total} limit={LIMIT} offset={offset} onChange={setOffset} />}
      </Card>

      {(creating || editing) && (
        <UserForm
          user={editing}
          areas={areas.data ?? []}
          isSelf={editing?.id === me?.id}
          onClose={() => { setCreating(false); setEditing(null); setParams({}); }}
          onSaved={(result) => {
            refresh();
            setCreating(false);
            setEditing(null);
            setParams({});
            if (result?.temporary_password) setSecret({ email: result.user.email, password: result.temporary_password });
            else toast("User saved");
          }}
        />
      )}

      {secret && (
        <Modal title="Temporary password" onClose={() => setSecret(null)} footer={<Button onClick={() => setSecret(null)}>Done</Button>}>
          <p>Share this password with <strong>{secret.email}</strong> through a secure channel. It is shown only once.</p>
          <div className="row" style={{ marginTop: 14 }}>
            <code className="mono" style={{ fontSize: "1.1rem", padding: "10px 14px", background: "var(--surface-2)", borderRadius: 10, flex: 1 }}>{secret.password}</code>
            <Button variant="secondary" onClick={() => { navigator.clipboard?.writeText(secret.password); toast("Copied"); }}>Copy</Button>
          </div>
        </Modal>
      )}
    </>
  );
}

function UserForm({
  user,
  areas,
  isSelf,
  onClose,
  onSaved,
}: {
  user: AdminUser | null;
  areas: Area[];
  isSelf: boolean;
  onClose: () => void;
  onSaved: (r?: { user: AdminUser; temporary_password: string | null }) => void;
}) {
  const [email, setEmail] = useState(user?.email ?? "");
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [phone, setPhone] = useState(user?.phone_number ?? "");
  const [role, setRole] = useState<UserRole>(user?.role ?? "analyst");
  const [areaId, setAreaId] = useState<string>(user?.home_area_id ? String(user.home_area_id) : "");
  const [password, setPassword] = useState("");

  const save = useMutation({
    mutationFn: async () => {
      const base = { full_name: fullName, role, phone_number: phone || null, home_area_id: areaId ? Number(areaId) : null };
      if (user) {
        await patch(`/admin/users/${user.id}`, base);
        return undefined;
      }
      return post<{ user: AdminUser; temporary_password: string | null }>("/admin/users", { ...base, email, password: password || null });
    },
    onSuccess: onSaved,
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }

  return (
    <Modal
      title={user ? `Edit ${user.full_name}` : "Add user"}
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button form="user-form" disabled={save.isPending}>{user ? "Save changes" : "Create user"}</Button>
        </>
      }
    >
      <form id="user-form" className="form" onSubmit={submit}>
        <div className="form-grid">
          <Field label="Full name"><input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} /></Field>
          <Field label="Email"><input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={!!user} /></Field>
          <Field label="Role" hint={isSelf ? "You can't change your own role." : undefined}>
            <select className="input" value={role} onChange={(e) => setRole(e.target.value as UserRole)} disabled={isSelf}>
              {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
          </Field>
          <Field label="Phone (optional)"><input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} /></Field>
          <Field label="Home area (optional)">
            <select className="input" value={areaId} onChange={(e) => setAreaId(e.target.value)}>
              <option value="">—</option>
              {areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          {!user && (
            <Field label="Password (optional)" hint="Leave empty to generate a temporary one.">
              <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} />
            </Field>
          )}
        </div>
        <ErrorText error={save.error} />
      </form>
    </Modal>
  );
}
