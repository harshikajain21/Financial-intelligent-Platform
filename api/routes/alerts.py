"""Alerts API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from alerts.dispatcher import AlertDispatcher
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("AlertsRouter")
_dispatcher = AlertDispatcher()


@router.get("/", summary="List recent alerts")
async def list_alerts(limit: int = 50) -> dict[str, Any]:
    """Return the most recent N alerts from the database."""
    try:
        return {"alerts": _dispatcher.get_recent_alerts(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/{alert_id}", summary="Dismiss an alert")
async def dismiss_alert(alert_id: int) -> dict[str, Any]:
    """Mark an alert as dismissed."""
    try:
        _dispatcher.dismiss(alert_id)
        return {"status": "dismissed", "alert_id": alert_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
