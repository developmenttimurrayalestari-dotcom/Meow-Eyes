import React from 'react';
import { formatIDR } from '../lib/api';

export const TINTING_GROUPS = { fashion:'Fashion', sunglass:'Sunglass', therapeutic:'Therapeutic', special:'Khusus' };
export const tintingStyle = color => {
  const hex = value => /^#[\da-f]{6}$/i.test(value || '') ? value : null;
  const top = hex(color?.hex_color);
  if (!top) return { background:'repeating-conic-gradient(#e5e7eb 0% 25%, #fff 0% 50%) 50% / 12px 12px' };
  return { background:color.kind === 'gradient'
    ? `linear-gradient(180deg, ${[top, hex(color.mid_hex_color), hex(color.bottom_hex_color) || '#FFFFFF'].filter(Boolean).join(', ')})`
    : top };
};

export default function TintingSwatch({ color, small = false }) {
  return <span aria-hidden="true" className={`block max-w-full rounded-[45%] border border-black/10 shadow-inner ${small ? 'h-6 w-9 shrink-0' : 'mx-auto h-20 w-24 sm:h-24 sm:w-28'}`} style={tintingStyle(color)} />;
}

export function TintingDetails({ tinting }) {
  if (!tinting) return null;
  return <div className="mt-2 flex items-center gap-2 text-xs" data-testid="tinting-details">
    <TintingSwatch color={tinting} small />
    <span>Tinting {tinting.code} · {tinting.name}<span className="block text-meow-gray">+ <span className="conveythis-no-translate notranslate" translate="no">{formatIDR(tinting.additional_price)}</span> / produk</span>
      {tinting.is_available === false && <span className="block text-red-600">Warna tidak tersedia. Hapus atau pilih warna lain pada checkout.</span>}
    </span>
  </div>;
}
