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
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(node, value);
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
async function mountCheckout() {
  await act(async () => root.render(<MemoryRouter initialEntries={[{ pathname: "/checkout", state: { selected_item_ids: ["cart-owned"] } }]}><CheckoutPage /></MemoryRouter>));
  await flush(); await flush();
}

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
