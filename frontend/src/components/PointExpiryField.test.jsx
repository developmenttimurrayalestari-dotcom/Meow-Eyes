import React, { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import PointExpiryField, { pointExpiryText } from './PointExpiryField';

let host, root;
beforeEach(() => { host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

function Form({ initial }) {
  const [days, setDays] = useState(initial);
  return <form><PointExpiryField value={days} onChange={setDays} /><output>{days}</output></form>;
}

test('forever checkbox hides days, stores permanent expiry and restores the previous duration', async () => {
  await act(async () => root.render(<Form initial={75} />));
  expect(host.querySelector('input[type=number]').min).toBe('1');
  await act(async () => host.querySelector('input[type=checkbox]').click());
  expect(host.querySelector('output').textContent).toBe('0');
  expect(host.querySelector('input[type=number]')).toBeNull();
  expect(host.querySelector('form').checkValidity()).toBe(true);
  await act(async () => host.querySelector('input[type=checkbox]').click());
  expect(host.querySelector('input[type=number]').value).toBe('75');
});

test('existing permanent rules load checked and can switch back to a valid duration', async () => {
  await act(async () => root.render(<Form initial={0} />));
  expect(host.querySelector('input').checked).toBe(true);
  expect(host.querySelector('input[type=number]')).toBeNull();
  await act(async () => host.querySelector('input').click());
  expect(host.querySelector('input[type=number]').value).toBe('30');
  expect(pointExpiryText(0)).toBe('Berlaku selamanya');
  expect(pointExpiryText(30)).toBe('Berlaku 30 hari');
});

test('an empty day field stays required instead of silently becoming permanent', async () => {
  await act(async () => root.render(<Form initial="" />));
  expect(host.querySelector('input[type=checkbox]').checked).toBe(false);
  expect(host.querySelector('input[type=number]')).not.toBeNull();
  expect(host.querySelector('form').checkValidity()).toBe(false);
});
