import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, apiError, formatIDR, imageSrc } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Trash2, Minus, Plus, ShoppingBag } from "lucide-react";
import { toast } from "sonner";

const CartPage = () => {
  const navigate = useNavigate();
  const { user, refreshCartCount } = useAuth();
  const [cart, setCart] = useState({ items: [], subtotal: 0 });
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCart = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const { data } = await api.get("/cart");
      setCart(data);
      setSelected((current) => Object.fromEntries(data.items.map((item) => [item.id, current[item.id] ?? true])));
      refreshCartCount();
    } catch (err) { setError(apiError(err, "Keranjang belum dapat dimuat.")); }
    finally { setLoading(false); }
  }, [refreshCartCount]);

  useEffect(() => { fetchCart(); }, [fetchCart]);

  const updateQty = async (id, newQty) => {
    try {
      await api.patch(`/cart/${id}`, { quantity: newQty });
      fetchCart();
    } catch { toast.error("Gagal update"); }
  };
  const removeItem = async (id) => {
    try { await api.delete(`/cart/${id}`); fetchCart(); } catch (err) { toast.error(apiError(err)); }
  };

  const allSelected = cart.items.length > 0 && cart.items.every((i) => selected[i.id]);
  const toggleAll = () => {
    const v = !allSelected;
    const next = {};
    for (const it of cart.items) next[it.id] = v;
    setSelected(next);
  };

  const selectedItems = cart.items.filter((i) => selected[i.id]);
  const selectedSubtotal = selectedItems.reduce((s, i) => s + i.subtotal, 0);

  const goCheckout = () => {
    if (selectedItems.length === 0) {
      toast.error("Pilih produk dulu");
      return;
    }
    const ids = selectedItems.map((i) => i.id);
    try { sessionStorage.setItem(`meow_checkout_items_${user.user_id}`, JSON.stringify(ids)); } catch { /* optional storage */ }
    navigate("/checkout", { state: { selected_item_ids: ids } });
  };

  if (error) return <div role="alert" className="max-w-xl mx-auto p-8 text-center"><p>{error}</p><button type="button" onClick={fetchCart} className="btn-secondary mt-4">Coba lagi</button></div>;
  if (loading) return <div className="min-h-[40vh] flex items-center justify-center">Memuat keranjang...</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-8" data-testid="cart-page">
      <h1 className="font-heading text-3xl md:text-4xl font-black mb-6">Keranjang ({cart.items.length})</h1>

      {cart.items.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center" data-testid="empty-cart">
          <ShoppingBag className="h-16 w-16 mx-auto text-meow-midnight/30" />
          <p className="font-heading font-black text-2xl mt-4">Keranjang masih kosong</p>
          <p className="text-meow-gray mt-2">Yuk pilih kacamata pertamamu di Meow Eyes.</p>
          <Link to="/products" className="btn-primary inline-block mt-6" data-testid="empty-cart-shop-btn">Belanja Sekarang</Link>
        </div>
      ) : (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-3xl p-6">
            <label className="flex items-center gap-2 pb-3 border-b border-meow-midnight/5 cursor-pointer">
              <input type="checkbox" checked={allSelected} onChange={toggleAll} data-testid="cart-select-all" />
              <span className="text-sm font-bold">Pilih Semua</span>
            </label>
            <div className="divide-y divide-meow-midnight/5">
              {cart.items.map((it) => (
                <div key={it.id} className="flex gap-3 py-4" data-testid={`cart-item-${it.id}`}>
                  <input
                    type="checkbox"
                    checked={!!selected[it.id]}
                    onChange={() => setSelected({ ...selected, [it.id]: !selected[it.id] })}
                    className="mt-1"
                    data-testid={`cart-checkbox-${it.id}`}
                  />
                  <img src={imageSrc(it.product.main_image)} alt="" className="w-20 h-20 rounded-2xl object-cover" />
                  <div className="flex-1 min-w-0">
                    <Link to={`/products/${it.product.slug}`} className="font-bold hover:text-meow-salmon line-clamp-1">{it.product.name}</Link>
                    {it.variant && (
                      <p className="text-xs text-meow-gray">{[it.variant.color, it.variant.size, it.variant.lens_type].filter(Boolean).join(" · ")}</p>
                    )}
                    {it.lens_product && (
                      <p className="text-xs text-meow-mint mt-1">+ Lensa: <span className="font-bold">{it.lens_product.name}</span>{it.lens_index ? ` · ${it.lens_index.name}` : ""}</p>
                    )}
                    <p className="font-heading font-extrabold text-meow-salmon mt-1">{formatIDR(it.unit_price)}</p>
                    {it.lens_price > 0 && (
                      <p className="text-[10px] text-meow-gray">Frame {formatIDR(it.frame_price)} + Lensa {formatIDR(it.lens_price)}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end justify-between">
                    <button onClick={() => removeItem(it.id)} className="text-meow-gray hover:text-red-500" data-testid={`cart-remove-${it.id}`}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                    <div className="flex items-center bg-meow-bg rounded-full">
                      <button onClick={() => updateQty(it.id, it.quantity - 1)} className="px-2 py-1" data-testid={`cart-minus-${it.id}`}><Minus className="h-3 w-3" /></button>
                      <span className="px-3 text-sm font-bold" data-testid={`cart-qty-${it.id}`}>{it.quantity}</span>
                      <button onClick={() => updateQty(it.id, it.quantity + 1)} className="px-2 py-1" data-testid={`cart-plus-${it.id}`}><Plus className="h-3 w-3" /></button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-3xl p-6 sticky top-24" data-testid="cart-summary">
              <h3 className="font-heading font-extrabold text-xl mb-4">Ringkasan</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Item terpilih</span><span className="font-bold">{selectedItems.length}</span></div>
                <div className="flex justify-between"><span>Subtotal</span><span className="font-bold">{formatIDR(selectedSubtotal)}</span></div>
              </div>
              <button onClick={goCheckout} className="w-full btn-primary mt-6" data-testid="checkout-btn">
                Lanjut Checkout →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;
