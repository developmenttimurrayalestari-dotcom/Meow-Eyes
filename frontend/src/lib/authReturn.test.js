import {
  authDestination, rememberAuthReturn, requestedAuthReturn, safeLocalReturn,
  safeMeowsurementReturn, takeAuthReturn, usesCustomerMeasurementFlow, securitySetupPath,
} from "./authReturn";

afterEach(() => { sessionStorage.clear(); jest.restoreAllMocks(); });

test.each(['google', 'facebook'])('social %s accounts complete password and PIN before continuing', provider => {
  const user = { provider, has_password: false, has_pin: true };
  expect(authDestination('/orders', true, user)).toBe('/setup-password?return_to=%2Forders');
  expect(authDestination('/meowsurement/', true, user)).toBe('/setup-password?return_to=%2Fmeowsurement%2F');
  expect(securitySetupPath({ ...user, has_password: true, has_pin: false })).toBe('/setup-pin');
  expect(authDestination('/orders', true, { ...user, has_password: true })).toBe('/orders');
  expect(safeLocalReturn('/setup-password')).toBe('/');
  expect(safeLocalReturn('/setup-pin')).toBe('/');
});

test("only local safe returns survive sign-in, including encoded URL attacks", () => {
  for (const unsafe of ["https://outside.test", "//outside.test/x", "/\\outside.test", "/%2foutside.test", "/%5coutside.test", "/\noutside", "/login", "/register/", "/auth/callback", "javascript:alert(1)"]) {
    expect(safeLocalReturn(unsafe)).toBe("/");
  }
  expect(safeLocalReturn("/meowsurement/?product_id=frame-1&variant_id=v2")).toBe("/meowsurement/?product_id=frame-1&variant_id=v2");
  expect(safeMeowsurementReturn("/orders")).toBe("/meowsurement/");
  expect(safeMeowsurementReturn("/meowsurement-other")).toBe("/meowsurement/");
});

test("Meowsurement and its profile gate use customer authentication without checkout PIN onboarding", () => {
  const target = "/meowsurement/?product_id=frame&variant_id=black";
  const profile = "/profile?returnTo=" + encodeURIComponent(target);
  expect(authDestination(target, false)).toBe(target);
  expect(authDestination(profile, false)).toBe(profile);
  expect(usesCustomerMeasurementFlow("/profile?returnTo=https://outside.test")).toBe(false);
  expect(authDestination("/checkout", false)).toBe("/setup-pin");
  expect(authDestination("/checkout", true)).toBe("/checkout");
  expect(authDestination("", true)).toBe("/");
});

test("authentication keeps the complete local destination from query or protected route state", () => {
  const target = "/profile?returnTo=%2Fmeowsurement%2F%3Fvariant_id%3Dv1#resep";
  expect(requestedAuthReturn({ search: "?returnTo=" + encodeURIComponent(target) })).toBe(target);
  expect(requestedAuthReturn({ state: { from: target } })).toBe(target);
  expect(requestedAuthReturn({ search: "?returnTo=//outside.test" })).toBe("");
});

test("Google return is short-lived, consumed once, and cannot load an external destination", () => {
  const now = jest.spyOn(Date, "now").mockReturnValue(1000);
  rememberAuthReturn("/meowsurement/?product_id=f");
  expect(takeAuthReturn()).toBe("/meowsurement/?product_id=f");
  expect(takeAuthReturn()).toBe("");
  rememberAuthReturn("/meowsurement/");
  now.mockReturnValue(601001);
  expect(takeAuthReturn()).toBe("");
  sessionStorage.setItem("meow_post_auth_return", JSON.stringify({ path: "//outside.test", expiresAt: 999999 }));
  expect(takeAuthReturn()).toBe("");
});
