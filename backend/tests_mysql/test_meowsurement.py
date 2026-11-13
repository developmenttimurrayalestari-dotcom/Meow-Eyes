"""Customer integration, immutable snapshots, and private evidence regressions.

SQLite exercises real relational transactions and HTTP ownership. It does not
substitute for the optional native MySQL 5.7 migration/locking suite.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import timedelta
import hashlib
from io import BytesIO

import httpx
from fastapi import FastAPI
from PIL import Image
import pytest
from sqlalchemy import func, select

from auth import current_user
from database import read_session, session_scope
from models import User
from mysql import models as m
from mysql.base import utcnow
from mysql.commerce import create_checkout
from mysql.meowsurement import ALGORITHM_VERSION, measurement_context
from tests_mysql.commerce_scenarios import seed_commerce_fixture
from tests_mysql.sql_helpers import isolated_database
import routes_meowsurement


PROFILE = {"expected_version": 0, "name": "Alicia Customer", "phone": "0812 3456 7890",
           "birth_date": "1990-02-01", "gender": "female", "address": "Alamat customer",
           "prescription": {"date": "2026-01-01", "od": {"sph": 0, "cyl": 0, "axis": None, "add": None},
                            "os": {"sph": -1.25, "cyl": -.5, "axis": 90, "add": None}, "notes": "Resep profesional"}}
SPEC = {"expected_version": 0, "specification": {"a": 50, "b": 38, "dbl": 18, "ed": 56,
         "temple_length": 140, "enabled": True, "symmetric": True, "source_note": "Kartu ukuran produsen"}, "variants": []}


@asynccontextmanager
async def client_fixture():
    async with isolated_database():
        fixture = await seed_commerce_fixture(bundle=True, quantity=1)
        fixture["admin_user"] = User(user_id=fixture["admin"], name="Admin", email="admin@example.com", role="admin")
        fixture["bob_user"] = User(user_id=fixture["bob"], name="Bob", email="bob@example.com")
        auth = {"user": fixture["user"]}
        app = FastAPI()
        app.dependency_overrides[current_user] = lambda: auth["user"]
        app.include_router(routes_meowsurement.router, prefix="/api")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            yield client, auth, fixture


async def prepared(client, auth, d, *, profile=PROFILE, spec=SPEC):
    auth["user"] = d["user"]
    saved_profile = await client.put("/api/customer/profile", json=deepcopy(profile))
    assert saved_profile.status_code == 200, saved_profile.text
    auth["user"] = d["admin_user"]
    saved_spec = await client.put(f'/api/admin/products/{d["frame"]}/frame-specification', json=deepcopy(spec))
    assert saved_spec.status_code == 200, saved_spec.text
    auth["user"] = d["user"]
    return {"product_id": d["frame"], "variant_id": d["vf"], "expected_profile_version": saved_profile.json()["profile"]["version"],
            "expected_spec_version": saved_spec.json()["version"], "examination_date": "2026-01-02",
            "working_distance_cm": 40, "required_parameters": ["distance_pd"], "mode": "manual"}


async def started(client, auth, d, **kwargs):
    payload = await prepared(client, auth, d, **kwargs)
    response = await client.post("/api/meowsurement/sessions", json=payload)
    assert response.status_code == 201, response.text
    detail = response.json()
    for value, prefix in ((detail["session"]["id"], "ms_"), (detail["revision"]["id"], "mr_")):
        assert value.startswith(prefix) and len(value) == len(prefix) + 32
        assert all(char in "0123456789abcdef" for char in value[len(prefix):])
    return detail, payload


async def revise(client, detail, data):
    return await client.post(f'/api/meowsurement/sessions/{detail["session"]["id"]}/revisions', json={
        "expected_revision_id": detail["revision"]["id"], "reason": "Pembacaan dan penandaan customer diperbarui.", "data": data})


def manual_data(detail, *, low=False):
    data = deepcopy(detail["revision"]["data"])
    data["results"]["distance_pd"] = {"valid": True, "method": "manual_instrument", "source": "manual_instrument",
        "algorithmVersion": ALGORITHM_VERSION, "values": {"rightMm": 31, "leftMm": 32, "binocularMm": 63},
        "quality": {"score": 40 if low else 80, "category": "low" if low else "high"},
        "measurementContext": measurement_context(data), "instrumentReference": "PD meter di toko, ID P-1",
        "operatorConfirmed": True, "sourceCaptureIds": [], "requiresReview": False, "clinicallyValidated": True}
    return data


def image_bytes(color="white"):
    output = BytesIO()
    image = Image.new("RGB", (100, 100), color)
    exif = Image.Exif()
    exif[0x010E] = "Private metadata removed by server"
    image.save(output, "PNG", exif=exif)
    return output.getvalue()


def local_capture(data, *, capture_id="cap_one", photo_id="local_one", photo_hash="a" * 64, view="frontal"):
    return {"id": capture_id, "photoId": photo_id, "photoHash": photo_hash, "view": view, "width": 100, "height": 100,
            "createdAt": "2026-01-02T00:00:00.000Z", "measurementContext": measurement_context(data), "points": {}, "measurements": {}}


def camera_data(detail):
    data = deepcopy(detail["revision"]["data"])
    data["consents"].update(capture=True)
    data["mode"] = "semi_automatic"
    calibration = {"valid": True, "method": "marker", "matrix": [1, 0, -10, 0, 1, -10, 0, 0, 1],
        "referencePlane": "Marker bidang fitting yang diperiksa", "image": {"width": 100, "height": 100},
        "geometry": {"corners": [{"x": 10, "y": 10}, {"x": 30, "y": 10}, {"x": 30, "y": 30}, {"x": 10, "y": 30}],
                     "widthMm": 20, "heightMm": 20},
        "evidence": {key: True for key in ("knownSize", "fullyVisible", "samePlane", "clearEdges")}}
    captures, source_measurements = [], []
    for i, shift in enumerate((0, .1, -.1)):
        capture = local_capture(data, capture_id=f"cap_{i}", photo_id=f"local_{i}", photo_hash=hashlib.sha256(str(i).encode()).hexdigest())
        capture["points"] = {"rightPupil": {"x": 19 - shift, "y": 50}, "leftPupil": {"x": 82 + shift, "y": 50},
                             "midlineTop": {"x": 50, "y": 40}, "midlineBottom": {"x": 50, "y": 60}}
        capture["calibration"] = deepcopy(calibration)
        capture["confirmations"] = {"landmarksConfirmed": True, "headPoseAcceptable": True, "gazeCorrect": True}
        values = {"rightMm": 31 + shift, "leftMm": 32 + shift, "binocularMm": 63 + 2 * shift, "workingDistanceCm": None,
                  "pdReference": "frame_bridge"}
        capture["measurements"] = {"distance_pd": {"valid": True, "method": "calibrated_planar_pd", "values": values,
            "algorithmVersion": ALGORITHM_VERSION, "measurementContext": measurement_context(data)}}
        captures.append(capture)
        source_measurements.append({"captureId": capture["id"], "photoHash": capture["photoHash"], "values": values})
    data["captures"] = captures
    data["results"]["distance_pd"] = {"valid": True, "method": "calibrated_planar_pd", "source": "camera", "algorithmVersion": ALGORITHM_VERSION,
        "values": {"rightMm": 31, "leftMm": 32, "binocularMm": 63, "workingDistanceCm": None, "pdReference": "frame_bridge"},
        "quality": {"score": 99, "category": "high"}, "calibration": deepcopy(calibration), "measurementContext": measurement_context(data),
        "sourceCaptureIds": [c["id"] for c in captures], "sourcePhotoHashes": [c["photoHash"] for c in captures],
        "sourceMeasurements": source_measurements, "aggregationMethod": "componentwise_median",
        "repeatability": {"valid": True, "sampleCount": 3, "inlierCount": 3,
                          "byField": {"rightMm": {"valid": True, "median": 31, "inlierCount": 3},
                                      "leftMm": {"valid": True, "median": 32, "inlierCount": 3}}}}
    return data


def test_profile_drafts_zero_rx_axis_gating_versions_and_checkout_history(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_MOCK_PAYMENTS", "1")
    monkeypatch.setenv("PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("SHIPPING_PROVIDER", "mock")
    async def run():
        async with client_fixture() as (client, auth, d):
            empty = await client.get("/api/customer/profile")
            assert empty.status_code == 200 and "no-store" in empty.headers["cache-control"]
            assert empty.json()["profile"]["version"] == 0 and not empty.json()["ready"]
            assert empty.json()["profile"]["name"] == d["user"].name
            blocked = await client.post("/api/meowsurement/sessions", json={"product_id": d["frame"], "variant_id": d["vf"],
                "expected_profile_version": 1, "expected_spec_version": 1})
            assert blocked.status_code == 422 and blocked.json()["detail"]["profile_url"] == "/profile"
            draft = deepcopy(PROFILE)
            draft["prescription"]["os"]["axis"] = None
            saved = await client.put("/api/customer/profile", json=draft)
            assert saved.status_code == 200, saved.text
            assert saved.json()["profile"]["prescription"]["od"]["sph"] == 0
            assert saved.json()["missing_fields"] == ["prescription.os.axis"]
            old_rx = saved.json()["profile"]["prescription"]["id"]
            assert (await client.put("/api/customer/profile", json=PROFILE)).status_code == 409
            completed = await client.put("/api/customer/profile", json={**PROFILE, "expected_version": 1})
            assert completed.status_code == 200 and completed.json()["ready"]
            rx = completed.json()["profile"]["prescription"]["id"]
            assert rx != old_rx
            renamed = await client.put("/api/customer/profile", json={"expected_version": 2, "name": "Alicia Baru"})
            assert renamed.json()["profile"]["prescription"]["id"] == rx
            for change in ({"birth_date": "2999-01-01"}, {"phone": "javascript:secret"}, {"gender": "admin"}):
                response = await client.put("/api/customer/profile", json={"expected_version": 3, **change})
                assert response.status_code == 422 and "no-store" in response.headers["cache-control"]
            invalid_axis = deepcopy(PROFILE)
            invalid_axis["prescription"]["od"]["axis"] = 181
            assert (await client.put("/api/customer/profile", json={**invalid_axis, "expected_version": 3})).status_code == 422
            async with read_session() as s:
                assert (await s.get(m.CartItem, d["cart"])).prescription_id == d["rx"]
                eye = await s.get(m.PrescriptionEye, (old_rx, "left"))
                assert eye.axis is None  # Completing the profile did not rewrite history.
                assert (await s.get(m.User, d["alice"])).name == "Alicia Baru"
            checkout = await create_checkout(d["alice"], d["req"])
            assert checkout["order"]["items"][0]["prescription"]["od_sph"] == -1.25
    asyncio.run(run())


def test_frame_specs_permissions_variant_ownership_aggregate_versions_and_active_catalog():
    async def run():
        async with client_fixture() as (client, auth, d):
            path = f'/api/admin/products/{d["frame"]}/frame-specification'
            assert (await client.put(path, json=SPEC)).status_code == 403
            auth["user"] = d["admin_user"]
            bad = deepcopy(SPEC)
            bad["variants"] = [{"variant_id": d["vl"], "inherit_default": False, "specification": SPEC["specification"]}]
            assert (await client.put(path, json=bad)).status_code == 422
            assert (await client.get(path)).json()["version"] == 0
            incomplete = deepcopy(SPEC)
            incomplete["specification"]["a"] = None
            assert (await client.put(path, json=incomplete)).status_code == 422
            saved = await client.put(path, json=SPEC)
            assert saved.status_code == 200, saved.text
            variant_spec = {**SPEC["specification"], "a": 53, "ed": 59}
            overridden = await client.put(path, json={**SPEC, "expected_version": 1,
                "variants": [{"variant_id": d["vf"], "inherit_default": False, "specification": variant_spec}]})
            assert overridden.status_code == 200, overridden.text
            assert overridden.json()["specification"]["version"] == 2
            assert overridden.json()["variants"][0]["effective_specification"]["a"] == 53
            assert overridden.json()["variants"][0]["effective_specification"]["version"] == 2
            assert (await client.put(path, json=SPEC)).status_code == 409
            auth["user"] = d["user"]
            choices = await client.get("/api/meowsurement/frames?query=Frame&page=1")
            assert choices.status_code == 200
            all_frames = (await client.get("/api/meowsurement/frames")).json()["products"]
            assert len(all_frames) == 1 and all_frames[0]["variants"][0]["frame_specification"]["a"] == 53
            async with session_scope() as s:
                (await s.get(m.Product, d["frame"])).is_active = False
            assert (await client.get(f'/api/products/{d["frame"]}/frame-specification')).status_code == 404
            assert (await client.get("/api/meowsurement/frames")).json()["products"] == []
    asyncio.run(run())


def test_session_snapshots_stay_immutable_cross_account_hidden_and_stale_edits_conflict():
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, create = await started(client, auth, d)
            path = f'/api/meowsurement/sessions/{detail["session"]["id"]}'
            assert detail["patient"]["id"] == d["alice"] and detail["patient"]["fullName"] == PROFILE["name"]
            assert detail["revision"]["data"]["prescription"]["od"]["sph"] == 0
            assert detail["revision"]["data"]["frame"]["a"] == 50
            forged = deepcopy(detail["revision"]["data"])
            forged["prescription"]["od"]["sph"] = -9
            assert (await revise(client, detail, forged)).status_code == 422
            forged = deepcopy(detail["revision"]["data"])
            forged["status"] = "approved"
            assert (await revise(client, detail, forged)).status_code == 422
            new = deepcopy(detail["revision"]["data"])
            new["notes"] = "Catatan berubah"
            saved = await revise(client, detail, new)
            assert saved.status_code == 200, saved.text
            assert saved.json()["session"]["status"] == "draft" and len(saved.json()["revisions"]) == 2
            assert (await revise(client, detail, new)).status_code == 409
            auth["user"] = d["bob_user"]
            assert (await client.get(path)).status_code == 404
            assert (await client.post(path + "/submit", json={"expected_revision_id": detail["revision"]["id"]})).status_code == 404
            assert (await client.get("/api/meowsurement/sessions")).json()["sessions"] == []
            auth["user"] = d["admin_user"]
            assert (await client.get("/api/meowsurement/bootstrap")).json()["can_review"]
            assert not (await client.get("/api/meowsurement/bootstrap")).json()["ready"]
            assert (await client.get(path)).status_code == 200  # Own prescription is not a reviewer prerequisite.
            await client.put(f'/api/admin/products/{d["frame"]}/frame-specification', json={**SPEC, "expected_version": 1,
                "specification": {**SPEC["specification"], "a": 55, "ed": 61}})
            auth["user"] = d["user"]
            updated = deepcopy(PROFILE)
            updated["prescription"]["od"]["sph"] = -2
            await client.put("/api/customer/profile", json={**updated, "expected_version": 1})
            historical = (await client.get(path)).json()
            assert historical["revision"]["data"]["frame"]["a"] == 50
            assert historical["revision"]["data"]["prescription"]["od"]["sph"] == 0
            assert historical["patient"]["fullName"] == PROFILE["name"]
            assert (await client.post("/api/meowsurement/sessions", json=create)).status_code == 409
    asyncio.run(run())


def test_submission_requires_results_independent_review_and_verified_reference():
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, _ = await started(client, auth, d)
            path = f'/api/meowsurement/sessions/{detail["session"]["id"]}'
            assert (await client.post(path + "/submit", json={"expected_revision_id": detail["revision"]["id"]})).status_code == 422
            saved = await revise(client, detail, manual_data(detail))
            assert saved.status_code == 200, saved.text
            detail = saved.json()
            assert detail["revision"]["data"]["results"]["distance_pd"]["requiresReview"] is True
            assert detail["revision"]["data"]["results"]["distance_pd"]["clinicallyValidated"] is False
            submitted = await client.post(path + "/submit", json={"expected_revision_id": detail["revision"]["id"]})
            assert submitted.status_code == 200, submitted.text
            assert submitted.json()["session"]["status"] == "pending_review"
            request = {"expected_revision_id": detail["revision"]["id"], "decision": "approved", "note": "Diperiksa dengan alat pembanding.", "evidence": {}}
            assert (await client.post(path + "/reviews", json=request)).status_code == 403
            auth["user"] = d["user"].model_copy(update={"role": "admin"})
            assert (await client.post(path + "/reviews", json=request)).status_code == 403
            auth["user"] = d["admin_user"]
            queue = (await client.get("/api/admin/meowsurement/sessions")).json()
            assert queue["total"] == 1 and queue["sessions"][0]["customerName"] == PROFILE["name"]
            assert (await client.post(path + "/reviews", json=request)).status_code == 422
            request["evidence"] = {"professionalVerified": True, "referenceInstrument": "PD meter P-1", "protocolId": "Toko-2026-01",
                                   "comparisonNotes": "Pembacaan OD/OS dibandingkan dengan alat referensi."}
            approved = await client.post(path + "/reviews", json=request)
            assert approved.status_code == 200, approved.text
            assert approved.json()["session"]["status"] == "approved" and len(approved.json()["reviews"]) == 1
            assert (await client.post(path + "/reviews", json=request)).status_code == 409
            auth["user"] = d["user"]
            low = manual_data(detail, low=True)
            amended = (await revise(client, detail, low)).json()
            assert amended["session"]["status"] == "draft"  # Old approval cannot approve a new revision.
            again = await client.post(path + "/submit", json={"expected_revision_id": amended["revision"]["id"]})
            assert again.json()["session"]["status"] == "needs_verification"
            auth["user"] = d["admin_user"]
            request["expected_revision_id"] = amended["revision"]["id"]
            assert (await client.post(path + "/reviews", json=request)).status_code == 422
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementReview)) == 1
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementMeasurement)) == 2
    asyncio.run(run())


def test_private_photo_explicit_consent_owner_provenance_export_and_deletion(tmp_path, monkeypatch):
    monkeypatch.setattr(routes_meowsurement, "PRIVATE_PHOTO_ROOT", tmp_path / "private")
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, _ = await started(client, auth, d)
            path = f'/api/meowsurement/sessions/{detail["session"]["id"]}'
            source = image_bytes()
            async def upload(**data):
                return await client.post(path + "/photos", files={"file": ("face.png", source, "image/png")}, data=data)
            assert (await upload(consent="true")).status_code == 422
            data = deepcopy(detail["revision"]["data"])
            data["consents"].update(capture=True, uploadPhotos=True, thumbnail=True)
            saved = await revise(client, detail, data)
            assert saved.status_code == 200, saved.text
            detail = saved.json()
            assert (await upload()).status_code == 422
            result = await upload(consent="true")
            assert result.status_code == 201, result.text
            photo = result.json()["photo"]
            assert photo["id"].startswith("mp_") and len(photo["id"]) == 35
            assert all(char in "0123456789abcdef" for char in photo["id"][3:])
            assert photo["sourceHash"] == hashlib.sha256(source).hexdigest() and photo["hash"] != photo["sourceHash"]
            assert "url" not in photo and "storage_path" not in photo
            url = path + "/photos/" + photo["id"]
            downloaded = await client.get(url)
            assert downloaded.status_code == 200 and "no-store" in downloaded.headers["cache-control"]
            assert Image.open(BytesIO(downloaded.content)).getexif() == {}
            auth["user"] = d["bob_user"]
            assert (await client.get(url)).status_code == 404
            auth["user"] = d["bob_user"].model_copy(update={"role": "staff", "permissions": ["product.view"]})
            assert (await client.get(url)).status_code == 404
            auth["user"] = d["admin_user"]
            assert (await client.get(url)).status_code == 200
            assert (await client.delete(url)).status_code == 404
            auth["user"] = d["user"]
            data = deepcopy(detail["revision"]["data"])
            data["captures"] = [local_capture(data, photo_id=photo["id"], photo_hash=photo["sourceHash"])]
            linked = await revise(client, detail, data)
            assert linked.status_code == 200, linked.text
            detail = linked.json()
            exported = await client.post(path + "/exports", json={"revision_id": detail["revision"]["id"], "format": "pdf", "confirmed": True,
                "include_photos": True, "photo_ids": [photo["id"]]})
            assert exported.status_code == 200, exported.text
            bad_hash = deepcopy(data)
            bad_hash["captures"][0]["photoHash"] = "b" * 64
            assert (await revise(client, detail, bad_hash)).status_code == 422
            deleted = await client.delete(url)
            assert deleted.status_code == 200 and deleted.json()["photo"]["deletedAt"]
            assert (await client.get(url)).status_code == 404
            assert list((tmp_path / "private").iterdir()) == []
            assert (await client.post(path + "/exports", json={"revision_id": detail["revision"]["id"], "format": "pdf", "confirmed": True,
                "include_photos": True, "photo_ids": [photo["id"]]})).status_code == 404
            # Metadata survives erasure and remains valid in an append-only annotation revision.
            data["notes"] = "Foto sudah dihapus sesuai pilihan customer."
            revised = await revise(client, detail, data)
            assert revised.status_code == 200, revised.text
            async with read_session() as s:
                stored = await s.get(m.MeowsurementPhoto, photo["id"])
                assert stored.deleted_at is not None
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementCapture)) == 2
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementAuditEvent).where(m.MeowsurementAuditEvent.action == "report.exported")) == 1
    asyncio.run(run())


def test_local_photo_refs_cannot_impersonate_persistent_photos_or_skip_export_confirmation():
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, _ = await started(client, auth, d)
            path = f'/api/meowsurement/sessions/{detail["session"]["id"]}'
            data = deepcopy(detail["revision"]["data"])
            data["consents"].update(capture=True, thumbnail=True)
            data["captures"] = [local_capture(data)]
            saved = await revise(client, detail, data)
            assert saved.status_code == 200, saved.text
            detail = saved.json()
            async with read_session() as s:
                capture = await s.scalar(select(m.MeowsurementCapture))
                assert capture.photo_id is None and capture.data["photoId"] == "local_one"
            assert (await client.get(path + "/photos/local_one")).status_code == 404
            for body in ({"confirmed": False}, {"confirmed": True, "include_photos": True, "photo_ids": ["local_one"]}):
                result = await client.post(path + "/exports", json={"revision_id": detail["revision"]["id"], "format": "json", **body})
                assert result.status_code == 422
            assert (await client.post(path + "/exports", json={"revision_id": detail["revision"]["id"], "format": "json", "confirmed": True})).status_code == 200
            data["captures"][0]["image"] = "data:image/png;base64,PRIVATESECRET"
            failed = await revise(client, detail, data)
            assert failed.status_code == 422 and "PRIVATESECRET" not in failed.text
            oversized = await client.post(path + "/revisions", content='{"large":"' + "x" * (2 * 1024 * 1024) + '"}',
                                          headers={"Content-Type": "application/json"})
            assert oversized.status_code == 413 and "no-store" in oversized.headers["cache-control"]
    asyncio.run(run())


def test_camera_results_recomputed_from_landmarks_and_private_provenance_not_client_flags():
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, _ = await started(client, auth, d)
            path = f'/api/meowsurement/sessions/{detail["session"]["id"]}'
            result = await revise(client, detail, camera_data(detail))
            assert result.status_code == 200, result.text
            detail = result.json()
            quality = detail["revision"]["data"]["results"]["distance_pd"]["quality"]
            assert quality["score"] == 69 and quality["category"] == "medium"
            assert quality["label"] == "Sedang" and quality["kind"] == "engineering_evidence"
            submit = await client.post(path + "/submit", json={"expected_revision_id": detail["revision"]["id"]})
            assert submit.status_code == 200, submit.text
            assert submit.json()["session"]["status"] == "pending_review"
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementCapture)) == 3
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementMeasurementSource)) == 3
            # A plausible-looking result cannot change the median of its actual sources.
            forged = deepcopy(detail["revision"]["data"])
            forged["results"]["distance_pd"]["values"].update(rightMm=35, binocularMm=67)
            tampered = await revise(client, detail, forged)
            assert tampered.status_code == 200
            detail = tampered.json()
            submit = await client.post(path + "/submit", json={"expected_revision_id": detail["revision"]["id"]})
            assert submit.status_code == 422 and "median" in submit.text
            # A valid=true calibration claim cannot override physical marker scale.
            forged = camera_data(detail)
            forged["captures"][0]["calibration"]["matrix"][0] = 2
            forged["results"]["distance_pd"]["calibration"]["matrix"][0] = 2
            tampered = await revise(client, detail, forged)
            assert tampered.status_code == 200, tampered.text
            detail = tampered.json()
            submit = await client.post(path + "/submit", json={"expected_revision_id": detail["revision"]["id"]})
            assert submit.status_code == 422 and ("skala" in submit.text or "landmark" in submit.text)
            # Reusing a photo hash as if it were three independent images also fails.
            recovered = camera_data(detail)
            recovered["results"]["distance_pd"]["sourcePhotoHashes"] = [recovered["captures"][0]["photoHash"]] * 3
            changed = (await revise(client, detail, recovered)).json()
            assert (await client.post(path + "/submit", json={"expected_revision_id": changed["revision"]["id"]})).status_code == 422
    asyncio.run(run())


def test_profile_and_frame_selected_versions_required_and_untrusted_fields_rejected():
    async def run():
        async with client_fixture() as (client, auth, d):
            payload = await prepared(client, auth, d)
            for extra in ({"patient_id": d["bob"]}, {"user_id": d["bob"]}, {"status": "approved"}):
                response = await client.post("/api/meowsurement/sessions", json={**payload, **extra})
                assert response.status_code == 422
            for field in ("expected_profile_version", "expected_spec_version"):
                assert (await client.post("/api/meowsurement/sessions", json={**payload, field: 99})).status_code == 409
            assert (await client.post("/api/meowsurement/sessions", json={**payload, "variant_id": d["vl"]})).status_code == 404
            auth["user"] = d["admin_user"]
            await client.put(f'/api/admin/products/{d["frame"]}/frame-specification', json={**SPEC, "expected_version": 1,
                "variants": [{"variant_id": d["vf"], "inherit_default": False, "specification": {**SPEC["specification"], "a": 51}}]})
            auth["user"] = d["user"]
            response = await client.post("/api/meowsurement/sessions", json={**payload, "expected_spec_version": 2})
            assert response.status_code == 201
            assert response.json()["revision"]["data"]["frame"]["a"] == 51
            assert response.json()["revision"]["data"]["frame"]["sourceScope"] == "variant"
            assert response.json()["revision"]["data"]["prescription"]["date"] == "2026-01-01"
            filtered = await client.get(f'/api/meowsurement/frames?product_id={d["frame"]}')
            assert filtered.json()["total"] == 1 and filtered.json()["products"][0]["specification_version"] == 2
            assert (await client.get(f'/api/meowsurement/frames?product_id={d["lens"]}')).json()["products"] == []
    asyncio.run(run())


def test_retention_cleanup_removes_expired_bytes_keeps_audit_and_retries_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(routes_meowsurement, "PRIVATE_PHOTO_ROOT", tmp_path / "private")
    async def run():
        async with client_fixture() as (client, auth, d):
            detail, _ = await started(client, auth, d)
            path = f'/api/meowsurement/sessions/{detail["session"]["id"]}'
            data = deepcopy(detail["revision"]["data"])
            data["consents"].update(capture=True, uploadPhotos=True)
            assert (await revise(client, detail, data)).status_code == 200
            photos = []
            for color in ("white", "black"):
                result = await client.post(path + "/photos", files={"file": ("face.png", image_bytes(color), "image/png")}, data={"consent": "true"})
                assert result.status_code == 201, result.text
                photos.append(result.json()["photo"])
            assert await routes_meowsurement.expire_private_photos() == {"expired": 0, "removed": 0}
            # Simulate a file already removed by storage maintenance; no exception on retry.
            (tmp_path / "private" / (photos[0]["id"] + ".jpg")).unlink()
            future = utcnow() + timedelta(days=31)
            monkeypatch.setattr(routes_meowsurement, "utcnow", lambda: future)
            assert (await client.get(path + "/photos/" + photos[1]["id"])).status_code == 404
            assert await routes_meowsurement.expire_private_photos() == {"expired": 2, "removed": 1}
            assert list((tmp_path / "private").iterdir()) == []
            assert await routes_meowsurement.expire_private_photos() == {"expired": 0, "removed": 0}
            async with read_session() as s:
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementPhoto)) == 2
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementPhoto).where(m.MeowsurementPhoto.deleted_at.is_not(None))) == 2
                assert await s.scalar(select(func.count()).select_from(m.MeowsurementAuditEvent).where(m.MeowsurementAuditEvent.action == "photo.expired")) == 2
    asyncio.run(run())


def test_retention_job_propagates_failure_without_logging_private_details(monkeypatch, caplog):
    from scheduler import job_expire_meowsurement_photos
    failure = OSError("PRIVATE_STORAGE_PATH_AND_CUSTOMER_DATA")

    async def failed_cleanup():
        raise failure

    monkeypatch.setattr(routes_meowsurement, "expire_private_photos", failed_cleanup)
    with pytest.raises(OSError) as error:
        asyncio.run(job_expire_meowsurement_photos())
    assert error.value is failure
    assert "Scheduled Meowsurement photo retention cleanup failed" in caplog.text
    assert "PRIVATE_STORAGE_PATH_AND_CUSTOMER_DATA" not in caplog.text
