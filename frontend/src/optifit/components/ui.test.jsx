import React, { act } from "react";
import { createRoot } from "react-dom/client";
import OptiFitApp from "../OptiFitApp";
import SessionDataForm, { blankSessionData } from "./SessionDataForm";
import { Preparation, aggregateCaptureResults, computeCapture } from "./CaptureWorkflow";
import { ExportDialog } from "./Results";
import { createCalibration } from "../vision";
import { measurementContext, invalidateChangedMeasurementContext } from "./measurementContext";
import { vault } from "../storage/vault";
import { generateReport, downloadReport, printReport } from "../reports";

jest.mock("../storage/vault", () => ({ vault: {
  getState: jest.fn(), getUser: jest.fn(), status: jest.fn(), subscribe: jest.fn(), lock: jest.fn(), touch: jest.fn(),
  recordExport: jest.fn(), getPhoto: jest.fn(),
} }));
jest.mock("../reports", () => ({ generateReport: jest.fn(), downloadReport: jest.fn(), printReport: jest.fn() }));

let host; let root;
const render = async node => act(async () => root.render(node));
const click = async element => act(async () => element.dispatchEvent(new MouseEvent("click", { bubbles: true })));
const submit = async form => act(async () => form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));
const button = text => [...host.querySelectorAll("button")].find(node => node.textContent.includes(text));
const inputFor = text => { const label = [...host.querySelectorAll("label")].find(node => node.textContent.includes(text)); return label?.querySelector("input,select,textarea") || (label?.htmlFor ? document.getElementById(label.htmlFor) : null); };
const fill = async (node, value) => act(async () => { Object.getOwnPropertyDescriptor(node instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, "value").set.call(node, value); node.dispatchEvent(new Event("input", { bubbles: true })); });
beforeEach(() => { jest.clearAllMocks(); host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host); vault.getPhoto.mockRejectedValue(new Error("Foto tidak tersedia")); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });

const contextData = () => ({ ...blankSessionData(), frame: { brand: "TEST FIXTURE", model: "Fixture", a: 52, b: 40, dbl: 18, ed: 55, symmetric: true, pdReference: "frame_bridge" } });
const confirmations = { landmarksConfirmed: true, frameVisible: true, pupilsVisible: true, noReflections: true, gazeCorrect: true, headPoseAcceptable: true, distanceAppropriate: true, scaleConsistent: true };
function capture(id, data = contextData(), delta = 0, view = "frontal") {
  const calibrationSpec = { method: "frame", image: { width: 400, height: 300 }, lengthMm: 100, segment: [{ x: 20, y: 240 }, { x: 220, y: 240 }], referencePlane: "Bidang referensi uji", evidence: { knownSize: true, fullyVisible: true, samePlane: true, clearEdges: true, frontoparallel: true } };
  const value = { id, photoHash: `hash-${id}`, view, calibrationSpec, calibration: createCalibration(calibrationSpec), measurementContext: measurementContext(data), confirmations, analysis: { valid: true, sharpness: "usable", exposure: "usable" }, points: { rightPupil: { x: 120 + delta, y: 100 }, leftPupil: { x: 250 + delta, y: 100 }, midlineTop: { x: 182, y: 80 }, midlineBottom: { x: 182, y: 180 } } };
  return { ...value, measurements: computeCapture(value, data) };
}

test("three independent annotated samples preserve unequal monocular PD", () => {
  const result = aggregateCaptureResults([capture("a", contextData(), -1), capture("b"), capture("c", contextData(), 1)]).distance_pd;
  expect(result.valid).toBe(true); expect(result.values.rightMm).toBe(31); expect(result.values.leftMm).toBe(34); expect(result.values.binocularMm).toBe(65);
  expect(result.repeatability.sampleCount).toBe(3); expect(result.sourcePhotoHashes).toHaveLength(3); expect(result.quality.score).toBeLessThanOrEqual(69);
});

test("duplicated photos cannot manufacture repeatability", () => {
  const first = capture("a");
  const result = aggregateCaptureResults([first, { ...capture("b"), photoHash: first.photoHash }, { ...capture("c"), photoHash: first.photoHash }]).distance_pd;
  expect(result.valid).toBe(false); expect(result.sampleCount).toBe(1); expect(result.repeatability.valid).toBe(false);
});

test("near PD at different working distances is never aggregated", () => {
  const first = contextData(); const other = { ...first, workingDistanceCm: 50 };
  const result = aggregateCaptureResults([capture("a", first, 0, "frontal_near"), capture("b", first, 1, "frontal_near"), capture("c", other, -1, "frontal_near")]).near_pd;
  expect(result.valid).toBe(false); expect(result.reasons.join(" ")).toContain("berbeda");
});

test("pantoscopic summaries retain original triples and label componentwise medians", () => {
  const triples = [[5, 0, 5], [8, 5, 3], [9, 2, 7]];
  const samples = triples.map(([rawDeg, headPitchDeg, correctedDeg], index) => {
    const sample = capture(`panto-${index}`);
    return { ...sample, view: "lateral_right", measurements: { pantoscopic_right: { ...sample.measurements.distance_pd, parameter: "pantoscopic", method: "lateral_plane_angle_manual_pitch", values: { rawDeg, headPitchDeg, correctedDeg, headPitchSource: "instrument" } } } };
  });
  const result = aggregateCaptureResults(samples).pantoscopic_right;
  expect(result.valid).toBe(true); expect(result.aggregationMethod).toBe("componentwise_median");
  expect(result.values).toMatchObject({ rawDeg: 8, headPitchDeg: 2, correctedDeg: 5 });
  expect(result.sourceMeasurements.map(row => [row.values.rawDeg, row.values.headPitchDeg, row.values.correctedDeg])).toEqual(triples);
});

test("pantoscopic sources with different head-pitch protocols cannot be combined", () => {
  const samples = ["instrument", "instrument", "manual_reference"].map((headPitchSource, index) => {
    const sample = capture(`panto-${index}`);
    return { ...sample, view: "lateral_right", measurements: { pantoscopic_right: { ...sample.measurements.distance_pd, parameter: "pantoscopic", method: "lateral_plane_angle_manual_pitch", values: { rawDeg: 8, headPitchDeg: 2, correctedDeg: 6, headPitchSource } } } };
  });
  const result = aggregateCaptureResults(samples).pantoscopic_right;
  expect(result.valid).toBe(false); expect(result.reasons.join(" ")).toContain("sumber head pitch");
});

test("calibration and context changes prevent stale camera measurements", () => {
  const data = contextData(); const first = capture("a", data);
  expect(computeCapture({ ...first, calibration: { valid: false } }, data).distance_pd.valid).toBe(false);
  expect(computeCapture(first, { ...data, frame: { ...data.frame, dbl: 20 } }).distance_pd.values).toBeNull();
  const source = { ...data, captures: [first], results: { distance_pd: { ...first.measurements.distance_pd, source: "camera" } } };
  const revised = invalidateChangedMeasurementContext(source, { ...source, workingDistanceCm: 45 });
  expect(revised.results.distance_pd.valid).toBe(false); expect(revised.captures[0].contextInvalidated).toBe(true); expect(source.captures[0].contextInvalidated).toBeUndefined();
});

test("technical preparation never supplies patient consent", async () => {
  const onSave = jest.fn(); await render(<Preparation data={blankSessionData()} onSave={onSave} />);
  await click(button("Semua persiapan siap"));
  expect(inputFor("Pasien menyetujui").checked).toBe(false); expect(button("Simpan persiapan").disabled).toBe(true);
  await click(inputFor("Pasien menyetujui")); await click(button("Simpan persiapan"));
  expect(onSave).toHaveBeenCalledTimes(1); expect(onSave.mock.calls[0][0].consents.capture).toBe(true); expect(onSave.mock.calls[0][0].consents.thumbnail).toBe(false);
});

test("session correction requires a reason and invalidates changed frame context", async () => {
  const data = contextData(); data.captures = [capture("a", data)]; data.results = { distance_pd: data.captures[0].measurements.distance_pd };
  const onSave = jest.fn(); await render(<SessionDataForm editing data={data} examinationDate="2026-01-01" onSave={onSave} onCancel={() => {}} />);
  await submit(host.querySelector("form")); expect(onSave).not.toHaveBeenCalled(); expect(host.textContent).toContain("Alasan revisi wajib");
  await fill(inputFor("DBL —"), "20"); await fill(inputFor("Alasan revisi data sesi"), "Frame diganti untuk pengukuran ulang.");
  await submit(host.querySelector("form"));
  expect(onSave).toHaveBeenCalledTimes(1); expect(onSave.mock.calls[0][0].results.distance_pd.valid).toBe(false); expect(onSave.mock.calls[0][0].frame.dbl).toBe(20);
});

test("report export needs explicit confirmation and audit before download", async () => {
  const data = blankSessionData(); const state = { organization: { name: "Optik Fixture" }, users: [], reviews: [], photos: [] };
  const events = []; generateReport.mockImplementation(async () => { events.push("generate"); return { blob: new Blob(["report"]), filename: "fixture.pdf" }; });
  vault.recordExport.mockImplementation(async () => { events.push("audit"); }); downloadReport.mockImplementation(() => events.push("download"));
  await render(<ExportDialog state={state} patient={{ id: "p" }} session={{ id: "s" }} revision={{ id: "r" }} data={data} onClose={() => {}} />);
  await submit(host.querySelector("form")); expect(generateReport).not.toHaveBeenCalled(); expect(button("Buat dan unduh").disabled).toBe(true);
  await click(inputFor("Saya mengonfirmasi ekspor")); await submit(host.querySelector("form"));
  expect(events).toEqual(["generate", "audit", "download"]); expect(generateReport.mock.calls[0][0].includePhotos).toBe(false); expect(printReport).not.toHaveBeenCalled();
});

test("vault locking during export blocks download", async () => {
  generateReport.mockResolvedValue({ blob: new Blob(["report"]), filename: "fixture.pdf" }); vault.recordExport.mockRejectedValue(new Error("Vault terkunci"));
  await render(<ExportDialog state={{ organization: {}, users: [], reviews: [], photos: [] }} patient={{ id: "p" }} session={{ id: "s" }} revision={{ id: "r" }} data={blankSessionData()} onClose={() => {}} />);
  await click(inputFor("Saya mengonfirmasi ekspor")); await submit(host.querySelector("form"));
  expect(downloadReport).not.toHaveBeenCalled(); expect(host.textContent).toContain("Vault terkunci");
});

test("locking removes patient UI immediately and offline readiness remains explicit", async () => {
  let listener; let state = { organization: { name: "Optik Fixture" }, users: [], patients: [{ id: "p", fullName: "PATIENT PRIVATE FIXTURE", recordNumber: "OF-TEST", createdAt: "2026-01-01" }], sessions: [], settings: {} };
  let user = { id: "admin", displayName: "Fixture Admin", role: "admin" };
  vault.getState.mockImplementation(() => state); vault.getUser.mockImplementation(() => user);
  vault.status.mockResolvedValue({ initialized: true, logins: [{ username: "fixture" }], locked: false });
  vault.subscribe.mockImplementation(callback => { listener = callback; return () => { listener = null; }; });
  vault.lock.mockImplementation(() => { state = null; user = null; listener?.(); });
  await render(<OptiFitApp offlineStatus={{ ready: false, reason: "Cache belum tersedia" }} />);
  expect(host.textContent).toContain("PATIENT PRIVATE FIXTURE"); expect(host.textContent).toContain("cache offline belum siap");
  await click(button("Kunci")); expect(host.textContent).not.toContain("PATIENT PRIVATE FIXTURE"); expect(host.textContent).toContain("Buka ruang kerja");
});
