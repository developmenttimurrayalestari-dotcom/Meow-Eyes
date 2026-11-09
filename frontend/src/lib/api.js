import axios from "axios";

const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/+$/, "");
export const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API_BASE,
});

// Attach token from localStorage as Bearer (fallback to httpOnly cookie)
api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("meow_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      // soft signal
      window.dispatchEvent(new Event("meow:unauthorized"));
    }
    return Promise.reject(err);
  }
);

export const setToken = (t) => {
  if (t) localStorage.setItem("meow_token", t);
  else localStorage.removeItem("meow_token");
};

export const formatIDR = (v) => {
  if (v == null || isNaN(v)) return "Rp 0";
  return "Rp " + Math.round(Number(v)).toLocaleString("id-ID");
};

/**
 * Resolve a stored image URL for rendering.
 * - Absolute `http(s)://` URLs are returned as-is (external CDN, Unsplash…).
 * - Relative `/api/uploads-files/...` paths are prefixed with the backend base
 *   so <img> tags in customer-facing pages render across environments.
 */
export const imageSrc = (url) => {
  if (!url) return "";
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("/api/")) return `${BACKEND_URL}${url}`;
  return url;
};

export const apiError = (error, fallback = "Permintaan belum berhasil. Silakan coba lagi.") => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).filter(Boolean).join("; ") || fallback;
  return fallback;
};

export const copyText = async (text) => {
  if (navigator.clipboard?.writeText && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const input = document.createElement("textarea");
  input.value = text;
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand("copy");
  input.remove();
  if (!copied) throw new Error("Salin tidak didukung oleh browser ini.");
};
