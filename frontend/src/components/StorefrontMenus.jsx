import React, { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { api } from '../lib/api';
import { navigationDestination } from '../lib/navigationLinks';
import { DEFAULT_MENUS } from '../lib/defaultNavigation';
import AppIcon from './AppIcon';

export const MENU_LOCATIONS = { header:'Menu Utama', footer:'Footer Eksplorasi', mobile:'Menu Bawah Mobile' };

export function useStorefrontMenus() {
  const [items, setItems] = useState(null);
  useEffect(() => {
    let alive = true, controller;
    const load = () => {
      controller?.abort(); controller = new AbortController();
      const request = controller;
      api.get('/menus', { signal: request.signal }).then(({data}) => {
        if (alive && !request.signal.aborted) setItems(data.items || []);
      }).catch(() => { if (alive && !request.signal.aborted) setItems(current => current ?? DEFAULT_MENUS); });
    };
    load(); window.addEventListener('focus',load); window.addEventListener('meow:menus-updated',load);
    return () => { alive=false; controller?.abort(); window.removeEventListener('focus',load); window.removeEventListener('meow:menus-updated',load); };
  }, []);
  return items || [];
}

function MenuLink({ item, location, user, cartCount }) {
  const current = useLocation();
  const profile = item.id === 'bn-profile' && item.url === '/profile' && !user;
  const target = navigationDestination(profile ? '/login' : item.url);
  if (!target) return null;
  const label = profile && item.label === 'Profil' ? 'Masuk' : item.label;
  const hasIcon = item.icon && item.icon !== 'none';
  const isMobile = location === 'mobile';
  const base = isMobile ? 'relative flex shrink-0 min-w-12 flex-col items-center text-[10px] gap-1' : location === 'header' ? `inline-flex items-center gap-1.5 font-semibold ${item.id === 'nav-contact' ? 'ml-auto' : ''}` : 'inline-flex items-center gap-1.5 hover:text-white';
  const style = active => `${base} ${isMobile ? active ? 'text-meow-amber' : 'text-white/80' : location === 'header' ? active || item.icon === 'flash' ? 'text-meow-salmon' : 'text-meow-midnight' : ''}`;
  const queryMatches = () => {
    const query = new URLSearchParams(item.url.split('?')[1]?.split('#')[0] || '');
    const selected = new URLSearchParams(current.search);
    return [...query].every(([key,value]) => selected.get(key) === value);
  };
  const content = <>{hasIcon && <AppIcon name={item.icon} className={isMobile ? 'h-5 w-5' : 'h-4 w-4'} />}<span>{label}</span>{isMobile && item.url.split(/[?#]/)[0] === '/cart' && cartCount > 0 && <span className="absolute -top-1 -right-2 bg-meow-salmon text-white text-[9px] font-bold rounded-full h-4 w-4 grid place-items-center">{cartCount}</span>}</>;
  if (target.internal && !target.reload && !item.new_tab) return <NavLink to={target.url} end={target.url === '/'} className={({isActive})=>style(isActive && queryMatches())} data-testid={item.id}>{content}</NavLink>;
  return <a href={target.url} target={item.new_tab ? '_blank' : undefined} rel={item.new_tab ? 'noopener noreferrer' : undefined} className={style(false)} data-testid={item.id}>{content}</a>;
}

export default function StorefrontMenus({ items, location, user, cartCount = 0 }) {
  const menus = items.filter(item=>item.location===location && item.is_active).slice().sort((a,b)=>a.sort_order-b.sort_order || a.id.localeCompare(b.id));
  if (!menus.length) return null;
  const links = menus.map(item=><MenuLink key={item.id} item={item} location={location} user={user} cartCount={cartCount} />);
  if (location === 'footer') return menus.map((item,index)=><li key={item.id}>{links[index]}</li>);
  return <nav aria-label={MENU_LOCATIONS[location]} data-testid={location==='mobile'?'bottom-nav':'main-menu'} className={location==='mobile'?'md:hidden fixed bottom-4 left-4 right-4 bg-meow-midnight/90 backdrop-blur-xl rounded-full flex justify-between items-center gap-6 px-6 py-3 shadow-2xl z-50 text-white overflow-x-auto no-scrollbar':'max-w-7xl mx-auto px-4 md:px-6 lg:px-8 flex items-center gap-5 min-h-11 py-2 text-sm whitespace-nowrap min-w-max'}>{links}</nav>;
}
