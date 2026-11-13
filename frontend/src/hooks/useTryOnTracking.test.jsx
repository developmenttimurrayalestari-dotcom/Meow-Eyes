import React, { act, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import useTryOnTracking from './useTryOnTracking';
import { createFaceTracker, faceFrameFit, smoothFaceFit } from '../lib/faceTracking';

jest.mock('../lib/faceTracking', () => ({
  createFaceTracker: jest.fn(), faceFrameFit: jest.fn(), smoothFaceFit: jest.fn((_previous, next) => next),
}));
let root, host, callback, tracker;
const video = { videoWidth: 640, videoHeight: 480, currentTime: 1 };
const image = { naturalWidth: 640, naturalHeight: 480 };
const stage = { clientWidth: 800, clientHeight: 600 };
function Harness({ cameraOn = false, photo = '', retry = 0 }) {
  const videoRef = useRef(video), photoRef = useRef(image), stageRef = useRef(stage);
  const result = useTryOnTracking({ videoRef, photoRef, stageRef, cameraOn, photo, retry, asset: { id: 'asset' } });
  return <output>{JSON.stringify(result)}</output>;
}
const render = async props => act(async () => root.render(<Harness {...props} />));
const frame = async time => { const next = callback; await act(async () => next(time)); };
const state = () => JSON.parse(host.querySelector('output').textContent);
beforeEach(() => {
  jest.clearAllMocks(); video.currentTime = 1; stage.clientWidth = 800;
  tracker = { detectForVideo: jest.fn(() => ({ faceLandmarks: [['face']] })), detect: jest.fn(() => ({ faceLandmarks: [['face']] })), close: jest.fn() };
  createFaceTracker.mockResolvedValue(tracker);
  faceFrameFit.mockReturnValue({ width: 60, x: 50, y: 40 });
  smoothFaceFit.mockImplementation((_previous, next) => next);
  jest.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage: jest.fn() });
  jest.spyOn(window, 'getComputedStyle').mockReturnValue({ objectFit: 'contain' });
  jest.spyOn(window, 'requestAnimationFrame').mockImplementation(next => { callback = next; return 1; });
  jest.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => {});
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { if (root) await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); });

test('camera inference updates the overlay, skips unchanged frames and hides it when a face is lost', async () => {
  await render({ cameraOn: true }); await frame(100);
  expect(createFaceTracker).toHaveBeenCalledWith('VIDEO');
  expect(state().state).toBe('tracking');
  expect(faceFrameFit.mock.calls[0][3]).toBe(true);
  await frame(200); expect(tracker.detectForVideo).toHaveBeenCalledTimes(1);
  video.currentTime = 2; faceFrameFit.mockReturnValue(null);
  await frame(300); expect(state()).toEqual({ state: 'searching', fit: null });
  await render({ cameraOn: false });
  expect(tracker.close).toHaveBeenCalledTimes(1);
  expect(state()).toEqual({ state: 'idle', fit: null });
});

test('photo detection runs once and reprojects when the viewport changes', async () => {
  await render({ photo: 'blob:local' }); await frame(100); await frame(200);
  expect(createFaceTracker).toHaveBeenCalledWith('IMAGE');
  expect(tracker.detect).toHaveBeenCalledTimes(1);
  expect(tracker.detectForVideo).not.toHaveBeenCalled();
  expect(faceFrameFit.mock.calls[0][3]).toBe(false);
  stage.clientWidth = 600; await frame(300);
  expect(tracker.detect).toHaveBeenCalledTimes(2);
});

test('detector resolving after unmount is disposed without starting inference', async () => {
  let resolve; createFaceTracker.mockReturnValue(new Promise(done => { resolve = done; }));
  await render({ cameraOn: true });
  await act(async () => root.unmount()); root = null;
  await act(async () => resolve(tracker));
  expect(tracker.close).toHaveBeenCalledTimes(1);
  expect(tracker.detectForVideo).not.toHaveBeenCalled();
});

test('model load failure hides the frame and can be retried', async () => {
  createFaceTracker.mockRejectedValueOnce(new Error('load failed'));
  await render({ cameraOn: true }); expect(state()).toEqual({ state: 'error', fit: null });
  await render({ cameraOn: true, retry: 1 }); await frame(100);
  expect(state().state).toBe('tracking');
});

test('a fullscreen resize reprojects a paused frame without restarting detection', async () => {
  await render({ cameraOn: true }); await frame(100);
  window.getComputedStyle.mockReturnValue({ objectFit: 'cover' });
  stage.clientWidth = 390;
  await frame(200);
  expect(tracker.detectForVideo).toHaveBeenCalledTimes(2);
  expect(faceFrameFit.mock.calls.at(-1)[5]).toBe('cover');
  expect(smoothFaceFit.mock.calls.at(-1)[0]).toBeNull();
  expect(createFaceTracker).toHaveBeenCalledTimes(1);
  expect(tracker.close).not.toHaveBeenCalled();
});
