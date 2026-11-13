const eyeFields = ["sph", "cyl", "axis", "add"];
export const PROFILE_FIELD_LABELS = Object.freeze({
  name: "Nama lengkap", phone: "Nomor telepon", birth_date: "Tanggal lahir",
  prescription: "Resep kacamata", "prescription.date": "Tanggal resep / pemeriksaan",
  prescription_date: "Tanggal resep / pemeriksaan",
  "prescription.od.sph": "SPH kanan (OD)", "prescription.od.cyl": "CYL kanan (OD)",
  "prescription.od.axis": "AXIS kanan (OD)", "prescription.os.sph": "SPH kiri (OS)",
  "prescription.os.cyl": "CYL kiri (OS)", "prescription.os.axis": "AXIS kiri (OS)",
});
export const profileFieldLabel = key => PROFILE_FIELD_LABELS[key] || String(key).replaceAll("_", " ");
export const localToday = () => {
  const date = new Date();
  return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
};
export function profileFormValues(profile = {}) {
  const rx = profile.prescription || {};
  return {
    name: profile.name || "", email: profile.email || "", phone: profile.phone || "",
    birth_date: profile.birth_date?.slice(0, 10) || "", gender: profile.gender || "",
    address: profile.address || "",
    prescription: {
      date: rx.date?.slice(0, 10) || "", notes: rx.notes || "",
      pd_total: rx.pd_total ?? "", pd_right: rx.pd_right ?? "", pd_left: rx.pd_left ?? "",
      od: Object.fromEntries(eyeFields.map(field => [field, rx.od?.[field] ?? ""])),
      os: Object.fromEntries(eyeFields.map(field => [field, rx.os?.[field] ?? ""])),
    },
  };
}
export function profileNumeric(value, label) {
  if (value === null || value === undefined || String(value).trim() === "") return null;
  const raw = String(value).trim();
  if (!/^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)$/.test(raw)) throw new Error(label + " harus berupa angka yang valid.");
  const number = Number(raw.replace(",", "."));
  if (!Number.isFinite(number)) throw new Error(label + " harus berupa angka yang valid.");
  return number;
}
export function profileSavePayload(values, version) {
  const rx = values.prescription || {};
  const prescription = {
    date: rx.date || null, notes: rx.notes?.trim() || "",
    ...Object.fromEntries(["pd_total", "pd_right", "pd_left"].map(field => {
      const number = profileNumeric(rx[field], "PD");
      if (number !== null && (number <= 0 || number > 999.99)) throw new Error("PD harus lebih besar dari 0 dan maksimal 999,99 mm.");
      return [field, number];
    })),
    ...Object.fromEntries(["od", "os"].map(eye => [eye, Object.fromEntries(eyeFields.map(field => {
      const number = profileNumeric(rx[eye]?.[field], eye.toUpperCase() + " " + field.toUpperCase());
      if (field === "axis" && number !== null && (!Number.isInteger(number) || number < 0 || number > 180)) throw new Error("AXIS harus bilangan bulat dari 0 sampai 180.");
      return [field, number];
    }))])),
  };
  return {
    expected_version: Number.isInteger(version) ? version : 0,
    name: values.name.trim(), phone: values.phone.trim() || null,
    birth_date: values.birth_date || null, gender: values.gender || null,
    address: values.address.trim() || null, prescription,
  };
}
export function profileRequestError(error, fallback = "Profil belum dapat disimpan.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (typeof detail?.message === "string") return detail.message;
  if (Array.isArray(detail)) return detail.map(item => item.msg).filter(Boolean).join("; ") || fallback;
  return error?.response ? fallback : error?.message || fallback;
}
