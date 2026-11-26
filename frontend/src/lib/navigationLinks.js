export function navigationDestination(url) {
  if (typeof url !== 'string' || /[\\\s\u0000-\u001f\u007f]/.test(url) || url.startsWith('//')) return null;
  if (url.startsWith('/')) return { url, internal: true, reload: /^\/meowsurement(?:\/|\?|#|$)/.test(url) };
  try { const parsed = new URL(url); if (['http:', 'https:'].includes(parsed.protocol) && !parsed.username && !parsed.password) return { url, internal: false, reload: true }; } catch { /* Invalid URLs are not navigable. */ }
  return null;
}
