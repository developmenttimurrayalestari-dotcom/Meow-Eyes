import React, { useRef } from 'react';

// The API keeps 0 as its no-expiration marker; admins use a checkbox instead.
export default function PointExpiryField({ value, onChange, label = 'Masa berlaku poin', inputClassName = 'block w-full mt-1 rounded-xl border p-2 text-sm' }) {

  const lastDays = useRef(30);
  const forever = value === 0 || value === '0';
  if (Number(value) > 0) lastDays.current = Number(value);
  return <fieldset className="space-y-2 text-sm">
    <legend className="font-medium">{label}</legend>
    <label className="flex items-center gap-2"><input type="checkbox" checked={forever} onChange={(e) => onChange(e.target.checked ? 0 : lastDays.current)} />{"Berlaku selamanya"}</label>
    {!forever && <label className="block">{"Jumlah hari"}<input required type="number" min="1" max="3650" className={inputClassName} value={value} onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))} /></label>}
  </fieldset>;
}

export const pointExpiryText = (days) => Number(days) === 0 ? 'Berlaku selamanya' : `Berlaku ${days} hari`;
