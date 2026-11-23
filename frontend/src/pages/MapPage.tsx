import { useQuery } from "@tanstack/react-query";
import "leaflet/dist/leaflet.css";
import { useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import { Link } from "react-router-dom";
import { get } from "../api/client";
import type { AreaAggregate, Facility, Infrastructure, School, Signal } from "../api/types";
import { Card, PageHeader } from "../components/ui";
import { humanize } from "../utils/format";
import { DEFAULT_CENTER, TILE_ATTRIBUTION, TILE_URL } from "../utils/map";

// Layer colours: reports/signals use warm status-like hues; places use the categorical palette.
const LAYERS = {
  reports: { label: "Community reports", color: "#eb6834" },
  signals: { label: "Signals", color: "#c2262e" },
  schools: { label: "Schools", color: "#2a78d6" },
  facilities: { label: "Health facilities", color: "#1baf7a" },
  infrastructure: { label: "Infrastructure", color: "#6250d6" },
} as const;
type LayerKey = keyof typeof LAYERS;

export default function MapPage() {
  const [days, setDays] = useState(14);
  const [visible, setVisible] = useState<Record<LayerKey, boolean>>({
    reports: true, signals: true, schools: true, facilities: true, infrastructure: false,
  });
  const areas = useQuery({ queryKey: ["areas-agg", days], queryFn: () => get<AreaAggregate[]>(`/analytics/areas?days=${days}`) });
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => get<School[]>("/geo/schools") });
  const facilities = useQuery({ queryKey: ["facilities"], queryFn: () => get<Facility[]>("/geo/facilities") });
  const infra = useQuery({ queryKey: ["infra"], queryFn: () => get<Infrastructure[]>("/geo/infrastructure") });
  const signals = useQuery({ queryKey: ["signals"], queryFn: () => get<Signal[]>("/signals") });
  const openSignals = signals.data?.filter((s) => ["detected", "under_review", "confirmed"].includes(s.status));

  const toggle = (k: LayerKey) => setVisible((v) => ({ ...v, [k]: !v[k] }));

  return (
    <>
      <PageHeader
        title="Geographic intelligence"
        subtitle="Aggregated reports alongside schools, health facilities and infrastructure."
        actions={
          <select className="input" style={{ width: "auto" }} value={days} onChange={(e) => setDays(Number(e.target.value))} aria-label="Time range">
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        }
      />
      <Card
        title="Layers"
        subtitle="Areas below the minimum count are hidden. Infrastructure is context, not evidence of a cause."
        actions={
          <div className="layer-toggles">
            {(Object.keys(LAYERS) as LayerKey[]).map((k) => (
              <label key={k} className={`chip ${visible[k] ? "on" : ""}`}>
                <input type="checkbox" checked={visible[k]} onChange={() => toggle(k)} />
                <span className="legend-dot" style={{ background: LAYERS[k].color, marginRight: 0 }} />
                {LAYERS[k].label}
              </label>
            ))}
          </div>
        }
        flush
      >
        <MapContainer center={DEFAULT_CENTER} zoom={13} className="map" scrollWheelZoom>
          <TileLayer attribution={TILE_ATTRIBUTION} url={TILE_URL} />
          {visible.reports &&
            areas.data?.filter((a) => a.centroid && !a.suppressed).map((a) => (
              <CircleMarker
                key={`a${a.area_id}`}
                center={[a.centroid!.latitude, a.centroid!.longitude]}
                radius={10 + Math.sqrt(a.report_count ?? 0) * 5}
                pathOptions={{ color: "#fff", weight: 2, fillColor: LAYERS.reports.color, fillOpacity: 0.55 }}
              >
                <Tooltip>{a.area_name}: {a.report_count} reports</Tooltip>
                <Popup>
                  <strong>{a.area_name}</strong><br />
                  {a.report_count} reports · top concern: {a.top_category}
                </Popup>
              </CircleMarker>
            ))}
          {visible.signals &&
            openSignals?.map((s) => {
              const p = s.school?.location ?? s.area?.centroid;
              if (!p) return null;
              return (
                <CircleMarker
                  key={`s${s.id}`}
                  center={[p.latitude, p.longitude]}
                  radius={26}
                  pathOptions={{ color: LAYERS.signals.color, weight: 2, dashArray: "6 5", fillOpacity: 0.06 }}
                >
                  <Popup>
                    <strong>Signal #{s.id}</strong> — {s.symptom_category}<br />
                    {s.school?.name ?? s.area?.name}: {s.report_count} reports (≈{s.baseline_count} expected)<br />
                    Status: {humanize(s.status)}<br />
                    <Link to={`/signals/${s.id}`}>Open investigation →</Link>
                  </Popup>
                </CircleMarker>
              );
            })}
          {visible.schools &&
            schools.data?.filter((s) => s.location).map((s) => (
              <CircleMarker key={`sc${s.id}`} center={[s.location!.latitude, s.location!.longitude]} radius={7}
                pathOptions={{ color: "#fff", weight: 2, fillColor: LAYERS.schools.color, fillOpacity: 1 }}>
                <Tooltip>{s.name}</Tooltip>
              </CircleMarker>
            ))}
          {visible.facilities &&
            facilities.data?.filter((f) => f.location).map((f) => (
              <CircleMarker key={`f${f.id}`} center={[f.location!.latitude, f.location!.longitude]} radius={7}
                pathOptions={{ color: "#fff", weight: 2, fillColor: LAYERS.facilities.color, fillOpacity: 1 }}>
                <Tooltip>{f.name}</Tooltip>
                <Popup><strong>{f.name}</strong><br />{humanize(f.facility_type)} · {f.opening_hours}<br />{f.phone_number}</Popup>
              </CircleMarker>
            ))}
          {visible.infrastructure &&
            infra.data?.filter((i) => i.location).map((i) => (
              <CircleMarker key={`i${i.id}`} center={[i.location!.latitude, i.location!.longitude]} radius={6}
                pathOptions={{ color: "#fff", weight: 2, fillColor: LAYERS.infrastructure.color, fillOpacity: 1 }}>
                <Tooltip>{i.name}</Tooltip>
                <Popup><strong>{i.name}</strong><br />{humanize(i.asset_type)} · source: {i.data_source}</Popup>
              </CircleMarker>
            ))}
        </MapContainer>
      </Card>
    </>
  );
}
