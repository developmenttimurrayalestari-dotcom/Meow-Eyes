let pending;
export function loadFacebookIdentity() {
  if (window.FB?.login) return Promise.resolve(window.FB);
  if (pending) return pending;
  pending = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://connect.facebook.net/id_ID/sdk.js'; script.async = true;
    let timer;
    const fail = () => { clearTimeout(timer); script.remove(); pending = undefined; reject(new Error('Facebook gagal dimuat. Periksa koneksi lalu coba lagi.')); };
    script.onload = () => { if (window.FB?.login) { clearTimeout(timer); resolve(window.FB); } else fail(); };
    script.onerror = fail; timer = setTimeout(fail, 15000); document.head.appendChild(script);
  });
  return pending;
}
