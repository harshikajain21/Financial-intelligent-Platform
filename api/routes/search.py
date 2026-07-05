# api/routes/search.py

from fastapi import APIRouter, Request
from api.limiter import limiter
from api.sanitizer import sanitize_query
from data.stock_universe import search_stocks, resolve_symbol

router = APIRouter()


@router.get("/search", summary="Search stocks by name or ticker")
@limiter.limit("30/minute")
async def search(request: Request, query: str, limit: int = 8):
    query = sanitize_query(query)
    if not query or len(query) < 2:
        return {"results": []}
    if limit > 20:
        limit = 20
    results = search_stocks(query, limit)
    return {"results": results}


@router.get("/resolve", summary="Resolve company name to ticker symbol")
@limiter.limit("30/minute")
async def resolve(request: Request, query: str, exchange: str = "NSE"):
    query    = sanitize_query(query)
    symbol   = resolve_symbol(query, exchange)
    return {"symbol": symbol, "exchange": exchange}