// ConveyThis owns translation and its cache. No translation service runs in our API.
const SCRIPT_ID = 'meow-conveythis-script';
const EXCLUDED = 'conveythis-no-translate';
const listeners = new Set();
let state = { language: 'id', phase: 'unconfigured', configured: false, message: '' };
let observer, readyTimer, translationTimer, activeKey = '', listening = false;
const update = patch => { state = { ...state, ...patch }; listeners.forEach(listener => listener()); };

export const conveyThisSnapshot = () => state;
export const subscribeConveyThis = listener => { listeners.add(listener); return () => listeners.delete(listener); };
export const isAdminPath = path => /^\/admin(?:\/|$)/.test(path);

export function protectTranslationInputs() {
  // Entered values and explicitly marked account/prescription data stay original.
  document.querySelectorAll('input, textarea, select, [data-conveythis-private]').forEach(element => {
    element.classList.add(EXCLUDED);
    element.setAttribute('translate', 'no');
  });
}

function controlLanguage(element) {
  const title = element.querySelector('.language_title')?.textContent || element.textContent || '';
  const label = title.trim().toLowerCase().replace(/\s+/g, ' ');
  if (['en', 'eng', 'english', 'inggris'].includes(label)) return 'en';
  if (['id', 'ind', 'indonesian', 'indonesia', 'bahasa indonesia'].includes(label)) return 'id';
  return null;
}

function nativeControl(language) {
  // The distributed SDK exposes these native controls and the language-changed
  // event; it does not expose the older guessed switchLanguage/translateTo APIs.
  return [...document.querySelectorAll('#conveythis-wrapper .conveythis-widget-language')]
    .find(element => controlLanguage(element) === language);
}

function scanWidget() {
  protectTranslationInputs();
  if (nativeControl('id') && nativeControl('en') && state.phase !== 'translating' && state.phase !== 'ready') {
    clearTimeout(readyTimer);
    update({ phase: 'ready', message: '' });
  }
}

function changedLanguage(event) {
  const language = event.detail?.language?.code2;
  if (!['id', 'en'].includes(language) || isAdminPath(window.location.pathname)) return;
  clearTimeout(translationTimer);
  document.documentElement.lang = language;
  update({ language, phase: 'ready', message: '' });
}

export function startConveyThis({ key = process.env.REACT_APP_CONVEYTHIS_API_KEY || '' } = {}) {
  if (isAdminPath(window.location.pathname)) return false;
  const publicKey = key.trim();
  if (!publicKey) return false;
  if (activeKey) return true; // One SDK, including when React StrictMode mounts twice.
  activeKey = publicKey;
  update({ configured: true, phase: 'loading', message: '' });
  protectTranslationInputs();
  if (!listening) {
    document.addEventListener('conveythis-language-changed', changedLanguage);
    listening = true;
  }
  observer = new MutationObserver(scanWidget);
  observer.observe(document.body, { childList: true, subtree: true });
  const script = document.createElement('script');
  script.id = SCRIPT_ID;
  const url = new URL('https://cdn.conveythis.com/javascript/conveythis.js');
  url.searchParams.set('api_key', publicKey);
  script.src = url.toString();
  script.async = true;
  const unavailable = () => {
    if (state.phase === 'loading') update({ phase: 'error', message: 'Penerjemah belum dapat dimuat. Muat ulang halaman untuk mencoba lagi.' });
  };
  script.onerror = unavailable;
  script.onload = scanWidget; // Script load alone does not mean the domain/key is accepted.
  readyTimer = setTimeout(unavailable, 30000);
  document.head.appendChild(script);
  return true;
}

export function requestPageLanguage(language) {
  if (!['id', 'en'].includes(language) || isAdminPath(window.location.pathname)) return false;
  if (language === state.language) return true;
  if (!state.configured || state.phase !== 'ready') return false;
  const control = nativeControl(language);
  if (!control) {
    update({ phase: 'error', message: 'Pilihan bahasa belum tersedia. Muat ulang halaman untuk mencoba lagi.' });
    return false;
  }
  update({ phase: 'translating', message: '' });
  translationTimer = setTimeout(() => {
    update({ phase: 'ready', message: 'Terjemahan belum berhasil. Silakan coba lagi.' });
  }, 30000);
  try { control.click(); }
  catch {
    clearTimeout(translationTimer);
    update({ phase: 'ready', message: 'Terjemahan belum berhasil. Silakan coba lagi.' });
    return false;
  }
  return true;
}

// Tests use this to tear down the SDK boundary without making external requests.
export function resetConveyThis() {
  observer?.disconnect(); observer = null;
  clearTimeout(readyTimer); clearTimeout(translationTimer);
  document.removeEventListener('conveythis-language-changed', changedLanguage);
  document.getElementById(SCRIPT_ID)?.remove();
  activeKey = ''; listening = false;
  document.documentElement.lang = 'id';
  update({ language: 'id', phase: 'unconfigured', configured: false, message: '' });
}
