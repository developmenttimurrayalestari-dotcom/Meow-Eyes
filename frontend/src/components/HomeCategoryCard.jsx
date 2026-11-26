import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Glasses, Layers, Package2, Sparkles, Tag } from 'lucide-react';
import { imageSrc } from '../lib/api';
import { navigationDestination } from '../lib/navigationLinks';

export const CARD_ICONS = { frame: Glasses, lens: Layers, package: Package2, sparkles: Sparkles, tag: Tag };
const themes = {
  coral: ['bg-rose-50', 'text-meow-salmon'], amber: ['bg-amber-50', 'text-meow-amber'],
  mint: ['bg-teal-50', 'text-meow-mint'], midnight: ['bg-slate-100', 'text-meow-midnight'],
};
export default function HomeCategoryCard({ item, preview = false }) {
  const [failedImage, setFailedImage] = useState(null);
  const hasImage = item.background_image && failedImage !== item.background_image;
  const Icon = CARD_ICONS[item.icon] || Glasses;
  const theme = themes[item.theme] || themes.coral;
  const link = navigationDestination(item.link_url);
  const Wrapper = preview || !link ? 'div' : link.internal && !link.reload ? Link : 'a';
  const props = preview || !link ? {} : link.internal && !link.reload ? { to: link.url } : { href: link.url, target: link.internal ? undefined : '_blank', rel: link.internal ? undefined : 'noopener noreferrer' };
  return <Wrapper {...props} className={`relative isolate block min-h-40 sm:min-h-44 overflow-hidden rounded-3xl border border-meow-midnight/10 p-6 ${theme[0]} ${preview ? '' : 'transition hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-meow-salmon'}`} data-testid={`home-category-card-${item.id || 'preview'}`}>
    {hasImage && <><img src={imageSrc(item.background_image)} alt="" aria-hidden="true" loading="lazy" decoding="async" onError={() => setFailedImage(item.background_image)} className="absolute inset-0 h-full w-full object-cover" /><span aria-hidden="true" className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/50 to-black/25" /></>}
    <div className="relative"><Icon className={`h-8 w-8 ${hasImage ? 'text-white' : theme[1]}`} aria-hidden="true" />
      <p className={`font-heading font-extrabold text-xl mt-3 break-words ${hasImage ? 'text-white' : 'text-meow-midnight'}`}>{item.title}</p>
      {item.description && <p className={`text-xs mt-1 break-words ${hasImage ? 'text-white/95' : 'text-meow-gray'}`}>{item.description}</p>}
    </div>
  </Wrapper>;
}
