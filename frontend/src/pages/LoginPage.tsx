import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { homeFor } from "../auth/home";
import { ErrorText } from "../components/ui";

const DEMO_ACCOUNTS = [
  ["parent@example.com", "Parent"],
  ["analyst@example.com", "Analyst"],
  ["reviewer@example.com", "Health reviewer"],
  ["institution@example.com", "Institution"],
];

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("parent@example.com");
  const [password, setPassword] = useState("SmartKids123!");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homeFor(user.role)} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await login(email, password);
      navigate(homeFor(me.role));
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <form className="card login-card" onSubmit={submit}>
        <h1>SmartKids</h1>
        <p className="muted">Smile &amp; Grow — sign in</p>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <ErrorText error={error} />
        <button disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <div className="demo-accounts">
          <span className="muted">Demo accounts (password SmartKids123!):</span>
          {DEMO_ACCOUNTS.map(([addr, label]) => (
            <button type="button" className="link" key={addr} onClick={() => setEmail(addr)}>
              {label}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
