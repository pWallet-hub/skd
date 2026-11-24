import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { get, post } from "../api/client";
import type { Area } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { homeFor } from "../auth/home";
import { GoogleButton } from "../components/GoogleButton";
import { Baby, ShieldCheck, Smile, Stethoscope } from "../components/icons";
import { Button, ErrorText, Field } from "../components/ui";

/** Self-registration for parents and guardians (staff accounts are created by admins). */
export default function RegisterPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const areas = useQuery({ queryKey: ["areas", "sector"], queryFn: () => get<Area[]>("/geo/areas?level=sector") });
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [areaId, setAreaId] = useState("");
  const [password, setPassword] = useState("");
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await post("/auth/register", {
        full_name: fullName,
        email,
        phone_number: phone || null,
        home_area_id: areaId ? Number(areaId) : null,
        password,
      });
      await login(email, password);
      navigate("/family?welcome=1");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <section className="auth-hero">
        <div className="row" style={{ gap: 10 }}>
          <div className="logo" style={{ background: "rgba(255,255,255,.16)" }}><Smile size={20} /></div>
          <strong>SmartKids · Smile &amp; Grow</strong>
        </div>
        <div>
          <h1>Join SmartKids — free for every family.</h1>
          <p>Keep your children's growth, vaccinations and health history in one safe place.</p>
          <div className="hero-points">
            <div className="hero-point"><span className="ic"><Baby size={18} /></span> Profiles for each child, growth charts and milestones</div>
            <div className="hero-point"><span className="ic"><Stethoscope size={18} /></span> Report concerns and get guidance instantly</div>
            <div className="hero-point"><span className="ic"><ShieldCheck size={18} /></span> You control what is shared — always</div>
          </div>
        </div>
        <p className="small" style={{ opacity: 0.7 }}>Prototype with fictional demo data.</p>
      </section>

      <section className="auth-panel">
        <form className="auth-form form" onSubmit={submit}>
          <div>
            <h2>Create your family account</h2>
            <p className="muted">For parents and guardians. Health staff accounts are created by an administrator.</p>
          </div>
          <GoogleButton label="Sign up with Google" />
          <div className="divider">or with email</div>
          <Field label="Full name"><input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required minLength={2} autoComplete="name" /></Field>
          <Field label="Email"><input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" /></Field>
          <div className="form-grid">
            <Field label="Phone (optional)"><input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" /></Field>
            <Field label="Your area">
              <select className="input" value={areaId} onChange={(e) => setAreaId(e.target.value)}>
                <option value="">Select…</option>
                {areas.data?.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </Field>
          </div>
          <Field label="Password" hint="At least 8 characters.">
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete="new-password" />
          </Field>
          <label className="check">
            <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} required />
            <span>I agree that SmartKids stores my family's information to provide this service. Community statistics only ever use anonymous, grouped data.</span>
          </label>
          <ErrorText error={error} />
          <Button disabled={busy || !agree} style={{ height: 44 }}>{busy ? "Creating account…" : "Create account"}</Button>
          <p className="small muted" style={{ textAlign: "center" }}>Already have an account? <Link to="/login">Sign in</Link></p>
        </form>
      </section>
    </div>
  );
}
