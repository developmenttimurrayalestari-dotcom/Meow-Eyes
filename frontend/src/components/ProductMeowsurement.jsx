import React, { useEffect, useState } from "react";
import { ArrowRight, Ruler } from "lucide-react";
import { api } from "../lib/api";

export function resolvedFrameSpecification(response, variantId) {
  if (!response) return null;
  if (!variantId) return response.specification || null;
  const row = response.variants?.find(item => (item.variant_id || item.id) === variantId);
  if (!row) return null;
  if (row.effective_specification) return row.effective_specification;
  return row.inherit_default === false ? row.specification || null : response.specification || null;
}
export function completeFrameSpecification(spec) {
  return spec?.enabled === true && spec.complete !== false && ["a", "b", "dbl"].every(key => spec[key] !== null && spec[key] !== "" && Number.isFinite(Number(spec[key])) && Number(spec[key]) > 0);
}
const mm = value => value !== null && value !== "" && Number.isFinite(Number(value)) ? Number(value).toLocaleString("id-ID", { maximumFractionDigits: 2 }) + " mm" : "Belum tersedia";

export default function ProductMeowsurement({ productId, variantId }) {
  const [state, setState] = useState({ productId: null, response: null }), [reload, setReload] = useState(0), [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); setError(false);
    api.get("/products/" + encodeURIComponent(productId) + "/frame-specification", { signal: controller.signal }).then(({ data }) => { if (!controller.signal.aborted) setState({ productId, response: data }); }).catch(() => { if (!controller.signal.aborted) { setState({ productId, response: null }); setError(true); } });
    return () => controller.abort();
  }, [productId, reload]);
  const spec = resolvedFrameSpecification(state.productId === productId ? state.response : null, variantId);
  const complete = completeFrameSpecification(spec);
  const query = new URLSearchParams({ product_id: productId }); if (variantId) query.set("variant_id", variantId);
  return <section className="mt-4 rounded-3xl border border-meow-midnight/10 bg-white p-5" data-testid="product-meowsurement">
    <div className="flex items-center gap-2"><Ruler className="h-5 w-5 text-meow-salmon" /><h2 className="font-heading text-xl font-black">Fitting dengan Meowsurement</h2></div>
    <p className="mt-2 text-sm text-meow-gray">Gunakan profil dan resep akun Meow Eyes Anda. Ukuran frame akan terisi sesuai varian yang dipilih.</p>
    {spec && <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">{[["a", "A"], ["b", "B"], ["dbl", "DBL"], ["ed", "ED"]].map(([key, label]) => <div key={key} className="bg-meow-bg p-3 rounded-xl"><dt className="text-xs text-meow-gray">{label}</dt><dd className="font-semibold mt-1" data-testid={"product-frame-spec-" + key}>{mm(spec[key])}</dd></div>)}</dl>}
    {complete ? <a href={"/meowsurement/?" + query.toString()} className="btn-secondary mt-4 inline-flex items-center gap-2" data-testid="open-meowsurement">Ukur fitting frame ini<ArrowRight className="h-4 w-4" /></a> : <p className="mt-3 text-sm text-meow-gray">{state.productId !== productId ? "Memeriksa spesifikasi frame…" : error ? "Spesifikasi pengukuran belum dapat dimuat." : "Meowsurement belum tersedia untuk varian ini. Pilih frame lain atau hubungi Meow Eyes."}</p>}
    {error && <button type="button" onClick={() => setReload(value => value + 1)} className="text-sm font-semibold underline mt-2">Coba muat spesifikasi</button>}
  </section>;
}
