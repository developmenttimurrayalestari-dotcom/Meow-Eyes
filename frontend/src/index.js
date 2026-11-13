import React from "react";
import ReactDOM from "react-dom/client";

const root = ReactDOM.createRoot(document.getElementById("root"));
const privateModule = /^\/meowsurement(?:\/|$)/.test(window.location.pathname);
// The measurement entry reuses website authentication through private APIs.
// Avoid storefront tracking, external fonts and unrelated network requests.
if (privateModule) {
  import("./optifit/entry").then(({ mountOptiFit }) => mountOptiFit(root)).catch(() => {
    root.render(<main style={{ padding: 32, fontFamily: "system-ui" }}><h1>Meowsurement belum dapat dibuka</h1><p>Hubungkan internet dan muat ulang untuk mengambil aplikasi serta data dari akun Meow Eyes.</p><button onClick={() => window.location.reload()}>Muat ulang</button></main>);
  });
} else {
  Promise.all([import("./App"), import("./index.css"), import("@tanstack/react-query")]).then(([{ default: App }, , { QueryClient, QueryClientProvider }]) => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60000, refetchOnWindowFocus: false } } });
    root.render(<React.StrictMode><QueryClientProvider client={queryClient}><App /></QueryClientProvider></React.StrictMode>);
    // Optional storefront typography must not reject the local CSS chunk or
    // block application startup if the external font service is unavailable.
    for (const family of ['Cabinet+Grotesk:wght@400;500;700;800;900', 'Figtree:wght@300;400;500;600;700;800']) {
      const link = document.createElement('link');
      link.rel = 'stylesheet'; link.media = 'print'; link.referrerPolicy = 'no-referrer';
      link.href = 'https://fonts.googleapis.com/css2?family=' + family + '&display=swap';
      link.onload = () => { link.media = 'all'; };
      link.onerror = () => link.remove();
      document.head.appendChild(link);
    }
  }).catch(() => { root.render(<p>Halaman belum dapat dimuat. Silakan muat ulang.</p>); });
}
