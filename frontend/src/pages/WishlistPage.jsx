import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, formatIDR, imageSrc } from "../lib/api";
import { Heart, X } from "lucide-react";
import { toast } from "sonner";

const WishlistPage = () => {
  const [items, setItems] = useState([]);
  const fetchData = () => api.get("/wishlist").then(({ data }) => setItems(data.items));
  useEffect(() => { fetchData(); }, []);
  const remove = async (pid) => {
    await api.delete(`/wishlist/${pid}`);
    toast.success("Dihapus dari wishlist");
    fetchData();
  };
  return (
    <div className="max-w-7xl mx-auto px-4 md:px-6 py-8" data-testid="wishlist-page">
      <h1 className="font-heading text-3xl md:text-4xl font-black mb-6">Wishlist</h1>
      {items.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center">
          <Heart className="h-16 w-16 mx-auto text-meow-midnight/30" />
          <p className="font-heading text-2xl font-black mt-3">Wishlist masih kosong</p>
          <p className="text-meow-gray mt-1">Simpan produk favoritmu untuk dilihat lagi nanti.</p>
          <Link to="/products" className="btn-primary inline-block mt-5">Belanja Sekarang</Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="wishlist-grid">
          {items.map((it) => (
            <div key={it.id} className="meow-card overflow-hidden relative">
              <button onClick={() => remove(it.product.id)} className="absolute top-3 right-3 z-10 bg-white/90 hover:bg-red-500 hover:text-white rounded-full p-2 shadow" data-testid={`remove-wishlist-${it.product.id}`}>
                <X className="h-4 w-4" />
              </button>
              <Link to={`/products/${it.product.slug}`} className="block">
                <div className="aspect-square overflow-hidden bg-meow-bg">
                  <img src={imageSrc(it.product.main_image)} alt="" className="w-full h-full object-cover" />
                </div>
                <div className="p-4">
                  <p className="font-bold text-sm line-clamp-1">{it.product.name}</p>
                  <p className="font-heading font-extrabold text-meow-salmon mt-1">{formatIDR(it.product.discount_price || it.product.price)}</p>
                </div>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WishlistPage;
