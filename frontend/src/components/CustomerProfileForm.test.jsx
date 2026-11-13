import React, { act } from "react";
import { createRoot } from "react-dom/client";
import CustomerProfileForm from "./CustomerProfileForm";
import { api } from "../lib/api";
import { profileFormValues, profileSavePayload } from "../lib/customerProfile";

jest.mock("../lib/api", () => ({ api: { get: jest.fn(), put: jest.fn() } }));

const saved = {
  profile: {
    user_id: "customer", name: "Dina", email: "dina@example.test", phone: "628123456789",
    birth_date: "1997-02-03", gender: null, address: "", version: 3,
    prescription: { id: "rx-3", date: "2025-02-04", od: { sph: 0, cyl: 0, axis: null, add: null }, os: { sph: -1.25, cyl: -0.5, axis: 90, add: 0 }, pd_total: 63, pd_right: 31, pd_left: 32, notes: "" },
  }, ready: true, missing_fields: [],
};
let host, root;
const field = label => host.querySelector('[aria-label="' + label + '"]');
const testId = id => host.querySelector('[data-testid="' + id + '"]');
const type = async (node, value) => act(async () => {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(node, value);
  node.dispatchEvent(new Event("input", { bubbles: true }));
});
const submit = async () => act(async () => testId("customer-profile-form").dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
const mount = async props => act(async () => root.render(<CustomerProfileForm userId="customer" {...props} />));
beforeEach(() => {
  jest.resetAllMocks();
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
  api.get.mockResolvedValue({ data: saved }); api.put.mockResolvedValue({ data: saved });
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test("profile loads canonical prescription and preserves zero versus unknown values", async () => {
  await mount({ returnTo: "/meowsurement/?product_id=f&variant_id=large" });
  expect(field("Mata kanan (OD) SPH (D)").value).toBe("0");
  expect(field("Mata kanan (OD) CYL (D)").value).toBe("0");
  expect(field("Mata kanan (OD) AXIS (°)").value).toBe("");
  expect(field("Mata kiri (OS) ADD (D), opsional").value).toBe("0");
  expect(testId("continue-meowsurement").getAttribute("href")).toBe("/meowsurement/?product_id=f&variant_id=large");
  expect(field("Email akun").readOnly).toBe(true);
  const payload = profileSavePayload(profileFormValues(saved.profile), saved.profile.version);
  expect(payload.prescription.od).toEqual({ sph: 0, cyl: 0, axis: null, add: null });
  expect(field("PD total (mm)").value).toBe("63");
  expect(payload.prescription).toEqual(expect.objectContaining({ pd_total: 63, pd_right: 31, pd_left: 32 }));
});

test("unsaved changes block continuation and save carries version, actual numbers and no account id", async () => {
  const onSaved = jest.fn().mockResolvedValue(undefined);
  await mount({ onSaved, returnTo: "/meowsurement/?product_id=f&variant_id=large" });
  await type(field("Nama lengkap"), "Dina Baru");
  await type(field("Mata kanan (OD) SPH (D)"), "-0.75");
  expect(testId("continue-meowsurement")).toBeNull();
  expect(testId("continue-meowsurement-disabled").disabled).toBe(true);
  api.put.mockResolvedValue({ data: { ...saved, profile: { ...saved.profile, name: "Dina Baru", version: 4, prescription: { ...saved.profile.prescription, od: { sph: -0.75, cyl: 0, axis: null, add: null } } } } });
  await submit();
  expect(api.put).toHaveBeenCalledWith("/customer/profile", expect.objectContaining({
    expected_version: 3, name: "Dina Baru",
    prescription: expect.objectContaining({ od: { sph: -0.75, cyl: 0, axis: null, add: null } }),
  }), { withCredentials: true });
  expect(api.put.mock.calls[0][1].user_id).toBeUndefined();
  expect(onSaved).toHaveBeenCalledTimes(1);
  expect(testId("continue-meowsurement").getAttribute("href")).toContain("variant_id=large");
});

test("incomplete profile remains a savable draft and cannot enter Meowsurement", async () => {
  const incomplete = { ...saved, ready: false, missing_fields: ["phone", "prescription.os.axis"], profile: { ...saved.profile, phone: null, prescription: { ...saved.profile.prescription, os: { sph: -1, cyl: -0.5, axis: null, add: null } } } };
  api.get.mockResolvedValue({ data: incomplete }); api.put.mockResolvedValue({ data: incomplete });
  await mount();
  expect(testId("profile-missing-fields").textContent).toContain("AXIS kiri (OS)");
  expect(testId("continue-meowsurement")).toBeNull();
  await submit();
  expect(api.put).toHaveBeenCalledTimes(1);
  expect(api.put.mock.calls[0][1].prescription.os.axis).toBeNull();
  expect(testId("continue-meowsurement")).toBeNull();
});

test("conflicting updates retain the draft and require explicit reload before saving", async () => {
  await mount();
  await type(field("Nama lengkap"), "Perubahan lokal");
  api.put.mockRejectedValue({ response: { status: 409, data: { detail: { message: "Profil telah diperbarui." } } } });
  await submit();
  expect(host.querySelector('[role="alert"]').textContent).toContain("Profil telah diperbarui");
  expect(field("Nama lengkap").value).toBe("Perubahan lokal");
  expect(testId("save-customer-profile").disabled).toBe(true);
  expect(testId("continue-meowsurement")).toBeNull();
  await submit();
  expect(api.put).toHaveBeenCalledTimes(1);
  api.get.mockResolvedValue({ data: { ...saved, profile: { ...saved.profile, version: 5, name: "Versi terbaru" } } });
  await act(async () => host.querySelector('[role="alert"] button').click());
  expect(field("Nama lengkap").value).toBe("Versi terbaru");
  expect(testId("save-customer-profile").disabled).toBe(false);
});

test("failed initial load cannot submit a blank version-zero profile", async () => {
  api.get.mockRejectedValue({ response: { status: 503, data: { detail: "Layanan belum siap" } } });
  await mount({ returnTo: "https://outside.test" });
  expect(testId("customer-profile-form")).toBeNull();
  expect(api.put).not.toHaveBeenCalled();
  expect(host.querySelector('[role="alert"]').textContent).toContain("Layanan belum siap");
  api.get.mockResolvedValue({ data: saved });
  await act(async () => host.querySelector('[role="alert"] button').click());
  expect(testId("continue-meowsurement").getAttribute("href")).toBe("/meowsurement/");
});
