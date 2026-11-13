"""Server-side submission/review policy; never trusts an approved client flag."""
from __future__ import annotations

import math
from statistics import median

from mysql.meowsurement import (ALGORITHM_VERSION, SETTINGS, camera_result, finite,
                               measurement_context, nonempty)


def _close(a, b, scale=1):
    return finite(a) and finite(b) and abs(a - b) <= 1e-6 * max(scale, abs(a), abs(b), 1)


def _point(point, image):
    return isinstance(point, dict) and finite(point.get("x")) and finite(point.get("y")) and 0 <= point["x"] <= image["width"] and 0 <= point["y"] <= image["height"]


def _transform(matrix, point):
    divisor = matrix[6] * point["x"] + matrix[7] * point["y"] + matrix[8]
    if abs(divisor) < 1e-10:
        return None
    x = (matrix[0] * point["x"] + matrix[1] * point["y"] + matrix[2]) / divisor
    y = (matrix[3] * point["x"] + matrix[4] * point["y"] + matrix[5]) / divisor
    return {"x": x, "y": y} if finite(x) and finite(y) else None


def calibration_valid(calibration, capture=None):
    if not isinstance(calibration, dict) or calibration.get("valid") is not True:
        return False
    matrix = calibration.get("matrix")
    method = calibration.get("method")
    if (method not in SETTINGS["calibrationMethods"] or not isinstance(matrix, list) or len(matrix) != 9 or
            not all(finite(v) for v in matrix) or not nonempty(calibration.get("referencePlane"))):
        return False
    if any(calibration.get("evidence", {}).get(key) is not True for key in ("knownSize", "fullyVisible", "samePlane", "clearEdges")):
        return False
    image = calibration.get("image") or {}
    if any(not isinstance(image.get(key), int) or not 16 <= image[key] <= 20000000 for key in ("width", "height")) or image["width"] * image["height"] > 20000000:
        return False
    if capture and (image["width"] != capture["width"] or image["height"] != capture["height"]):
        return False
    geometry = calibration.get("geometry") or {}
    if method == "frame":
        points = geometry.get("segment")
        length = geometry.get("lengthMm")
        if calibration.get("evidence", {}).get("frontoparallel") is not True or not finite(length) or length <= 0 or not isinstance(points, list) or len(points) != 2:
            return False
        targets = [(0, 0), (length, 0)]
        if any(not _point(point, image) for point in points):
            return False
        dx, dy = points[1]["x"] - points[0]["x"], points[1]["y"] - points[0]["y"]
        if dx * dx + dy * dy < 16:
            return False
        factor = length / (dx * dx + dy * dy)
        expected = [factor * dx, factor * dy, -factor * (dx * points[0]["x"] + dy * points[0]["y"]),
                    -factor * dy, factor * dx, factor * (dy * points[0]["x"] - dx * points[0]["y"]), 0, 0, 1]
        if not all(_close(a, b) for a, b in zip(matrix, expected)):
            return False
    else:
        points = geometry.get("corners")
        width, height = geometry.get("widthMm"), geometry.get("heightMm")
        if not finite(width) or not finite(height) or width <= 0 or height <= 0 or not isinstance(points, list) or len(points) != 4 or any(not _point(p, image) for p in points):
            return False
        targets = [(0, 0), (width, 0), (width, height), (0, height)]
        edges = [(points[(i + 1) % 4]["x"] - p["x"], points[(i + 1) % 4]["y"] - p["y"]) for i, p in enumerate(points)]
        lengths = [math.hypot(*edge) for edge in edges]
        if min(lengths) < 4:
            return False
        turns = [edges[i][0] * edges[(i + 1) % 4][1] - edges[i][1] * edges[(i + 1) % 4][0] for i in range(4)]
        if min(turns) <= 0 or min(turns[i] / (lengths[i] * lengths[(i + 1) % 4]) for i in range(4)) < .15:
            return False
        if max(lengths[0] / lengths[2], lengths[2] / lengths[0], lengths[1] / lengths[3], lengths[3] / lengths[1]) > 4:
            return False
    for point, target in zip(points, targets):
        converted = _transform(matrix, point)
        if converted is None or not _close(converted["x"], target[0]) or not _close(converted["y"], target[1]):
            return False
    return True


def _vector(a, b):
    return b["x"] - a["x"], b["y"] - a["y"]


def _unit(vector):
    length = math.hypot(*vector)
    return (vector[0] / length, vector[1] / length) if length > 1e-12 else None


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def recompute_capture(key, capture):
    """Repeat the shipped planar arithmetic from original coordinate landmarks.

    This verifies traceability/numerical consistency, not clinical accuracy.
    Physical same-plane and professional reference evidence remain required.
    """
    calibration = capture.get("calibration")
    if not calibration_valid(calibration, capture):
        return None
    pd = key.endswith("_pd")
    vertex = key.startswith("vertex_")
    names = (["rightPupil", "leftPupil", "midlineTop", "midlineBottom"] if pd else
             ["cornea", "backLens", "gazeStart", "gazeEnd"] if vertex else
             ["lensTop", "lensBottom", "verticalTop", "verticalBottom"])
    confirmations = ["landmarksConfirmed", "headPoseAcceptable", "gazeCorrect" if pd else "surfaceVisible" if vertex else "verticalReferenceConfirmed"]
    if any(capture.get("confirmations", {}).get(k) is not True for k in confirmations):
        return None
    source = capture.get("points") or {}
    if any(not _point(source.get(name), calibration["image"]) for name in names):
        return None
    matrix = calibration["matrix"]
    anchor = (calibration.get("geometry", {}).get("corners") or calibration.get("geometry", {}).get("segment"))[0]
    anchor_denominator = matrix[6] * anchor["x"] + matrix[7] * anchor["y"] + matrix[8]
    if abs(anchor_denominator) < 1e-10:
        return None
    points = {}
    for name in names:
        point = source[name]
        divisor = matrix[6] * point["x"] + matrix[7] * point["y"] + matrix[8]
        if divisor * anchor_denominator <= 0:
            return None
        converted = _transform(matrix, point)
        if converted is None:
            return None
        points[name] = converted
    if pd:
        vertical = _unit(_vector(points["midlineTop"], points["midlineBottom"]))
        if vertical is None:
            return None
        horizontal = (vertical[1], -vertical[0])
        right = _dot(_vector(points["midlineTop"], points["rightPupil"]), horizontal)
        left = _dot(_vector(points["midlineTop"], points["leftPupil"]), horizontal)
        return {"rightMm": abs(right), "leftMm": abs(left), "binocularMm": abs(right) + abs(left)} if right * left < 0 else None
    if vertex:
        gaze = _unit(_vector(points["gazeStart"], points["gazeEnd"]))
        if gaze is None:
            return None
        distance = _dot(_vector(points["cornea"], points["backLens"]), gaze)
        return {"vertexMm": distance} if distance > 0 else None
    lens, vertical = _unit(_vector(points["lensTop"], points["lensBottom"])), _unit(_vector(points["verticalTop"], points["verticalBottom"]))
    pitch = capture.get("headPitchDeg")
    if lens is None or vertical is None or capture.get("inwardDirection") not in {"left", "right"} or not finite(pitch) or abs(pitch) >= 90:
        return None
    if capture.get("headPitchSource") not in {"instrument", "manual_reference", "operator_reference"}:
        return None
    raw = math.degrees(math.atan2(_cross(vertical, lens), _dot(vertical, lens))) * (1 if capture["inwardDirection"] == "left" else -1)
    return {"rawDeg": raw, "headPitchDeg": pitch, "correctedDeg": raw - pitch} if abs(raw) < 90 and abs(raw - pitch) < 90 else None


def _repeatability(values):
    if len(values) < 3 or not all(finite(v) for v in values):
        return None
    centre = median(values)
    mad = median(abs(v - centre) for v in values)
    inliers = [v for v in values if mad <= 1e-12 or .67448975 * abs(v - centre) / mad <= 3.5]
    return {"median": median(inliers), "inlierCount": len(inliers)} if len(inliers) >= 3 else None


def evaluate_submission(data, *, approval=False):
    errors, warnings = [], []
    context = measurement_context(data)
    results = {**data.get("manualMeasurements", {}), **data.get("results", {})}
    captures = {c["id"]: c for c in data.get("captures", [])}
    low = False
    for key in data["requiredParameters"]:
        result = results.get(key)
        if not isinstance(result, dict) or result.get("valid") is not True:
            errors.append(f"{key}: hasil valid belum tersedia")
            continue
        if result.get("algorithmVersion") != ALGORITHM_VERSION:
            errors.append(f"{key}: versi algoritma tidak didukung")
        if result.get("contextInvalidated") or result.get("measurementContext") != context:
            errors.append(f"{key}: konteks frame atau jarak kerja telah berubah")
        quality = result.get("quality") or {}
        score, category = quality.get("score"), quality.get("category")
        if not finite(score) or not 0 <= score <= 100 or category not in {"high", "medium", "low"}:
            errors.append(f"{key}: bukti kualitas tidak lengkap")
        if category == "low" or (finite(score) and score < 50):
            low = True
        values = result.get("values") or {}
        if not isinstance(values, dict):
            errors.append(f"{key}: nilai hasil tidak valid")
            continue
        if key.endswith("_pd"):
            if any(not finite(values.get(k)) or values[k] <= 0 for k in ("rightMm", "leftMm", "binocularMm")):
                errors.append(f"{key}: PD kanan dan kiri harus terukur secara independen")
            elif abs(values["rightMm"] + values["leftMm"] - values["binocularMm"]) > .011:
                errors.append(f"{key}: jumlah PD binocular tidak konsisten")
            if key == "near_pd" and values.get("workingDistanceCm") != data["workingDistanceCm"]:
                errors.append("near_pd: jarak kerja tidak cocok dengan sesi")
        elif key.startswith("vertex_"):
            if not finite(values.get("vertexMm")) or values["vertexMm"] <= 0:
                errors.append(f"{key}: jarak vertex harus positif")
        else:
            angle = values.get("correctedDeg", values.get("angleDeg"))
            if not finite(angle) or abs(angle) >= 90:
                errors.append(f"{key}: sudut tidak valid")
            if key.startswith("wrap_") and not nonempty(result.get("referenceConvention") or values.get("angleReference")):
                errors.append(f"{key}: referensi sudut harus dicatat")
        if not camera_result(result):
            if result.get("method") != "manual_instrument" or not nonempty(result.get("instrumentReference")) or result.get("operatorConfirmed") is not True:
                errors.append(f"{key}: alat referensi dan konfirmasi pembacaan wajib dicatat")
            fields = ("rightDeg", "leftDeg") if key.startswith(("wrap_", "pantoscopic_")) else ("rightMm", "leftMm")
            if any(not finite(values.get(field)) for field in fields):
                errors.append(f"{key}: pembacaan alat kanan dan kiri wajib disimpan")
            continue
        if key.startswith("wrap_"):
            errors.append("Pengukuran wrap kamera belum didukung")
            continue
        expected_method = "calibrated_planar_pd" if key.endswith("_pd") else "lateral_gaze_projection" if key.startswith("vertex_") else "lateral_plane_angle_manual_pitch"
        if result.get("method") != expected_method or not calibration_valid(result.get("calibration")):
            errors.append(f"{key}: metode atau skala kalibrasi tidak valid")
        expected_view = "frontal" if key == "distance_pd" else "frontal_near" if key == "near_pd" else "lateral_right" if key.endswith("_right") else "lateral_left"
        ids, hashes = result.get("sourceCaptureIds") or [], result.get("sourcePhotoHashes") or []
        if not ids or len(ids) != len(set(ids)) or not isinstance(hashes, list) or len(hashes) != len(ids) or len(set(hashes)) != len(hashes):
            errors.append(f"{key}: foto sumber berbeda wajib terhubung ke setiap hasil")
            continue
        if not any(captures.get(capture_id, {}).get("calibration") == result.get("calibration") for capture_id in ids):
            errors.append(f"{key}: ringkasan kalibrasi tidak berasal dari foto sumber")
        sample_values = []
        source_measurements = result.get("sourceMeasurements") or []
        for index, capture_id in enumerate(ids):
            capture = captures.get(capture_id)
            if (not capture or capture.get("view") != expected_view or capture.get("superseded") or capture.get("contextInvalidated")
                    or capture.get("measurementContext") != context or capture.get("photoHash") != hashes[index]):
                errors.append(f"{key}: foto sumber aktif tidak cocok dengan konteks hasil")
                continue
            computed = recompute_capture(key, capture)
            stored = capture.get("measurements", {}).get(key) or {}
            if computed is None or stored.get("valid") is not True or stored.get("method") != expected_method or any(
                    not _close(v, (stored.get("values") or {}).get(field)) for field, v in computed.items()):
                errors.append(f"{key}: hasil tidak cocok dengan landmark dan skala sampel")
                continue
            if not any(isinstance(source, dict) and source.get("captureId") == capture_id and source.get("photoHash") == capture["photoHash"]
                       and source.get("values") == stored.get("values") for source in source_measurements):
                errors.append(f"{key}: pasangan nilai sumber belum tersimpan")
            sample_values.append(computed)
        fields = ["rightMm", "leftMm"] if key.endswith("_pd") else ["vertexMm"] if key.startswith("vertex_") else ["rawDeg", "headPitchDeg", "correctedDeg"]
        # Valid camera aggregates are always derived from three distinct samples.
        if len(sample_values) < 3:
            errors.append(f"{key}: setidaknya tiga sampel berbeda yang valid diperlukan")
        else:
            repeatability = result.get("repeatability") or {}
            if repeatability.get("valid") is not True or repeatability.get("sampleCount") != len(ids) or not finite(repeatability.get("inlierCount")) or repeatability["inlierCount"] < 3:
                errors.append(f"{key}: bukti repeatability tidak lengkap")
            for field in fields:
                computed = _repeatability([sample[field] for sample in sample_values])
                declared = (repeatability.get("byField") or {}).get(field) or {}
                if computed is None or not _close(values.get(field), computed["median"]) or declared.get("valid") is not True or declared.get("inlierCount") != computed["inlierCount"] or not _close(declared.get("median"), computed["median"]):
                    errors.append(f"{key}: median/repeatability {field} tidak cocok dengan sumber")
        if key.startswith("pantoscopic_") and not nonempty(values.get("headPitchSource")):
            errors.append(f"{key}: sumber head pitch harus dicatat")
        warnings.append("Estimasi kamera memerlukan pembanding referensi dan review independen.")
    if low:
        warnings.append("Kualitas rendah memerlukan verifikasi atau pengukuran ulang.")
        if approval:
            errors.append("Hasil berkualitas rendah tidak dapat disetujui")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings)),
            "status": "draft" if errors else "needs_verification" if low else "pending_review"}
