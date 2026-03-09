import logging

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from app.db import engine

logger = logging.getLogger(__name__)

app = FastAPI(title="Magnet API", version="0.1.0")


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
