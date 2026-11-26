import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { api, imageSrc } from '../lib/api';

const destination = (banner) => {
  if (banner.link_type === 'none') return null;
  const url = banner.link_url || (banner.link_type === 'flash_sale' ? '/flash-sale' : banner.link_type === 'shop_now' ? '/shop-now' : '');
  if (typeof url !== 'string' || /[\\\s\u0000-\u001f]/.test(url) || url.startsWith('//')) return null;
  if (url.startsWith('/')) return { internal: true, url };
  try { const parsed = new URL(url); if (['http:', 'https:'].includes(parsed.protocol) && !parsed.username && !parsed.password) return { internal: false, url }; } catch { /* No clickable link for malformed destinations. */ }
  return null;
};

export default function PromoPopup() {
  const { pathname, key } = useLocation();
  const [banners, setBanners] = useState([]), [index, setIndex] = useState(0), [open, setOpen] = useState(false);
  const closeButton = useRef(null);
  const [dismissed, setDismissed] = useState(false);
  const eligible = pathname === '/';
  const close = () => { setOpen(false); setDismissed(true); };
  useEffect(() => {
    setBanners([]); setIndex(0); setOpen(false); setDismissed(false);
    if (!eligible) return;
    let cancelled = false;
    const controller = new AbortController();
    const device = window.matchMedia?.('(max-width: 767px)').matches ?? window.innerWidth < 768;
    api.get('/banners', { params: { position: 'popup', device: device ? 'mobile' : 'desktop' }, signal: controller.signal }).then(({ data }) => {
      if (cancelled) return;
      const now = Date.now();
      const items = (data.banners || []).filter(banner => banner.position === 'popup' && banner.is_active && banner.image_desktop?.trim()
        && (!banner.start_at || Date.parse(banner.start_at) <= now) && (!banner.end_at || Date.parse(banner.end_at) > now)
        && ['all', device ? 'mobile' : 'desktop'].includes(banner.target_device || 'all'));
      setBanners(items.sort((a, b) => a.sort_order - b.sort_order || a.id.localeCompare(b.id)).map(banner => ({ ...banner, selectedImage: device && banner.image_mobile ? banner.image_mobile : banner.image_desktop })));
    }).catch(() => { /* Promotions must never prevent browsing when the CMS is unavailable. */ });
    return () => { cancelled = true; controller.abort(); };
  }, [eligible, key]);
  const banner = banners[index];
  const show = () => {
    if (!eligible || dismissed) return;
    setOpen(true);
  };
  if (!eligible || !banner) return null;
  const link = destination(banner);
  const image = <img src={imageSrc(banner.selectedImage)} alt={banner.alt_text || banner.title} className="w-full max-h-[75dvh] object-contain rounded-xl" onError={close} />;
  return <>
    {!open && !dismissed && <img key={key + banner.id + banner.selectedImage} src={imageSrc(banner.selectedImage)} alt="" className="hidden" data-testid="promo-popup-preload" onLoad={show} onError={() => {
      if (banner.selectedImage !== banner.image_desktop) setBanners(items => items.map((item, i) => i === index ? { ...item, selectedImage: item.image_desktop } : item));
      else setIndex(value => value + 1);
    }} />}
    <Dialog.Root open={open} onOpenChange={value => { if (value) setOpen(true); else close(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm" />
        <Dialog.Content aria-describedby={undefined} onOpenAutoFocus={event => { event.preventDefault(); closeButton.current?.focus(); }} className="fixed left-1/2 top-1/2 z-[81] w-[92vw] max-w-xl -translate-x-1/2 -translate-y-1/2 rounded-2xl bg-white p-2 shadow-2xl focus:outline-none" data-testid="promo-popup">
          <Dialog.Title className="sr-only">{banner.title || 'Promo Meow Eyes'}</Dialog.Title>
          {link ? link.internal ? <Link to={link.url} onClick={close} aria-label={`Lihat promo: ${banner.title}`} className="block rounded-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-meow-salmon">{image}<span className="block py-2 text-center text-sm font-bold text-meow-salmon">Lihat promo →</span></Link>
            : <a href={link.url} target="_blank" rel="noopener noreferrer" onClick={close} aria-label={`Lihat promo: ${banner.title}`} className="block rounded-xl">{image}<span className="block py-2 text-center text-sm font-bold text-meow-salmon">Lihat promo →</span></a> : image}
          <Dialog.Close ref={closeButton} aria-label="Tutup promo" className="absolute right-3 top-3 grid h-10 w-10 place-items-center rounded-full bg-white text-meow-midnight shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-meow-salmon" data-testid="close-promo-popup"><X className="h-5 w-5" aria-hidden="true" /></Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  </>;
}
