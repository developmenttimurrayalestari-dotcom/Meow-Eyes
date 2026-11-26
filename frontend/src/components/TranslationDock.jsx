import React, { useEffect, useId, useRef, useState, useSyncExternalStore } from 'react';
import { ChevronRight, Globe, X } from 'lucide-react';
import { connectConveyThisDock, conveyThisSnapshot, subscribeConveyThis } from '../lib/conveyThis';
import './TranslationDock.css';

export default function TranslationDock({ closeKey }) {
  const state = useSyncExternalStore(subscribeConveyThis, conveyThisSnapshot, conveyThisSnapshot);
  const [open, setOpen] = useState(false);
  const root = useRef(null), trigger = useRef(null);
  const pendingChoice = useRef(false);
  const titleId = useId();
  const busy = ['loading', 'translating'].includes(state.phase);
  useEffect(() => { connectConveyThisDock(); }, []);
  useEffect(() => { setOpen(false); }, [closeKey]);
  useEffect(() => {
    const reveal = () => { if (conveyThisSnapshot().configured) setOpen(true); };
    window.addEventListener('meow:open-translation', reveal);
    return () => window.removeEventListener('meow:open-translation', reveal);
  }, []);
  useEffect(() => {
    if (!open) { pendingChoice.current = false; return; }
    const close = () => { setOpen(false); trigger.current?.focus(); };
    const confirmed = () => { if (pendingChoice.current) close(); };
    const outside = event => { if (!root.current?.contains(event.target)) setOpen(false); };
    const keyboard = event => { if (event.key === 'Escape') { event.preventDefault(); close(); } };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('keydown', keyboard);
    document.addEventListener('conveythis-language-changed', confirmed);
    return () => {
      document.removeEventListener('pointerdown', outside);
      document.removeEventListener('keydown', keyboard);
      document.removeEventListener('conveythis-language-changed', confirmed);
    };
  }, [open]);
  return <div ref={root} hidden={!state.configured} className="meow-translation-dock conveythis-no-translate notranslate" translate="no" data-testid="translation-dock" data-open={open} onClickCapture={event => { if (event.target.closest?.('.conveythis-widget-language')) pendingChoice.current = true; }}>
    <button ref={trigger} type="button" className="meow-translation-handle" aria-label="Translate — pilih bahasa" aria-expanded={open} aria-controls="meow-translation-panel" onClick={() => setOpen(value => !value)}>
      <Globe size={19} aria-hidden="true" /><span>Translate</span><ChevronRight size={14} aria-hidden="true" className={open ? 'meow-translation-chevron-open' : ''} />
    </button>
    <section id="meow-translation-panel" inert={!open} aria-hidden={!open} aria-labelledby={titleId} className="meow-translation-panel" data-testid="translation-panel" aria-busy={busy}>
      <div className="meow-translation-heading"><strong id={titleId}>Pilih bahasa</strong><button type="button" aria-label="Tutup pilihan bahasa" onClick={() => { setOpen(false); trigger.current?.focus(); }}><X size={18} aria-hidden="true" /></button></div>
      {busy && <p role="status">{state.phase === 'translating' ? 'Menerjemahkan halaman…' : 'Menyiapkan pilihan bahasa…'}</p>}
      {state.message && <p role="status">{state.message}</p>}
      <div id="meow-conveythis-widget" className="meow-translation-native conveythis-no-translate notranslate" translate="no" />
    </section>
  </div>;
}
