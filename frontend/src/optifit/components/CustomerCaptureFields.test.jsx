import React, { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CustomerScaleFields, CustomerPhotoChecks } from './CustomerCaptureFields';
import { frameScaleSpec } from '../domain/frameScale';

let host, root;
beforeEach(() => { host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
test('scale uses session dimensions without a method picker or editable length and requires explicit confirmation', async () => {
  function Harness() {
    const [spec, setSpec] = useState(frameScaleSpec({ a: 52, b: 40 }, 'frontal'));
    return <CustomerScaleFields spec={spec} setSpec={setSpec} calibration={{ valid: false }} frame={{ a: 52, b: 40 }} view="frontal"/>;
  }
  await act(async () => root.render(<Harness/>));
  expect(host.querySelectorAll('input[type=number]')).toHaveLength(0);
  expect(host.querySelector('select')).toBeNull();
  expect(host.querySelector('[data-testid="customer-frame-reference"]').textContent).toContain('52 mm');
  expect(host.textContent).not.toMatch(/Lebar benda|Tinggi benda|operator/);
  expect(host.querySelector('input[type=checkbox]').checked).toBe(false);
});
test('vertex hides head angle and vertical reference checks; panto shows them', async () => {
  const props = { confirmations: {}, setConfirmations: jest.fn(), headPitchDeg: '', headPitchSource: '', inwardDirection: '' };
  await act(async () => root.render(<CustomerPhotoChecks {...props} vertex/>));
  expect(host.textContent).toContain('permukaan belakang lensa');
  expect(host.textContent).not.toMatch(/Kemiringan kepala|Garis pembanding tegak/);
  await act(async () => root.render(<CustomerPhotoChecks {...props} panto/>));
  expect(host.textContent).toContain('Kemiringan kepala');
  expect(host.textContent).not.toContain('permukaan belakang lensa');
  expect(host.querySelector('input[type=number]').value).toBe('');
});
