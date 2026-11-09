"""Schema-only Step 1 entry point; this is not the storefront backend yet.

Run from backend/: uvicorn mysql_bootstrap:app --host 127.0.0.1 --port 8001
The application server:app now serves the migrated MySQL routes. This optional
diagnostic entry point mounts no commerce/auth/CMS routers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mysql.config import MySQLSettings
from mysql.database import Database, EXPECTED_SCHEMA_REVISION, TARGET_MYSQL_VERSION


def create_app(settings: MySQLSettings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database = Database(settings or MySQLSettings.from_env())
        app.state.mysql_database = database
        try:
            yield
        finally:
            await database.dispose()

    app = FastAPI(
        title="Meow Eyes — MySQL 5.7 Schema Foundation",
        version="step-1-mysql57",
        description=(
            "Database foundation only. Commerce, authentication, CMS, payments, "
            "and shipping are not enabled in this entry point."
        ),
        lifespan=lifespan,
    )

    def status_payload() -> dict:
        return {
            "mode": "schema_only",
            "database": "mysql",
            "database_target": TARGET_MYSQL_VERSION,
            "commerce_routes_enabled": False,
            "expected_schema_revision": EXPECTED_SCHEMA_REVISION,
        }

    @app.get("/api/health/live", tags=["health"])
    async def live() -> dict:
        return {"ok": True, **status_payload()}

    @app.get("/api/health/ready", tags=["health"])
    async def ready(request: Request) -> JSONResponse:
        result = await request.app.state.mysql_database.check_readiness()
        return JSONResponse(
            status_code=200 if result.ready else 503,
            content={"ok": result.ready, "reason": result.reason, **status_payload()},
        )

    return app


# Configuration is validated on application startup, never during module import.
app = create_app()
