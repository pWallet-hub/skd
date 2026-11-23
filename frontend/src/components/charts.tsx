/**
 * Small dependency-free charts. Single series → no legend; the card title names it.
 * Colour: reference palette slot 1 (--series-1). Bars are thin, rounded at the data end,
 * anchored to the baseline, with a per-bar hover tooltip.
 */
import { useState } from "react";

export interface DailyPoint {
  day: string;
  count: number;
}

const fmtDay = (d: string) =>
  new Date(`${d}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export function DailyBars({ data, height = 200, unit = "reports" }: { data: DailyPoint[]; height?: number; unit?: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const width = 640;
  const pad = { top: 12, right: 8, bottom: 26, left: 30 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;
  const max = Math.max(4, ...data.map((d) => d.count));
  const niceMax = Math.ceil(max / 4) * 4;
  const ticks = [0, niceMax / 4, niceMax / 2, (3 * niceMax) / 4, niceMax];
  const slot = innerW / Math.max(1, data.length);
  const barW = Math.max(3, Math.min(14, slot - 4));
  const y = (v: number) => pad.top + innerH - (v / niceMax) * innerH;

  return (
    <div className="chart" onMouseLeave={() => setHover(null)}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Daily ${unit}`}>
        <g className="axis">
          {ticks.map((t) => (
            <g key={t}>
              <line className="grid-line" x1={pad.left} x2={width - pad.right} y1={y(t)} y2={y(t)} />
              <text x={pad.left - 8} y={y(t) + 4} textAnchor="end">
                {t}
              </text>
            </g>
          ))}
          {data.map((d, i) =>
            i % Math.ceil(data.length / 6) === 0 ? (
              <text key={d.day} x={pad.left + slot * i + slot / 2} y={height - 6} textAnchor="middle">
                {fmtDay(d.day)}
              </text>
            ) : null,
          )}
        </g>
        {data.map((d, i) => {
          const x = pad.left + slot * i + (slot - barW) / 2;
          const h = Math.max(0, (d.count / niceMax) * innerH);
          const r = Math.min(4, barW / 2, h);
          const top = pad.top + innerH - h;
          // Rounded top, square base anchored to the baseline.
          const base = pad.top + innerH;
          const path =
            h === 0
              ? ""
              : `M${x},${base} V${top + r} Q${x},${top} ${x + r},${top} H${x + barW - r} Q${x + barW},${top} ${x + barW},${top + r} V${base} Z`;
          return (
            <g key={d.day} onMouseEnter={() => setHover(i)}>
              {/* generous hit target */}
              <rect x={pad.left + slot * i} y={pad.top} width={slot} height={innerH} fill="transparent" />
              {path && <path d={path} className={`bar ${hover !== null && hover !== i ? "dim" : ""}`} />}
            </g>
          );
        })}
      </svg>
      {hover !== null && data[hover] && (
        <div
          className="chart-tip"
          style={{
            left: `${((pad.left + slot * hover + slot / 2) / width) * 100}%`,
            top: `${(y(data[hover].count) / height) * 100}%`,
          }}
        >
          <strong>{data[hover].count}</strong> {unit} · {fmtDay(data[hover].day)}
        </div>
      )}
    </div>
  );
}

export function HBarList({ items }: { items: { label: string; value: number }[] }) {
  const max = Math.max(1, ...items.map((i) => i.value));
  return (
    <div>
      {items.map((item) => (
        <div className="hbar" key={item.label} title={`${item.label}: ${item.value}`}>
          <span className="hbar-label">{item.label}</span>
          <div className="hbar-track">
            <div className="hbar-fill" style={{ width: `${(item.value / max) * 100}%` }} />
          </div>
          <span className="hbar-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
