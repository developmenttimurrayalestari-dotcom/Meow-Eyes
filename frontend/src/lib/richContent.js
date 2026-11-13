import DOMPurify from 'dompurify';
import { imageSrc } from './api';

export function contentUrl(value, image = false) {
  const url = (value || '').trim();
  if (!url || /[\s\\\u0000-\u001f]/.test(url) || url.startsWith('//')) return null;
  if (image && /\/api\/prescriptions\//i.test(url)) return null;
  try {
    const parsed = new URL(url, window.location.origin);
    if (parsed.username || parsed.password) return null;
    if (!['http:', 'https:', ...(image ? [] : ['mailto:', 'tel:'])].includes(parsed.protocol)) return null;
    return url;
  } catch { return null; }
}

// Keep only the typography styles the editor exposes. Layout/URL-bearing CSS
// is excluded, so pasted HTML cannot cover the page or load CSS resources.
function safeStyle(node) {
  const source = node.style;
  const result = document.createElement('span').style;
  for (const property of ['color', 'background-color']) {
    const value = source.getPropertyValue(property);
    if (/^(#[\da-f]{3,8}|[a-z]+|rgba?\([\d.,%\s]+\)|hsla?\([\d.,%\s]+\))$/i.test(value)) result.setProperty(property, value);
  }
  if (['left', 'center', 'right', 'justify'].includes(source.textAlign)) result.textAlign = source.textAlign;
  if (['Arial', 'Georgia', 'Verdana', '"Times New Roman"', '"Courier New"', 'sans-serif', 'serif', 'monospace'].includes(source.fontFamily)) result.fontFamily = source.fontFamily;
  if (/^\d+(\.\d+)?px$/.test(source.fontSize) && parseFloat(source.fontSize) >= 8 && parseFloat(source.fontSize) <= 96) result.fontSize = source.fontSize;
  if (/^[1-3](\.\d+)?$/.test(source.lineHeight) && Number(source.lineHeight) <= 3) result.lineHeight = source.lineHeight;
  if (['IMG', 'TABLE', 'COL'].includes(node.tagName) && /^(\d{1,4}(\.\d+)?px|\d{1,3}(\.\d+)?%)$/.test(source.width)) result.width = source.width;
  if (result.cssText) node.setAttribute('style', result.cssText);
  else node.removeAttribute('style');
}

export function sanitizeRichContent(html, { resolveImages = false } = {}) {
  const fragment = DOMPurify.sanitize(html || '', {
    USE_PROFILES: { html: true }, RETURN_DOM_FRAGMENT: true,
    ADD_ATTR: ['colwidth'],
    FORBID_TAGS: ['style', 'form', 'input', 'button', 'textarea', 'select', 'iframe', 'object', 'embed', 'base', 'link'],
  });
  const container = document.createElement('div'); container.appendChild(fragment);
  container.querySelectorAll('[style]').forEach(safeStyle);
  container.querySelectorAll('a[href]').forEach(node => {
    const href = contentUrl(node.getAttribute('href'));
    if (!href) node.removeAttribute('href');
    if (node.getAttribute('target') === '_blank') node.setAttribute('rel', 'noopener noreferrer');
  });
  container.querySelectorAll('img').forEach(node => {
    const src = contentUrl(node.getAttribute('src'), true);
    node.removeAttribute('srcset');
    if (!src) { node.remove(); return; }
    if (node.hasAttribute('data-align') && !['left', 'center', 'right'].includes(node.getAttribute('data-align'))) node.removeAttribute('data-align');
    node.setAttribute('src', resolveImages ? imageSrc(src) : src);
  });
  return container.innerHTML;
}

export function hasRichContent(html) {
  const element = document.createElement('div'); element.innerHTML = sanitizeRichContent(html);
  return Boolean(element.textContent.trim() || element.querySelector('img,table,hr'));
}
