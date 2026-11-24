import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { HeartPulse, ShieldCheck, Smile, TrendingUp } from "../components/icons";
import { Badge, Card, Loading } from "../components/ui";
import { ageLabel, formatDate, formatDateTime } from "../utils/format";

interface HealthCard {
  display_name: string;
  age_months: number;
  date_of_birth: string;
  sex: string;
  latest_height_cm: number | null;
  latest_weight_kg: number | null;
  measured_on: string | null;
  vaccines: { name: string; status: string; given_on: string | null; due_date: string }[];
  recent_concerns: string[];
  health_notes: string | null;
  expires_at: string;
}

const TONE: Record<string, string> = { given: "resolved", due: "pending_approval", overdue: "confirmed", upcoming: "draft" };

/** Public page opened by scanning a child's QR health card (no login). */
export default function HealthCardPage() {
  const { token } = useParams();
  const card = useQuery({
    queryKey: ["health-card", token],
    queryFn: async () => {
      const res = await fetch(`/api/v1/health-card/${token}`);
      const body = await res.json();
      if (!res.ok) throw new ApiError(res.status, body.detail ?? "Unavailable");
      return body as HealthCard;
    },
    retry: false,
  });

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", padding: "24px 16px" }}>
      <div style={{ maxWidth: 760, margin: "0 auto" }} className="stack">
        <div className="row" style={{ gap: 10 }}>
          <div className="logo"><Smile size={20} /></div>
          <div>
            <div className="brand-name">SmartKids health card</div>
            <div className="brand-sub">Read-only summary shared by the parent</div>
          </div>
        </div>
        {card.isLoading && <Card><Loading rows={5} /></Card>}
        {card.error && (
          <Card>
            <h2>This health card is not available</h2>
            <p className="muted" style={{ marginTop: 6 }}>{(card.error as Error).message}. Ask the parent to create a new QR code.</p>
          </Card>
        )}
        {card.data && (
          <>
            <Card>
              <h1>{card.data.display_name}</h1>
              <p className="muted">{ageLabel(card.data.age_months)} · born {formatDate(card.data.date_of_birth)} · {card.data.sex}</p>
              <p className="small muted" style={{ marginTop: 6 }}>Link valid until {formatDateTime(card.data.expires_at)}</p>
            </Card>
            <div className="grid grid-2">
              <Card title={<span className="row" style={{ gap: 8 }}><TrendingUp size={18} /> Latest growth</span>}>
                <p className="strong">{card.data.latest_height_cm ?? "—"} cm · {card.data.latest_weight_kg ?? "—"} kg</p>
                <p className="muted small">{card.data.measured_on ? `Measured ${formatDate(card.data.measured_on)}` : "No measurements"}</p>
              </Card>
              <Card title={<span className="row" style={{ gap: 8 }}><HeartPulse size={18} /> Recent concerns (parent-reported)</span>}>
                {card.data.recent_concerns.length === 0 ? <p className="muted">None recorded.</p> : (
                  <ul style={{ margin: 0, paddingLeft: 18 }}>{card.data.recent_concerns.map((c) => <li key={c}>{c}</li>)}</ul>
                )}
              </Card>
            </div>
            <Card title={<span className="row" style={{ gap: 8 }}><ShieldCheck size={18} /> Vaccinations</span>} flush>
              <div className="table-wrap">
                <table className="table">
                  <thead><tr><th>Vaccine</th><th>Due</th><th>Status</th></tr></thead>
                  <tbody>
                    {card.data.vaccines.map((v) => (
                      <tr key={v.name}>
                        <td className="strong">{v.name}</td>
                        <td className="small">{formatDate(v.due_date)}</td>
                        <td><Badge value={TONE[v.status]} label={v.status === "given" ? `Given ${formatDate(v.given_on)}` : v.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            <p className="small muted" style={{ textAlign: "center" }}>Prototype with fictional data. Parent reports are observations, not diagnoses.</p>
          </>
        )}
      </div>
    </div>
  );
}
