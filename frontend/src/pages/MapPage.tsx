import { useQuery } from "@tanstack/react-query";
import "leaflet/dist/leaflet.css";
import { useState } from "react";
import { CircleMarker, LayersControl, LayerGroup, MapContainer, Popup, TileLayer } from "react-leaflet";
import { get } from "../api/client";
import type { AreaAggregate, Facility, Infrastructure, School, Signal } from "../api/types";
import { Card } from "../components/ui";

const KIGALI: [number, number] = [-1.955, 30.09];

export default function MapPage() {
  const [days, setDays] = useState(14);
  const areas = useQuery({
    queryKey: ["areas-agg", days],
    queryFn: () => get<AreaAggregate[]>(`/analytics/areas?days=${days}`),
  });
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => get<School[]>("/geo/schools") });
  const facilities = useQuery({ queryKey: ["facilities"], queryFn: () => get<Facility[]>("/geo/facilities") });
  const infra = useQuery({ queryKey: ["infra"], queryFn: () => get<Infrastructure[]>("/geo/infrastructure") });
  const signals = useQuery({ queryKey: ["signals"], queryFn: () => get<Signal[]>("/signals") });

  const openSignals = signals.data?.filter((s) => ["detected", "under_review", "confirmed"].includes(s.status));

  return (
    <Card
      title="Geographic intelligence"
      actions={
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
        </select>
      }
    >
      <p className="muted small">
        Aggregated, de-identified data. Areas below the minimum count are hidden. Infrastructure is context
        for investigators, not evidence of a cause.
      </p>
      <MapContainer center={KIGALI} zoom={13} className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <LayersControl position="topright">
          <LayersControl.Overlay checked name="Community reports">
            <LayerGroup>
              {areas.data
                ?.filter((a) => a.centroid && !a.suppressed)
                .map((a) => (
                  <CircleMarker
                    key={a.area_id}
                    center={[a.centroid!.latitude, a.centroid!.longitude]}
                    radius={8 + Math.sqrt(a.report_count ?? 0) * 5}
                    pathOptions={{ color: "#e4572e", fillOpacity: 0.35 }}
                  >
                    <Popup>
                      <strong>{a.area_name}</strong>
                      <br />
                      {a.report_count} reports · top: {a.top_category}
                    </Popup>
                  </CircleMarker>
                ))}
            </LayerGroup>
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="Alerts / signals">
            <LayerGroup>
              {openSignals?.map((s) => {
                const p = s.school?.location ?? s.area?.centroid;
                if (!p) return null;
                return (
                  <CircleMarker
                    key={s.id}
                    center={[p.latitude, p.longitude]}
                    radius={22}
                    pathOptions={{ color: "#b00020", dashArray: "6 4", fillOpacity: 0.08 }}
                  >
                    <Popup>
                      <strong>Signal #{s.id}</strong> — {s.symptom_category}
                      <br />
                      {s.school?.name ?? s.area?.name}: {s.report_count} reports (expected ~{s.baseline_count})
                      <br />
                      Status: {s.status}
                    </Popup>
                  </CircleMarker>
                );
              })}
            </LayerGroup>
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="Schools">
            <LayerGroup>
              {schools.data?.filter((s) => s.location).map((s) => (
                <CircleMarker key={s.id} center={[s.location!.latitude, s.location!.longitude]} radius={6}
                  pathOptions={{ color: "#1d4ed8", fillOpacity: 0.9 }}>
                  <Popup>{s.name}</Popup>
                </CircleMarker>
              ))}
            </LayerGroup>
          </LayersControl.Overlay>
          <LayersControl.Overlay checked name="Health facilities">
            <LayerGroup>
              {facilities.data?.filter((f) => f.location).map((f) => (
                <CircleMarker key={f.id} center={[f.location!.latitude, f.location!.longitude]} radius={6}
                  pathOptions={{ color: "#15803d", fillOpacity: 0.9 }}>
                  <Popup>
                    <strong>{f.name}</strong>
                    <br />
                    {f.facility_type.replace("_", " ")} · {f.opening_hours}
                  </Popup>
                </CircleMarker>
              ))}
            </LayerGroup>
          </LayersControl.Overlay>
          <LayersControl.Overlay name="Infrastructure">
            <LayerGroup>
              {infra.data?.filter((i) => i.location).map((i) => (
                <CircleMarker key={i.id} center={[i.location!.latitude, i.location!.longitude]} radius={5}
                  pathOptions={{ color: "#7c3aed", fillOpacity: 0.9 }}>
                  <Popup>
                    <strong>{i.name}</strong>
                    <br />
                    {i.asset_type.replace("_", " ")} · source: {i.data_source}
                  </Popup>
                </CircleMarker>
              ))}
            </LayerGroup>
          </LayersControl.Overlay>
        </LayersControl>
      </MapContainer>
      <div className="legend">
        <span className="dot" style={{ background: "#e4572e" }} /> Reports
        <span className="dot" style={{ background: "#b00020" }} /> Signal
        <span className="dot" style={{ background: "#1d4ed8" }} /> School
        <span className="dot" style={{ background: "#15803d" }} /> Health facility
        <span className="dot" style={{ background: "#7c3aed" }} /> Infrastructure
      </div>
    </Card>
  );
}
