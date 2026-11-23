import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import "leaflet/dist/leaflet.css";
import { useState, type FormEvent } from "react";
import { CircleMarker, MapContainer, TileLayer, useMapEvents } from "react-leaflet";
import { del, get, patch, post } from "../../api/client";
import type { Area, Facility, Infrastructure, LatLng, School } from "../../api/types";
import { CheckCircle2, Droplets, Hospital, MapPin, Pencil, Plus, School as SchoolIcon, Trash2 } from "../../components/icons";
import { Modal } from "../../components/Modal";
import { useToast } from "../../components/Toast";
import { Badge, Button, Card, EmptyState, ErrorText, Field, Loading, PageHeader, Tabs } from "../../components/ui";
import { humanize } from "../../utils/format";
import { DEFAULT_CENTER, TILE_ATTRIBUTION, TILE_URL } from "../../utils/map";

type Kind = "schools" | "facilities" | "infrastructure";
type Place = (School | Facility | Infrastructure) & Record<string, unknown>;

const KIND_META: Record<Kind, { label: string; singular: string; icon: JSX.Element }> = {
  schools: { label: "Schools", singular: "school", icon: <SchoolIcon size={16} /> },
  facilities: { label: "Health facilities", singular: "health facility", icon: <Hospital size={16} /> },
  infrastructure: { label: "Infrastructure", singular: "infrastructure item", icon: <Droplets size={16} /> },
};
const FACILITY_TYPES = ["hospital", "health_center", "health_post", "clinic", "pharmacy"];
const ASSET_TYPES = ["water_source", "water_point", "sanitation", "market", "other"];

export default function PlacesPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const [kind, setKind] = useState<Kind>("schools");
  const [editing, setEditing] = useState<Place | "new" | null>(null);
  const places = useQuery({ queryKey: ["places", kind], queryFn: () => get<Place[]>(`/geo/${kind}`) });
  const areas = useQuery({ queryKey: ["areas", "sector"], queryFn: () => get<Area[]>("/geo/areas?level=sector") });
  const areaName = (id: number | null) => areas.data?.find((a) => a.id === id)?.name ?? "—";

  const remove = useMutation({
    mutationFn: (p: Place) => del(`/geo/${kind}/${p.id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["places"] }); toast("Deleted"); },
    onError: (e) => toast(e.message, "error"),
  });

  return (
    <>
      <PageHeader
        title="Places"
        subtitle="Reference data shown on the map and used to group reports."
        actions={<Button icon={<Plus size={16} />} onClick={() => setEditing("new")}>Add {KIND_META[kind].singular}</Button>}
      />
      <Tabs<Kind>
        value={kind}
        onChange={setKind}
        tabs={(Object.keys(KIND_META) as Kind[]).map((k) => ({ value: k, label: KIND_META[k].label, icon: KIND_META[k].icon }))}
      />
      <Card flush>
        {places.isLoading && <div style={{ padding: 20 }}><Loading /></div>}
        {places.data?.length === 0 && <EmptyState title={`No ${KIND_META[kind].label.toLowerCase()} yet`} icon={<MapPin size={22} />} />}
        {!!places.data?.length && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Name</th><th>Type</th><th>Area</th><th>Location</th>{kind !== "infrastructure" && <th>Verified</th>}<th /></tr>
              </thead>
              <tbody>
                {places.data.map((p) => (
                  <tr key={p.id}>
                    <td className="strong">{p.name}</td>
                    <td>{humanize(String(p.facility_type ?? p.asset_type ?? "school"))}</td>
                    <td>{areaName(p.area_id)}</td>
                    <td className="mono">{p.location ? `${p.location.latitude.toFixed(4)}, ${p.location.longitude.toFixed(4)}` : "—"}</td>
                    {kind !== "infrastructure" && (
                      <td>{p.is_verified ? <Badge value="active" label="Verified" icon={<CheckCircle2 size={12} />} /> : <Badge value="draft" label="Unverified" />}</td>
                    )}
                    <td>
                      <div className="row" style={{ flexWrap: "nowrap", gap: 4 }}>
                        <Button variant="ghost" size="sm" aria-label="Edit" onClick={() => setEditing(p)}><Pencil size={15} /></Button>
                        <Button variant="ghost" size="sm" aria-label="Delete" onClick={() => confirm(`Delete “${p.name}”?`) && remove.mutate(p)}><Trash2 size={15} /></Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {editing && (
        <PlaceForm
          kind={kind}
          place={editing === "new" ? null : editing}
          areas={areas.data ?? []}
          onClose={() => setEditing(null)}
          onSaved={() => {
            qc.invalidateQueries({ queryKey: ["places"] });
            qc.invalidateQueries({ queryKey: [kind === "infrastructure" ? "infra" : kind] });
            setEditing(null);
            toast("Saved");
          }}
        />
      )}
    </>
  );
}

function ClickToPlace({ onPick }: { onPick: (p: LatLng) => void }) {
  useMapEvents({ click: (e) => onPick({ latitude: +e.latlng.lat.toFixed(6), longitude: +e.latlng.lng.toFixed(6) }) });
  return null;
}

function PlaceForm({ kind, place, areas, onClose, onSaved }: { kind: Kind; place: Place | null; areas: Area[]; onClose: () => void; onSaved: () => void }) {
  const [name, setName] = useState(place?.name ?? "");
  const [areaId, setAreaId] = useState(place?.area_id ? String(place.area_id) : "");
  const [location, setLocation] = useState<LatLng | null>(place?.location ?? null);
  const [verified, setVerified] = useState(Boolean(place?.is_verified));
  const [type, setType] = useState(String(place?.facility_type ?? place?.asset_type ?? (kind === "facilities" ? "health_center" : "water_point")));
  const [phone, setPhone] = useState(String(place?.phone_number ?? ""));
  const [hours, setHours] = useState(String(place?.opening_hours ?? ""));
  const [source, setSource] = useState(String(place?.data_source ?? ""));

  const save = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = { name, area_id: areaId ? Number(areaId) : null, location };
      if (kind !== "infrastructure") body.is_verified = verified;
      if (kind === "facilities") Object.assign(body, { facility_type: type, phone_number: phone || null, opening_hours: hours || null });
      if (kind === "infrastructure") Object.assign(body, { asset_type: type, data_source: source || null });
      return place ? patch(`/geo/${kind}/${place.id}`, body) : post(`/geo/${kind}`, body);
    },
    onSuccess: onSaved,
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }
  const center: [number, number] = location ? [location.latitude, location.longitude] : DEFAULT_CENTER;

  return (
    <Modal
      wide
      title={`${place ? "Edit" : "Add"} ${KIND_META[kind].singular}`}
      onClose={onClose}
      footer={<><Button variant="ghost" onClick={onClose}>Cancel</Button><Button form="place-form" disabled={save.isPending}>Save</Button></>}
    >
      <form id="place-form" className="form" onSubmit={submit}>
        <div className="form-grid">
          <Field label="Name"><input className="input" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></Field>
          <Field label="Area">
            <select className="input" value={areaId} onChange={(e) => setAreaId(e.target.value)}>
              <option value="">—</option>
              {areas.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          {kind !== "schools" && (
            <Field label="Type">
              <select className="input" value={type} onChange={(e) => setType(e.target.value)}>
                {(kind === "facilities" ? FACILITY_TYPES : ASSET_TYPES).map((t) => <option key={t} value={t}>{humanize(t)}</option>)}
              </select>
            </Field>
          )}
          {kind === "facilities" && (
            <>
              <Field label="Phone"><input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} /></Field>
              <Field label="Opening hours"><input className="input" value={hours} onChange={(e) => setHours(e.target.value)} placeholder="Mon–Sat 07:00–19:00" /></Field>
            </>
          )}
          {kind === "infrastructure" && (
            <Field label="Data source"><input className="input" value={source} onChange={(e) => setSource(e.target.value)} placeholder="Who provided this data?" /></Field>
          )}
        </div>
        <Field label="Location" hint={location ? `${location.latitude}, ${location.longitude} — click the map to move it` : "Click the map to set the location"}>
          <MapContainer center={center} zoom={13} className="map picker">
            <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
            <ClickToPlace onPick={setLocation} />
            {location && <CircleMarker center={[location.latitude, location.longitude]} radius={9} pathOptions={{ color: "#fff", weight: 2, fillColor: "#0d8573", fillOpacity: 1 }} />}
          </MapContainer>
        </Field>
        {kind !== "infrastructure" && (
          <label className="check">
            <input type="checkbox" checked={verified} onChange={(e) => setVerified(e.target.checked)} />
            Verified — details have been confirmed with the institution
          </label>
        )}
        <ErrorText error={save.error} />
      </form>
    </Modal>
  );
}
