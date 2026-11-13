import React, { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import CameraCapture from './CameraCapture';
import LandmarkEditor from './LandmarkEditor';

let host; let root;
const render = async node => act(async () => root.render(node));
const click = async element => act(async () => element.dispatchEvent(new MouseEvent('click', { bubbles: true })));
beforeEach(() => {
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
  jest.spyOn(window, 'Image').mockImplementation(() => ({ naturalWidth: 100, naturalHeight: 100, set src(value) { this.source = value; this.onload?.(); } }));
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); });

test('camera requires actual consent/checklist and does not request permission on render', async () => {
  const getUserMedia = jest.fn(); Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia }, configurable: true });
  await render(<CameraCapture consent={false} checklistComplete={true} />);
  expect(host.querySelector('[data-testid="optifit-camera-start"]').disabled).toBe(true); expect(getUserMedia).not.toHaveBeenCalled();
  await render(<CameraCapture consent checklistComplete />); expect(getUserMedia).not.toHaveBeenCalled();
});

test('customer camera controls sit directly below preview without operator fields', async () => {
  await render(<CameraCapture customerMode consent checklistComplete />);
  const station = host.querySelector('[data-testid="optifit-camera-station"]');
  expect(station.children[0].querySelector('video')).not.toBeNull();
  expect(station.children[1].getAttribute('data-testid')).toBe('optifit-camera-controls');
  expect(station.querySelector('[data-testid="optifit-camera-start"]')).not.toBeNull();
  expect(host.querySelector('[data-testid="optifit-quality-indicators"]')).toBeNull();
  expect(host.textContent).not.toMatch(/operator|Aktifkan sensor/);
});

test('camera arriving after close is stopped rather than attached', async () => {
  Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
  let resolve; const pending = new Promise(done => { resolve = done; }); const stop = jest.fn();
  Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia: jest.fn(() => pending) }, configurable: true });
  await render(<CameraCapture consent checklistComplete />);
  await click(host.querySelector('[data-testid="optifit-camera-start"]'));
  await click(host.querySelector('[aria-label="Tutup kamera"]'));
  await act(async () => resolve({ getTracks: () => [{ stop }] }));
  expect(stop).toHaveBeenCalledTimes(1); expect(host.querySelector('video').srcObject).toBeNull();
});

test('camera denial preserves manual fallback and unknown position indicators', async () => {
  const error = Object.assign(new Error('denied'), { name: 'NotAllowedError' });
  Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia: jest.fn().mockRejectedValue(error) }, configurable: true });
  await render(<CameraCapture consent checklistComplete />); await click(host.querySelector('[data-testid="optifit-camera-start"]'));
  expect(host.textContent).toContain('Izin kamera ditolak'); expect(host.textContent).toContain('Tidak terukur otomatis');
});

test('landmark correction undo/redo retains raw coordinate state', async () => {
  const observed = jest.fn();
  function Harness() {
    const [points, setPoints] = useState({ rightPupil: { x: 10, y: 15 } });
    return <LandmarkEditor image={{ dataUrl: 'data:image/png;base64,AA==', width: 100, height: 100 }} points={points}
      pointDefinitions={[{ key: 'rightPupil', label: 'Pupil OD' }]} onChange={next => { observed(next); setPoints(next); }} />;
  }
  await render(<Harness />);
  const svg = host.querySelector('[role="application"]');
  svg.getScreenCTM = () => ({ inverse: () => ({}) });
  svg.createSVGPoint = () => ({ x: 0, y: 0, matrixTransform() { return { x: this.x, y: this.y }; } });
  await act(async () => svg.dispatchEvent(new MouseEvent('pointerdown', { bubbles: true, clientX: 40, clientY: 50, button: 0 })));
  await act(async () => svg.dispatchEvent(new MouseEvent('pointerup', { bubbles: true, clientX: 40, clientY: 50, button: 0 })));
  expect(observed).toHaveBeenLastCalledWith({ rightPupil: { x: 40, y: 50 } });
  await click(host.querySelector('[aria-label="Undo koreksi"]')); expect(observed).toHaveBeenLastCalledWith({ rightPupil: { x: 10, y: 15 } });
  await click(host.querySelector('[aria-label="Redo koreksi"]')); expect(observed).toHaveBeenLastCalledWith({ rightPupil: { x: 40, y: 50 } });
});

test('mismatched decoded image dimensions block edits and candidate actions', async () => {
  const changed = jest.fn();
  await render(<LandmarkEditor image={{ dataUrl: 'data:image/png;base64,AA==', width: 90, height: 100 }} points={{ rightPupil: { x: 10, y: 15 } }}
    pointDefinitions={[{ key: 'rightPupil', label: 'Pupil OD' }]} onChange={changed} />);
  expect(host.textContent).toContain('Dimensi metadata tidak sama');
  const svg = host.querySelector('[role="application"]');
  await act(async () => svg.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'ArrowRight' })));
  expect(changed).not.toHaveBeenCalled();
  expect([...host.querySelectorAll('button')].find(button => button.textContent.includes('Cari kandidat')).disabled).toBe(true);
});

test('read-only landmark review permits pan and selection without mutating points', async () => {
  const changed = jest.fn();
  await render(<LandmarkEditor disabled image={{ dataUrl: 'data:image/png;base64,AA==', width: 100, height: 100 }} points={{ rightPupil: { x: 10, y: 15 } }}
    pointDefinitions={[{ key: 'rightPupil', label: 'Pupil OD' }]} onChange={changed} />);
  expect(host.querySelector('select').disabled).toBe(false);
  const svg = host.querySelector('[role="application"]');
  svg.getScreenCTM = () => ({ inverse: () => ({}) });
  svg.createSVGPoint = () => ({ x: 0, y: 0, matrixTransform() { return { x: this.x, y: this.y }; } });
  await act(async () => svg.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'ArrowRight' })));
  await click([...host.querySelectorAll('button')].find(button => button.textContent.includes('Geser gambar')));
  await act(async () => svg.dispatchEvent(new MouseEvent('pointerdown', { bubbles: true, clientX: 10, clientY: 10, button: 0 })));
  await act(async () => svg.dispatchEvent(new MouseEvent('pointermove', { bubbles: true, clientX: 40, clientY: 30, button: 0 })));
  await act(async () => svg.dispatchEvent(new MouseEvent('pointerup', { bubbles: true, clientX: 40, clientY: 30, button: 0 })));
  expect(svg.querySelector('g').getAttribute('transform')).toBe('translate(30 20) scale(1)');
  expect(changed).not.toHaveBeenCalled();
});
