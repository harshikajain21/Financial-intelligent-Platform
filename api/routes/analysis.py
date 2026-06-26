"""
Analysis routes — triggers the full financial analysis pipeline.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from orchestrator.master_orchestrator import MasterOrchestrator
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("AnalysisRouter")
_orchestrator = MasterOrchestrator()


class AnalysisRequest(BaseModel):
    tickers: list[str] = Field(..., example=["AAPL", "MSFT"], min_items=1)
    start: str = Field(..., example="2023-01-01", description="ISO-8601 start date")
    end: str = Field(..., example="2024-01-01", description="ISO-8601 end date")
    interval: str = Field("1d", example="1d", description="Price interval: 1d | 1wk | 1mo")


class AnalysisResponse(BaseModel):
    status: str
    tickers: list[str]
    result: dict[str, Any]


@router.post("/run", response_model=AnalysisResponse, summary="Run full financial analysis")
async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """Execute the complete multi-agent financial analysis pipeline.

    Returns a comprehensive report covering market data, sentiment,
    technical indicators, risk metrics, forecasts, and recommendations.
    """
    logger.info("Analysis request: tickers=%s start=%s end=%s", request.tickers, request.start, request.end)
    try:
        result = _orchestrator.analyse(
            tickers=request.tickers,
            start=request.start,
            end=request.end,
            interval=request.interval,
        )
        return AnalysisResponse(status="ok", tickers=request.tickers, result=result)
    except Exception as exc:
        logger.error("Analysis failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/recommendation/{ticker}", summary="Get recommendation for a single ticker")
async def get_recommendation(ticker: str) -> dict[str, Any]:
    """Quick recommendation endpoint — runs the full pipeline for a single ticker
    with default date range (last 1 year)."""
    import datetime

    end = datetime.date.today().isoformat()
    start = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()

    try:
        result = _orchestrator.analyse(tickers=[ticker], start=start, end=end)
        fusion = result.get("fusion", {}).get(ticker, {})
        return {
            "ticker": ticker,
            "recommendation": fusion.get("recommendation"),
            "confidence": fusion.get("confidence"),
            "composite_score": fusion.get("composite_score"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
