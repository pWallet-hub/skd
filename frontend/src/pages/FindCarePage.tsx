import { useQuery } from "@tanstack/react-query";
import "leaflet/dist/leaflet.css";
import { useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import { get } from "../api/client";
import type { Area, FacilityNearby, LatLng } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Hospital, LocateFixed, Navigation, Phone } from "../components/icons";
import { Badge, Button, Card, EmptyState, Loading, PageHeader } from "../components/ui";
import { humanize } from "../utils/format";
import { DEFAULT_CENTER, TILE_ATTRIBUTION, TILE_URL } from "../utils/map";

/** Nearby health facilities, from the family's home area or the device location. */
export default function FindCarePage() {
  const { user } = useAuth();
  const [here, setHere] = useState<LatLng | null>(null);
  const [locating, setLocating] = useState(false);
  const areas = useQuery({ queryKey: ["areas", "sector"], queryFn: () => get<Area[]>("/geo/areas?level=sector") });
  const home = areas.data?.find((a) => a.id === user?.home_area_id)?.centroid ?? null;
  const origin: LatLng = here ?? home ?? { latitude: DEFAULT_CENTER[0], longitude: DEFAULT_CENTER[1] };

  const nearby = useQuery({
    queryKey: ["nearby", origin.latitude, origin.longitude],
    queryFn: () => get<FacilityNearby[]>(`/geo/facilities/nearby?latitude=${origin.latitude}&longitude=${origin.longitude}&radius_m=15000&limit=10`),
    enabled: !areas.isLoading,
  });

  function useMyLocation() {
    if (!navigator.geolocation) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (p) => { setHere({ latitude: p.coords.latitude, longitude: p.coords.longitude }); setLocating(false); },
      () => setLocating(false),
      { timeout: 8000 },
    );
  }

  return (
    <>
      <PageHeader
        title="Find care nearby"
        subtitle={here ? "Closest to your current location." : "Closest to your home area. Use your location for more precise results."}
        actions={<Button variant="secondary" icon={<LocateFixed size={16} />} onClick={useMyLocation} disabled={locating}>{locating ? "Locating…" : "Use my location"}</Button>}
      />
      <div className="callout warn" style={{ marginBottom: 18 }}>
        <Hospital size={20} />
        <div>In an emergency, go to the nearest hospital immediately or call your local emergency number.</div>
      </div>
      <div className="grid grid-main">
        <Card flush>
          <MapContainer key={`${origin.latitude},${origin.longitude}`} center={[origin.latitude, origin.longitude]} zoom={13} className="map" style={{ height: 520, borderRadius: "var(--radius-lg)" }}>
            <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
            <CircleMarker center={[origin.latitude, origin.longitude]} radius={8} pathOptions={{ color: "#fff", weight: 3, fillColor: "#2a78d6", fillOpacity: 1 }}>
              <Popup>{here ? "You are here" : "Your home area"}</Popup>
            </CircleMarker>
            {nearby.data?.filter((f) => f.location).map((f) => (
              <CircleMarker key={f.id} center={[f.location!.latitude, f.location!.longitude]} radius={9} pathOptions={{ color: "#fff", weight: 2, fillColor: "#1baf7a", fillOpacity: 1 }}>
                <Popup><strong>{f.name}</strong><br />{humanize(f.facility_type)} · {(f.distance_m / 1000).toFixed(1)} km</Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </Card>
        <Card title="Nearest facilities" flush>
          {nearby.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
          {nearby.data?.length === 0 && <EmptyState title="No facilities within 15 km" icon={<Hospital size={22} />} />}
          <ul className="list">
            {nearby.data?.map((f) => (
              <li key={f.id} className="list-item">
                <div className="list-icon brand"><Hospital size={18} /></div>
                <div className="body">
                  <div className="strong">{f.name}</div>
                  <div className="muted small">{humanize(f.facility_type)} · {(f.distance_m / 1000).toFixed(1)} km · {f.opening_hours}</div>
                  <div className="row" style={{ marginTop: 6 }}>
                    {f.is_verified && <Badge value="active" label="Verified" />}
                    {f.phone_number && <a className="btn btn-ghost btn-sm" href={`tel:${f.phone_number.replace(/\s/g, "")}`}><Phone size={14} /> Call</a>}
                    {f.location && (
                      <a className="btn btn-ghost btn-sm" target="_blank" rel="noreferrer"
                        href={`https://www.openstreetmap.org/directions?route=${origin.latitude}%2C${origin.longitude}%3B${f.location.latitude}%2C${f.location.longitude}`}>
                        <Navigation size={14} /> Directions
                      </a>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </>
  );
}
