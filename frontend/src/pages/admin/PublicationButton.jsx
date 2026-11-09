import React, { useState } from "react";
import { toast } from "sonner";
import { api } from "../../lib/api";
import { adminError } from "./adminUtils";

export default function PublicationButton({ resource, id, status, onSaved }) {
  const [busy, setBusy] = useState(false);
  const published = status === "published";
  const toggle = async () => {
    setBusy(true);
    try {
      await api.put(`/admin/${resource}/${id}`, { status: published ? "unpublished" : "published" });
      toast.success(published ? "Konten tidak lagi tampil di website" : "Konten diterbitkan");
      await onSaved();
    } catch (error) { toast.error(adminError(error)); }
    finally { setBusy(false); }
  };
  return <button type="button" onClick={toggle} disabled={busy} aria-pressed={published} className={`rounded-full border px-3 py-1 text-xs font-bold disabled:opacity-50 ${published ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-zinc-200 bg-zinc-50 text-zinc-700"}`} data-testid={`publication-${id}`}>{busy ? "Menyimpan…" : published ? "Unpublish" : "Publish"}</button>;
}
