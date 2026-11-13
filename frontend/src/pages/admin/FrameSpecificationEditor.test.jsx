import React, { act } from "react";
import { createRoot } from "react-dom/client";
import FrameSpecificationEditor from "./FrameSpecificationEditor";
import { api } from "../../lib/api";
import { completeFrameSpecification, resolvedFrameSpecification } from "../../components/ProductMeowsurement";

jest.mock("../../lib/api", () => ({ api: { get: jest.fn(), put: jest.fn() } }));
jest.mock("../../components/ui/dialog", () => ({
  Dialog: ({ children }) => <div>{children}</div>,
  DialogContent: ({ children }) => <div>{children}</div>,
  DialogDescription: ({ children }) => <p>{children}</p>,
  DialogTitle: ({ children }) => <h2>{children}</h2>,
}));
const base = { a: 52, b: 38, dbl: 18, ed: 58, temple_length: 140, symmetric: true, enabled: true, source_note: "Datasheet", version: 4 };
const response = { product_id: "frame", version: 4, specification: base, variants: [{ variant_id: "black", inherit_default: true, specification: null }, { variant_id: "large", inherit_default: false, specification: { ...base, a: 56, ed: 64 } }] };
const product = { id: "frame", name: "Frame", variants: [{ id: "black", sku: "BLACK", size: "M" }, { id: "large", sku: "BLACK-L", size: "L" }] };
let host, root;
const testId = id => host.querySelector('[data-testid="' + id + '"]');
const mount = async () => act(async () => root.render(<FrameSpecificationEditor product={product} onClose={jest.fn()} />));
const submit = async () => act(async () => host.querySelector("form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
beforeEach(() => { jest.resetAllMocks(); host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host); api.get.mockResolvedValue({ data: response }); api.put.mockResolvedValue({ data: { ...response, version: 5 } }); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test("public resolution honors explicit overrides, inheritance and unknown variant refusal", () => {
  expect(resolvedFrameSpecification(response, "black").a).toBe(52);
  expect(resolvedFrameSpecification(response, "large").a).toBe(56);
  expect(resolvedFrameSpecification(response, "wrong-product-variant")).toBeNull();
  expect(completeFrameSpecification(base)).toBe(true);
  expect(completeFrameSpecification({ ...base, enabled: false })).toBe(false);
  expect(completeFrameSpecification({ ...base, ed: null })).toBe(true);
  expect(completeFrameSpecification({ ...base, complete: false })).toBe(false);
});

test("admin saves typed default and variant geometry with aggregate optimistic version", async () => {
  await mount();
  expect(testId("default-frame-a").value).toBe("52");
  expect(testId("variant-black-a")).toBeNull();
  expect(testId("variant-large-a").value).toBe("56");
  await act(async () => testId("frame-variant-spec-black").querySelector('input[type="checkbox"]').click());
  expect(testId("variant-black-a").value).toBe("52");
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(testId("variant-black-a"), "54");
    testId("variant-black-a").dispatchEvent(new Event("input", { bubbles: true }));
  });
  await submit();
  expect(api.put).toHaveBeenCalledWith("/admin/products/frame/frame-specification", expect.objectContaining({
    expected_version: 4,
    specification: expect.objectContaining({ a: 52, ed: 58, enabled: true }),
    variants: [
      { variant_id: "black", inherit_default: false, specification: expect.objectContaining({ a: 54, b: 38, dbl: 18, ed: 58 }) },
      { variant_id: "large", inherit_default: false, specification: expect.objectContaining({ a: 56, ed: 64 }) },
    ],
  }), { withCredentials: true });
});

test("frame conflict blocks resubmission until explicit reload and load failure has no editable form", async () => {
  await mount();
  api.put.mockRejectedValue({ response: { status: 409, data: { detail: "Spesifikasi berubah" } } });
  await submit();
  expect(testId("save-frame-specification").disabled).toBe(true);
  await submit();
  expect(api.put).toHaveBeenCalledTimes(1);
  api.get.mockRejectedValue({ response: { status: 503, data: { detail: "Layanan belum siap" } } });
  await act(async () => host.querySelector('[role="alert"] button').click());
  expect(host.querySelector("form")).toBeNull();
});
