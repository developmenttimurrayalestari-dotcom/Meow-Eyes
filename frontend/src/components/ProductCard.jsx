import React from "react";
import { Link } from "react-router-dom";
import { Heart, Star } from "lucide-react";
import { formatIDR, imageSrc } from "../lib/api";

const Badge = ({ children, className = "" }) => (
  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full ${className}`}>{children}</span>
);

const ProductCard = ({ product, onWishlist }) => {
  const price = product.flash_sale_price ?? product.discount_price ?? product.price;
  const hasDiscount = product.discount_price && product.discount_price < product.price;
  const hasFlash = product.flash_sale_price != null;
  const discountPct = hasFlash
    ? Math.round((1 - product.flash_sale_price / product.price) * 100)
    : hasDiscount
      ? Math.round((1 - product.discount_price / product.price) * 100)
      : 0;

  return (
    <Link
      to={`/products/${product.slug}`}
      className="meow-card group block overflow-hidden"
      data-testid={`product-card-${product.slug}`}
    >
      <div className="relative overflow-hidden aspect-square bg-meow-bg">
        <img
          src={imageSrc(product.main_image)}
          alt={product.name}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute top-3 left-3 flex flex-col gap-1">
          {hasFlash && <Badge className="bg-meow-salmon text-white">⚡ Flash {discountPct}%</Badge>}
          {!hasFlash && hasDiscount && <Badge className="bg-meow-amber text-meow-midnight">-{discountPct}%</Badge>}
          {(product.is_new_arrival || product.badges?.includes("new")) && <Badge className="bg-meow-mint text-white">New</Badge>}
          {product.badges?.includes("bestseller") && <Badge className="bg-meow-midnight text-meow-amber">Best Seller</Badge>}
        </div>
        {onWishlist && (
          <button
            data-testid={`wishlist-btn-${product.slug}`}
            onClick={(e) => { e.preventDefault(); onWishlist(product); }}
            className="absolute top-3 right-3 bg-white/90 hover:bg-meow-salmon hover:text-white rounded-full p-2 shadow"
          >
            <Heart className="h-4 w-4" />
          </button>
        )}
      </div>
      <div className="p-4 space-y-1.5">
        <p className="font-bold text-sm md:text-base text-meow-midnight line-clamp-2 leading-tight">{product.name}</p>
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          <p className="font-heading font-extrabold text-meow-salmon text-base whitespace-nowrap">{formatIDR(price)}</p>
          {(hasDiscount || hasFlash) && (
            <p className="text-xs text-meow-gray line-through whitespace-nowrap">{formatIDR(product.price)}</p>
          )}
        </div>
        <div className="flex flex-wrap justify-between gap-x-2 gap-y-1 text-xs text-meow-gray">
          <span className="inline-flex items-center gap-1"><Star className="h-3 w-3 fill-meow-amber text-meow-amber" aria-label="Rating" />{product.rating_count ? Number(product.rating_avg || 0).toFixed(1) : "—"} ({product.rating_count || 0})</span>
          <span>Terjual {product.sold_count || 0}</span>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;
