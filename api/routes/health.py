"""Health check routes."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/", summary="Health check")
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready", summary="Readiness check")
async def readiness_check() -> dict:
    """Readiness probe — verifies database connectivity."""
    try:
        from database.connection import get_db_connection
        engine = get_db_connection()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ready" if db_ok else "degraded",
        "database": "ok" if db_ok else "unavailable",
        "timestamp": datetime.utcnow().isoformat(),
    }
