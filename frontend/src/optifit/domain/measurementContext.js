// Captures and derived results retain the actual fitting context at acquisition.
// Editing a frame/reference/working distance must never silently reinterpret
// landmarks collected under the preceding context.
export function measurementContext(data = {}) {
  const frame = data.frame || {};
  return {
    frame: {
      brand: frame.brand || "", model: frame.model || "", productId: frame.productId ?? null,
      a: frame.a ?? null, b: frame.b ?? null, dbl: frame.dbl ?? null, ed: frame.ed ?? null,
      pdReference: frame.pdReference || "unspecified", symmetric: frame.symmetric === true,
    },
    workingDistanceCm: data.workingDistanceCm ?? null,
  };
}

export function sameMeasurementContext(first, second) {
  if (!first || !second) return first === second;
  if (!first.frame || !second.frame) return false;
  const frameFields = ["brand", "model", "productId", "a", "b", "dbl", "ed", "pdReference", "symmetric"];
  // Encrypted canonical JSON sorts object keys. Property insertion order must
  // never turn an unchanged context into a different fitting measurement.
  return Object.hasOwn(first, "workingDistanceCm") && Object.hasOwn(second, "workingDistanceCm")
    && first.workingDistanceCm === second.workingDistanceCm
    && frameFields.every(key => Object.hasOwn(first.frame, key) && Object.hasOwn(second.frame, key) && first.frame[key] === second.frame[key]);
}

export function invalidateChangedMeasurementContext(previous, next) {
  if (!previous || sameMeasurementContext(measurementContext(previous), measurementContext(next))) return next;
  const reason = "Konteks frame, referensi PD, atau jarak kerja berubah. Ulangi pengambilan / pembacaan untuk konteks baru; nilai sebelumnya tetap ada di riwayat.";
  const invalidatedAt = new Date().toISOString();
  const invalidate = map => Object.fromEntries(Object.entries(map || {}).map(([key, result]) => [key, {
    ...result, valid: false, contextInvalidated: true, contextInvalidatedAt: invalidatedAt,
    reasons: [...(result.reasons || []), reason],
  }]));
  return {
    ...next,
    captures: (next.captures || []).map(capture => ({ ...capture, contextInvalidated: true, contextInvalidatedAt: invalidatedAt })),
    results: invalidate(next.results),
    manualMeasurements: invalidate(next.manualMeasurements),
  };
}
