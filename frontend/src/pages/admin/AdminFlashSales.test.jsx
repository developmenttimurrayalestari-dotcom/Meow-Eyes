import React, { act } from "react";
import { createRoot } from "react-dom/client";
import AdminFlashSales from "./AdminFlashSales";
import { api } from "../../lib/api";

jest.mock("../../lib/api", () => ({ api: { get: jest.fn(), delete: jest.fn() }, formatIDR: value => `Rp ${value}` }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
let root, host;
const campaign = { id: "sale", name: "Promo anak", start_at: "2026-01-01T00:00:00Z", end_at: "2099-01-01T00:00:00Z", is_active: true, items: [], category_rules: [] };
const click = async node => act(async () => node.dispatchEvent(new MouseEvent("click", { bubbles: true })));
beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(window, "confirm").mockReturnValue(true);
  api.get.mockImplementation(url => Promise.resolve({ data: url === "/admin/flash-sales" ? { flash_sales: [campaign] } : url === "/admin/categories" ? { categories: [] } : { products: [] } }));
  api.delete.mockResolvedValue({ data: { ok: true } });
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); });
const mount = async () => act(async () => root.render(<AdminFlashSales />));
test("confirmed deletion removes the campaign from admin", async () => {
  await mount();
  await click(host.querySelector('[data-testid="delete-flash-sale"]'));
  expect(window.confirm).toHaveBeenCalled();
  expect(api.delete).toHaveBeenCalledWith("/admin/flash-sales/sale");
  expect(host.querySelector('[data-testid="flash-sale"]')).toBeNull();
});
test("cancelling deletion leaves the campaign and makes no delete request", async () => {
  window.confirm.mockReturnValue(false);
  await mount();
  await click(host.querySelector('[data-testid="delete-flash-sale"]'));
  expect(api.delete).not.toHaveBeenCalled();
  expect(host.querySelector('[data-testid="flash-sale"]')).not.toBeNull();
});
test("campaign history rejection is displayed without removing the campaign", async () => {
  api.delete.mockRejectedValue({ response: { status: 409, data: { detail: "Gunakan Nonaktifkan untuk menghentikan promo." } } });
  await mount();
  await click(host.querySelector('[data-testid="delete-flash-sale"]'));
  expect(host.querySelector('[role="alert"]').textContent).toContain("Nonaktifkan");
  expect(host.querySelector('[data-testid="flash-sale"]')).not.toBeNull();
});
