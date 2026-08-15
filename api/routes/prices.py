# api/routes/prices.py

from fastapi import APIRouter, HTTPException, Request
from api.limiter import limiter
from api.sanitizer import sanitize_symbol
from config.settings import settings
from utils.logger import get_logger
import requests

router = APIRouter()
logger = get_logger("PricesRouter")

ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y"}

PERIOD_TO_OUTPUTSIZE = {
    "1mo": 25,
    "3mo": 70,
    "6mo": 140,
    "1y": 280,
    "2y": 560,
}

BASE_URL = "https://api.twelvedata.com"


@router.get("/prices/{symbol}", summary="Get price history for a stock symbol")
@limiter.limit("20/minute")
async def get_prices(request: Request, symbol: str, period: str = "6mo"):
    symbol = sanitize_symbol(symbol)
    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period. Allowed: {ALLOWED_PERIODS}")

    if not settings.TWELVE_DATA_API_KEY:
        raise HTTPException(status_code=500, detail="Price data provider not configured.")

    try:
        logger.info(f"Fetching price history for {symbol}")

        outputsize = PERIOD_TO_OUTPUTSIZE.get(period, 140)
        resp = requests.get(
            f"{BASE_URL}/time_series",
            params={
                "symbol": symbol,
                "interval": "1day",
                "outputsize": outputsize,
                "order": "ASC",
                "apikey": settings.TWELVE_DATA_API_KEY,
            },
            timeout=15,
        )

        if resp.status_code == 429:
            raise HTTPException(status_code=503, detail="Price data provider rate limited. Try again shortly.")
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("status") == "error" or payload.get("code"):
            msg = payload.get("message", "Unknown Twelve Data error")
            if payload.get("code") == 429:
                raise HTTPException(status_code=503, detail="Price data provider rate limited. Try again shortly.")
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}: {msg}")

        values = payload.get("values")
        if not values:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

        data = []
        for row in values:
            try:
                data.append({
                    "date"  : row["datetime"][:10],
                    "open"  : round(float(row["open"]), 2),
                    "high"  : round(float(row["high"]), 2),
                    "low"   : round(float(row["low"]), 2),
                    "close" : round(float(row["close"]), 2),
                    "volume": int(float(row.get("volume") or 0)),
                })
            except (KeyError, ValueError, TypeError):
                continue

        data.sort(key=lambda d: d["date"])

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
        raise HTTPException(status_code=500, detail="Failed to fetch price data.")