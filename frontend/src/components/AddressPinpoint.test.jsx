import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import L from 'leaflet';
import AddressPinpoint from './AddressPinpoint';
import { api } from '../lib/api';

jest.mock('../lib/api', () => ({ api: { post: jest.fn() }, apiError: (err, fallback) => err.response?.data?.detail || fallback }));
let host, root, mapSpy;
const click = async (node) => act(async () => node.click());
const button = (text) => [...host.querySelectorAll('button')].find(node => node.textContent === text);
const type = async (text) => act(async () => {
  const input = host.querySelector('input[type=search]');
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, text);
  input.dispatchEvent(new Event('input', { bubbles: true }));
});
const instance = () => mapSpy.mock.results.at(-1).value;
beforeEach(() => { jest.clearAllMocks(); mapSpy = jest.spyOn(L, 'map'); host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); mapSpy.mockRestore(); });
const render = async (props = {}) => act(async () => root.render(<AddressPinpoint value={{ latitude: '', longitude: '' }} onChange={jest.fn()} {...props} />));

test('map click and draggable pin update coordinates, and external edits recenter the map', async () => {
  const onChange = jest.fn();
  await render({ onChange });
  expect(instance().options.touchZoom).toBe(true);
  expect(instance().scrollWheelZoom.enabled()).toBe(true);
  await act(async () => instance().fire('click', { latlng: L.latLng(-6.1754, 106.8272) }));
  expect(onChange).toHaveBeenLastCalledWith({ latitude: '-6.1754000', longitude: '106.8272000' });
  await render({ onChange, value: { latitude: -6.2, longitude: 106.8 } });
  let pin; instance().eachLayer(layer => { if (layer instanceof L.Marker) pin = layer; });
  expect(pin.dragging.enabled()).toBe(true);
  await act(async () => { pin.setLatLng([-6.21, 106.81]); pin.fire('dragend'); });
  expect(onChange).toHaveBeenLastCalledWith({ latitude: '-6.2100000', longitude: '106.8100000' });
  await render({ onChange, value: { latitude: -7.1, longitude: 110.3 } });
  expect(instance().getCenter().lat).toBeCloseTo(-7.1);
  expect(instance().getCenter().lng).toBeCloseTo(110.3);
});

test('search is explicit and selecting a result updates only the delivery point', async () => {
  const onChange = jest.fn();
  api.post.mockResolvedValue({ data: { results: [{ label: 'Monas, Jakarta', latitude: -6.1754, longitude: 106.8272 }] } });
  await render({ onChange, searchHint: 'Jalan Medan Merdeka, Jakarta' });
  expect(api.post).not.toHaveBeenCalled();
  await type('Monas Jakarta');
  expect(api.post).not.toHaveBeenCalled();
  await click(button('Cari'));
  expect(api.post).toHaveBeenCalledWith('/shipping/map-search', { query: 'Monas Jakarta' }, expect.objectContaining({ signal: expect.anything() }));
  expect(onChange).not.toHaveBeenCalled();
  await click(button('Monas, Jakarta'));
  expect(onChange).toHaveBeenCalledWith({ latitude: '-6.1754000', longitude: '106.8272000' });
});

test('failed search retains manual map selection and clear-point controls', async () => {
  const onChange = jest.fn();
  api.post.mockRejectedValue(new Error('offline'));
  await render({ onChange, searchHint: 'Jakarta' });
  await click(button('Cari'));
  expect(host.textContent).toContain('Pencarian belum tersedia');
  await act(async () => instance().fire('click', { latlng: L.latLng(-6, 107) }));
  expect(onChange).toHaveBeenCalledWith({ latitude: '-6.0000000', longitude: '107.0000000' });
  await click(button('Hapus titik'));
  expect(onChange).toHaveBeenLastCalledWith({ latitude: '', longitude: '' });
});

test('saving disables map and pin interactions, including pending geolocation', async () => {
  const onChange = jest.fn(); let located;
  Object.defineProperty(navigator, 'geolocation', { configurable: true, value: { getCurrentPosition: jest.fn(callback => { located = callback; }) } });
  await render({ onChange, value: { latitude: -6, longitude: 107 } });
  await click(button('Gunakan Lokasi Saya'));
  await render({ onChange, disabled: true, value: { latitude: -6, longitude: 107 } });
  expect(instance().dragging.enabled()).toBe(false);
  expect(instance().scrollWheelZoom.enabled()).toBe(false);
  await act(async () => { instance().fire('click', { latlng: L.latLng(-7, 108) }); located({ coords: { latitude: -7, longitude: 108 } }); });
  expect(onChange).not.toHaveBeenCalled();
});

test('editing query cancels stale results and unmount aborts pending search', async () => {
  let resolve;
  api.post.mockImplementation(() => new Promise(done => { resolve = done; }));
  await render({ searchHint: 'Jakarta' });
  await click(button('Cari'));
  const firstSignal = api.post.mock.calls[0][2].signal;
  await type('Bandung');
  expect(firstSignal.aborted).toBe(true);
  await act(async () => resolve({ data: { results: [{ label: 'Old address', latitude: -6, longitude: 107 }] } }));
  expect(host.textContent).not.toContain('Old address');
  await click(button('Cari'));
  const signal = api.post.mock.calls[1][2].signal;
  await act(async () => root.render(null));
  expect(signal.aborted).toBe(true);
});
