import React, { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import ShippingOptions from './ShippingOptions';

jest.mock('../lib/api', () => ({ formatIDR: value => `Rp ${value}` }));
let host, root;
const quote = (id, type, label) => ({ quote_id:id, service_type:type, courier_code:'JNE',
  courier_name:'JNE', service_code:id, service_label:label, cost:10000, etd:'1–2 hari' });
const choices = [quote('regular','regular','Reguler'),quote('express','express','Esok Sampai'),
  quote('same','same_day','Sameday'),quote('instant','instant','Instant Bike'),
  quote('cargo','cargo','Reguler'),quote('cargo-2','cargo','Fast Track')];
const click = node => act(async () => node.dispatchEvent(new MouseEvent('click',{bubbles:true})));
beforeEach(() => { host=document.createElement('div'); document.body.appendChild(host); root=createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test('categories use provider types and changing category selects its exact quote', async () => {
  const changed=jest.fn();
  function Demo() {
    const [selected,setSelected]=useState(choices[0]);
    return <ShippingOptions options={choices} selected={selected} onChange={option => { changed(option);setSelected(option); }} />;
  }
  await act(async () => root.render(<Demo />));
  expect([...host.querySelectorAll('button')].map(button => button.textContent)).toEqual([
    'Reguler (1)','Express (1)','Same-day (1)','Instant (1)','Cargo (2)',
  ]);
  expect(host.querySelectorAll('input[type=radio]')).toHaveLength(1);
  await click(host.querySelector('[data-testid=shipping-type-cargo]'));
  expect(changed).toHaveBeenLastCalledWith(choices[4]);
  expect(host.querySelector('[data-testid=shipping-group-cargo]').textContent).toContain('Reguler');
  const inputs=host.querySelectorAll('input[type=radio]');
  expect(inputs).toHaveLength(2); expect(inputs[0].checked).toBe(true);
  await click(inputs[1]);
  expect(changed).toHaveBeenLastCalledWith(choices[5]);
  await click(host.querySelector('[data-testid=shipping-type-cargo]'));
  expect(inputs[1].checked).toBe(true); // Clicking the active category keeps the chosen service.
  await click(host.querySelector('[data-testid=shipping-type-same_day]'));
  expect(changed).toHaveBeenLastCalledWith(choices[2]);
  expect(host.querySelectorAll('input[type=radio]')).toHaveLength(1);
});

test('older responses are grouped by service, without confusing the courier brand with express', async () => {
  const options=[{...quote('REG',undefined,'Reguler'),courier_name:'J&T Express'},
    quote('CTCYES23',undefined,'City to City Yakin Esok Sampai'),
    quote('FT',undefined,'Fast Track'), quote('NEW',undefined,'Layanan khusus')];
  await act(async () => root.render(<ShippingOptions options={options} selected={options[0]} onChange={jest.fn()} />));
  expect(host.querySelector('[data-testid=shipping-type-regular]').getAttribute('aria-pressed')).toBe('true');
  expect(host.querySelector('[data-testid=shipping-type-express]')).not.toBeNull();
  expect(host.querySelector('[data-testid=shipping-type-cargo]')).not.toBeNull();
  expect(host.querySelector('[data-testid=shipping-type-other]')).not.toBeNull();
  expect(host.querySelector('[data-testid=shipping-type-instant]')).toBeNull();
});

test('submitting disables both category changes and courier selection', async () => {
  await act(async () => root.render(<ShippingOptions options={choices} selected={choices[3]} disabled onChange={jest.fn()} />));
  expect([...host.querySelectorAll('button,input')].every(control => control.disabled)).toBe(true);
  expect(host.querySelector('[data-testid=shipping-type-instant]').getAttribute('aria-pressed')).toBe('true');
});

test('refreshed options remove unavailable groups without retaining an empty panel', async () => {
  await act(async () => root.render(<ShippingOptions options={choices} selected={choices[3]} onChange={jest.fn()} />));
  await act(async () => root.render(<ShippingOptions options={[choices[0]]} selected={choices[0]} onChange={jest.fn()} />));
  expect(host.querySelector('[data-testid=shipping-type-instant]')).toBeNull();
  expect(host.querySelector('[data-testid=shipping-group-regular]')).not.toBeNull();
});
