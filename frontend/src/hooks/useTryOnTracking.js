import { useEffect, useRef, useState } from 'react';
import { createFaceTracker, faceFrameFit, smoothFaceFit } from '../lib/faceTracking';

export default function useTryOnTracking({ videoRef, photoRef, stageRef, cameraOn, photo, asset, retry }) {
  const [tracking, setTracking] = useState({ state: 'idle', fit: null });
  const assetRef = useRef(asset);
  assetRef.current = asset;
  useEffect(() => {
    let cancelled = false, tracker, animation, previous = null, lastTime = -1, lastTick = -Infinity, photoKey = '', previousGeometry = '';
    if (!cameraOn && !photo) { setTracking({ state: 'idle', fit: null }); return undefined; }
    setTracking({ state: 'loading', fit: null });
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    if (!context) { setTracking({ state: 'error', fit: null }); return undefined; }
    const tick = timestamp => {
      if (cancelled) return;
      try {
        const element = cameraOn ? videoRef.current : photoRef.current;
        const stage = stageRef.current;
        const width = cameraOn ? element?.videoWidth : element?.naturalWidth;
        const height = cameraOn ? element?.videoHeight : element?.naturalHeight;
        const stageSize = { width: stage?.clientWidth, height: stage?.clientHeight };
        const objectFit = element ? window.getComputedStyle(element).objectFit : 'contain';
        const geometry = `${width}:${height}:${stageSize.width}:${stageSize.height}:${objectFit}`;
        const key = `${photo}:${geometry}:${assetRef.current.id}`;
        const ready = width > 0 && height > 0 && stageSize.width > 0 && stageSize.height > 0 && context;
        const changed = cameraOn ? element.currentTime !== lastTime || geometry !== previousGeometry : key !== photoKey;
        if (ready && changed && timestamp - lastTick >= 80) {
          if (geometry !== previousGeometry) previous = null;
          previousGeometry = geometry;
          lastTick = timestamp; lastTime = element.currentTime; photoKey = key;
          // Keep local inference small and bounded for mobile/CPU devices.
          const scale = Math.min(1, 640 / Math.max(width, height));
          canvas.width = Math.max(1, Math.round(width * scale));
          canvas.height = Math.max(1, Math.round(height * scale));
          context.drawImage(element, 0, 0, canvas.width, canvas.height);
          const result = cameraOn ? tracker.detectForVideo(canvas, timestamp) : tracker.detect(canvas);
          const fit = faceFrameFit(result.faceLandmarks?.[0], { width, height }, stageSize, cameraOn, assetRef.current, objectFit);
          previous = smoothFaceFit(previous, fit);
          setTracking({ state: fit ? 'tracking' : 'searching', fit: previous });
        }
        animation = requestAnimationFrame(tick);
      } catch {
        previous = null;
        setTracking({ state: 'error', fit: null });
      }
    };
    createFaceTracker(cameraOn ? 'VIDEO' : 'IMAGE').then(result => {
      if (cancelled) { result.close(); return; }
      tracker = result;
      setTracking({ state: 'searching', fit: null });
      animation = requestAnimationFrame(tick);
    }).catch(() => { if (!cancelled) setTracking({ state: 'error', fit: null }); });
    return () => { cancelled = true; cancelAnimationFrame(animation); tracker?.close(); };
  }, [cameraOn, photo, retry, videoRef, photoRef, stageRef]);
  return tracking;
}
