import React, { useId } from 'react';
import { formatIDR } from '../lib/api';

const TYPES = [
  ['regular', 'Reguler'], ['express', 'Express'], ['same_day', 'Same-day'],
  ['instant', 'Instant'], ['cargo', 'Cargo'], ['other', 'Lainnya'],
];

function serviceType(option) {
  const type = option?.service_type === 'sameday' ? 'same_day' : option?.service_type;
  if (TYPES.some(([key]) => key === type)) return type;
  // Compatibility with older API responses and demo quotes. Courier brands
  // such as "J&T Express" must not make a regular service appear as Express.
  const label = `${option?.service_label || ''} ${option?.service_code || ''}`.toLowerCase();
  if (/same[\s_-]*day|sds|^same$/.test(label.trim())) return 'same_day';
  if (/instant|instan|insgrab/.test(label)) return 'instant';
  if (/cargo|kargo|truck|jtr|fast track|\bft\b/.test(label)) return 'cargo';
  if (/express|ekspres|next[\s_-]*day|esok|\byes\b|ctcyes|\bbest\b|\bons\b|\bods\b/.test(label)) return 'express';
  if (/regul[ae]r|\breg\b|regpack|jagopack|satria lite|standard|\bez\b|^ctc\d+\s*$/.test(label)) return 'regular';
  return 'other';
}

export default function ShippingOptions({ options, selected, onChange, disabled = false }) {
  const id = useId();
  const groups = TYPES.map(([key, label]) => ({ key, label, options: options.filter(option => serviceType(option) === key) }))
    .filter(group => group.options.length);
  const active = groups.find(group => group.key === serviceType(selected)) || groups[0];
  if (!active) return null;
  return <div className="space-y-3" data-testid="shipping-options">
    <div role="group" aria-label="Jenis layanan pengiriman" className="flex flex-wrap gap-2">
      {groups.map(group => <button key={group.key} type="button" disabled={disabled}
        aria-pressed={active.key === group.key} aria-controls={`${id}-services`}
        data-testid={`shipping-type-${group.key}`}
        onClick={() => { if (active.key !== group.key) onChange(group.options[0]); }}
        className={`min-h-10 rounded-xl border px-3 py-2 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-meow-salmon disabled:opacity-50 ${active.key === group.key ? 'border-meow-salmon bg-meow-salmon/10 text-meow-midnight' : 'border-meow-midnight/10 bg-white text-meow-gray hover:bg-meow-bg'}`}>
        {group.label} <span className="ml-1 text-xs">({group.options.length})</span>
      </button>)}
    </div>
    <fieldset id={`${id}-services`} className="min-w-0" data-testid={`shipping-group-${active.key}`}>
      <legend className="mb-2 text-sm font-bold">Layanan {active.label}</legend>
      <div className="max-h-80 space-y-2 overflow-y-auto p-0.5">
        {active.options.map((option, index) => {
          const checked = selected?.quote_id ? selected.quote_id === option.quote_id
            : selected?.courier_code === option.courier_code && selected?.service_code === option.service_code;
          return <label key={option.quote_id || `${option.courier_code}-${option.service_code}-${index}`}
            className={`flex items-start gap-2 rounded-2xl border-2 p-3 cursor-pointer ${checked ? 'border-meow-salmon bg-meow-salmon/5' : 'border-meow-midnight/5'}`}>
            <input type="radio" name="checkout-shipping" disabled={disabled} checked={checked}
              onChange={() => onChange(option)} className="mt-1 shrink-0" />
            <span className="min-w-0 flex-1 text-sm"><span className="font-bold">{option.courier_name || option.courier_code} · {option.service_label || option.service_code}</span>
              {option.etd && <span className="block text-xs text-meow-gray">Estimasi {option.etd}</span>}
              {Number(option.insurance_cost) > 0 && <span className="block text-xs text-meow-gray">Termasuk asuransi <span className="conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{formatIDR(option.insurance_cost)}</span></span>}
            </span>
            <span className="shrink-0 whitespace-nowrap text-sm font-bold text-meow-salmon conveythis-no-translate notranslate" translate="no" data-conveythis-private="">{formatIDR(option.cost)}</span>
          </label>;
        })}
      </div>
    </fieldset>
  </div>;
}
