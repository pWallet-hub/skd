import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { get, patch, post, upload } from "../api/client";
import type { Area, Child, School } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Modal } from "./Modal";
import { Button, ErrorText, Field } from "./ui";

const INTERESTS = ["reading", "music", "drawing", "numbers", "nature", "dancing", "football", "stories"];
const today = () => new Date().toISOString().slice(0, 10);

/** Add or edit a child profile (with optional photo, stored privately in SeaweedFS). */
export function ChildForm({ child, onClose, onSaved }: { child?: Child; onClose: () => void; onSaved: (c: Child) => void }) {
  const { user } = useAuth();
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => get<School[]>("/geo/schools") });
  const areas = useQuery({ queryKey: ["areas", "sector"], queryFn: () => get<Area[]>("/geo/areas?level=sector") });

  const [name, setName] = useState(child?.display_name ?? "");
  const [dob, setDob] = useState(child?.date_of_birth ?? "");
  const [sex, setSex] = useState(child?.sex ?? "unspecified");
  const [areaId, setAreaId] = useState(String(child?.area_id ?? user?.home_area_id ?? ""));
  const [schoolId, setSchoolId] = useState(String(child?.school_id ?? ""));
  const [interests, setInterests] = useState<string[]>(child?.learning_interests ?? []);
  const [photo, setPhoto] = useState<File | null>(null);

  const save = useMutation({
    mutationFn: async () => {
      const body = {
        display_name: name,
        date_of_birth: dob,
        sex,
        area_id: areaId ? Number(areaId) : null,
        school_id: schoolId ? Number(schoolId) : null,
        learning_interests: interests,
      };
      let saved = child ? await patch<Child>(`/children/${child.id}`, body) : await post<Child>("/children", body);
      if (photo) saved = await upload<Child>(`/children/${saved.id}/photo`, photo);
      return saved;
    },
    onSuccess: onSaved,
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }
  const toggle = (i: string) => setInterests((xs) => (xs.includes(i) ? xs.filter((x) => x !== i) : [...xs, i]));

  return (
    <Modal
      title={child ? `Edit ${child.display_name}` : "Add a child"}
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button form="child-form" disabled={save.isPending}>{save.isPending ? "Saving…" : child ? "Save changes" : "Add child"}</Button>
        </>
      }
    >
      <form id="child-form" className="form" onSubmit={submit}>
        <div className="form-grid">
          <Field label="Name or nickname" hint="Only you and authorised health staff see this.">
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} required maxLength={100} />
          </Field>
          <Field label="Date of birth">
            <input className="input" type="date" value={dob} max={today()} onChange={(e) => setDob(e.target.value)} required />
          </Field>
          <Field label="Sex">
            <select className="input" value={sex} onChange={(e) => setSex(e.target.value)}>
              <option value="female">Girl</option>
              <option value="male">Boy</option>
              <option value="unspecified">Prefer not to say</option>
            </select>
          </Field>
          <Field label="Area (sector)">
            <select className="input" value={areaId} onChange={(e) => setAreaId(e.target.value)}>
              <option value="">—</option>
              {areas.data?.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          <Field label="School (optional)">
            <select className="input" value={schoolId} onChange={(e) => setSchoolId(e.target.value)}>
              <option value="">Not in school</option>
              {schools.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field label="Photo (optional)" hint="Stored privately; only you can see it.">
            <input className="input" type="file" accept="image/jpeg,image/png,image/webp" style={{ paddingTop: 8 }} onChange={(e) => setPhoto(e.target.files?.[0] ?? null)} />
          </Field>
        </div>
        <Field label="Interests">
          <div className="chips">
            {INTERESTS.map((i) => (
              <label key={i} className={`chip ${interests.includes(i) ? "on" : ""}`} style={{ textTransform: "capitalize" }}>
                <input type="checkbox" checked={interests.includes(i)} onChange={() => toggle(i)} />
                {i}
              </label>
            ))}
          </div>
        </Field>
        <ErrorText error={save.error} />
      </form>
    </Modal>
  );
}
