export const MEASUREMENT_TYPES = [
  { id: 'distance_pd', title: 'Jarak pupil jauh', description: 'Jarak antar pusat mata saat melihat jauh.', icon: 'eye', parameters: ['distance_pd'], views: ['frontal'] },
  { id: 'near_pd', title: 'Jarak pupil dekat', description: 'Jarak antar pusat mata pada jarak membaca Anda.', icon: 'book', parameters: ['near_pd'], views: ['frontal_near'] },
  { id: 'vertex', title: 'Jarak lensa ke mata', description: 'Jarak bagian belakang lensa ke mata, dilihat dari samping.', icon: 'ruler', parameters: ['vertex_right', 'vertex_left'], views: ['lateral_right', 'lateral_left'] },
  { id: 'pantoscopic', title: 'Kemiringan lensa', description: 'Kemiringan lensa terhadap posisi kepala saat dipakai.', icon: 'angle', parameters: ['pantoscopic_right', 'pantoscopic_left'], views: ['lateral_right', 'lateral_left'] },
  { id: 'wrap', title: 'Lengkungan frame', description: 'Catat sudut lengkungan dari alat atau hasil pemeriksaan yang Anda miliki.', icon: 'wrap', parameters: ['wrap_right', 'wrap_left'], views: ['three_quarter_right', 'three_quarter_left'] },
];
export const measurementType = parameters => MEASUREMENT_TYPES.find(type => (parameters || []).some(key => type.parameters.includes(key))) || MEASUREMENT_TYPES[0];
export function customerViews(parameters = []) {
  return [...new Set(MEASUREMENT_TYPES.filter(type => type.parameters.some(key => parameters.includes(key))).flatMap(type => type.views))];
}
export function frameInputPayload({ source, product, variant, manual, profileVersion }) {
  if (!['catalog', 'manual'].includes(source)) throw new Error('Pilih sumber ukuran frame.');
  if (source === 'catalog') {
    const spec = variant?.effective_specification || variant?.frame_specification || product?.frame_specification || product?.specification;
    if (!product || !variant || !spec?.enabled || !['a', 'b', 'dbl'].every(key => Number.isFinite(Number(spec[key])) && Number(spec[key]) > 0)) throw new Error('Pilih frame dan varian dengan ukuran A, B, dan DBL yang lengkap. ED boleh kosong.');
    return { product_id: product.id, variant_id: variant.id, expected_profile_version: profileVersion,
      expected_spec_version: product.specification_version ?? product.spec_version ?? product.frame_specification?.version ?? product.specification?.version ?? spec.version };
  }
  const values = {};
  for (const key of ['a', 'b', 'dbl', 'ed']) {
    const raw = manual?.[key];
    const value = raw === '' || raw == null ? null : Number(String(raw).replace(',', '.'));
    if ((key !== 'ed' && value === null) || (value !== null && (!Number.isFinite(value) || value < .01 || value > 99999.99))) throw new Error('Isi lebar (A), tinggi (B), dan jarak antar lensa (DBL) dengan angka positif dalam mm. ED opsional.');
    values[key] = value;
  }
  return { expected_profile_version: profileVersion, manual_frame: { ...values, model: manual?.model?.trim() || 'Frame ukuran manual' } };
}
