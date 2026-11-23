import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { homeFor } from "../auth/home";
import { HeartPulse, MapPin, Radar, Shield, ShieldCheck, Smile, Stethoscope, Users } from "../components/icons";
import { Button, ErrorText, Field } from "../components/ui";

const DEMO_ACCOUNTS = [
  { email: "parent@example.com", label: "Parent", icon: <Users size={16} /> },
  { email: "analyst@example.com", label: "Analyst", icon: <Radar size={16} /> },
  { email: "reviewer@example.com", label: "Health reviewer", icon: <Stethoscope size={16} /> },
  { email: "institution@example.com", label: "Institution", icon: <MapPin size={16} /> },
  { email: "admin@example.com", label: "Administrator", icon: <Shield size={16} /> },
];
const DEMO_PASSWORD = "SmartKids123!";

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  async function signIn(e?: FormEvent, demoEmail?: string) {
    e?.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await login(demoEmail ?? email, demoEmail ? DEMO_PASSWORD : password);
      navigate(homeFor(me.role));
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
          <div className="logo" style={{ background: "rgba(255,255,255,.16)" }}>
            <Smile size={20} />
          </div>
          <strong>SmartKids · Smile &amp; Grow</strong>
        </div>
        <div>
          <h1>Every child's wellbeing, connected to the community around them.</h1>
          <p>
            One place for families to follow their children's health and growth — and for health teams to
            spot community concerns early, review them carefully, and respond.
          </p>
          <div className="hero-points">
            <div className="hero-point">
              <span className="ic"><HeartPulse size={18} /></span> Child profiles, growth and health history
            </div>
            <div className="hero-point">
              <span className="ic"><Radar size={18} /></span> Early detection of unusual community patterns
            </div>
            <div className="hero-point">
              <span className="ic"><ShieldCheck size={18} /></span> Human review before any alert — privacy by design
            </div>
          </div>
        </div>
        <p className="small" style={{ opacity: 0.7 }}>Prototype with fictional demo data.</p>
      </section>

      <section className="auth-panel">
        <form className="auth-form form" onSubmit={signIn}>
          <div>
            <h2>Welcome back</h2>
            <p className="muted">Sign in to continue.</p>
          </div>
          <Field label="Email">
            <input className="input" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </Field>
          <Field label="Password">
            <input className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </Field>
          <ErrorText error={error} />
          <Button disabled={busy} style={{ height: 44 }}>{busy ? "Signing in…" : "Sign in"}</Button>

          <div>
            <div className="divider">or try a demo account</div>
            <div className="demo-grid">
              {DEMO_ACCOUNTS.map((a) => (
                <button type="button" key={a.email} className="demo-btn" disabled={busy} onClick={() => signIn(undefined, a.email)}>
                  {a.icon}
                  {a.label}
                </button>
              ))}
            </div>
            <p className="small muted" style={{ marginTop: 10 }}>
              All demo accounts use the password <span className="mono">{DEMO_PASSWORD}</span>
            </p>
          </div>
        </form>
      </section>
    </div>
  );
}
