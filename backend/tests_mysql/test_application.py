"""Application lifecycle, liveness/readiness and safe database HTTP errors."""
import asyncio
import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError, OperationalError
from mysql.database import ReadinessResult
import server


def test_openapi_exposes_all_legacy_operations_and_mysql_health():
    schema = server.app.openapi()
    assert schema["info"]["version"] == "2.0-mysql57"
    assert "/api/health/live" in schema["paths"] and "/api/health/ready" in schema["paths"]
    operations = sum(sum(k in {"get", "post", "put", "patch", "delete", "head", "options"}
                         for k in methods) for methods in schema["paths"].values())
    assert operations >= 165
    for path, method in [
        ("/api/settings/whatsapp", "get"),
        ("/api/uploads/prescription", "post"),
        ("/api/cart/{cart_item_id}/prescription", "patch"),
        ("/api/orders/{order_id}/review", "post"),
        ("/api/products/{product_id}/try-on", "get"),
        ("/api/admin/try-on-assets", "post"),
    ]:
        assert method in schema["paths"][path]


def test_startup_fails_closed_without_starting_jobs(monkeypatch):
    events = []
    async def failed_start():
        events.append("probe")
        return ReadinessResult(False, "schema_revision_mismatch")
    async def close():
        events.append("dispose")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setattr(server, "initialize", failed_start)
    monkeypatch.setattr(server, "get_database", lambda: object())
    monkeypatch.setattr(server, "start_scheduler", lambda: events.append("start"))
    monkeypatch.setattr(server, "stop_scheduler", lambda: events.append("stop"))
    monkeypatch.setattr(server, "close_client", close)
    async def scenario():
        with pytest.raises(RuntimeError, match="schema_revision_mismatch"):
            async with server.lifespan(FastAPI()):
                pytest.fail("startup must not serve business requests")
    asyncio.run(scenario())
    assert "start" not in events and events == ["probe", "stop", "dispose"]


def test_production_requires_explicit_cors_origins(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    async def scenario():
        with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
            async with server.lifespan(FastAPI()):
                pytest.fail("must refuse incomplete production configuration")
    asyncio.run(scenario())


def test_liveness_and_readiness_remain_distinct(monkeypatch):
    class Unready:
        async def check_readiness(self):
            return ReadinessResult(False, "database_unavailable")
    monkeypatch.setattr(server, "get_database", lambda: Unready())
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app), base_url="http://test") as client:
            live = await client.get("/api/health/live")
            ready = await client.get("/api/health/ready")
            assert live.status_code == 200 and live.json()["mode"] == "application"
            assert ready.status_code == 503 and ready.json()["database_target"] == "5.7.24-log"
    asyncio.run(scenario())


@pytest.mark.parametrize("error,status,code", [
    (IntegrityError("SECRET_SQL", {"password": "SECRET_PASSWORD"}, Exception(1062, "SECRET_DRIVER")), 409, "integrity_conflict"),
    (OperationalError("SECRET_SQL", {"token": "SECRET_TOKEN"}, Exception(1644, "SECRET_DRIVER")), 422, "validation_failed"),
    (OperationalError("SECRET_SQL", {}, Exception(1213, "SECRET_DRIVER")), 409, "transaction_retry"),
    (OperationalError("SECRET_SQL", {}, Exception(2003, "SECRET_DRIVER")), 503, "database_unavailable"),
])
def test_database_http_errors_do_not_leak_sql_or_credentials(error, status, code):
    app = FastAPI()
    app.add_exception_handler(IntegrityError, server.integrity_error_handler)
    from sqlalchemy.exc import DBAPIError
    app.add_exception_handler(DBAPIError, server.database_error_handler)
    @app.get("/fail")
    async def fail():
        raise error
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/fail")
            assert response.status_code == status
            assert response.json()["code"] == code
            assert "SECRET" not in response.text
    asyncio.run(scenario())


def test_runtime_environment_preserves_literal_dollar_secrets(tmp_path, monkeypatch):
    from mysql.config import load_runtime_environment, MySQLSettings
    names = ("APP_ENV", "MYSQL_HOST", "MYSQL_PORT", "MYSQL_DATABASE", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_SSL_MODE")
    for name in names:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("UNRELATED_VAR", "must-not-be-substituted")
    env_file = tmp_path / "mysql.env"
    env_file.write_text("APP_ENV=test\nMYSQL_HOST=127.0.0.1\nMYSQL_PORT=3306\nMYSQL_DATABASE=test_meow_literal\nMYSQL_USER=fixture\nMYSQL_PASSWORD='literal-${UNRELATED_VAR}-#-value'\nMYSQL_SSL_MODE=disabled\n")
    # Track variables set by dotenv so monkeypatch restores the caller's process.
    for name in names:
        monkeypatch.setenv(name, "placeholder")
        monkeypatch.delenv(name)
    load_runtime_environment(env_file)
    settings = MySQLSettings.from_env(env_file=env_file)
    assert settings.password == "literal-${UNRELATED_VAR}-#-value"
