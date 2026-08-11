# agents/market_data_agent.py

import requests
import yfinance as yf
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent, AgentResult, AgentError
from config.settings import settings
from database.connection import SessionLocal
from database.models import FundamentalsCache


PERIOD_TO_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 182,
    "1y": 365,
}

FUNDAMENTALS_CACHE_TTL_HOURS = 12

EMPTY_FUNDAMENTALS = {
    "market_cap": None, "pe_ratio": None, "forward_pe": None, "eps": None,
    "dividend_yield": None, "beta": None, "52w_high": None, "52w_low": None,
    "avg_volume": None, "sector": None, "industry": None, "country": None,
    "employees": None, "revenue": None, "profit_margin": None, "roe": None,
    "debt_to_equity": None, "current_ratio": None, "short_name": None, "exchange": None,
}


class MarketDataAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MarketDataAgent", max_retries=3)
        self.api_key = settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"

    def execute(self, symbol: str, period: str = "6mo", **kwargs) -> AgentResult:
        self.logger.info(f"Fetching market data for {symbol} | period={period}")

        if not self.api_key:
            raise AgentError("FINNHUB_API_KEY is not configured")

        # Price candles — Finnhub (reliable, own rate limit)
        price_data = self._fetch_candles(symbol, period)
        if not price_data:
            raise AgentError(f"No price data returned for {symbol}")

        # Fundamentals — yfinance, cached in SQLite, best-effort
        fundamentals = self._get_fundamentals_cached(symbol)

        latest = price_data[-1]
        snapshot = {
            "symbol": symbol,
            "date"  : latest["date"],
            "open"  : latest["open"],
            "high"  : latest["high"],
            "low"   : latest["low"],
            "close" : latest["close"],
            "volume": latest["volume"],
        }

        output_data = {
            "snapshot"      : snapshot,
            "fundamentals"  : fundamentals,
            "price_history" : price_data,
            "bars_fetched"  : len(price_data),
        }

        score = self._calculate_data_quality_score(fundamentals)

        self.logger.info(
            f"{symbol} | Close: {snapshot['close']} | "
            f"Bars: {len(price_data)} | Quality score: {score}"
        )

        return AgentResult(
            agent_name = self.name,
            success    = True,
            data       = output_data,
            score      = score,
            metadata   = {"symbol": symbol, "period": period}
        )

    # ---------- Price candles (Finnhub) ----------

    def _fetch_candles(self, symbol: str, period: str) -> list:
        days = PERIOD_TO_DAYS.get(period, 182)
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        resp = requests.get(
            f"{self.base_url}/stock/candle",
            params={
                "symbol": symbol,
                "resolution": "D",
                "from": int(start.timestamp()),
                "to": int(end.timestamp()),
                "token": self.api_key,
            },
            timeout=15,
        )

        if resp.status_code == 429:
            raise AgentError("Too Many Requests. Rate limited. Try after a while.")
        resp.raise_for_status()
        payload = resp.json()

        if payload.get("s") != "ok":
            return []

        records = []
        for t, o, h, l, c, v in zip(
            payload["t"], payload["o"], payload["h"], payload["l"], payload["c"], payload["v"]
        ):
            records.append({
                "date"  : datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                "open"  : round(float(o), 4),
                "high"  : round(float(h), 4),
                "low"   : round(float(l), 4),
                "close" : round(float(c), 4),
                "volume": int(v),
            })
        return records

    # ---------- Fundamentals (yfinance, cached in SQLite, best-effort) ----------

    def _get_fundamentals_cached(self, symbol: str) -> dict:
        db = SessionLocal()
        try:
            row = db.query(FundamentalsCache).filter_by(symbol=symbol).first()
            if row and row.updated_at > datetime.utcnow() - timedelta(hours=FUNDAMENTALS_CACHE_TTL_HOURS):
                self.logger.info(f"Fundamentals cache hit for {symbol}")
                return row.data

            fundamentals = self._fetch_fundamentals_yfinance(symbol)

            if fundamentals and any(v is not None for v in fundamentals.values()):
                if row:
                    row.data = fundamentals
                    row.updated_at = datetime.utcnow()
                else:
                    db.add(FundamentalsCache(
                        symbol=symbol,
                        data=fundamentals,
                        updated_at=datetime.utcnow(),
                    ))
                db.commit()
            elif row:
                # yfinance failed this time but we have a stale cache — better than nothing
                self.logger.info(f"Using stale fundamentals cache for {symbol}")
                return row.data

            return fundamentals
        except Exception as e:
            self.logger.warning(f"Fundamentals cache lookup failed for {symbol}: {e}")
            return self._fetch_fundamentals_yfinance(symbol)
        finally:
            db.close()

    def _fetch_fundamentals_yfinance(self, symbol: str) -> dict:
        try:
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            })
            ticker = yf.Ticker(symbol, session=session)
            info = ticker.info or {}

            if info.get("regularMarketPrice") is None and info.get("marketCap") is None:
                self.logger.warning(f"yfinance returned no usable fundamentals for {symbol}")
                return dict(EMPTY_FUNDAMENTALS)

            return {
                "market_cap"     : info.get("marketCap"),
                "pe_ratio"       : info.get("trailingPE"),
                "forward_pe"     : info.get("forwardPE"),
                "eps"            : info.get("trailingEps"),
                "dividend_yield" : info.get("dividendYield"),
                "beta"           : info.get("beta"),
                "52w_high"       : info.get("fiftyTwoWeekHigh"),
                "52w_low"        : info.get("fiftyTwoWeekLow"),
                "avg_volume"     : info.get("averageVolume"),
                "sector"         : info.get("sector"),
                "industry"       : info.get("industry"),
                "country"        : info.get("country"),
                "employees"      : info.get("fullTimeEmployees"),
                "revenue"        : info.get("totalRevenue"),
                "profit_margin"  : info.get("profitMargins"),
                "roe"            : info.get("returnOnEquity"),
                "debt_to_equity" : info.get("debtToEquity"),
                "current_ratio"  : info.get("currentRatio"),
                "short_name"     : info.get("shortName"),
                "exchange"       : info.get("exchange"),
            }
        except Exception as e:
            self.logger.warning(f"yfinance fundamentals fetch failed for {symbol}, continuing without them: {e}")
            return dict(EMPTY_FUNDAMENTALS)

    def _calculate_data_quality_score(self, fundamentals: dict) -> float:
        total_fields  = len(fundamentals)
        filled_fields = sum(1 for v in fundamentals.values() if v is not None)
        return round((filled_fields / total_fields) * 100, 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if not result.data:
            return False
        if result.data.get("bars_fetched", 0) == 0:
            return False
        return True