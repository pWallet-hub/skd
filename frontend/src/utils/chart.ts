import type { DailyPoint } from "../components/charts";

/** Fill missing days with zeros so the time axis is continuous. */
export function fillDays(points: { day: string; count: number }[], days: number): DailyPoint[] {
  const map = new Map<string, number>();
  for (const p of points) map.set(p.day, (map.get(p.day) ?? 0) + p.count);
  const out: DailyPoint[] = [];
  const today = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    out.push({ day: key, count: map.get(key) ?? 0 });
  }
  return out;
}
