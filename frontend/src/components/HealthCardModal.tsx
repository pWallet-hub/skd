import { useMutation } from "@tanstack/react-query";
import QRCode from "qrcode";
import { useEffect, useState } from "react";
import { post } from "../api/client";
import type { Child } from "../api/types";
import { Modal } from "./Modal";
import { useToast } from "./Toast";
import { Button, ErrorText, Field } from "./ui";
import { formatDateTime } from "../utils/format";

interface ShareLink {
  token: string;
  url: string;
  expires_at: string;
}

/** Digital health card: a time-limited QR code a health worker can scan at the clinic. */
export function HealthCardModal({ child, onClose }: { child: Child; onClose: () => void }) {
  const toast = useToast();
  const [hours, setHours] = useState(24);
  const [qr, setQr] = useState<string | null>(null);
  const share = useMutation({ mutationFn: () => post<ShareLink>(`/children/${child.id}/share`, { hours }) });

  useEffect(() => {
    if (!share.data) return;
    QRCode.toDataURL(share.data.url, { width: 280, margin: 1, color: { dark: "#0b3a34", light: "#ffffff" } })
      .then(setQr)
      .catch(() => setQr(null));
  }, [share.data]);

  return (
    <Modal
      title={`${child.display_name}'s health card`}
      onClose={onClose}
      footer={
        share.data ? (
          <>
            <Button variant="secondary" onClick={() => { navigator.clipboard?.writeText(share.data!.url); toast("Link copied"); }}>Copy link</Button>
            {qr && <a className="btn btn-secondary" href={qr} download={`${child.display_name}-health-card.png`}>Download QR</a>}
            <Button onClick={onClose}>Done</Button>
          </>
        ) : (
          <>
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button onClick={() => share.mutate()} disabled={share.isPending}>Create QR code</Button>
          </>
        )
      }
    >
      {!share.data ? (
        <div className="form">
          <p>
            Show this QR code at a clinic. The health worker can scan it to see {child.display_name}'s vaccinations,
            latest growth and recent concerns — <strong>read-only</strong>, and only until the link expires.
          </p>
          <Field label="Valid for">
            <select className="input" value={hours} onChange={(e) => setHours(Number(e.target.value))}>
              <option value={1}>1 hour</option>
              <option value={24}>24 hours</option>
              <option value={72}>3 days</option>
              <option value={168}>7 days</option>
            </select>
          </Field>
          <ErrorText error={share.error} />
        </div>
      ) : (
        <div style={{ textAlign: "center" }}>
          {qr ? <img src={qr} alt={`QR code for ${child.display_name}'s health card`} style={{ width: 240, height: 240 }} /> : <p className="muted">Generating…</p>}
          <p className="small muted" style={{ marginTop: 8 }}>Expires {formatDateTime(share.data.expires_at)}</p>
          <p className="mono small" style={{ wordBreak: "break-all", marginTop: 8 }}>{share.data.url}</p>
        </div>
      )}
    </Modal>
  );
}
