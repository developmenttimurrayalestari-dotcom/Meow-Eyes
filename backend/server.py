"""Meow Eyes FastAPI main application."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Depends
from mysql.config import load_runtime_environment
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_runtime_environment(ROOT_DIR / ".env.mysql")

from database import initialize, get_database, close_client  # noqa: E402
from routes_auth import router as auth_router  # noqa: E402
from routes_catalog import router as catalog_router  # noqa: E402
from routes_shopping import router as shopping_router  # noqa: E402
from routes_orders import router as orders_router  # noqa: E402
from routes_engagement import router as engagement_router  # noqa: E402
from routes_admin import router as admin_router  # noqa: E402
from routes_export import router as export_router  # noqa: E402
from routes_content import router as content_router  # noqa: E402
from routes_admin_content import router as admin_content_router  # noqa: E402
from routes_uploads import router as uploads_router, public_upload_file  # noqa: E402
from routes_features import router as features_router  # noqa: E402
from routes_integrations import router as integrations_router  # noqa: E402
from routes_meowsurement import router as meowsurement_router  # noqa: E402
from scheduler import start_scheduler, stop_scheduler, scheduler  # noqa: E402
from auth import current_admin  # noqa: E402
from models import User  # noqa: E402

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("meow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cors_origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "").split(",") if origin.strip()]
    if os.environ.get("APP_ENV", "development") == "production" and (not cors_origins or "*" in cors_origins):
        raise RuntimeError("CORS_ORIGINS must contain explicit frontend origins in production")
    try:
        result = await initialize()
        app.state.mysql_database = get_database()
        if not result.ready:
            raise RuntimeError(f"MySQL startup check failed: {result.reason}")
        logger.info("MySQL schema is ready")
        if os.environ.get("SCHEDULER_ENABLED", "1") == "1":
            start_scheduler()
        yield
    finally:
        stop_scheduler()
        await close_client()


app = FastAPI(title="Meow Eyes Marketplace", version="2.0-mysql57", lifespan=lifespan)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"app": "Meow Eyes", "version": "2.0-mysql57", "ok": True}


@api_router.get("/health")
async def health():
    result = await get_database().check_readiness()
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=200 if result.ready else 503, content={
        "ok": result.ready, "scheduler_running": scheduler.running,
        "database": "mysql", "database_target": "5.7.24-log", "reason": result.reason,
    })


@api_router.get("/health/live")
async def health_live():
    return {"ok": True, "database": "mysql", "mode": "application"}


@api_router.get("/health/ready")
async def health_ready():
    return await health()


@api_router.get("/admin/scheduler/status")
async def scheduler_status(admin: User = Depends(current_admin)):
    """Return currently registered jobs with their next-run timestamp (admin-only)."""
    jobs = []
    for j in scheduler.get_jobs():
        jobs.append({
            "id": j.id,
            "name": j.func_ref or j.name,
            "trigger": str(j.trigger),
            "next_run_time": j.next_run_time.isoformat() if getattr(j, "next_run_time", None) else None,
        })
    return {"running": scheduler.running, "jobs": jobs}


@api_router.post("/admin/scheduler/run/{job_id}")
async def scheduler_run_now(job_id: str, admin: User = Depends(current_admin)):
    """Trigger a scheduler job immediately (admin-only, useful for QA)."""
    from scheduler import (
        job_expire_pending_orders, job_activate_flash_sales,
        job_poll_shipments, job_auto_complete_orders,
        job_expire_meowsurement_photos,
    )
    from fastapi import HTTPException
    handlers = {
        "expire-pending-orders": job_expire_pending_orders,
        "activate-flash-sales": job_activate_flash_sales,
        "poll-shipments": job_poll_shipments,
        "auto-complete-orders": job_auto_complete_orders,
        "expire-meowsurement-photos": job_expire_meowsurement_photos,
    }
    fn = handlers.get(job_id)
    if not fn:
        raise HTTPException(400, f"Unknown job id: {job_id}")
    try:
        await fn()
    except Exception as e:
        logger.exception("scheduler_run_now failed")
        raise HTTPException(500, "Job execution failed; inspect the server log") from None
    return {"ok": True, "job": job_id}


# Mount sub-routers
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(shopping_router)
api_router.include_router(orders_router)
api_router.include_router(engagement_router)
from routes_loyalty import router as loyalty_router
from routes_returns import router as returns_router
api_router.include_router(loyalty_router)
api_router.include_router(returns_router)
api_router.include_router(admin_router)
api_router.include_router(export_router)
api_router.include_router(content_router)
api_router.include_router(admin_content_router)
api_router.include_router(uploads_router)
api_router.include_router(features_router)
api_router.include_router(integrations_router)
api_router.include_router(meowsurement_router)

app.include_router(api_router)

# Preserve public asset URLs but authorize visibility against relational
# metadata. A StaticFiles mount would bypass private-asset visibility entirely.
app.add_api_route("/api/uploads-files/{file_path:path}", public_upload_file,
                  methods=["GET", "HEAD"], include_in_schema=False,
                  name="uploads-files")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[v.strip() for v in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Consistent safe errors: never expose SQL, parameters, credentials or raw rows.
from sqlalchemy.exc import IntegrityError, DBAPIError  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    return JSONResponse(status_code=409, content={
        "detail": "Data duplikat atau masih digunakan oleh data lain", "code": "integrity_conflict"})


@app.exception_handler(DBAPIError)
async def database_error_handler(request, exc):
    code = (getattr(exc.orig, "args", ()) or (None,))[0]
    if code == 1644:
        return JSONResponse(status_code=422, content={
            "detail": "Data tidak memenuhi aturan integritas", "code": "validation_failed"})
    if code in (1205, 1213):
        return JSONResponse(status_code=409, headers={"Retry-After": "1"}, content={
            "detail": "Data sedang diproses. Silakan ulangi permintaan.", "code": "transaction_retry"})
    logger.error("Database request failed (%s)", type(exc).__name__)
    return JSONResponse(status_code=503, content={
        "detail": "Database sementara tidak tersedia", "code": "database_unavailable"})
