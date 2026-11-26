import React, { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { isAdminPath, startConveyThis } from '../lib/conveyThis';
import TranslationDock from './TranslationDock';

// Compatibility for old inline call sites; the single floating dock owns the UI.
export function TranslationButtons() { return null; }

export function StandaloneTranslation({ children }) {
  useEffect(() => { startConveyThis(); }, []);
  return <>{children}<TranslationDock /></>;
}

export function ConveyThisBoundary({ children }) {
  const { pathname, search, hash, key } = useLocation();
  const initialAdmin = useRef(isAdminPath(pathname));
  const admin = isAdminPath(pathname), crossing = admin !== initialAdmin.current;
  useEffect(() => {
    if (crossing) {
      // Third-party observers cannot be unloaded by removing a script tag. A new
      // document ensures no customer translator can observe an admin screen.
      window.location.replace(pathname + search + hash);
    } else if (!admin) startConveyThis();
  }, [admin, crossing, pathname, search, hash]);
  if (crossing) return <main role="status" className="p-6">Membuka halaman...</main>;
  if (admin) return children;
  return <>{children}<TranslationDock closeKey={key} /></>;
}
