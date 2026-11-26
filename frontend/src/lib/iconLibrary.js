export const ICON_ALIASES = { frame:'glasses', lens:'layers', package:'package-2', home:'house', shop:'sparkles', games:'gamepad-2', cart:'shopping-cart', profile:'user', article:'book-open', flash:'zap', contact:'mail', sparkles:'sparkles', glasses:'glasses', tag:'tag' };
export const iconName = value => typeof value !== 'string' ? '' : value.startsWith('lucide:') ? value.slice(7) : Object.prototype.hasOwnProperty.call(ICON_ALIASES,value) ? ICON_ALIASES[value] : value;
let pending;
export function loadIconCatalog() {
  if (!pending) pending = import('./iconCatalog.json').then(module => module.default || module).catch(error => { pending=undefined; throw error; });
  return pending;
}
const terms = [
  ['camera image picture scan','foto kamera gambar fotografi'], ['heart smile user person','hati cinta orang profil pengguna'],
  ['shopping basket cart store bag','belanja toko keranjang tas'], ['glasses eye view','kacamata mata lensa lihat'],
  ['house home building','rumah beranda gedung'], ['package box truck delivery','paket kotak pengiriman barang'],
  ['gamepad dice puzzle trophy','permainan games hadiah piala'], ['mail message phone contact','pesan email telepon kontak'],
  ['star sparkles sun moon','bintang kilau matahari bulan'], ['book notebook file text','buku artikel dokumen tulisan'],
  ['search filter list menu','cari saring daftar menu'], ['tag ticket percent badge','diskon promo voucher label'],
  ['zap flame bolt','kilat flash cepat'], ['calendar clock timer','kalender waktu tanggal jam'],
];
export function iconSearchText(name) {
  return [name.replace(/-/g,' '), ...Object.entries(ICON_ALIASES).filter(([,canonical])=>canonical===name).map(([alias])=>alias), ...terms.filter(([keys])=>keys.split(' ').some(key=>name.includes(key))).map(([,words])=>words)].join(' ').toLowerCase();
}
