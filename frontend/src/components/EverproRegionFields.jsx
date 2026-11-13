import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { api, apiError } from '../lib/api';

const levels = [
  { path: 'provinces', id: 'province_id', field: 'province', label: 'Provinsi' },
  { path: 'cities', id: 'city_id', parent: 'province_id', field: 'city', label: 'Kota / Kabupaten' },
  { path: 'districts', id: 'district_id', parent: 'city_id', field: 'district', label: 'Kecamatan' },
  { path: 'subdistricts', id: 'subdistrict_id', parent: 'district_id', field: 'subdistrict', label: 'Kelurahan / Desa' },
];
const normalize = value => String(value || '').trim().replace(/\s+/g, ' ').toLocaleLowerCase('id');

function useOptions(level, parentId = '') {
  const [state, setState] = useState({ parentId, options: [], loading: !level.parent, error: '' });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); let active = true;
    if (level.parent && !parentId) { setState({ parentId, options: [], loading: false, error: '' }); return () => { active = false; controller.abort(); }; }
    setState({ parentId, options: [], loading: true, error: '' });
    api.get('/shipping/locations/' + level.path, { params: level.parent ? { [level.parent]: parentId } : {}, signal: controller.signal })
      .then(({ data }) => {
        if (!Array.isArray(data?.locations)) throw new Error('Respons data wilayah tidak valid.');
        if (active) setState({ parentId, options: data.locations, loading: false, error: '' });
      }).catch(error => { if (active) setState({ parentId, options: [], loading: false, error: apiError(error, 'Data wilayah belum dapat dimuat. Coba kembali.') }); });
    return () => { active = false; controller.abort(); };
  }, [level, parentId, retry]);
  return { ...(state.parentId === parentId ? state : { options: [], loading: true, error: '' }), retry: () => setRetry(value => value + 1) };
}

export default function EverproRegionFields({ value, onChange, initialAddress }) {
  const prefix = useId(); const touched = useRef(false);
  const provinces = useOptions(levels[0]);
  const cities = useOptions(levels[1], value.province_id);
  const districts = useOptions(levels[2], value.city_id);
  const villages = useOptions(levels[3], value.district_id);
  const choose = useCallback((index, identity, automatic = false) => {
    if (!automatic) touched.current = true;
    const lists = [provinces.options, cities.options, districts.options, villages.options];
    const option = lists[index].find(row => row.id === identity);
    const next = { ...value, postal_code: '' };
    for (let i = index; i < levels.length; i += 1) { next[levels[i].id] = ''; next[levels[i].field] = ''; }
    if (option) { next[levels[index].id] = option.id; next[levels[index].field] = option.name; if (index === 3) next.postal_code = option.postal_code; }
    onChange(next);
  }, [value, onChange, provinces.options, cities.options, districts.options, villages.options]);
  useEffect(() => {
    if (!initialAddress || touched.current) return;
    const lists = [provinces, cities, districts, villages];
    for (let i = 0; i < levels.length; i += 1) {
      const level = levels[i];
      if (value[level.id]) continue;
      if (level.parent && !value[level.parent]) return;
      const match = lists[i].options.find(row => normalize(row.name) === normalize(initialAddress[level.field])
        && (i !== 3 || row.postal_code === initialAddress.postal_code));
      if (match) choose(i, match.id, true);
      return;
    }
  }, [initialAddress, value, provinces, cities, districts, villages, choose]);
  return <>
    <p className="sm:col-span-2 text-xs text-meow-gray">Pilih wilayah sesuai data EVERPRO. Kode pos terisi otomatis setelah kelurahan/desa dipilih.</p>
    {[provinces, cities, districts, villages].map((state, index) => {
      const level = levels[index]; const missingParent = level.parent && !value[level.parent];
      return <div key={level.id} className="min-w-0"><label htmlFor={prefix + level.id} className="block text-xs font-semibold">{level.label}</label>
        <select id={prefix + level.id} name={level.field} value={value[level.id] || ''} onChange={event => choose(index, event.target.value)} required
          disabled={missingParent || state.loading || Boolean(state.error)} data-testid={'addr-' + level.field}
          className="block w-full mt-1 px-3 py-2.5 rounded-xl bg-meow-bg border border-meow-midnight/10 focus:border-meow-salmon outline-none disabled:opacity-60">
          <option value="">{state.loading ? 'Memuat wilayah…' : missingParent ? `Pilih ${levels[index - 1].label.toLowerCase()} dahulu` : state.error ? 'Data wilayah belum tersedia' : 'Pilih ' + level.label.toLowerCase()}</option>
          {state.options.map(row => <option key={row.id} value={row.id}>{row.name}</option>)}
        </select>
        {state.loading && <span role="status" className="text-xs text-meow-gray">Memuat {level.label.toLowerCase()}…</span>}
        {state.error && <div role="alert" className="text-xs text-red-600 mt-1">{state.error} <button type="button" onClick={state.retry} className="font-bold underline">Coba lagi</button></div>}
        {!missingParent && !state.loading && !state.error && !state.options.length && <p className="text-xs text-meow-gray mt-1">Wilayah belum tersedia di EVERPRO.</p>}
      </div>;
    })}
    <label className="block text-xs font-semibold">Kode pos
      <input name="postal_code" value={value.postal_code || ''} readOnly required autoComplete="shipping postal-code" placeholder="Otomatis dari kelurahan/desa" data-testid="addr-postal_code"
        className="block w-full mt-1 px-3 py-2.5 rounded-xl bg-meow-bg border border-meow-midnight/10 outline-none"/>
    </label>
  </>;
}
