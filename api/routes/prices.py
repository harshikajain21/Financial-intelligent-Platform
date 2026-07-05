# api/routes/prices.py

from fastapi import APIRouter, HTTPException, Request
from api.limiter import limiter
from api.sanitizer import sanitize_symbol
import yfinance as yf
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("PricesRouter")

ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y"}


@router.get("/prices/{symbol}", summary="Get price history for a stock symbol")
@limiter.limit("20/minute")
async def get_prices(request: Request, symbol: str, period: str = "6mo"):
    symbol = sanitize_symbol(symbol)

    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period. Allowed: {ALLOWED_PERIODS}")

    try:
        logger.info(f"Fetching price history for {symbol}")
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

        hist = hist.reset_index()
        data = []
        for _, row in hist.iterrows():
            data.append({
                "date"  : str(row["Date"])[:10],
                "close" : round(float(row["Close"]), 2),
                "open"  : round(float(row["Open"]), 2),
                "high"  : round(float(row["High"]), 2),
                "low"   : round(float(row["Low"]), 2),
                "volume": int(row["Volume"]),
            })

        closes      = [d["close"] for d in data]
        start_price = closes[0] if closes else 0
        end_price   = closes[-1] if closes else 0
        change_pct  = round(((end_price - start_price) / start_price) * 100, 2) if start_price else 0

        return {
            "symbol"      : symbol,
            "period"      : period,
            "data"        : data,
            "current"     : end_price,
            "change_pct"  : change_pct,
            "period_high" : round(max(closes), 2) if closes else 0,
            "period_low"  : round(min(closes), 2) if closes else 0,
            "bars"        : len(data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price data. Please try again.")