import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProductDetailPage from "./ProductDetailPage";
import { api } from "../lib/api";

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({ ...jest.requireActual("react-router-dom"), useNavigate: () => mockNavigate }));
jest.mock("../lib/api", () => ({ api: { get: jest.fn(), post: jest.fn() }, apiError: (err, fallback) => fallback, imageSrc: (value) => value, formatIDR: (value) => `Rp ${value}` }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ user: { user_id: "buyer" }, refreshCartCount: jest.fn() }) }));
jest.mock("../components/VirtualTryOn", () => ({productId}) => <div data-testid="product-try-on" data-product-id={productId} />);

let host, root, resolveFirst, resolveSecond;
const product = { id: "frame", slug: "frame", name: "Frame", price: 100, product_type: "frame", variants: [
  { id: "v1", sku: "SILVER", color: "Silver", stock: 10, reserved: 0, price_override: null },
  { id: "v2", sku: "BLACK", color: "Black", stock: 10, reserved: 0, price_override: 200 },
] };
const bundle = (variantId, total) => ({ data: { frame: { id: "frame", variant_id: variantId }, picks: [
  { tier: "basic", label: "Hemat", lens_product_id: "lens", lens_variant_id: "lens-first", frame_variant_id: variantId, lens_product_name: "Lensa", lens_index_id: "index", lens_index_name: "1.56", available: true, available_stock: 10, bundle_total: total, savings: 0 },
] } });
const click = async (node) => act(async () => node.dispatchEvent(new MouseEvent("click", { bubbles: true })));
beforeEach(() => {
  jest.clearAllMocks();
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
  const first = new Promise((resolve) => { resolveFirst = resolve; });
  const second = new Promise((resolve) => { resolveSecond = resolve; });
  api.get.mockImplementation((url, config) => {
    if (url === "/products/frame") return Promise.resolve({ data: { product, breadcrumb: [], reviews: [], related: [] } });
    if (url === "/products/frame/frame-specification") return Promise.resolve({ data: { specification: { a: 52, b: 38, dbl: 18, ed: 58, enabled: true }, variants: [{ variant_id: "v1", inherit_default: true }, { variant_id: "v2", inherit_default: false, specification: { a: 56, b: 40, dbl: 18, ed: 64, enabled: true } }] } });
    if (url.startsWith("/lens/options")) return Promise.resolve({ data: { lens_products: [{ id: "lens", name: "Lensa", price: 80, discount_price: null, variants: [{ id: "lens-first", price_override: 30, stock: 10, reserved: 0 }] }], lens_indexes: [] } });
    if (url.startsWith("/lens/recommended")) return config.params.variant_id === "v2" ? second : first;
    return Promise.reject(new Error("Unexpected API"));
  });
  api.post.mockResolvedValue({ data: { ok: true } });
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
const mount = async () => act(async () => root.render(<MemoryRouter initialEntries={["/products/frame"]}><Routes><Route path="/products/:slug" element={<ProductDetailPage />} /></Routes></MemoryRouter>));

test.each(['frame','package','lens'])('product detail VTO eligibility for %s',async kind=>{
  const fallback=api.get.getMockImplementation();
  api.get.mockImplementation((url,config)=>url==='/products/frame'?Promise.resolve({data:{product:{...product,product_type:kind,variants:[]},breadcrumb:[],reviews:[],related:[]}}):fallback(url,config));
  await mount();
  expect(Boolean(host.querySelector('[data-testid="product-try-on"]'))).toBe(kind!=='lens');
});

const choosePrescriptionPhoto = async (file) => {
  await mount();
  await click(host.querySelector('[data-testid="want-lens-checkbox"]'));
  const select = host.querySelector('[data-testid="lens-product-select"]');
  await act(async () => {
    select.value = "lens";
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  const input = host.querySelector('input[type="file"]');
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  await act(async () => input.dispatchEvent(new Event("change", { bubbles: true })));
};

test("prescription photo replaces manual fields and its private upload is linked to the cart", async () => {
  URL.createObjectURL = jest.fn(() => "blob:prescription-preview");
  URL.revokeObjectURL = jest.fn();
  const file = new File(["photo"], "resep.png", { type: "image/png" });
  await choosePrescriptionPhoto(file);
  expect(host.querySelector('[aria-label="Kanan (OD) SPH"]')).toBeNull();
  expect(host.querySelector('img[alt="Pratinjau foto resep kacamata"]').getAttribute("src")).toBe("blob:prescription-preview");
  expect(api.post).not.toHaveBeenCalled();
  api.post.mockResolvedValueOnce({ data: { id: "private-rx" } }).mockResolvedValueOnce({ data: { ok: true } });
  await click(host.querySelector('[data-testid="add-to-cart-btn"]'));
  expect(api.post.mock.calls[0][0]).toBe("/uploads/prescription");
  expect(api.post.mock.calls[0][1].get("file")).toBe(file);
  expect(api.post).toHaveBeenLastCalledWith("/cart", expect.objectContaining({ prescription: { attachment_upload_id: "private-rx" } }));
  await click(host.querySelector('[aria-label="Hapus foto resep"]'));
  expect(host.querySelector('img[alt="Pratinjau foto resep kacamata"]')).toBeNull();
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:prescription-preview");
});

test("unsupported prescription files are rejected without uploading", async () => {
  await choosePrescriptionPhoto(new File(["svg"], "resep.svg", { type: "image/svg+xml" }));
  expect(host.querySelector('[role="alert"]').textContent).toContain("maksimal 8 MB");
  expect(api.post).not.toHaveBeenCalled();
});

test("failed prescription upload prevents adding a cart item without its photo", async () => {
  URL.createObjectURL = jest.fn(() => "blob:prescription-preview");
  URL.revokeObjectURL = jest.fn();
  await choosePrescriptionPhoto(new File(["photo"], "resep.jpg", { type: "image/jpeg" }));
  api.post.mockRejectedValueOnce(new Error("Upload failed"));
  await click(host.querySelector('[data-testid="buy-now-btn"]'));
  expect(api.post).toHaveBeenCalledTimes(1);
  expect(api.post.mock.calls[0][0]).toBe("/uploads/prescription");
  expect(mockNavigate).not.toHaveBeenCalled();
  expect(host.querySelector('[data-testid="add-to-cart-btn"]').disabled).toBe(false);
});

test("bundle picks follow the selected frame variant and stale replies cannot replace them", async () => {
  await mount();
  await click(host.querySelector('[data-testid="variant-BLACK"]'));
  expect(host.querySelector('[data-testid="bundle-buy-basic"]')).toBeNull();
  await act(async () => resolveSecond(bundle("v2", 230)));
  expect(host.querySelector('[data-testid="bundle-total-basic"]').textContent).toBe("Rp 230");
  await act(async () => resolveFirst(bundle("v1", 130)));
  expect(host.querySelector('[data-testid="bundle-total-basic"]').textContent).toBe("Rp 230");
  await click(host.querySelector('[data-testid="bundle-buy-basic"]'));
  expect(api.post).toHaveBeenCalledWith("/cart", expect.objectContaining({ product_id: "frame", variant_id: "v2", lens_variant_id: "lens-first", lens_product_id: "lens", quantity: 1 }));
});

test("manual lens choice displays its selected SKU override and sends that exact lens SKU", async () => {
  await mount();
  await click(host.querySelector('[data-testid="want-lens-checkbox"]'));
  const select = host.querySelector('[data-testid="lens-product-select"]');
  expect(select.textContent).toContain("Lensa — Rp 30");
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set.call(select, "lens");
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  await click(host.querySelector('[data-testid="add-to-cart-btn"]'));
  expect(api.post).toHaveBeenCalledWith("/cart", expect.objectContaining({ variant_id: "v1", lens_variant_id: "lens-first", lens_product_id: "lens", quantity: 1 }));
});

test("Meowsurement entry carries selected product and variant and shows its actual geometry", async () => {
  await mount();
  expect(host.querySelector('[data-testid="open-meowsurement"]').getAttribute("href")).toBe("/meowsurement/?product_id=frame&variant_id=v1");
  expect(host.querySelector('[data-testid="product-frame-spec-a"]').textContent).toBe("52 mm");
  await click(host.querySelector('[data-testid="variant-BLACK"]'));
  expect(host.querySelector('[data-testid="open-meowsurement"]').getAttribute("href")).toBe("/meowsurement/?product_id=frame&variant_id=v2");
  expect(host.querySelector('[data-testid="product-frame-spec-a"]').textContent).toBe("56 mm");
});
