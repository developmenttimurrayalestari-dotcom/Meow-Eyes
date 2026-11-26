import React, { useEffect, useRef, useSyncExternalStore } from 'react';
import { useLocation } from 'react-router-dom';
import { Globe } from 'lucide-react';
import { conveyThisSnapshot, isAdminPath, requestPageLanguage, startConveyThis, subscribeConveyThis } from '../lib/conveyThis';

// Keep the controls disabled while preserving imports used by customer layouts.
// Replace this placeholder export when restoring the implementation below.
export function TranslationButtons() { return null; }

// export function TranslationButtons() {
//   const state = useSyncExternalStore(subscribeConveyThis, conveyThisSnapshot, conveyThisSnapshot);
//   const busy = ['loading', 'translating'].includes(state.phase);
//   return <div className="conveythis-no-translate notranslate text-meow-midnight" translate="no" data-testid="translation-buttons">
//     <div role="group" aria-label="Bahasa halaman" className="inline-flex flex-wrap items-center gap-1 rounded-xl border border-meow-midnight/10 bg-white p-1 text-xs font-semibold">
//       <span className="inline-flex items-center gap-1 px-2"><Globe className="h-4 w-4" aria-hidden="true" />Bahasa</span>
//       {[['id', 'Bahasa Indonesia'], ['en', 'English']].map(([code, label]) => <button key={code} type="button" lang={code}
//         aria-pressed={state.language === code} disabled={busy || code === 'en' && (!state.configured || state.phase === 'error')}
//         title={code === 'en' && !state.configured ? 'Terjemahan bahasa Inggris belum tersedia.' : undefined}
//         onClick={() => requestPageLanguage(code)}
//         className={`min-h-9 rounded-lg px-3 py-2 disabled:opacity-40 ${state.language === code ? 'bg-meow-midnight text-white' : 'hover:bg-meow-bg'}`}>{label}</button>)}
//     </div>
//     {busy && <p role="status" className="mt-1 text-xs">{state.phase === 'loading' ? 'Menyiapkan penerjemah...' : 'Menerjemahkan halaman...'}</p>}
//     {state.message && <p role="status" className="mt-1 max-w-xs text-xs">{state.message}</p>}
//   </div>;
// }

function VendorWidgetHost() {
  return <div id="meow-conveythis-widget" className="conveythis-no-translate notranslate" translate="no" />;
}

export function StandaloneTranslation({ children }) {
  useEffect(() => { startConveyThis(); }, []);
  return <>{children}<VendorWidgetHost /></>;
}

export function ConveyThisBoundary({ children }) {
  const { pathname, search, hash } = useLocation();
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
  const authPage = /^\/(?:login|register|setup-pin|setup-password|verify-email)(?:\/|$)/.test(pathname);
  return <>{children}{authPage && <div className="fixed top-3 right-3 z-40 rounded-xl bg-white/95 p-2 shadow-sm"><TranslationButtons /></div>}<VendorWidgetHost /></>;
}
