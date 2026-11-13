// Only relative same-origin destinations are accepted after sign-in.
export function safeLocalReturn(value, fallback = "/") {
  if (typeof value !== "string" || value.length > 2048 || !value.startsWith("/") || /^\/[\\/]/.test(value) || /[\\\u0000-\u001f\u007f]/.test(value)) return fallback;
  try {
    const target = new URL(value, window.location.origin);
    if (target.origin !== window.location.origin || target.username || target.password) return fallback;
    const decoded = decodeURIComponent(target.pathname);
    if (/^\/[\\/]/.test(decoded) || /[\\\u0000-\u001f\u007f]/.test(decoded) || ["/login", "/register", "/auth/callback"].includes(target.pathname.replace(/\/$/, ""))) return fallback;
    return target.pathname + target.search + target.hash;
  } catch { return fallback; }
}

export function isMeowsurementPath(value) {
  const safe = safeLocalReturn(value, "");
  return /^\/meowsurement(?:\/|[?#]|$)/.test(safe);
}

export function safeMeowsurementReturn(value, fallback = "/meowsurement/") {
  const safe = safeLocalReturn(value, "");
  return isMeowsurementPath(safe) ? safe : fallback;
}

export function requestedAuthReturn(location = {}) {
  const params = new URLSearchParams(location.search || "");
  const explicit = params.get("return_to") || params.get("next") || params.get("returnTo");
  return safeLocalReturn(explicit || location.state?.from, "");
}

export function usesCustomerMeasurementFlow(destination) {
  if (isMeowsurementPath(destination)) return true;
  const safe = safeLocalReturn(destination, "");
  if (!safe) return false;
  const target = new URL(safe, window.location.origin);
  return target.pathname === "/profile" && isMeowsurementPath(target.searchParams.get("return_to") || target.searchParams.get("next") || target.searchParams.get("returnTo"));
}

export function authDestination(destination, hasPin) {
  const safe = safeLocalReturn(destination, "/");
  return usesCustomerMeasurementFlow(safe) || hasPin ? safe : "/setup-pin";
}

export function rememberAuthReturn(destination) {
  try {
    const safe = safeLocalReturn(destination, "");
    if (safe) sessionStorage.setItem("meow_post_auth_return", JSON.stringify({ path: safe, expiresAt: Date.now() + 10 * 60 * 1000 }));
    else sessionStorage.removeItem("meow_post_auth_return");
  } catch { /* Login remains usable when session storage is unavailable. */ }
}

export function takeAuthReturn() {
  try {
    const raw = sessionStorage.getItem("meow_post_auth_return"); sessionStorage.removeItem("meow_post_auth_return");
    const value = raw ? JSON.parse(raw) : null;
    return value && Number.isFinite(value.expiresAt) && value.expiresAt > Date.now() ? safeLocalReturn(value.path, "") : "";
  } catch { return ""; }
}

export function navigateAfterAuthentication(destination, navigate) {
  if (isMeowsurementPath(destination)) window.location.replace(destination);
  else navigate(destination, { replace: true });
}
