import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { ConveyThisBoundary, TranslationButtons } from './ConveyThisTranslation';
import { conveyThisSnapshot, requestPageLanguage, resetConveyThis, startConveyThis } from '../lib/conveyThis';

let host, root, originalKey;
beforeEach(() => {
  originalKey = process.env.REACT_APP_CONVEYTHIS_API_KEY;
  delete process.env.REACT_APP_CONVEYTHIS_API_KEY;
  window.history.replaceState(null, '', '/');
  resetConveyThis();
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  jest.useFakeTimers();
});
afterEach(async () => {
  await act(async () => root.unmount()); host.remove();
  resetConveyThis(); document.getElementById('conveythis-wrapper')?.remove();
  jest.useRealTimers();
  if (originalKey === undefined) delete process.env.REACT_APP_CONVEYTHIS_API_KEY;
  else process.env.REACT_APP_CONVEYTHIS_API_KEY = originalKey;
});

const languageEvent = language => document.dispatchEvent(new CustomEvent('conveythis-language-changed', { detail: { language: { code2: language } } }));
function nativeWidget() {
  const widget = document.createElement('div'); widget.id = 'conveythis-wrapper';
  const controls = {};
  for (const [code, title] of [['id', 'Bahasa Indonesia'], ['en', 'English']]) {
    const element = document.createElement('div'); element.className = 'conveythis-widget-language';
    const label = document.createElement('span'); label.className = 'language_title'; label.textContent = title;
    element.appendChild(label); widget.appendChild(element); controls[code] = element;
  }
  document.body.appendChild(widget);
  document.getElementById('meow-conveythis-script').dispatchEvent(new Event('load'));
  return controls;
}

test('shows Indonesian/English buttons without faking a translation when no key is configured', async () => {
  await act(async () => root.render(<TranslationButtons />));
  const [indonesia, english] = host.querySelectorAll('button');
  expect(indonesia.textContent).toBe('Bahasa Indonesia'); expect(indonesia.disabled).toBe(false);
  expect(indonesia.getAttribute('aria-pressed')).toBe('true'); expect(english.disabled).toBe(true);
  expect(startConveyThis()).toBe(false);
  expect(document.getElementById('meow-conveythis-script')).toBeNull();
});

test('loads the official SDK once, encodes its public key and protects input values', async () => {
  await act(async () => root.render(<><TranslationButtons /><label>Catatan resep<textarea defaultValue="private prescription" /></label></>));
  act(() => { startConveyThis({key:'pub_test&locale=en'}); startConveyThis({key:'pub_test&locale=en'}); });
  const scripts = document.querySelectorAll('#meow-conveythis-script'); expect(scripts.length).toBe(1);
  const url = new URL(scripts[0].src);
  expect(url.origin).toBe('https://cdn.conveythis.com');
  expect(url.pathname).toBe('/javascript/conveythis.js');
  expect(url.searchParams.get('api_key')).toBe('pub_test&locale=en'); expect(url.searchParams.has('locale')).toBe(false);
  const input = host.querySelector('textarea');
  expect(input.value).toBe('private prescription'); expect(input.getAttribute('translate')).toBe('no');
  expect(input.classList.contains('conveythis-no-translate')).toBe(true);
});

test('uses actual native controls and waits for the SDK event before marking English or Indonesian active', async () => {
  await act(async () => root.render(<TranslationButtons />));
  act(() => startConveyThis({key:'pub_test'}));
  let controls;
  await act(async () => { controls = nativeWidget(); });
  const clickEnglish = jest.fn(); controls.en.addEventListener('click', clickEnglish);
  act(() => host.querySelectorAll('button')[1].click());
  expect(clickEnglish).toHaveBeenCalledTimes(1);
  expect(conveyThisSnapshot().phase).toBe('translating'); expect(conveyThisSnapshot().language).toBe('id');
  act(() => languageEvent('en'));
  expect(document.documentElement.lang).toBe('en');
  expect(host.querySelectorAll('button')[1].getAttribute('aria-pressed')).toBe('true');
  const clickIndonesia = jest.fn(() => languageEvent('id')); controls.id.addEventListener('click', clickIndonesia);
  act(() => host.querySelectorAll('button')[0].click());
  expect(clickIndonesia).toHaveBeenCalledTimes(1); expect(document.documentElement.lang).toBe('id');
  expect(host.querySelectorAll('button')[0].getAttribute('aria-pressed')).toBe('true');
  expect(requestPageLanguage('fr')).toBe(false);
});

test('script failure leaves the page and form usable with an informative status', async () => {
  await act(async () => root.render(<><TranslationButtons /><input defaultValue="Mira" /></>));
  act(() => startConveyThis({key:'pub_test'}));
  act(() => document.getElementById('meow-conveythis-script').dispatchEvent(new Event('error')));
  expect(conveyThisSnapshot().phase).toBe('error');
  expect(host.textContent).toContain('Penerjemah belum dapat dimuat');
  expect(host.querySelector('input').value).toBe('Mira');
  expect(host.querySelectorAll('button')[0].getAttribute('aria-pressed')).toBe('true');
});

test('a script that loads without accepted languages times out instead of pretending the integration is ready', async () => {
  act(() => startConveyThis({key:'pub_test'}));
  document.getElementById('meow-conveythis-script').dispatchEvent(new Event('load'));
  expect(conveyThisSnapshot().phase).toBe('loading');
  act(() => jest.advanceTimersByTime(30000));
  expect(conveyThisSnapshot().phase).toBe('error');
});

test('unsuccessful translation keeps the previous language selected and allows another attempt', async () => {
  act(() => startConveyThis({key:'pub_test'}));
  await act(async () => nativeWidget());
  act(() => requestPageLanguage('en'));
  act(() => jest.advanceTimersByTime(30000));
  expect(conveyThisSnapshot().language).toBe('id');
  expect(conveyThisSnapshot().message).toContain('Terjemahan belum berhasil');
  expect(requestPageLanguage('en')).toBe(true);
});

test('does not inject the SDK or language controls on admin pages', async () => {
  process.env.REACT_APP_CONVEYTHIS_API_KEY = 'pub_test';
  window.history.replaceState(null, '', '/admin/products');
  await act(async () => root.render(<MemoryRouter initialEntries={['/admin/products']}><ConveyThisBoundary><h1>Admin Produk</h1></ConveyThisBoundary></MemoryRouter>));
  expect(host.textContent).toBe('Admin Produk');
  expect(document.getElementById('meow-conveythis-script')).toBeNull();
  expect(host.querySelector('[data-testid="translation-buttons"]')).toBeNull();
  expect(startConveyThis({key:'pub_test'})).toBe(false);
});

test('auth customer pages receive the same language buttons', async () => {
  await act(async () => root.render(<MemoryRouter initialEntries={['/login']}><ConveyThisBoundary><h1>Masuk</h1></ConveyThisBoundary></MemoryRouter>));
  expect(host.querySelectorAll('[data-testid="translation-buttons"] button').length).toBe(2);
  expect(host.querySelector('#meow-conveythis-widget')).not.toBeNull();
});
