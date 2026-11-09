import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CatalogPagination, { catalogPage } from "./CatalogPagination";
import HtmlContent from "./HtmlContent";
import PrescriptionForm, { prescriptionValues } from "./PrescriptionForm";
import { TryOnStudio } from "./VirtualTryOn";
import { api } from "../lib/api";

jest.mock("../lib/api", () => ({ api: { get: jest.fn(), post: jest.fn(), patch: jest.fn() }, apiError: (error, fallback) => error.response?.data?.detail || fallback, imageSrc: (value) => value }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock("./ui/dialog", () => ({ Dialog: () => null, DialogContent: () => null, DialogTitle: () => null, DialogTrigger: () => null, DialogDescription: () => null }));

let host;
let root;
const render = async (element) => { await act(async () => { root.render(element); }); };
const click = async (element) => { await act(async () => { element.dispatchEvent(new MouseEvent("click", { bubbles: true })); }); };
const type = async (element, value) => {
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(element, value);
    element.dispatchEvent(new Event("input", { bubbles: true }));
  });
};
beforeEach(() => {
  jest.clearAllMocks();
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { if (root) await act(async () => root.unmount()); host.remove(); });

test("catalog pages sanitize invalid URL input and paginate at fifteen items", async () => {
  expect(catalogPage("-2")).toBe(1);
  expect(catalogPage("not-a-page")).toBe(1);
  expect(catalogPage("2")).toBe(2);
  const changed = jest.fn();
  await render(<CatalogPagination page={1} total={31} onChange={changed} />);
  expect(host.textContent).toContain("Halaman 1 dari 3");
  expect(host.querySelector('[aria-label="Halaman sebelumnya"]').disabled).toBe(true);
  await click(host.querySelector('[aria-label="Halaman berikutnya"]'));
  expect(changed).toHaveBeenCalledWith(2);
  await render(<CatalogPagination page={1} total={15} onChange={changed} />);
  expect(host.querySelector("nav")).toBeNull();
});

test("published HTML preserves prose while removing executable attributes, markup and forms", async () => {
  await render(<HtmlContent html={'<h2>Frame</h2><script>window.bad=true</script><img src="frame.png" onerror="alert(1)"><a href="javascript:alert(1)">link</a><form><input name="email"></form><p style="position:fixed">safe</p>'} />);
  expect(host.querySelector("h2").textContent).toBe("Frame");
  expect(host.querySelector("script,form,input,[onerror],[style]")).toBeNull();
  expect(host.querySelector("a").hasAttribute("href")).toBe(false);
});

test("prescription adapter distinguishes entered zero from empty measurements", () => {
  const values = prescriptionValues({ od_sph: 0, os_cyl: -0.75, od_axis: 0, pd: 64 });
  expect(values.od_sph).toBe(0);
  expect(values.od_axis).toBe(0);
  expect(values.os_add).toBe("");
  expect(values.pd_total).toBe(64);
  expect(values.pd_right).toBe("");
});

test("prescription saves AXIS and ADD with blanks as null and reports unsaved state", async () => {
  const dirty = jest.fn();
  api.patch.mockResolvedValue({ data: { prescription: { od_sph: 0, od_axis: 90, od_add: 1.25 } } });
  await render(<PrescriptionForm item={{ id: "cart-rx", product: { name: "Frame" }, lens_product: { name: "Lensa" }, prescription: null }} onDirtyChange={dirty} />);
  await type(host.querySelector('[aria-label="Kanan (OD) SPH"]'), "0");
  await type(host.querySelector('[aria-label="Kanan (OD) AXIS"]'), "90");
  await type(host.querySelector('[aria-label="Kanan (OD) ADD"]'), "1.25");
  expect(dirty).toHaveBeenLastCalledWith("cart-rx", true);
  await act(async () => { host.querySelector("form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })); });
  expect(api.patch).toHaveBeenCalledWith("/cart/cart-rx/prescription", expect.objectContaining({ od_sph: 0, od_axis: 90, od_add: 1.25, os_sph: null, pd_total: null, attachment_upload_id: null }));
  expect(dirty).toHaveBeenLastCalledWith("cart-rx", false);
});

test("prescription upload rejects unsupported files before any HTTP request", async () => {
  await render(<PrescriptionForm item={{ id: "cart-rx", product: { name: "Frame" }, lens_product: { name: "Lensa" } }} />);
  const input = host.querySelector('input[type="file"]');
  Object.defineProperty(input, "files", { value: [new File(["not-an-image"], "script.svg", { type: "image/svg+xml" })], configurable: true });
  await act(async () => { input.dispatchEvent(new Event("change", { bubbles: true })); });
  expect(api.post).not.toHaveBeenCalled();
  expect(host.querySelector('[role="alert"]').textContent).toContain("maksimal 8 MB");
});

test("try-on requests camera only on a click and stops a stream that resolves after closing", async () => {
  let resolveStream;
  const stop = jest.fn();
  const getUserMedia = jest.fn(() => new Promise((resolve) => { resolveStream = resolve; }));
  Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
  Object.defineProperty(navigator, "mediaDevices", { value: { getUserMedia }, configurable: true });
  await render(<TryOnStudio assets={[{ id: "asset", asset_type: "image", source_url: "frame.png", scale: 1 }]} name="Frame" />);
  expect(getUserMedia).not.toHaveBeenCalled();
  await click(host.querySelector('[data-testid="try-on-camera"]'));
  expect(getUserMedia).toHaveBeenCalledWith(expect.objectContaining({ audio: false }));
  await act(async () => root.unmount()); root = null;
  await act(async () => resolveStream({ getTracks: () => [{ stop }] }));
  expect(stop).toHaveBeenCalledTimes(1);
});

test("try-on stops an active camera when the tab becomes hidden", async () => {
  const stop = jest.fn();
  const getUserMedia = jest.fn().mockResolvedValue({ getTracks: () => [{ stop }] });
  Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
  Object.defineProperty(navigator, "mediaDevices", { value: { getUserMedia }, configurable: true });
  const play = jest.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  await render(<TryOnStudio assets={[{ id: "asset", asset_type: "image", source_url: "frame.png" }]} name="Frame" />);
  await click(host.querySelector('[data-testid="try-on-camera"]'));
  expect(host.textContent).toContain("Hentikan Kamera");
  Object.defineProperty(document, "hidden", { value: true, configurable: true });
  await act(async () => document.dispatchEvent(new Event("visibilitychange")));
  expect(stop).toHaveBeenCalledTimes(1);
  expect(host.textContent).toContain("Mulai Kamera");
  Object.defineProperty(document, "hidden", { value: false, configurable: true });
  play.mockRestore();
});
