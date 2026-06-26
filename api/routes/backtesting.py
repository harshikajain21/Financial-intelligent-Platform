"""Backtesting API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backtesting.engine import BacktestEngine
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("BacktestRouter")


class BacktestRequest(BaseModel):
    ticker: str = Field(..., example="AAPL")
    strategy: str = Field(..., example="sma_crossover", description="Strategy identifier")
    start: str = Field(..., example="2020-01-01")
    end: str = Field(..., example="2023-01-01")
    initial_capital: float = Field(100_000.0, example=100000.0)
    params: dict[str, Any] = Field(default_factory=dict, description="Strategy-specific parameters")


@router.post("/run", summary="Run a backtest")
async def run_backtest(request: BacktestRequest) -> dict[str, Any]:
    """Execute a backtest for the given ticker and strategy."""
    engine = BacktestEngine()
    try:
        result = engine.run(
            ticker=request.ticker,
            strategy_name=request.strategy,
            start=request.start,
            end=request.end,
            initial_capital=request.initial_capital,
            strategy_params=request.params,
        )
        return {"status": "ok", "result": result}
    except Exception as exc:
        logger.error("Backtest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
