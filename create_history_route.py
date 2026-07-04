# create_history_route.py

content = '''# api/routes/history.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.repository import AnalysisRepository, WatchlistRepository
from typing import List, Optional
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("HistoryRouter")


@router.get(
    "/history/{symbol}",
    summary="Get analysis history for a symbol"
)
async def get_history(
    symbol: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Returns last N analyses for a symbol."""
    symbol = symbol.upper().strip()
    records = AnalysisRepository.get_history(db, symbol, limit)
    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No history found for {symbol}"
        )
    return {
        "symbol"  : symbol,
        "count"   : len(records),
        "history" : [r.to_dict() for r in records]
    }


@router.get(
    "/history/{symbol}/latest",
    summary="Get latest analysis for a symbol"
)
async def get_latest(symbol: str, db: Session = Depends(get_db)):
    """Returns the most recent analysis for a symbol."""
    symbol = symbol.upper().strip()
    record = AnalysisRepository.get_latest(db, symbol)
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for {symbol}"
        )
    return record.to_dict()


@router.get(
    "/dashboard",
    summary="Get latest analysis for all tracked symbols"
)
async def get_dashboard(db: Session = Depends(get_db)):
    """Returns recent analyses for dashboard overview."""
    records = AnalysisRepository.get_all_latest(db, limit=20)
    return {
        "count"   : len(records),
        "results" : [r.to_dict() for r in records]
    }


@router.post(
    "/watchlist/{symbol}",
    summary="Add symbol to watchlist"
)
async def add_to_watchlist(
    symbol: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Add a stock symbol to your watchlist."""
    symbol = symbol.upper().strip()
    if not symbol.isalpha():
        raise HTTPException(status_code=400, detail="Invalid symbol")
    record = WatchlistRepository.add_symbol(db, symbol, notes)
    return {"message": f"{symbol} added to watchlist", "data": record.to_dict()}


@router.get(
    "/watchlist",
    summary="Get your watchlist"
)
async def get_watchlist(db: Session = Depends(get_db)):
    """Returns all symbols in your watchlist."""
    records = WatchlistRepository.get_watchlist(db)
    return {
        "count"     : len(records),
        "watchlist" : [r.to_dict() for r in records]
    }


@router.delete(
    "/watchlist/{symbol}",
    summary="Remove symbol from watchlist"
)
async def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    """Remove a symbol from your watchlist."""
    symbol = symbol.upper().strip()
    removed = WatchlistRepository.remove_symbol(db, symbol)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{symbol} not in watchlist")
    return {"message": f"{symbol} removed from watchlist"}
'''

with open("api/routes/history.py", "w") as f:
    f.write(content)
    print("api/routes/history.py written")