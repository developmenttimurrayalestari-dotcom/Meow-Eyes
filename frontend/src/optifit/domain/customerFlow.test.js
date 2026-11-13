import { customerViews, frameInputPayload, MEASUREMENT_TYPES } from './customerFlow';

const manual = { a: '52', b: '40', dbl: '18', ed: '' };
test('manual frame requires three dimensions, permits no ED and sends no catalog identity', () => {
  expect(frameInputPayload({ source: 'manual', manual, profileVersion: 4 })).toEqual({
    expected_profile_version: 4, manual_frame: { a: 52, b: 40, dbl: 18, ed: null, model: 'Frame ukuran manual' },
  });
  for (const key of ['a', 'b', 'dbl']) for (const value of ['', '0', '-1', 'no', Infinity]) {
    expect(() => frameInputPayload({ source: 'manual', manual: { ...manual, [key]: value } })).toThrow();
  }
  expect(() => frameInputPayload({ source: 'manual', manual: { ...manual, ed: -1 } })).toThrow();
});
test('catalog sends IDs and authoritative version only, with ED optional', () => {
  const product = { id: 'p', specification_version: 3 };
  const variant = { id: 'v', effective_specification: { a: 52, b: 40, dbl: 18, ed: null, enabled: true } };
  expect(frameInputPayload({ source: 'catalog', product, variant, manual, profileVersion: 4 })).toEqual({
    product_id: 'p', variant_id: 'v', expected_profile_version: 4, expected_spec_version: 3,
  });
  expect(() => frameInputPayload({ source: 'catalog', product, manual })).toThrow();
  expect(() => frameInputPayload({ source: 'unknown', manual })).toThrow();
});
test('each card limits camera views to its measurement', () => {
  expect(MEASUREMENT_TYPES).toHaveLength(5);
  expect(customerViews(['near_pd'])).toEqual(['frontal_near']);
  expect(customerViews(['vertex_right', 'vertex_left'])).toEqual(['lateral_right', 'lateral_left']);
  expect(customerViews(['wrap_right'])).toEqual(['three_quarter_right', 'three_quarter_left']);
});
