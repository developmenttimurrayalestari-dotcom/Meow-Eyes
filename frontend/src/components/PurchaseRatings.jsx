import React, { useCallback, useEffect, useState } from "react";
import { Star, CheckCircle2 } from "lucide-react";
import { api, apiError, imageSrc } from "../lib/api";
import { toast } from "sonner";

function RatingForm({ orderId, product, existing, onSaved }) {
  const [rating, setRating] = useState(0);
  const [body, setBody] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const id = product ? product.product_id : "transaction";
  const save = async (event) => {
    event.preventDefault();
    if (!rating) { setError("Pilih rating 1–5 bintang."); return; }
    setSaving(true); setError("");
    try {
      await api.post(product ? `/products/${product.product_id}/reviews` : `/orders/${orderId}/review`, { order_id: orderId, rating, body: body.trim() });
      toast.success("Terima kasih! Ulasan Anda tersimpan."); await onSaved();
    } catch (err) { setError(apiError(err, "Ulasan belum berhasil disimpan.")); }
    finally { setSaving(false); }
  };
  if (existing) return <div className="rounded-2xl bg-meow-mint/10 p-4 text-sm" data-testid={`review-saved-${id}`}>
    <p className="font-bold flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-meow-mint" />{product?.name || "Pengalaman checkout"} · {existing.rating}/5</p>
    {existing.body && <p className="mt-1 text-meow-gray whitespace-pre-line">{existing.body}</p>}
    {existing.status === "pending" && <p className="text-xs mt-2">Ulasan tersimpan dan menunggu moderasi.</p>}
  </div>;
  return <form onSubmit={save} className="rounded-2xl border border-meow-midnight/10 p-4 space-y-3" data-testid={`rating-form-${id}`}>
    <div className="flex gap-2 items-center">
      {product?.image && <img src={imageSrc(product.image)} alt="" className="h-11 w-11 rounded-lg object-cover" />}
      <p className="text-sm font-bold">{product?.name || "Bagaimana pengalaman checkout Anda?"}</p>
    </div>
    <fieldset disabled={saving}><legend className="sr-only">Rating {product?.name || "transaksi"}</legend>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((score) => <label key={score} className="cursor-pointer p-1.5 rounded-lg focus-within:ring-2 focus-within:ring-meow-salmon">
          <input type="radio" name={`rating-${orderId}-${id}`} value={score} checked={rating === score} onChange={() => setRating(score)} className="sr-only" aria-label={`${score} bintang`} />
          <Star aria-hidden="true" className={`h-7 w-7 ${score <= rating ? "text-meow-amber fill-meow-amber" : "text-meow-midnight/20"}`} />
        </label>)}
      </div>
    </fieldset>
    <label className="block text-xs font-semibold">{product ? "Ulasan produk" : "Masukan Anda (opsional)"}
      <textarea required={Boolean(product)} disabled={saving} maxLength={10000} rows={2} value={body} onChange={(event) => setBody(event.target.value)}
        className="block w-full mt-1 p-3 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none" />
    </label>
    {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
    <button type="submit" disabled={saving || !rating || (Boolean(product) && !body.trim())} className="btn-primary text-sm py-2 disabled:opacity-50">{saving ? "Mengirim…" : "Kirim Ulasan"}</button>
  </form>;
}

export default function PurchaseRatings({ orderId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(() => api.get(`/orders/${orderId}/review-eligibility`).then(({ data: response }) => { setData(response); setError(""); }).catch((err) => setError(apiError(err, "Form ulasan belum dapat dimuat."))), [orderId]);
  useEffect(() => { load(); }, [load]);
  if (!data && !error) return <p className="text-sm text-meow-gray py-4">Memuat ulasan pembelian…</p>;
  if (error) return <div role="alert" className="p-4 bg-white rounded-2xl text-sm"><p>{error}</p><button type="button" onClick={load} className="mt-2 font-bold underline">Coba lagi</button></div>;
  if (!data.eligible && !data.order_review && !data.products?.some((product) => product.review)) return null;
  return <section className="bg-white rounded-3xl p-6 mt-6" data-testid="purchase-ratings">
    <h2 className="font-heading font-extrabold text-xl">Ulas Pembelian Anda</h2>
    <p className="text-sm text-meow-gray mt-1 mb-4">Pembayaran berhasil. Bagikan pengalaman checkout Anda sekarang; ulasan produk juga dapat diisi setelah Anda mencobanya.</p>
    <div className="space-y-3">
      {(data.eligible || data.order_review) && <RatingForm orderId={orderId} existing={data.order_review} onSaved={load} />}
      {data.products?.filter((product) => product.eligible || product.review).map((product) => <details key={product.product_id} className="rounded-2xl border border-meow-midnight/10 p-3">
        <summary className="font-bold text-sm cursor-pointer">{product.review ? "Ulasan tersimpan" : "Beri ulasan produk"} · {product.name}</summary>
        <div className="mt-3"><RatingForm orderId={orderId} product={product} existing={product.review} onSaved={load} /></div>
      </details>)}
    </div>
  </section>;
}
