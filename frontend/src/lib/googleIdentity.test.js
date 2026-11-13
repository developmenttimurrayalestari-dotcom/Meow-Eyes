beforeEach(() => { jest.resetModules(); delete window.google; });
afterEach(() => { document.head.querySelectorAll('script[src="https://accounts.google.com/gsi/client"]').forEach((node) => node.remove()); jest.useRealTimers(); });

test("Google SDK is loaded once directly from Google and shared by concurrent callers", async () => {
  const { loadGoogleIdentity } = require("./googleIdentity");
  const first = loadGoogleIdentity(), second = loadGoogleIdentity();
  expect(first).toBe(second);
  const script = document.head.querySelector('script[src="https://accounts.google.com/gsi/client"]');
  window.google = { accounts: { id: { initialize: jest.fn() } } };
  script.dispatchEvent(new Event("load"));
  expect(await first).toBe(window.google.accounts.id);
  expect(await loadGoogleIdentity()).toBe(window.google.accounts.id);
});

test("a blocked SDK can be retried without stale failed scripts", async () => {
  const { loadGoogleIdentity } = require("./googleIdentity");
  const first = loadGoogleIdentity();
  document.head.querySelector('script[src="https://accounts.google.com/gsi/client"]').dispatchEvent(new Event("error"));
  await expect(first).rejects.toThrow("gagal dimuat");
  const second = loadGoogleIdentity();
  expect(document.head.querySelectorAll('script[src="https://accounts.google.com/gsi/client"]')).toHaveLength(1);
  window.google = { accounts: { id: {} } };
  document.head.querySelector('script[src="https://accounts.google.com/gsi/client"]').dispatchEvent(new Event("load"));
  await expect(second).resolves.toBe(window.google.accounts.id);
});

test("a stalled SDK times out and allows retry", async () => {
  jest.useFakeTimers();
  const { loadGoogleIdentity } = require("./googleIdentity");
  const pending = loadGoogleIdentity();
  jest.advanceTimersByTime(15000);
  await expect(pending).rejects.toThrow("gagal dimuat");
  expect(document.head.querySelector('script[src="https://accounts.google.com/gsi/client"]')).toBeNull();
});

test("each sign-in gets an independent cryptographically random nonce", () => {
  const { googleNonce } = require("./googleIdentity");
  const first = googleNonce();
  expect(first).toMatch(/^[a-f0-9]{48}$/);
  expect(googleNonce()).not.toBe(first);
});
