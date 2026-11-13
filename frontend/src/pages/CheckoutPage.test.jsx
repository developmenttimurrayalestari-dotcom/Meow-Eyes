import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import CheckoutPage from "./CheckoutPage";
import { api } from "../lib/api";

jest.mock("../lib/api", () => ({ api: { get: jest.fn(), post: jest.fn(), patch: jest.fn() }, apiError: (err, fallback) => err.response?.data?.detail || fallback, imageSrc: (value) => value, formatIDR: (value) => `Rp ${value || 0}` }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ user: { user_id: "customer", has_pin: true, points_balance: 10 }, refreshMe: jest.fn(), refreshCartCount: jest.fn() }) }));

let host;
let root;
const flush = async () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
const click = async (node) => act(async () => node.dispatchEvent(new MouseEvent("click", { bubbles: true })));
const type = async (node, value) => act(async () => {
  const prototype = node instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(prototype, "value").set.call(node, value);
  node.dispatchEvent(new Event("input", { bubbles: true }));
});
const quote = { quote_id: "quote-owned", courier_code: "jne", service_code: "REG", courier_name: "JNE", service_label: "Reguler", cost: 10000, expires_at: "2099-01-01T00:00:00Z", provider: "everpro" };
beforeEach(() => {
  jest.clearAllMocks(); sessionStorage.clear();
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
  api.get.mockImplementation((url) => Promise.resolve({ data: {
    "/addresses": { addresses: [{ id: "address-owned", label: "Rumah", recipient: "Customer", city: "Bandung", province: "Jawa Barat", postal_code: "40111", is_default: true }] },
    "/cart": { items: [{ id: "cart-owned", quantity: 1, unit_price: 100000, subtotal: 100000, product: { name: "Frame", main_image: "frame.png" } }] },
    "/integrations/status": { payment: { provider: "doku", ready: true, mock: false }, shipping: { provider: "everpro", ready: true, mock: false } },
    "/roulette/my-rewards": { spins: [] },
  }[url] }));
  api.post.mockImplementation((url) => {
    if (url === "/checkout/shipping-options") return Promise.resolve({ data: { options: [quote] } });
    if (url === "/checkout/preview") return Promise.resolve({ data: { subtotal: 100000, total: 110000, shipping: { cost: 10000 } } });
    return Promise.reject(new Error("Network timeout"));
  });
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
async function mountCheckout(selected = ["cart-owned"]) {
  await act(async () => root.render(<MemoryRouter initialEntries={[{ pathname: "/checkout", state: { selected_item_ids: selected } }]}><CheckoutPage /></MemoryRouter>));
  await flush(); await flush();
}

test("each selected cart line has its own photo and notes, including a quantity of two without added lenses", async () => {
  const originalGet = api.get.getMockImplementation();
  const originalPost = api.post.getMockImplementation();
  api.get.mockImplementation((url) => url === "/cart" ? Promise.resolve({ data: { items: [
    { id: "cart-owned", quantity: 2, unit_price: 100000, subtotal: 200000, product: { name: "Frame A" } },
    { id: "cart-package", quantity: 1, unit_price: 200000, subtotal: 200000, product: { name: "Paket B" } },
    { id: "cart-unselected", quantity: 1, product: { name: "Tidak dipilih" } },
  ] } }) : originalGet(url));
  api.post.mockImplementation((url, body) => url === "/uploads/prescription"
    ? Promise.resolve({ data: { id: `upload-${body.get("file").name}` } }) : originalPost(url, body));
  api.patch.mockImplementation((url, payload) => Promise.resolve({ data: { prescription: { id: url, ...payload } } }));
  await mountCheckout(["cart-owned", "cart-package"]);
  const forms = [...host.querySelectorAll('[data-testid^="prescription-"]')];
  expect(forms).toHaveLength(2);
  expect(host.querySelector('[data-testid="prescription-cart-unselected"]')).toBeNull();
  expect(forms[0].textContent).toContain("Satu resep berlaku untuk seluruh 2 produk");
  expect(forms[0].querySelector('input[type="number"]')).toBeNull();
  for (const [index, form] of forms.entries()) {
    await type(form.querySelector("textarea"), `Catatan resep ${index + 1}`);
    const input = form.querySelector('input[type="file"]');
    Object.defineProperty(input, "files", { configurable: true, value: [new File(["photo"], `resep-${index + 1}.png`, { type: "image/png" })] });
    await act(async () => input.dispatchEvent(new Event("change", { bubbles: true })));
  }
  expect(forms[0].querySelector("textarea").value).toBe("Catatan resep 1");
  expect(forms[1].querySelector("textarea").value).toBe("Catatan resep 2");
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  await act(async () => forms[0].dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
  await flush();
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  await act(async () => forms[1].dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
  await flush(); await flush();
  expect(api.patch).toHaveBeenCalledWith("/cart/cart-owned/prescription", expect.objectContaining({ notes: "Catatan resep 1", attachment_upload_id: "upload-resep-1.png" }));
  expect(api.patch).toHaveBeenCalledWith("/cart/cart-package/prescription", expect.objectContaining({ notes: "Catatan resep 2", attachment_upload_id: "upload-resep-2.png" }));
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(false);
});

test("saving Frame and Paket Lens Index choices refreshes authoritative totals and keeps each row separate", async () => {
  const originalGet = api.get.getMockImplementation();
  const indexes = [{ id: 'standard', name: 'Standard', additional_price: 50000 }, { id: 'photo', name: 'Photochromic', additional_price: 75000 }];
  const rows = [
    { id: 'cart-owned', quantity: 2, frame_price: 100000, unit_price: 100000, subtotal: 200000, product: { name: 'Frame', product_type: 'frame' } },
    { id: 'cart-package', quantity: 1, frame_price: 200000, unit_price: 200000, subtotal: 200000, product: { name: 'Paket', product_type: 'package' } },
  ];
  api.get.mockImplementation((url) => {
    if (url === '/cart') return Promise.resolve({ data: { items: rows } });
    if (url === '/cart/cart-owned/lens-options') return Promise.resolve({ data: { items: indexes } });
    if (url === '/cart/cart-package/lens-options') return Promise.resolve({ data: { items: [indexes[0]], lens_types: [{ name: 'Single Vision' }] } });
    return originalGet(url);
  });
  let quoteNumber = 0;
  api.post.mockImplementation((url) => {
    if (url === '/checkout/shipping-options') return Promise.resolve({ data: { options: [{ ...quote, quote_id: `quote-${++quoteNumber}` }] } });
    const subtotal = rows.reduce((sum, row) => sum + row.subtotal, 0);
    const lens_subtotal = rows.reduce((sum, row) => sum + (row.lens_price || 0) * row.quantity, 0);
    return Promise.resolve({ data: { subtotal, product_subtotal: subtotal - lens_subtotal, lens_subtotal, total: subtotal + 10000, shipping: { cost: 10000 } } });
  });
  api.patch.mockImplementation((url, prescription) => {
    const row = rows.find(item => url === `/cart/${item.id}/prescription`);
    row.prescription = prescription;
    row.lens_index = indexes.find(index => index.id === prescription.lens_index_id) || null;
    row.lens_price = row.product.product_type === 'frame' ? row.lens_index?.additional_price || 0 : 0;
    row.unit_price = row.frame_price + row.lens_price;
    row.subtotal = row.unit_price * row.quantity;
    return Promise.resolve({ data: { prescription, cart_item: { ...row } } });
  });
  await mountCheckout(['cart-owned', 'cart-package']);
  const frame = host.querySelector('[data-testid="rx-lens-cart-owned"]');
  const pack = host.querySelector('[data-testid="rx-lens-cart-package"]');
  expect(frame.options.length).toBe(3);
  expect(pack.options.length).toBe(2);
  expect(pack.textContent).toContain('Termasuk harga paket');
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 410000');
  await act(async () => { frame.value = 'photo'; frame.dispatchEvent(new Event('change', { bubbles: true })); });
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  await act(async () => host.querySelector('[data-testid="prescription-cart-owned"]').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await flush(); await flush();
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 560000');
  expect(host.querySelector('[data-testid="checkout-product-subtotal"]').textContent).toBe('Rp 400000');
  expect(host.querySelector('[data-testid="checkout-lens-subtotal"]').textContent).toBe('Rp 150000');
  await act(async () => { pack.value = 'standard'; pack.dispatchEvent(new Event('change', { bubbles: true })); });
  await act(async () => host.querySelector('[data-testid="prescription-cart-package"]').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await flush(); await flush();
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 560000');
  expect(host.querySelector('[data-testid="checkout-lens-subtotal"]').textContent).toBe('Rp 150000');
  expect(frame.value).toBe('photo'); expect(pack.value).toBe('standard');
  expect(api.patch).toHaveBeenCalledWith('/cart/cart-owned/prescription', expect.objectContaining({ lens_index_id: 'photo' }));
  expect(api.patch).toHaveBeenCalledWith('/cart/cart-package/prescription', expect.objectContaining({ lens_index_id: 'standard' }));
  await act(async () => { frame.value = ''; frame.dispatchEvent(new Event('change', { bubbles: true })); });
  await act(async () => host.querySelector('[data-testid="prescription-cart-owned"]').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await flush(); await flush();
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 410000');
  expect(host.querySelector('[data-testid="checkout-lens-subtotal"]').textContent).toBe('Rp 0');
});

test('an old price response cannot overwrite saved lens pricing when the shipping quote ID stays the same', async () => {
  const originalGet = api.get.getMockImplementation();
  const row = { id: 'cart-owned', quantity: 1, frame_price: 449000, lens_price: 0, unit_price: 449000, subtotal: 449000,
    product: { name: 'Frame', product_type: 'frame' } };
  const index = { id: 'thin', name: 'Super Thin', additional_price: 350000 };
  api.get.mockImplementation(url => {
    if (url === '/cart') return Promise.resolve({ data: { items: [row] } });
    if (url === '/cart/cart-owned/lens-options') return Promise.resolve({ data: { items: [index] } });
    return originalGet(url);
  });
  const pending = [];
  api.post.mockImplementation(url => url === '/checkout/shipping-options'
    ? Promise.resolve({ data: { options: [quote] } }) : new Promise(resolve => pending.push(resolve)));
  api.patch.mockImplementation((_url, prescription) => Promise.resolve({ data: { prescription, cart_item: {
    ...row, lens_index: index, lens_price: 350000, unit_price: 799000, subtotal: 799000, prescription,
  } } }));
  await mountCheckout();
  expect(pending).toHaveLength(1);
  const select = host.querySelector('[data-testid="rx-lens-cart-owned"]');
  await act(async () => { select.value = 'thin'; select.dispatchEvent(new Event('change', { bubbles: true })); });
  await act(async () => host.querySelector('[data-testid="prescription-cart-owned"]').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await flush(); await flush();
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  expect(pending).toHaveLength(2);
  await act(async () => pending[1]({ data: { subtotal: 799000, product_subtotal: 449000, lens_subtotal: 350000, total: 807000, shipping: { cost: 8000 } } }));
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 807000');
  expect(host.querySelector('[data-testid="checkout-lens-subtotal"]').textContent).toBe('Rp 350000');
  expect(host.querySelector('[data-testid="checkout-item-pricing-cart-owned"]').textContent).toContain('Lensa · Super Thin: Rp 350000');
  await act(async () => pending[0]({ data: { subtotal: 449000, product_subtotal: 449000, lens_subtotal: 0, total: 457000, shipping: { cost: 8000 } } }));
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 807000');
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(false);
});

test('Frame can checkout without lenses or prescription, including after reverting optional edits', async () => {
  const originalGet = api.get.getMockImplementation();
  api.get.mockImplementation(async url => {
    if (url === '/cart/cart-owned/lens-options') return { data: { items: [{ id: 'thin', name: 'Thin', additional_price: 350000 }] } };
    const response = await originalGet(url);
    if (url === '/cart') Object.assign(response.data.items[0], { frame_price: 100000, lens_price: 0,
      product: { name: 'Frame', main_image: 'frame.png', product_type: 'frame' } });
    return response;
  });
  await mountCheckout();
  const form = host.querySelector('[data-testid="prescription-cart-owned"]');
  const select = host.querySelector('[data-testid="rx-lens-cart-owned"]');
  const submit = host.querySelector('[data-testid="submit-order-btn"]');
  expect(select.value).toBe('');
  expect(select.selectedOptions[0].textContent).toBe('Beli frame saja (tanpa lensa)');
  expect([...form.querySelectorAll('input,textarea,select')].every(input => !input.required)).toBe(true);
  expect(submit.disabled).toBe(false);
  await act(async () => { select.value = 'thin'; select.dispatchEvent(new Event('change', { bubbles: true })); });
  expect(submit.disabled).toBe(true);
  await act(async () => { select.value = ''; select.dispatchEvent(new Event('change', { bubbles: true })); });
  expect(submit.disabled).toBe(false);
  await type(form.querySelector('textarea'), 'Catatan sementara');
  expect(submit.disabled).toBe(true);
  await type(form.querySelector('textarea'), '');
  expect(submit.disabled).toBe(false);
  for (let i = 0; i < 6; i += 1) await type(host.querySelector(`[data-testid="checkout-pin-${i}"]`), String(i + 1));
  await click(submit); await flush();
  expect(api.patch).not.toHaveBeenCalled();
  expect(api.post).not.toHaveBeenCalledWith('/uploads/prescription', expect.anything());
  expect(api.post).toHaveBeenCalledWith('/checkout/confirm', expect.objectContaining({ selected_item_ids: ['cart-owned'] }), expect.anything());
  expect(host.querySelector('[data-testid="checkout-lens-subtotal"]').textContent).toBe('Rp 0');
});

test('choosing Frame only removes an existing lens bundle and its surcharge', async () => {
  const originalGet = api.get.getMockImplementation();
  let row = { id: 'cart-owned', quantity: 1, frame_price: 100000, lens_price: 50000, unit_price: 150000, subtotal: 150000,
    product: { name: 'Frame', product_type: 'frame' }, lens_product: { id: 'lens', name: 'Lensa' }, lens_index: null };
  api.get.mockImplementation(url => {
    if (url === '/cart') return Promise.resolve({ data: { items: [row] } });
    if (url === '/cart/cart-owned/lens-options') return Promise.resolve({ data: { items: [] } });
    return originalGet(url);
  });
  api.post.mockImplementation(url => Promise.resolve({ data: url === '/checkout/shipping-options' ? { options: [quote] }
    : { subtotal: row.subtotal, product_subtotal: row.frame_price, lens_subtotal: row.lens_price, total: row.subtotal + 10000, shipping: { cost: 10000 } } }));
  api.patch.mockImplementation((_url, payload) => {
    expect(payload.frame_only).toBe(true);
    row = { ...row, lens_product: null, lens_variant: null, lens_index: null, prescription: null, lens_price: 0, unit_price: 100000, subtotal: 100000 };
    return Promise.resolve({ data: { prescription: null, cart_item: row } });
  });
  await mountCheckout();
  const select = host.querySelector('[data-testid="rx-lens-cart-owned"]');
  expect(select.selectedOptions[0].textContent).toContain('Lensa — tanpa tambahan Lens Index');
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 160000');
  await act(async () => { select.value = ''; select.dispatchEvent(new Event('change', { bubbles: true })); });
  await act(async () => host.querySelector('[data-testid="prescription-cart-owned"]').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await flush(); await flush();
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe('Rp 110000');
  expect(host.querySelector('[data-testid="checkout-lens-subtotal"]').textContent).toBe('Rp 0');
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(false);
});

test("flash sale checkout disables other promotions and submits no stacked discounts", async () => {
  const originalGet = api.get.getMockImplementation();
  api.get.mockImplementation(async url => {
    const response = await originalGet(url);
    if (url === "/cart") response.data.items[0].flash_sale_active = true;
    return response;
  });
  await mountCheckout();
  expect(host.querySelector('[data-testid="voucher-input"]').disabled).toBe(true);
  expect(host.querySelector('[data-testid="points-input"]').disabled).toBe(true);
  expect(host.textContent).toContain("Flash Sale diprioritaskan");
  const calls = api.post.mock.calls.filter(([url]) => url === "/checkout/preview");
  expect(calls[calls.length - 1][1]).toEqual(expect.objectContaining({ voucher_code: null, use_points: 0, roulette_spin_id: null }));
});

test("checkout sends the owned shipping quote and reuses the same request key after network failure", async () => {
  await mountCheckout();
  for (let i = 0; i < 6; i += 1) await type(host.querySelector(`[data-testid="checkout-pin-${i}"]`), String(i + 1));
  const submit = host.querySelector('[data-testid="submit-order-btn"]');
  expect(submit.disabled).toBe(false);
  await click(submit); await flush();
  await click(submit); await flush();
  const calls = api.post.mock.calls.filter(([url]) => url === "/checkout/confirm");
  expect(calls).toHaveLength(2);
  expect(calls[0][1]).toEqual(expect.objectContaining({ shipping_quote_id: "quote-owned", address_id: "address-owned", selected_item_ids: ["cart-owned"], pin: "123456" }));
  expect(calls[0][2].headers["Idempotency-Key"]).toBeTruthy();
  expect(calls[0][2].headers["Idempotency-Key"]).toEqual(calls[1][2].headers["Idempotency-Key"]);
  expect(sessionStorage.getItem("meow_checkout_request_customer")).not.toContain("123456");
});

test("changing a voucher blocks checkout until a fresh server price returns", async () => {
  await mountCheckout();
  let resolvePreview;
  api.post.mockImplementation((url) => url === "/checkout/preview" ? new Promise((resolve) => { resolvePreview = resolve; }) : Promise.reject(new Error("unexpected request")));
  await type(host.querySelector('[data-testid="voucher-input"]'), "PROMO");
  await click([...host.querySelectorAll("button")].find((button) => button.textContent === "Terapkan"));
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe("Menghitung…");
  await act(async () => resolvePreview({ data: { subtotal: 100000, voucher_discount: 10000, total: 100000, shipping: { cost: 10000 } } }));
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(false);
  expect(host.querySelector('[data-testid="checkout-total"]').textContent).toBe("Rp 100000");
});

test('editing the same address clears the old quote and fetches new shipping options after saving', async () => {
  const originalGet = api.get.getMockImplementation();
  api.get.mockImplementation((url, config) => {
    const rows = { '/shipping/locations/provinces': [{ id: 'p', name: 'Jawa Barat' }], '/shipping/locations/cities': [{ id: 'c', name: 'Bandung' }],
      '/shipping/locations/districts': [{ id: 'd', name: 'Bandung Wetan' }], '/shipping/locations/subdistricts': [{ id: 'v', name: 'Citarum', postal_code: '40115' }] };
    return rows[url] ? Promise.resolve({ data: { locations: rows[url] } }) : originalGet(url, config);
  });
  const updated = { id: 'address-owned', label: 'Rumah', recipient: 'Customer', phone: '081234567890', street: 'Jl. QA Baru', province: 'Jawa Barat', city: 'Bandung', district: 'Bandung Wetan', subdistrict: 'Citarum', postal_code: '40115' };
  api.patch.mockResolvedValue({ data: { address: updated } });
  await mountCheckout();
  const before = api.post.mock.calls.filter(([url]) => url === '/checkout/shipping-options').length;
  await click(host.querySelector('[data-testid="checkout-edit-address-address-owned"]')); await flush();
  expect(host.querySelector('[data-testid="submit-order-btn"]').disabled).toBe(true);
  for (const [name, value] of [['district', 'd'], ['subdistrict', 'v']]) await act(async () => { const node = host.querySelector('[data-testid="addr-' + name + '"]'); node.value = value; node.dispatchEvent(new Event('change', { bubbles: true })); });
  await act(async () => host.querySelector('[data-testid="address-form"]').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await flush();
  expect(api.patch).toHaveBeenCalledWith('/addresses/address-owned', expect.objectContaining({ postal_code: '40115', subdistrict: 'Citarum' }));
  expect(api.post.mock.calls.filter(([url]) => url === '/checkout/shipping-options').length).toBeGreaterThan(before);
  expect(host.querySelector('[data-testid="address-section"]').textContent).toContain('Citarum');
});
