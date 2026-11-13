import React, { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import { api } from "../lib/api";
import { loadGoogleIdentity } from "../lib/googleIdentity";

const mockLoginWithGoogle = jest.fn();
jest.mock("../contexts/AuthContext", () => ({ useAuth: () => ({ loginWithGoogle: mockLoginWithGoogle, login: jest.fn(), register: jest.fn() }) }));
jest.mock("../lib/api", () => ({ api: { get: jest.fn() }, apiError: (err, fallback) => err.response?.data?.detail || fallback }));
jest.mock("../lib/googleIdentity", () => ({ loadGoogleIdentity: jest.fn(), googleNonce: () => "native-browser-nonce-12345678901234567890" }));
jest.mock("sonner", () => ({ toast: { success: jest.fn(), error: jest.fn() } }));

let host, root, sdk;
const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
beforeEach(() => {
  jest.clearAllMocks();
  sdk = { initialize: jest.fn(), renderButton: jest.fn((element) => {
    const button = document.createElement("button"); button.textContent = "Official Google button"; element.appendChild(button);
  }) };
  api.get.mockResolvedValue({ data: { enabled: true, client_id: "native.apps.googleusercontent.com" } });
  loadGoogleIdentity.mockResolvedValue(sdk);
  mockLoginWithGoogle.mockResolvedValue({ name: "Customer", has_pin: true });
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
async function mount(path = "/login") {
  await act(async () => root.render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} />
    <Route path="/orders" element={<p>Customer orders</p>} /><Route path="/setup-pin" element={<p>Setup PIN</p>} />
    <Route path="/" element={<p>Home</p>} />
  </Routes></MemoryRouter>));
  await flush();
}

test("login renders the official Google button and keeps the local return destination", async () => {
  await mount("/login?returnTo=%2Forders");
  expect(api.get).toHaveBeenCalledWith("/auth/google/config", expect.any(Object));
  expect(sdk.initialize).toHaveBeenCalledWith(expect.objectContaining({ client_id: "native.apps.googleusercontent.com", auto_select: false, ux_mode: "popup" }));
  expect(sdk.renderButton.mock.calls[0][1].text).toBe("signin_with");
  await act(async () => sdk.initialize.mock.calls[0][0].callback({ credential: "signed-google-token" }));
  expect(mockLoginWithGoogle).toHaveBeenCalledWith("signed-google-token", "native-browser-nonce-12345678901234567890");
  expect(host.textContent).toBe("Customer orders");
});

test("Google registration works without filling the password form and preserves PIN onboarding", async () => {
  mockLoginWithGoogle.mockResolvedValue({ name: "New customer", has_pin: false });
  await mount("/register");
  expect(sdk.renderButton.mock.calls[0][1].text).toBe("signup_with");
  expect(host.querySelector('[data-testid="register-email"]').value).toBe("");
  await act(async () => sdk.initialize.mock.calls[0][0].callback({ credential: "new-user-token" }));
  expect(host.textContent).toBe("Setup PIN");
});

test.each(["/login", "/register"])("missing Client ID keeps the password form usable on %s", async (path) => {
  api.get.mockResolvedValue({ data: { enabled: false, client_id: null } });
  await mount(path);
  expect(loadGoogleIdentity).not.toHaveBeenCalled();
  expect(host.textContent).toContain("Google belum tersedia");
  expect(host.querySelector('button[type="submit"]').disabled).toBe(false);
});

test("Google SDK failure offers retry, while authentication errors remain visible", async () => {
  loadGoogleIdentity.mockRejectedValueOnce(new Error("SDK blocked"));
  await mount();
  expect(host.querySelector('[role="alert"]').textContent).toContain("SDK blocked");
  await act(async () => [...host.querySelectorAll("button")].find((button) => button.textContent.includes("Muat ulang")).click());
  await flush();
  mockLoginWithGoogle.mockRejectedValueOnce({ response: { data: { detail: "Akun dinonaktifkan" } } });
  await act(async () => sdk.initialize.mock.calls[0][0].callback({ credential: "token" }));
  expect(host.querySelector('[role="alert"]').textContent).toBe("Akun dinonaktifkan");
  expect(host.querySelector('[data-testid="login-page"]')).not.toBeNull();
});

test("stale SDK callbacks after leaving the form cannot log in", async () => {
  await mount();
  const callback = sdk.initialize.mock.calls[0][0].callback;
  await act(async () => root.render(<p>Other screen</p>));
  await act(async () => callback({ credential: "stale-token" }));
  expect(mockLoginWithGoogle).not.toHaveBeenCalled();
});

test("duplicate SDK callbacks exchange one credential at a time", async () => {
  let resolve;
  mockLoginWithGoogle.mockImplementation(() => new Promise((done) => { resolve = done; }));
  await mount();
  const callback = sdk.initialize.mock.calls[0][0].callback;
  let first;
  await act(async () => { first = callback({ credential: "token" }); await callback({ credential: "token" }); });
  expect(mockLoginWithGoogle).toHaveBeenCalledTimes(1);
  await act(async () => { resolve({ name: "Customer", has_pin: true }); await first; });
});
