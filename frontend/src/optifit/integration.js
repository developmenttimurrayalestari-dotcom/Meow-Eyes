/** Explicit read-only import actions. Never called at module import/boot. */
const base = String(process.env.REACT_APP_BACKEND_URL || '').replace(/\/+$/, '');
async function request(path, authenticated = false) {
  if (!navigator.onLine) throw new Error('Pengambilan data Meow Eyes memerlukan koneksi. Data lokal tetap dapat digunakan.');
  const token = authenticated ? localStorage.getItem('meow_token') : null;
  if (authenticated && !token) throw new Error('Masuk ke akun Meow Eyes pada tab toko terlebih dahulu, lalu kembali ke OptiFit.');
  const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(base + '/api' + path, { method: 'GET', credentials: 'omit', cache: 'no-store', referrerPolicy: 'no-referrer', headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: controller.signal });
    if (!response.ok) throw new Error(response.status === 401 ? 'Sesi Meow Eyes berakhir. Masuk kembali di tab toko.' : 'Data Meow Eyes belum dapat diambil.');
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Koneksi Meow Eyes melewati batas waktu. Coba kembali ketika jaringan tersedia.');
    if (error instanceof TypeError) throw new Error('Server Meow Eyes belum dapat dijangkau.');
    throw error;
  } finally { clearTimeout(timer); }
}
export async function loadCustomerProfile({ confirmed = false } = {}) {
  if (!confirmed) throw new Error('Konfirmasi pengambilan profil diperlukan.');
  const body = await request('/auth/me', true); const user = body.user;
  if (!user?.id && !user?.user_id) throw new Error('Profil pelanggan tidak lengkap.');
  return { id: user.id || user.user_id, user_id: user.id || user.user_id, name: user.name || user.full_name || '', full_name: user.name || user.full_name || '', email: user.email || '', phone: user.phone || '', address: user.address || '', birth_date: user.birth_date || user.date_of_birth || '', gender: user.gender || '' };
}
export async function loadFrameCatalog({ query = '', confirmed = false } = {}) {
  if (!confirmed) throw new Error('Konfirmasi pengambilan katalog diperlukan.');
  const text = typeof query === 'string' ? query : '';
  const response = await request('/products?product_type=frame&limit=100&page=1&q=' + encodeURIComponent(text.slice(0, 120)));
  // Product identity only. Dimensions must be measured/confirmed by the operator;
  // SKU, commercial labels and photos are not a validated calibration source.
  return (response.products || []).map(p => ({ id: p.id, name: p.name, model: p.name, slug: p.slug, brand: p.brand_name || '', source: 'meow_eyes_catalog', dimensionsVerified: false }));
}
