import React, { useEffect, useRef } from "react";
import { imageSrc } from "../lib/api";

function disposeScene(scene) {
  if (!scene) return;
  const materials = new Set();
  const textures = new Set();
  const bitmaps = new Set();
  const geometries = new Set();
  scene.traverse((node) => {
    if (node.geometry) geometries.add(node.geometry);
    for (const material of Array.isArray(node.material) ? node.material : node.material ? [node.material] : []) materials.add(material);
  });
  for (const material of materials) for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
  for (const texture of textures) {
    if (texture.source?.data?.close) bitmaps.add(texture.source.data);
    texture.dispose();
  }
  for (const bitmap of bitmaps) bitmap.close();
  for (const material of materials) material.dispose();
  for (const geometry of geometries) geometry.dispose();
}

// Rendering is event-driven: camera video stays in its native <video>, while
// the transparent WebGL layer is redrawn only on model/fit/viewport changes.
export default function TryOnModel({ asset, fit, onReady, onError }) {
  const container = useRef(null);
  const latestFit = useRef(fit);
  const renderFit = useRef(null);
  const callbacks = useRef({ onReady, onError });
  latestFit.current = fit;
  callbacks.current = { onReady, onError };
  useEffect(() => {
    const host = container.current;
    const controller = new AbortController();
    let cancelled = false;
    let renderer;
    let resizeObserver;
    let loadedScene;
    let handleResize;
    const start = async () => {
      try {
        const [THREE, { GLTFLoader }] = await Promise.all([import("three"), import("three/addons/loaders/GLTFLoader.js")]);
        if (cancelled) return;
        const source = new URL(imageSrc(asset.source_url), window.location.origin);
        if (!["https:", "http:"].includes(source.protocol) || source.username || source.password) throw new Error("Sumber model tidak valid.");
        renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "low-power" });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setClearColor(0x000000, 0);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;
        renderer.domElement.style.width = "100%";
        renderer.domElement.style.height = "100%";
        renderer.domElement.setAttribute("aria-hidden", "true");
        host.appendChild(renderer.domElement);
        const scene = new THREE.Scene();
        const camera = new THREE.OrthographicCamera(-2, 2, 2, -2, 0.01, 100);
        camera.position.set(0, 0, 10);
        camera.lookAt(0, 0, 0);
        scene.add(new THREE.HemisphereLight(0xffffff, 0x8b91a6, 3));
        const key = new THREE.DirectionalLight(0xffffff, 4); key.position.set(3, 4, 6); scene.add(key);
        const fill = new THREE.DirectionalLight(0xffffff, 2); fill.position.set(-3, 1, 3); scene.add(fill);
        const response = await fetch(source.href, { signal: controller.signal, credentials: "omit" });
        if (!response.ok) throw new Error("Model tidak dapat diunduh.");
        if (Number(response.headers.get("content-length")) > 30 * 1024 * 1024) throw new Error("Model terlalu besar untuk pratinjau.");
        const bytes = await response.arrayBuffer();
        if (bytes.byteLength > 30 * 1024 * 1024) throw new Error("Model terlalu besar untuk pratinjau.");
        if (cancelled) return;
        const loader = new GLTFLoader();
        const gltf = await loader.parseAsync(bytes, new URL(".", source).href);
        loadedScene = gltf.scene;
        if (cancelled) { disposeScene(loadedScene); loadedScene = null; return; }
        const box = new THREE.Box3().setFromObject(loadedScene);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        const width = size.x || Math.max(size.y, size.z);
        if (!Number.isFinite(width) || width <= 0) throw new Error("Model tidak memiliki geometri yang dapat ditampilkan.");
        loadedScene.position.sub(center);
        const normalized = new THREE.Group();
        normalized.add(loadedScene);
        normalized.scale.setScalar(2 / width);
        const pose = new THREE.Group();
        pose.add(normalized); scene.add(pose);
        let halfWidth = 2;
        renderFit.current = (value) => {
          if (cancelled) return;
          const factor = value.width / 100 * halfWidth;
          pose.scale.setScalar(factor);
          pose.position.set((value.x / 100 - 0.5) * halfWidth * 2, (0.5 - value.y / 100) * 4, value.depth || 0);
          pose.rotation.set(THREE.MathUtils.degToRad(value.pitch), THREE.MathUtils.degToRad(value.yaw), THREE.MathUtils.degToRad(-value.roll));
          renderer.render(scene, camera);
        };
        handleResize = () => {
          if (cancelled) return;
          const w = Math.max(1, host.clientWidth); const h = Math.max(1, host.clientHeight);
          halfWidth = 2 * w / h;
          camera.left = -halfWidth; camera.right = halfWidth;
          camera.updateProjectionMatrix(); renderer.setSize(w, h, false);
          renderFit.current?.(latestFit.current);
        };
        if (window.ResizeObserver) { resizeObserver = new ResizeObserver(handleResize); resizeObserver.observe(host); }
        window.addEventListener("resize", handleResize);
        handleResize(); callbacks.current.onReady?.();
      } catch (error) {
        if (!cancelled) callbacks.current.onError?.("Model 3D belum dapat ditampilkan di browser ini. Gunakan gambar pratinjau jika tersedia, atau coba browser dengan WebGL 2.");
      }
    };
    start();
    return () => {
      cancelled = true; controller.abort(); renderFit.current = null;
      resizeObserver?.disconnect(); if (handleResize) window.removeEventListener("resize", handleResize);
      disposeScene(loadedScene);
      if (renderer) { renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove(); }
    };
  }, [asset.id, asset.source_url]);
  useEffect(() => { renderFit.current?.(fit); }, [fit]);
  return <div ref={container} className="absolute inset-0 pointer-events-none" data-testid="try-on-model" />;
}
