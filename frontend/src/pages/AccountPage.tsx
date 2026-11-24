import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { get, patch, post } from "../api/client";
import type { Area } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Check, KeyRound, Smile, UserCog } from "../components/icons";
import { useToast } from "../components/Toast";
import { Avatar, Button, Card, ErrorText, Field, PageHeader } from "../components/ui";
import { formatDate, ROLE_LABEL } from "../utils/format";
import { canInstall, isInstalled, isIOS, onInstallChange, promptInstall } from "../utils/install";

export default function AccountPage() {
  const { user, refresh } = useAuth();
  const toast = useToast();
  const areas = useQuery({ queryKey: ["areas", "sector"], queryFn: () => get<Area[]>("/geo/areas?level=sector") });
  const [name, setName] = useState(user?.full_name ?? "");
  const [phone, setPhone] = useState(user?.phone_number ?? "");
  const [areaId, setAreaId] = useState(String(user?.home_area_id ?? ""));
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [installable, setInstallable] = useState(canInstall());
  useEffect(() => onInstallChange(() => setInstallable(canInstall())), []);

  const saveProfile = useMutation({
    mutationFn: () => patch("/auth/me", { full_name: name, phone_number: phone || null, home_area_id: areaId ? Number(areaId) : null }),
    onSuccess: async () => { await refresh(); toast("Profile saved"); },
  });
  const changePassword = useMutation({
    mutationFn: () => post("/auth/change-password", { current_password: current, new_password: next }),
    onSuccess: () => { setCurrent(""); setNext(""); setConfirm(""); toast("Password changed"); },
  });

  if (!user) return null;
  const mismatch = confirm.length > 0 && next !== confirm;

  return (
    <>
      <PageHeader title="My account" subtitle="Your profile, password and app settings." />
      <div className="grid grid-main">
        <div className="stack">
          <Card title={<span className="row" style={{ gap: 8 }}><UserCog size={18} /> Profile</span>}>
            <form className="form" onSubmit={(e: FormEvent) => { e.preventDefault(); saveProfile.mutate(); }}>
              <div className="row" style={{ gap: 14 }}>
                <Avatar name={user.full_name} size="lg" />
                <div>
                  <div className="strong">{user.email}</div>
                  <div className="muted small">{ROLE_LABEL[user.role]} · member since {formatDate(user.created_at)}</div>
                </div>
              </div>
              <div className="form-grid">
                <Field label="Full name"><input className="input" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></Field>
                <Field label="Phone"><input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" /></Field>
                <Field label="Home area" hint="Used to show nearby care and relevant community alerts.">
                  <select className="input" value={areaId} onChange={(e) => setAreaId(e.target.value)}>
                    <option value="">—</option>
                    {areas.data?.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                </Field>
              </div>
              <ErrorText error={saveProfile.error} />
              <div><Button disabled={saveProfile.isPending} icon={<Check size={16} />}>Save profile</Button></div>
            </form>
          </Card>

          <Card title={<span className="row" style={{ gap: 8 }}><KeyRound size={18} /> Change password</span>}>
            <form className="form" onSubmit={(e: FormEvent) => { e.preventDefault(); changePassword.mutate(); }}>
              <Field label="Current password"><input className="input" type="password" value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" /></Field>
              <div className="form-grid">
                <Field label="New password" hint="At least 8 characters."><input className="input" type="password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} autoComplete="new-password" /></Field>
                <Field label="Repeat new password"><input className="input" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required autoComplete="new-password" /></Field>
              </div>
              {mismatch && <p className="error-text">The new passwords don't match.</p>}
              <ErrorText error={changePassword.error} />
              <div><Button disabled={changePassword.isPending || mismatch || !next}>Change password</Button></div>
            </form>
          </Card>
        </div>

        <Card title={<span className="row" style={{ gap: 8 }}><Smile size={18} /> SmartKids on your phone</span>}>
          {isInstalled() ? (
            <p>✅ You're using the installed app.</p>
          ) : installable ? (
            <div className="stack" style={{ gap: 12 }}>
              <p>Install SmartKids on this device to open it like any other app — straight from your home screen.</p>
              <div><Button onClick={async () => { if (await promptInstall()) toast("SmartKids installed"); }}>Install app</Button></div>
            </div>
          ) : isIOS() ? (
            <p>On iPhone or iPad: tap the <strong>Share</strong> button in Safari, then <strong>Add to Home Screen</strong>.</p>
          ) : (
            <p>Open this site in Chrome or Edge on your phone and choose <strong>Install app</strong> (or <strong>Add to Home screen</strong>) from the browser menu.</p>
          )}
          <p className="muted small" style={{ marginTop: 12 }}>The app keeps working when the connection drops; your data is only ever loaded live and securely.</p>
        </Card>
      </div>
    </>
  );
}
