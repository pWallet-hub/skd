import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ChevronLeft, ChevronRight, Sparkles } from "./icons";

/* ------------------------------------------------------------- layout --- */
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div className="titles">
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

export function Card({
  title,
  subtitle,
  actions,
  children,
  flush,
  className = "",
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  flush?: boolean;
  className?: string;
}) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <div className="card-head">
          <div className="titles">
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      <div className={`card-body ${flush ? "flush" : ""}`}>{children}</div>
    </section>
  );
}

/* ------------------------------------------------------------ buttons --- */
type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  variant = "primary",
  size,
  icon,
  children,
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: "sm"; icon?: ReactNode }) {
  return (
    <button className={`btn btn-${variant} ${size ? "btn-sm" : ""} ${className}`} {...rest}>
      {icon}
      {children}
    </button>
  );
}

/* ------------------------------------------------------------- badges --- */
const TONE: Record<string, string> = {
  // signals
  detected: "warn",
  under_review: "info",
  confirmed: "danger",
  dismissed: "",
  resolved: "ok",
  // alerts
  draft: "",
  pending_approval: "warn",
  approved: "info",
  published: "ok",
  retracted: "",
  info: "info",
  advisory: "warn",
  warning: "danger",
  // notifications
  community_alert: "danger",
  guidance: "brand",
  reminder: "info",
  follow_up: "info",
  // content
  in_review: "warn",
  archived: "",
  // reports
  ongoing: "warn",
  recovered: "ok",
  parent_observation: "",
  clinically_confirmed: "info",
  // users
  active: "ok",
  inactive: "danger",
  admin: "danger",
  health_reviewer: "info",
  analyst: "brand",
  institution: "warn",
  parent: "",
};

export function Badge({ value, label, icon }: { value: string; label?: string; icon?: ReactNode }) {
  const tone = TONE[value] ?? "";
  return (
    <span className={`badge ${tone ? `badge-${tone}` : ""}`}>
      {icon}
      {label ?? value.replace(/_/g, " ")}
    </span>
  );
}

/* -------------------------------------------------------------- stats --- */
export function StatCard({
  label,
  value,
  icon,
  tone = "brand",
  sub,
}: {
  label: string;
  value: ReactNode;
  icon: ReactNode;
  tone?: "brand" | "info" | "warn" | "danger" | "ok";
  sub?: ReactNode;
}) {
  return (
    <div className="stat">
      <div className={`stat-icon ${tone}`}>{icon}</div>
      <div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
        {sub && <div className="stat-sub">{sub}</div>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------- states --- */
export function EmptyState({
  title,
  message,
  icon,
  action,
}: {
  title: string;
  message?: string;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon ?? <Sparkles size={22} />}</div>
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {action && <div style={{ marginTop: 14 }}>{action}</div>}
    </div>
  );
}

export function Skeleton({ height = 16, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} />;
}

export function Loading({ rows = 3 }: { rows?: number }) {
  return (
    <div className="stack" style={{ gap: 10, padding: "4px 0" }}>
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} height={18} width={`${90 - i * 12}%`} />
      ))}
    </div>
  );
}

export function ErrorText({ error }: { error: unknown }) {
  if (!error) return null;
  return <p className="error-text">{error instanceof Error ? error.message : String(error)}</p>;
}

/* --------------------------------------------------------------- misc --- */
export function Avatar({ name, src, size }: { name: string; src?: string | null; size?: "lg" }) {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return <div className={`avatar ${size ?? ""}`}>{src ? <img src={src} alt="" /> : initials}</div>;
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="field">
      {label}
      {children}
      {hint && <span className="hint">{hint}</span>}
    </label>
  );
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="switch" title={label}>
      <input type="checkbox" checked={checked} aria-label={label} onChange={(e) => onChange(e.target.checked)} />
      <span />
    </label>
  );
}

export function Tabs<T extends string>({
  tabs,
  value,
  onChange,
}: {
  tabs: { value: T; label: string; icon?: ReactNode }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((t) => (
        <button
          key={t.value}
          role="tab"
          aria-selected={value === t.value}
          className={`tab ${value === t.value ? "active" : ""}`}
          onClick={() => onChange(t.value)}
        >
          {t.icon}
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Pagination({
  total,
  limit,
  offset,
  onChange,
}: {
  total: number;
  limit: number;
  offset: number;
  onChange: (offset: number) => void;
}) {
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + limit, total);
  return (
    <div className="pagination">
      <span>
        {from}–{to} of {total}
      </span>
      <div className="row">
        <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))} icon={<ChevronLeft size={16} />}>
          Previous
        </Button>
        <Button variant="secondary" size="sm" disabled={to >= total} onClick={() => onChange(offset + limit)}>
          Next <ChevronRight size={16} />
        </Button>
      </div>
    </div>
  );
}
