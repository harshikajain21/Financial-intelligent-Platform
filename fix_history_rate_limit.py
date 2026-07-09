# fix_history_rate_limit.py

content = """
# api/routes/history.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from api.limiter import limiter
from database.connection import get_db
from database.repository import AnalysisRepository, WatchlistRepository
from typing import Optional
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("HistoryRouter")


@router.get("/history/{symbol}", summary="Get analysis history for a symbol")
@limiter.limit("30/minute")
async def get_history(request: Request, symbol: str, limit: int = 10, db: Session = Depends(get_db)):
    symbol = symbol.upper().strip()
    if limit > 50:
        limit = 50
    records = AnalysisRepository.get_history(db, symbol, limit)
    if not records:
        raise HTTPException(status_code=404, detail=f"No history found for {symbol}")
    return {"symbol": symbol, "count": len(records), "history": [r.to_dict() for r in records]}


@router.get("/history/{symbol}/latest", summary="Get latest analysis for a symbol")
@limiter.limit("30/minute")
async def get_latest(request: Request, symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper().strip()
    record = AnalysisRepository.get_latest(db, symbol)
    if not record:
        raise HTTPException(status_code=404, detail=f"No analysis found for {symbol}")
    return record.to_dict()


@router.get("/dashboard", summary="Get latest analysis for all tracked symbols")
@limiter.limit("30/minute")
async def get_dashboard(request: Request, db: Session = Depends(get_db)):
    records = AnalysisRepository.get_all_latest(db, limit=20)
    return {"count": len(records), "results": [r.to_dict() for r in records]}


@router.post("/watchlist/{symbol}", summary="Add symbol to watchlist")
@limiter.limit("20/minute")
async def add_to_watchlist(request: Request, symbol: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    symbol = symbol.upper().strip()
    if not symbol.isalpha() and '.' not in symbol:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    record = WatchlistRepository.add_symbol(db, symbol, notes)
    return {"message": f"{symbol} added to watchlist", "data": record.to_dict()}


@router.get("/watchlist", summary="Get your watchlist")
@limiter.limit("30/minute")
async def get_watchlist(request: Request, db: Session = Depends(get_db)):
    records = WatchlistRepository.get_watchlist(db)
    return {"count": len(records), "watchlist": [r.to_dict() for r in records]}


@router.delete("/watchlist/{symbol}", summary="Remove symbol from watchlist")
@limiter.limit("20/minute")
async def remove_from_watchlist(request: Request, symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper().strip()
    removed = WatchlistRepository.remove_symbol(db, symbol)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{symbol} not in watchlist")
    return {"message": f"{symbol} removed from watchlist"}
"""

with open("api/routes/history.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("api/routes/history.py updated with rate limiting")