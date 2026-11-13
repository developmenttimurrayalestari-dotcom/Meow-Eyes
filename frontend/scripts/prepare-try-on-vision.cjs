// Explicit setup command; runtime face images never leave the browser.
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const modelUrl = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task';
(async () => {
  const target = path.join(root, 'public/try-on/vision');
  const runtime = path.join(root, 'node_modules/@mediapipe/tasks-vision/wasm');
  await fs.mkdir(path.join(target, 'wasm'), { recursive: true });
  const manifest = { package: '@mediapipe/tasks-vision', version: '1.2.2', modelSource: modelUrl, files: {} };
  for (const name of await fs.readdir(runtime)) {
    if (!/\.(wasm|js)$/.test(name)) continue;
    const bytes = await fs.readFile(path.join(runtime, name));
    await fs.writeFile(path.join(target, 'wasm', name), bytes);
    manifest.files[`wasm/${name}`] = { bytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex') };
  }
  const response = await fetch(modelUrl);
  if (!response.ok) throw new Error(`Model download failed: HTTP ${response.status}`);
  const model = Buffer.from(await response.arrayBuffer());
  if (model.length < 1000000 || model.length > 30000000) throw new Error('Unexpected model size');
  await fs.writeFile(path.join(target, 'face_landmarker.task'), model);
  manifest.files['face_landmarker.task'] = { bytes: model.length, sha256: crypto.createHash('sha256').update(model).digest('hex') };
  await fs.writeFile(path.join(target, 'NOTICE.txt'), 'MediaPipe Tasks Vision 1.2.2\nCopyright Google LLC. SDK license: Apache-2.0.\nhttps://github.com/google-ai-edge/mediapipe/blob/master/LICENSE\nModel source: ' + modelUrl + '\nModel documentation: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker\n');
  await fs.writeFile(path.join(target, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log(`Face tracking ready: ${Object.keys(manifest.files).length} local assets.`);
})().catch(error => { console.error(error.message); process.exitCode = 1; });
