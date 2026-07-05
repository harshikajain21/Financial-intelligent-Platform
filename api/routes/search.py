# api/routes/search.py

from fastapi import APIRouter
from data.stock_universe import search_stocks, resolve_symbol

router = APIRouter()


@router.get("/search", summary="Search stocks by name or ticker")
async def search(query: str, limit: int = 8):
    if not query or len(query) < 2:
        return {"results": []}
    results = search_stocks(query, limit)
    return {"results": results}


@router.get("/resolve", summary="Resolve company name to ticker symbol")
async def resolve(query: str, exchange: str = "NSE"):
    symbol = resolve_symbol(query, exchange)
    return {"symbol": symbol, "exchange": exchange}