export function adminError(error, fallback = "Perubahan belum tersimpan. Silakan coba lagi.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || "Data tidak valid").join(". ");
  return fallback;
}

// datetime-local is interpreted in the operator's local timezone; the API stores UTC.
export function localDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export const utcDateTime = (value) => value ? new Date(value).toISOString() : null;

export const inputClass = "w-full rounded-xl border border-zinc-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-meow-amber";
