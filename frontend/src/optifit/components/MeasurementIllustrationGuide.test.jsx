import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import MeasurementIllustrationGuide from './MeasurementIllustrationGuide';
import { measurementGuide } from '../domain/measurementGuides';

let host, root;
beforeEach(() => { host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
const render = async node => act(async () => root.render(node));
const click = async text => act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes(text)).click());
const data = { requiredParameters: ['near_pd'], frame: { pdReference: 'facial_midline' }, workingDistanceCm: 35, captures: [] };

test('photo, reference and landmark examples are separate and never insert sample points into customer data', async () => {
  const original = JSON.stringify(data);
  await render(<MeasurementIllustrationGuide data={data}/>);
  expect(host.textContent).toContain('35 cm');
  expect(host.querySelectorAll('[data-illustration-point]')).toHaveLength(0);
  await click('Acuan frame');
  expect(host.querySelectorAll('[data-illustration-point]')).toHaveLength(2);
  expect(host.querySelector('[data-illustration-point="rightPupil"]')).toBeNull();
  await click('Tandai titik');
  await click('Pusat pupil kanan');
  expect(host.querySelector('.of-illustration-detail').textContent).toContain('bukan pantulan lampu');
  expect(host.querySelector('[data-guide-point="rightPupil"]').getAttribute('aria-pressed')).toBe('true');
  expect(JSON.stringify(data)).toBe(original);
});

test('switching method and side resets the guide and retains only the applicable landmarks', async () => {
  const vertex = { ...data, requiredParameters: ['vertex_right', 'vertex_left'] };
  await render(<MeasurementIllustrationGuide data={vertex} view="lateral_right" initialStage="points"/>);
  expect(host.querySelector('[data-guide-point="backLens"]')).not.toBeNull();
  expect(host.querySelector('[data-guide-point="lensTop"]')).toBeNull();
  await render(<MeasurementIllustrationGuide data={vertex} view="lateral_left" method="frame" initialStage="points"/>);
  expect(host.textContent).toContain('Sisi kiri (OS)');
  expect(host.querySelector('[data-guide-point="markerTL"]')).toBeNull();
  expect(host.querySelector('[data-guide-point="scaleStart"]')).not.toBeNull();
});

test('left-side example uses lens height and flips gaze toward the face front', () => {
  const guide = measurementGuide({ parameters: ['vertex_left'], view: 'lateral_left' });
  const p = Object.fromEntries(guide.points.map(point => [point.key, point]));
  expect(p.markerTL).toBeUndefined();
  expect(p.scaleStart.y).toBeLessThan(p.scaleEnd.y);
  expect(p.gazeEnd.x).toBeLessThan(p.gazeStart.x);
  expect(p.backLens.x).toBeLessThan(p.cornea.x);
});

test('catalog PD guide uses frame bridge reference; manual PD guide uses facial reference', () => {
  const guide = pdReference => measurementGuide({ parameters: ['distance_pd'], pdReference });
  expect(guide('frame_bridge').points.find(point => point.key === 'midlineTop').label).toContain('kacamata');
  expect(guide('facial_midline').points.find(point => point.key === 'midlineTop').label).toContain('wajah');
});

test('panto requires a real vertical and head angle; wrap never offers fabricated camera points', async () => {
  const panto = measurementGuide({ parameters: ['pantoscopic_right'], method: 'frame' });
  expect(panto.points.map(point => point.key)).toEqual(['scaleStart', 'scaleEnd', 'lensTop', 'lensBottom', 'verticalTop', 'verticalBottom']);
  expect(panto.points.find(point => point.key === 'verticalTop').detail).toContain('Tepi layar bukan bukti');
  await render(<MeasurementIllustrationGuide data={{ ...data, requiredParameters: ['wrap_right', 'wrap_left'] }} initialStage="points"/>);
  expect(host.querySelector('[data-guide-point]')).toBeNull();
  expect(host.textContent).not.toContain('Tandai titik');
  await click('Catat & simpan');
  expect(host.textContent).toContain('tidak menghitung sudut lengkungan dari foto biasa');
});
