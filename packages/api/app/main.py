import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine

logger = logging.getLogger(__name__)

app = FastAPI(title="Magnet API", version="0.1.0")


@app.get("/health")
async def health_check():
    db_status = "unreachable"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        logger.warning("Database health check failed")
    return {"status": "ok", "db": db_status}
