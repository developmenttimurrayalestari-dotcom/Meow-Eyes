import React, { act } from "react";
import { createRoot } from "react-dom/client";
import AdminMeowsurement from "./AdminMeowsurement";
import { api } from "../../lib/api";

let mockUser;
jest.mock("../../lib/api", () => ({ api: { get: jest.fn() } }));
jest.mock("../../contexts/AuthContext", () => ({ useAuth: () => ({ user: mockUser }) }));
let host, root;
const mount = async () => act(async () => root.render(<AdminMeowsurement />));
beforeEach(() => {
  jest.resetAllMocks(); mockUser = { role: "staff", permissions: ["meowsurement.review"] };
  host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host);
  api.get.mockResolvedValue({ data: { sessions: [{ id: "session-1", customerName: "Dina", frameName: "Frame Hitam", status: "pending_review", revisionNumber: 2, examinationDate: "2025-02-04" }], page: 1, total_pages: 2, total: 16 } });
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

test("reviewer sees queue with full-document session link and status filter resets pagination", async () => {
  await mount();
  expect(api.get).toHaveBeenLastCalledWith("/admin/meowsurement/sessions", expect.objectContaining({ params: { page: 1, page_size: 15 }, withCredentials: true }));
  expect(host.querySelector('[data-testid="open-measurement-review-session-1"]').getAttribute("href")).toBe("/meowsurement/?review_session=session-1");
  expect(host.textContent).toContain("Dina");
  await act(async () => host.querySelector('[aria-label="Halaman berikutnya"]').click());
  expect(api.get).toHaveBeenLastCalledWith("/admin/meowsurement/sessions", expect.objectContaining({ params: { page: 2, page_size: 15 } }));
  await act(async () => {
    const select = host.querySelector('[aria-label="Status pengukuran"]');
    Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value").set.call(select, "approved");
    select.dispatchEvent(new Event("change", { bubbles: true }));
  });
  expect(api.get).toHaveBeenLastCalledWith("/admin/meowsurement/sessions", expect.objectContaining({ params: { page: 1, page_size: 15, status: "approved" } }));
});

test("staff without review permission cannot load customer measurement queue", async () => {
  mockUser = { role: "staff", permissions: ["order.view"] };
  await mount();
  expect(api.get).not.toHaveBeenCalled();
  expect(host.querySelector('[role="alert"]').textContent).toContain("belum memiliki izin");
});
