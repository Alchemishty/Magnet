import logging
import os

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db import engine
from app.routes import (
    assets_router,
    briefs_router,
    jobs_router,
    projects_router,
    ws_router,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Magnet API", version="0.1.0")

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(briefs_router)
app.include_router(assets_router)
app.include_router(jobs_router)
app.include_router(ws_router)


def _check_db() -> str:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return "connected"


@app.get("/health")
async def health_check():
    try:
        db_status = await run_in_threadpool(_check_db)
    except Exception:
        logger.warning("Database health check failed")
        db_status = "unreachable"
    return {"status": "ok", "db": db_status}
