export function referralCode() {
  try { const value = sessionStorage.getItem('meow_referral') || ''; return /^[A-Za-z0-9]{1,32}$/.test(value) ? value.toUpperCase() : ''; } catch { return ''; }
}
export function rememberReferral(value) {
  const code = String(value || '').trim().toUpperCase();
  try { if (/^[A-Za-z0-9]{1,32}$/.test(code)) sessionStorage.setItem('meow_referral', code); else sessionStorage.removeItem('meow_referral'); } catch { /* optional session storage */ }
  return code;
}
export function clearReferral() { try { sessionStorage.removeItem('meow_referral'); } catch { /* optional session storage */ } }
