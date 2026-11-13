import React from 'react';
import { ArrowRight, BookOpen, Eye, Glasses, MoveDiagonal, Ruler } from 'lucide-react';
import { MEASUREMENT_TYPES } from '../domain/customerFlow';

const icons = { eye: Eye, book: BookOpen, ruler: Ruler, angle: MoveDiagonal, wrap: Glasses };
export default function MeasurementDashboard({ onSelect }) {
  return <section aria-label="Pilih jenis pengukuran" className="of-measurement-menu" data-testid="measurement-dashboard">
    {MEASUREMENT_TYPES.map(type => { const Icon = icons[type.icon]; return <button key={type.id} type="button" className="of-measurement-menu-card" onClick={() => onSelect(type)} data-testid={`measurement-card-${type.id}`}>
      <span className="of-measurement-menu-icon"><Icon size={28} /></span><strong>{type.title}</strong><span>{type.description}</span><small>Mulai pengukuran <ArrowRight size={16}/></small>
    </button>; })}
  </section>;
}
