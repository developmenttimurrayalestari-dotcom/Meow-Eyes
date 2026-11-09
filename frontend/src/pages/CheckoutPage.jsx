import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { api, apiError, formatIDR, imageSrc } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { MapPin, Truck, Ticket, Coins, Plus, Shield, X, Glasses, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import AddressForm from "../components/AddressForm";
import PrescriptionForm from "../components/PrescriptionForm";

const newRequestId = () => window.crypto?.randomUUID?.() || `checkout-${Array.from(window.crypto.getRandomValues(new Uint32Array(4))).map((value) => value.toString(16)).join("")}`;

export default function CheckoutPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, refreshMe, refreshCartCount } = useAuth();
  const [selectedItemIds] = useState(() => {
    try {
      const fromRoute = location.state?.selected_item_ids;
      const stored = JSON.parse(sessionStorage.getItem(`meow_checkout_items_${user?.user_id}`) || "[]");
      const ids = [...new Set((fromRoute || stored).filter((value) => typeof value === "string"))].sort();
      if (ids.length) sessionStorage.setItem(`meow_checkout_items_${user?.user_id}`, JSON.stringify(ids));
      return ids;
    } catch { return location.state?.selected_item_ids || []; }
  });
  const [cartItems, setCartItems] = useState([]);
  const [cartVersion, setCartVersion] = useState(0);
  const [addresses, setAddresses] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addressId, setAddressId] = useState("");
  const [shippingOptions, setShippingOptions] = useState([]);
  const [shipping, setShipping] = useState(null);
  const [shippingLoading, setShippingLoading] = useState(false);
  const [shippingError, setShippingError] = useState("");
  const [shippingReload, setShippingReload] = useState(0);
  const [voucher, setVoucher] = useState("");
  const [voucherDraft, setVoucherDraft] = useState("");
  const [usePoints, setUsePoints] = useState(0);
  const [rouletteSpinId, setRouletteSpinId] = useState(null);
  const [availableRewards, setAvailableRewards] = useState([]);
  const [integrations, setIntegrations] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewKey, setPreviewKey] = useState("");
  const [previewError, setPreviewError] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [initialError, setInitialError] = useState("");
  const [pin, setPin] = useState(["", "", "", "", "", ""]);
  const [dirtyPrescriptions, setDirtyPrescriptions] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [now, setNow] = useState(Date.now());
  const pinRef = useRef([]);
  const requestRef = useRef(null);
  const selectedKey = selectedItemIds.join(",");

  const loadInitial = useCallback(async () => {
    setInitialLoading(true); setInitialError("");
    try {
      const [addressResponse, cartResponse, statusResponse] = await Promise.all([
        api.get("/addresses"), api.get("/cart"), api.get("/integrations/status"),
      ]);
      const loadedAddresses = addressResponse.data.addresses || [];
      setAddresses(loadedAddresses);
      setAddressId((current) => loadedAddresses.some((item) => item.id === current) ? current : (loadedAddresses.find((item) => item.is_default) || loadedAddresses[0])?.id || "");
      setCartItems((cartResponse.data.items || []).filter((item) => selectedItemIds.includes(item.id)));
      setIntegrations(statusResponse.data);
    } catch (err) { setInitialError(apiError(err, "Data checkout belum dapat dimuat.")); }
    finally { setInitialLoading(false); }
  }, [selectedItemIds]);
  useEffect(() => { loadInitial(); }, [loadInitial]);
  useEffect(() => {
    api.get("/roulette/my-rewards").then(({ data }) => setAvailableRewards((data.spins || []).filter((spin) => !spin.used && new Date(spin.expires_at).getTime() > Date.now() && ["discount", "free_shipping"].includes(spin.reward_type)))).catch(() => {});
    const timer = window.setInterval(() => setNow(Date.now()), 15000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setShipping(null); setShippingOptions([]); setShippingError(""); setPreview(null);
    if (!addressId || !selectedKey || initialLoading || initialError) return () => controller.abort();
    setShippingLoading(true);
    api.post("/checkout/shipping-options", { address_id: addressId, selected_item_ids: selectedItemIds }, { signal: controller.signal }).then(({ data }) => {
      setShippingOptions(data.options || []);
      setShipping(data.options?.[0] ? { ...data.options[0], address_id: addressId } : null);
      if (!data.options?.length) setShippingError("Belum ada layanan pengiriman untuk alamat ini. Periksa kode pos atau hubungi toko.");
    }).catch((err) => { if (!controller.signal.aborted) setShippingError(apiError(err, "Ongkir belum dapat dihitung. Periksa alamat dan coba lagi.")); })
      .finally(() => { if (!controller.signal.aborted) setShippingLoading(false); });
    return () => controller.abort();
  }, [addressId, selectedKey, selectedItemIds, cartVersion, shippingReload, initialLoading, initialError]);

  const payload = useMemo(() => ({
    address_id: addressId, courier_code: shipping?.courier_code, service_code: shipping?.service_code,
    shipping_quote_id: shipping?.quote_id || null, voucher_code: voucher || null,
    use_points: usePoints || 0, roulette_spin_id: rouletteSpinId, selected_item_ids: selectedItemIds,
  }), [addressId, shipping, voucher, usePoints, rouletteSpinId, selectedItemIds]);
  const payloadKey = JSON.stringify(payload);
  const shippingExpired = Boolean(shipping?.expires_at && new Date(shipping.expires_at).getTime() <= now);
  const currentShipping = Boolean(shipping && shipping.address_id === addressId && !shippingExpired);
  useEffect(() => {
    const controller = new AbortController();
    setPreview(null); setPreviewKey(""); setPreviewError("");
    if (!currentShipping) return () => controller.abort();
    setPreviewLoading(true);
    api.post("/checkout/preview", JSON.parse(payloadKey), { signal: controller.signal }).then(({ data }) => {
      setPreview(data); setPreviewKey(payloadKey);
    }).catch((err) => { if (!controller.signal.aborted) setPreviewError(apiError(err, "Ringkasan belum dapat dihitung.")); })
      .finally(() => { if (!controller.signal.aborted) setPreviewLoading(false); });
    return () => controller.abort();
  }, [payloadKey, currentShipping]);

  const handleDirty = useCallback((id, dirty) => setDirtyPrescriptions((current) => current[id] === dirty ? current : { ...current, [id]: dirty }), []);
  const handlePrescriptionSaved = useCallback((id, prescription) => {
    setCartItems((current) => current.map((item) => item.id === id ? { ...item, prescription } : item));
    setCartVersion((version) => version + 1);
  }, []);
  const hasUnsavedPrescription = Object.values(dirtyPrescriptions).some(Boolean);
  const validPreview = preview && previewKey === payloadKey && currentShipping && !previewLoading;
  const setPinAt = (index, value) => {
    if (!/^\d?$/.test(value)) return;
    setPin((current) => current.map((digit, i) => i === index ? value : digit));
    if (value && index < 5) pinRef.current[index + 1]?.focus();
  };
  const submit = async () => {
    if (submitting || !validPreview || hasUnsavedPrescription) return;
    if (pin.some((digit) => digit === "")) { setSubmitError("Masukkan PIN 6 digit."); pinRef.current[0]?.focus(); return; }
    setSubmitting(true); setSubmitError("");
    try {
      if (!requestRef.current || requestRef.current.fingerprint !== payloadKey) {
        const storageKey = `meow_checkout_request_${user.user_id}`;
        let existing = null;
        try { existing = JSON.parse(sessionStorage.getItem(storageKey) || "null"); } catch { /* optional session storage */ }
        requestRef.current = existing?.fingerprint === payloadKey ? existing : { fingerprint: payloadKey, key: newRequestId() };
        try { sessionStorage.setItem(storageKey, JSON.stringify(requestRef.current)); } catch { /* still retained in this page */ }
      }
      const { data } = await api.post("/checkout/confirm", { ...payload, pin: pin.join("") }, { headers: { "Idempotency-Key": requestRef.current.key } });
      try { sessionStorage.removeItem(`meow_checkout_items_${user.user_id}`); sessionStorage.removeItem(`meow_checkout_request_${user.user_id}`); } catch { /* optional session storage */ }
      refreshMe(); refreshCartCount();
      toast.success("Pesanan dibuat. Lanjutkan pembayaran.");
      navigate(`/payment/${data.order.order_number}`, { state: { order: data.order, payment: data.payment, payment_error: data.payment_error } });
    } catch (err) { setSubmitError(apiError(err, "Pesanan belum terkonfirmasi. Coba lagi dengan pilihan yang sama, atau periksa daftar pesanan Anda.")); }
    finally { setSubmitting(false); }
  };
  if (!user) return null;
  if (!selectedItemIds.length) return <div className="max-w-3xl mx-auto py-12 text-center" data-testid="checkout-empty">Pilih produk untuk checkout. <Link to="/cart" className="text-meow-salmon underline">Kembali ke keranjang</Link></div>;
  if (initialLoading) return <p className="text-center py-16" role="status">Memuat checkout…</p>;
  if (initialError) return <div role="alert" className="max-w-xl mx-auto p-8 text-center"><p>{initialError}</p><button type="button" onClick={loadInitial} className="btn-secondary mt-4">Coba lagi</button></div>;
  if (cartItems.length !== selectedItemIds.length) return <div className="max-w-xl mx-auto p-8 text-center"><p>Isi keranjang telah berubah. Pilih kembali produk yang akan dibeli.</p><Link className="btn-primary inline-block mt-4" to="/cart">Periksa Keranjang</Link><Link className="block mt-3 underline" to="/orders">Lihat pesanan yang sudah dibuat</Link></div>;

  return <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-8" data-testid="checkout-page">
    <h1 className="font-heading text-3xl md:text-4xl font-black mb-6">Checkout</h1>
    <div className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-5 min-w-0">
        <section className="bg-white rounded-3xl p-5 md:p-6" data-testid="address-section">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
            <h2 className="font-heading font-extrabold text-xl flex items-center gap-2"><MapPin className="h-5 w-5 text-meow-salmon" />Alamat Pengiriman</h2>
            <button type="button" disabled={submitting} onClick={() => setShowAddForm(!showAddForm)} className="text-sm font-bold text-meow-salmon flex items-center gap-1">{showAddForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}{showAddForm ? "Tutup" : "Tambah"}</button>
          </div>
          {showAddForm ? <AddressForm defaultAddress={!addresses.length} onCancel={() => setShowAddForm(false)} onSaved={(address) => { setAddresses((items) => [...items.map((item) => address.is_default ? { ...item, is_default: false } : item), address]); setAddressId(address.id); setShowAddForm(false); }} />
            : !addresses.length ? <p className="text-sm text-meow-gray">Tambahkan alamat pengiriman untuk menghitung ongkir.</p>
              : <div className="space-y-2">{addresses.map((address) => <label key={address.id} className={`flex gap-2 p-3 rounded-2xl border-2 cursor-pointer ${addressId === address.id ? "border-meow-salmon bg-meow-salmon/5" : "border-meow-midnight/5"}`}>
                <input type="radio" name="checkout-address" disabled={submitting} checked={addressId === address.id} onChange={() => setAddressId(address.id)} className="mt-1" />
                <span className="text-sm"><span className="font-bold">{address.label} — {address.recipient}</span> · {address.phone}<br /><span className="text-meow-gray">{[address.street, address.subdistrict, address.district, address.city, address.province, address.postal_code].filter(Boolean).join(", ")}</span></span>
              </label>)}</div>}
        </section>

        <section className="bg-white rounded-3xl p-5 md:p-6">
          <h2 className="font-heading font-extrabold text-xl mb-4">Produk Pilihan</h2>
          <div className="divide-y divide-meow-midnight/10">{cartItems.map((item) => <div key={item.id} className="flex items-center gap-3 py-3">
            <img src={imageSrc(item.product.main_image)} alt="" className="w-14 h-14 rounded-xl object-cover" />
            <div className="flex-1 text-sm"><p className="font-bold">{item.product.name}</p>{item.lens_product && <p className="text-xs text-meow-gray">+ {item.lens_product.name}</p>}<p>{item.quantity} × {formatIDR(item.unit_price)}</p></div>
            <span className="font-bold text-sm">{formatIDR(item.subtotal)}</span>
          </div>)}</div>
        </section>
        {cartItems.some((item) => item.lens_product) && <section className="bg-white rounded-3xl p-5 md:p-6 space-y-4" data-testid="checkout-prescriptions">
          <div><h2 className="font-heading font-extrabold text-xl flex items-center gap-2"><Glasses className="h-5 w-5 text-meow-salmon" />Resep Frame + Lensa</h2><p className="text-sm text-meow-gray mt-1">Salin ukuran SPH, CYL, AXIS, ADD, dan PD sesuai resep. Setiap paket memiliki resep tersendiri.</p></div>
          {cartItems.filter((item) => item.lens_product).map((item) => <PrescriptionForm key={item.id} item={item} onDirtyChange={handleDirty} onSaved={handlePrescriptionSaved} disabled={submitting} />)}
        </section>}
        {addressId && <section className="bg-white rounded-3xl p-5 md:p-6" data-testid="shipping-section">
          <div className="flex items-center justify-between gap-2 mb-3"><h2 className="font-heading font-extrabold text-xl flex items-center gap-2"><Truck className="h-5 w-5 text-meow-mint" />Pengiriman</h2><button type="button" onClick={() => setShippingReload((value) => value + 1)} disabled={shippingLoading || submitting} className="text-xs font-bold flex items-center gap-1"><RefreshCw className={`h-3.5 w-3.5 ${shippingLoading ? "animate-spin" : ""}`} />Cek ulang</button></div>
          {shippingLoading ? <p role="status" className="text-sm text-meow-gray">Menghitung ongkir…</p> : shippingError ? <p role="alert" className="text-sm text-red-600">{shippingError}</p> : <div className="space-y-2 max-h-80 overflow-y-auto">{shippingOptions.map((option, index) => {
            const key = option.quote_id || `${option.courier_code}-${option.service_code}-${index}`;
            const checked = shipping?.quote_id ? shipping.quote_id === option.quote_id : shipping?.courier_code === option.courier_code && shipping?.service_code === option.service_code;
            return <label key={key} className={`flex items-start gap-2 p-3 rounded-2xl border-2 cursor-pointer ${checked ? "border-meow-salmon bg-meow-salmon/5" : "border-meow-midnight/5"}`}>
              <input type="radio" name="checkout-shipping" disabled={submitting} checked={checked} onChange={() => setShipping({ ...option, address_id: addressId })} className="mt-1" />
              <span className="text-sm flex-1"><span className="font-bold">{option.courier_name || option.courier_code} · {option.service_label || option.service_code}</span>{option.etd && <span className="block text-xs text-meow-gray">Estimasi {option.etd}</span>}{Number(option.insurance_cost) > 0 && <span className="block text-xs text-meow-gray">Termasuk asuransi {formatIDR(option.insurance_cost)}</span>}</span>
              <span className="text-sm font-bold text-meow-salmon">{formatIDR(option.cost)}</span>
            </label>;
          })}</div>}
          {shippingExpired && <p role="alert" className="mt-3 text-sm text-amber-700">Penawaran ongkir telah berakhir. Klik Cek ulang untuk memperbarui.</p>}
          {integrations.shipping?.mock && <p className="text-xs text-amber-700 mt-3">Mode demo: tarif dan pengiriman disimulasikan.</p>}
        </section>}

        <section className="bg-white rounded-3xl p-5 md:p-6 space-y-4" data-testid="promo-section">
          <h2 className="font-heading font-extrabold text-xl flex items-center gap-2"><Ticket className="h-5 w-5 text-meow-amber" />Promo & Reward</h2>
          <label className="block text-xs font-bold">Kode voucher<div className="flex gap-2 mt-1"><input value={voucherDraft} disabled={submitting} onChange={(event) => setVoucherDraft(event.target.value.toUpperCase())} placeholder="Masukkan kode voucher" className="min-w-0 flex-1 px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10" data-testid="voucher-input" /><button type="button" disabled={submitting} onClick={() => setVoucher(voucherDraft.trim())} className="btn-secondary text-xs py-2 px-4">Terapkan</button></div></label>
          {voucher && <p className="text-xs">Voucher: {voucher} <button type="button" onClick={() => { setVoucher(""); setVoucherDraft(""); }} className="ml-2 underline">Hapus</button></p>}
          <label className="block text-xs font-bold"><span className="flex items-center gap-1"><Coins className="h-3 w-3" />Pakai Poin · Saldo {user.points_balance || 0} (1 poin = Rp100)</span><input type="number" min="0" max={user.points_balance || 0} step="1" disabled={submitting} value={usePoints} onChange={(event) => setUsePoints(Math.min(user.points_balance || 0, Math.max(0, Math.floor(Number(event.target.value) || 0))))} className="w-full mt-1 px-3 py-2 rounded-xl bg-meow-bg border border-meow-midnight/10" data-testid="points-input" /></label>
          {!!availableRewards.length && <label className="block text-xs font-bold">Reward Roulette<select value={rouletteSpinId || ""} disabled={submitting} onChange={(event) => setRouletteSpinId(event.target.value || null)} className="w-full mt-1 px-3 py-2 rounded-xl bg-meow-bg"><option value="">Tidak digunakan</option>{availableRewards.map((reward) => <option key={reward.id} value={reward.id}>{reward.reward_label}</option>)}</select></label>}
        </section>
        <section className="bg-white rounded-3xl p-5 md:p-6" data-testid="pin-section">
          <h2 className="font-heading font-extrabold text-xl flex items-center gap-2"><Shield className="h-5 w-5 text-meow-mint" />Verifikasi PIN</h2>
          {!user.has_pin ? <p className="mt-3 text-sm">Atur PIN untuk melanjutkan checkout. <Link to="/setup-pin" className="text-meow-salmon underline">Setup PIN →</Link></p> : <><p className="mt-2 text-sm text-meow-gray">Masukkan PIN 6 digit untuk membuat pesanan.</p><div className="flex gap-2 mt-3" data-testid="checkout-pin-row">{pin.map((digit, index) => <input key={index} ref={(el) => { pinRef.current[index] = el; }} type="password" autoComplete="off" inputMode="numeric" maxLength={1} aria-label={`Digit PIN ${index + 1}`} value={digit} disabled={submitting} onChange={(event) => setPinAt(index, event.target.value)} onPaste={(event) => { const value = event.clipboardData.getData("text").trim(); if (/^\d{6}$/.test(value)) { event.preventDefault(); setPin(value.split("")); pinRef.current[5]?.focus(); } }} onKeyDown={(event) => { if (event.key === "Backspace" && !pin[index] && index > 0) pinRef.current[index - 1]?.focus(); }} className="w-10 sm:w-12 h-12 sm:h-14 text-center text-xl font-bold rounded-2xl border-2 border-meow-midnight/10 bg-meow-bg focus:border-meow-salmon outline-none" data-testid={`checkout-pin-${index}`} />)}</div></>}
        </section>
      </div>
      <aside><div className="bg-white rounded-3xl p-6 sticky top-28" data-testid="checkout-summary">
        <h2 className="font-heading font-extrabold text-xl mb-4">Ringkasan Pesanan</h2>
        <div className="space-y-2 text-sm" aria-busy={previewLoading}>
          <Row label="Subtotal" value={validPreview ? formatIDR(preview.subtotal) : "—"} />
          <Row label="Voucher" value={validPreview ? `−${formatIDR(preview.voucher_discount)}` : "—"} />
          <Row label="Poin" value={validPreview ? `−${formatIDR(preview.points_discount)}` : "—"} />
          <Row label="Reward Roulette" value={validPreview ? `−${formatIDR(preview.roulette_discount)}` : "—"} />
          <Row label={`Ongkir${preview?.free_shipping ? " (GRATIS)" : ""}`} value={validPreview ? formatIDR(preview.shipping?.cost ?? preview.shipping_cost) : "—"} />
          <div className="border-t pt-3 mt-3 flex justify-between"><span className="font-bold">Total</span><span className="font-heading font-black text-xl text-meow-salmon" data-testid="checkout-total">{previewLoading ? "Menghitung…" : validPreview ? formatIDR(preview.total) : "—"}</span></div>
        </div>
        {previewError && <p role="alert" className="text-sm text-red-600 mt-3">{previewError}</p>}
        {hasUnsavedPrescription && <p role="alert" className="text-sm text-amber-700 mt-3">Simpan perubahan resep sebelum membuat pesanan.</p>}
        {!integrations.payment?.ready && <p role="alert" className="text-sm text-amber-700 mt-3">Pembayaran sementara belum tersedia. Silakan coba lagi atau hubungi toko.</p>}
        {submitError && <p role="alert" className="text-sm text-red-600 mt-3">{submitError}</p>}
        <button type="button" onClick={submit} disabled={submitting || !validPreview || !user.has_pin || hasUnsavedPrescription || !integrations.payment?.ready} className="w-full btn-primary mt-5 disabled:opacity-50" data-testid="submit-order-btn">{submitting ? "Membuat Pesanan…" : "Buat Pesanan & Bayar"}</button>
        <p className="text-xs text-meow-gray mt-3 text-center">Selesaikan pembayaran sebelum batas waktu pada halaman pembayaran.</p>
        {integrations.payment?.mock && <p className="text-xs text-amber-700 mt-2 text-center">Mode demo: pembayaran disimulasikan.</p>}
      </div></aside>
    </div>
  </div>;
}

const Row = ({ label, value }) => <div className="flex justify-between gap-3"><span className="text-meow-gray">{label}</span><span className="font-bold">{value}</span></div>;
