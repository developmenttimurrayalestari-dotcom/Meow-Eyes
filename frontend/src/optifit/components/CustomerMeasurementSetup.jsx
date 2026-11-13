import React, { useEffect, useRef, useState } from 'react';
import { Camera, Glasses } from 'lucide-react';
import { imageSrc } from '../../lib/api';
import { workspaceError } from '../storage/serverWorkspace';
import { frameInputPayload, MEASUREMENT_TYPES } from '../domain/customerFlow';
import { Button, Field, Notice, formatNumber, todayLocal } from './ui';

export default function CustomerMeasurementSetup({ store, profile, onCreated, type = MEASUREMENT_TYPES[0] }) {
  const queryParams = new URLSearchParams(window.location.search);
  const [source, setSource] = useState(queryParams.get('product_id') ? 'catalog' : 'manual');
  const [manual, setManual] = useState({ a: '', b: '', dbl: '', ed: '', model: '' });
  const [productId, setProductId] = useState(queryParams.get('product_id') || ''), [variantId, setVariantId] = useState(queryParams.get('variant_id') || '');
  const [products, setProducts] = useState([]), [query, setQuery] = useState(''), [page, setPage] = useState(1), [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const [date, setDate] = useState(todayLocal()), [distance, setDistance] = useState(40);
  const sequence = useRef(0);
  const load = async (selected = '', nextPage = 1) => {
    const current = ++sequence.current; setLoading(true); setError('');
    try { const result = await store.frames({ query, productId: selected, page: nextPage }); if (sequence.current === current) { setProducts(result.products || result.items || []); setPage(result.page || nextPage); setTotalPages(result.total_pages || 1); } }
    catch (err) { if (sequence.current === current) setError(workspaceError(err)); }
    finally { if (sequence.current === current) setLoading(false); }
  };
  useEffect(() => { if (source === 'catalog') void load(productId); return () => { sequence.current += 1; }; // Explicit search handles subsequent queries.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);
  const selected = products.find(product => product.id === productId), variant = selected?.variants?.find(item => item.id === variantId);
  const spec = variant?.effective_specification || variant?.frame_specification || selected?.frame_specification || selected?.specification;
  let framePayload, validation;
  try { framePayload = frameInputPayload({ source, product: selected, variant, manual, profileVersion: profile.version }); }
  catch (err) { validation = err.message; }
  const submit = async event => {
    event.preventDefault(); if (!framePayload || busy) return;
    setBusy(true); setError('');
    try { onCreated(await store.createSession({ ...framePayload, examination_date: date,
      working_distance_cm: type.id === 'near_pd' ? Number(distance) : 40, required_parameters: type.parameters, mode: 'semi_automatic' })); }
    catch (err) { setError(workspaceError(err)); }
    finally { setBusy(false); }
  };
  return <section className="of-card" data-testid={`measurement-setup-${type.id}`}>
    <div className="of-section-heading"><div><h2>{type.title}</h2><p>{type.description}</p></div><Glasses size={28}/></div>
    {type.id === 'wrap' && <Notice>Sudut ini dicatat dari alat atau hasil pemeriksaan. Foto biasa saja belum cukup untuk menghitung lengkungan frame secara akurat.</Notice>}
    <Notice>Ukuran frame ini menjadi acuan pengukuran foto. Gunakan frame yang sama saat difoto; tidak perlu benda pembanding tambahan.</Notice>
    <fieldset className="of-frame-source"><legend>Frame yang digunakan</legend>{[['manual', 'Isi ukuran sendiri'], ['catalog', 'Pilih frame dari toko']].map(([value, text]) => <label className="of-check" key={value}><input type="radio" name="frame-source" checked={source === value} onChange={() => { setSource(value); setError(''); }} />{text}</label>)}</fieldset>
    {source === 'catalog' && <><form className="of-inline-form" onSubmit={event => { event.preventDefault(); void load(); }}><input aria-label="Cari frame Meowsurement" value={query} onChange={event => setQuery(event.target.value)} placeholder="Cari nama frame atau SKU"/><Button type="submit" variant="secondary" disabled={loading}>Cari frame</Button></form>
      {loading ? <p role="status">Memuat frame…</p> : <div className="of-frame-grid">{products.map(product => <button type="button" key={product.id} className={`of-frame-option ${product.id === productId ? 'is-selected' : ''}`} onClick={() => { setProductId(product.id); setVariantId(product.variants?.length === 1 ? product.variants[0].id : ''); }} data-testid={`select-frame-${product.id}`}>{product.main_image && <img src={imageSrc(product.main_image)} alt=""/>}<span><strong>{product.name}</strong><small>{product.sku}</small></span></button>)}</div>}
      {!loading && !products.length && <Notice>Belum ada frame sesuai pencarian. Anda tetap bisa memilih Isi ukuran sendiri.</Notice>}
      {totalPages > 1 && <div className="of-actions"><Button variant="secondary" disabled={loading || page <= 1} onClick={() => load('', page - 1)}>Frame sebelumnya</Button><span>{page} / {totalPages}</span><Button variant="secondary" disabled={loading || page >= totalPages} onClick={() => load('', page + 1)}>Frame berikutnya</Button></div>}</>}
    <form className="of-form" onSubmit={submit}>
      {source === 'manual' ? <><p>Anda tidak perlu memilih atau membeli frame dari toko. Masukkan ukuran frame yang Anda gunakan.</p><div className="of-grid-three">{[['a', 'Lebar lensa (A)'], ['b', 'Tinggi lensa (B)'], ['dbl', 'Jarak antar lensa (DBL)']].map(([key, label]) => <Field key={key} label={`${label} — mm`} required><input aria-label={label} type="number" inputMode="decimal" min="0.01" max="99999.99" step="0.01" required value={manual[key]} onChange={event => setManual(previous => ({ ...previous, [key]: event.target.value }))}/></Field>)}</div><details><summary>Ukuran tambahan (opsional)</summary><Field label="ED / diameter efektif (mm), opsional"><input aria-label="ED opsional" type="number" min="0.01" max="99999.99" step="0.01" value={manual.ed} onChange={event => setManual(previous => ({ ...previous, ed: event.target.value }))}/></Field><Field label="Nama frame (opsional)"><input maxLength={160} value={manual.model} onChange={event => setManual(previous => ({ ...previous, model: event.target.value }))}/></Field></details><p className="of-small of-muted">A adalah ukuran mendatar dan B ukuran tegak satu lensa. ED boleh kosong; tidak dihitung otomatis dari diagonal kotak.</p></> : selected && <><Field label="Varian frame" required><select value={variantId} onChange={event => setVariantId(event.target.value)} required><option value="">Pilih warna / ukuran</option>{selected.variants?.map(item => <option key={item.id} value={item.id}>{[item.color, item.size, item.sku].filter(Boolean).join(' · ')}</option>)}</select></Field>{variant && <div className="of-frame-spec" data-testid="selected-frame-spec"><div className="of-grid-three">{[['a', 'Lebar (A)'], ['b', 'Tinggi (B)'], ['dbl', 'Jarak antar lensa (DBL)']].map(([key, label]) => <div key={key}><small>{label}</small><strong>{spec?.[key] == null ? 'Belum diisi' : `${formatNumber(spec[key])} mm`}</strong></div>)}</div>{validation && <Notice tone="warning">Spesifikasi frame belum lengkap. {validation}</Notice>}</div>}</>}
      <Field label="Tanggal pengukuran"><input type="date" value={date} max={todayLocal()} onChange={event => setDate(event.target.value)} required/></Field>
      {type.id === 'near_pd' && <Field label="Jarak membaca Anda (cm)" required><input aria-label="Jarak membaca" type="number" min="1" max="10000" step="0.1" value={distance} onChange={event => setDistance(event.target.value)} required/><small>Jarak mata ke buku atau benda yang dilihat saat foto diambil.</small></Field>}
      {error && <Notice tone="danger">{error}</Notice>}<Button type="submit" busy={busy} disabled={!framePayload || (source === 'catalog' && loading)}><Camera size={18}/>Mulai pengukuran</Button>
    </form>
  </section>;
}
