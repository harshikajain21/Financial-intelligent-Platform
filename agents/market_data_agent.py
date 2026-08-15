# agents/market_data_agent.py

import requests
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent, AgentResult, AgentError
from config.settings import settings


PERIOD_TO_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 182,
    "1y": 365,
}

# Twelve Data "outputsize" is a row count, not a date range — approximate
# trading days (roughly 5/7 of calendar days) with a small buffer.
PERIOD_TO_OUTPUTSIZE = {
    "1mo": 25,
    "3mo": 70,
    "6mo": 140,
    "1y": 280,
}


class MarketDataAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MarketDataAgent", max_retries=3)
        self.api_key = settings.TWELVE_DATA_API_KEY
        self.base_url = "https://api.twelvedata.com"

    def execute(self, symbol: str, period: str = "6mo", **kwargs) -> AgentResult:
        self.logger.info(f"Fetching market data for {symbol} | period={period}")

        if not self.api_key:
            raise AgentError("TWELVE_DATA_API_KEY is not configured")

        price_data = self._fetch_candles(symbol, period)
        if not price_data:
            raise AgentError(f"No price data returned for {symbol}")

        fundamentals = self._fetch_fundamentals(symbol)

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

    # ---------- Price candles (Twelve Data) ----------

    def _fetch_candles(self, symbol: str, period: str) -> list:
        outputsize = PERIOD_TO_OUTPUTSIZE.get(period, 140)

        resp = requests.get(
            f"{self.base_url}/time_series",
            params={
                "symbol": symbol,
                "interval": "1day",
                "outputsize": outputsize,
                "order": "ASC",          # oldest first, matches your old contract
                "apikey": self.api_key,
            },
            timeout=15,
        )

        if resp.status_code == 429:
            raise AgentError("Too Many Requests. Rate limited. Try after a while.")
        resp.raise_for_status()
        payload = resp.json()

        # Twelve Data returns HTTP 200 even on logical errors — check "status"/"code"
        if payload.get("status") == "error" or payload.get("code"):
            msg = payload.get("message", "Unknown Twelve Data error")
            if payload.get("code") == 429:
                raise AgentError("Too Many Requests. Rate limited. Try after a while.")
            raise AgentError(f"Twelve Data error for {symbol}: {msg}")

        values = payload.get("values")
        if not values:
            return []

        records = []
        for row in values:
            try:
                records.append({
                    "date"  : row["datetime"][:10],
                    "open"  : round(float(row["open"]), 4),
                    "high"  : round(float(row["high"]), 4),
                    "low"   : round(float(row["low"]), 4),
                    "close" : round(float(row["close"]), 4),
                    "volume": int(float(row.get("volume") or 0)),
                })
            except (KeyError, ValueError, TypeError):
                continue

        # Twelve Data honors "order" param, but sort defensively anyway
        records.sort(key=lambda r: r["date"])
        return records

    # ---------- Fundamentals snapshot (best-effort, Twelve Data) ----------
    # Deep fundamentals (ROE, D/E, PEG, growth) live in FundamentalAnalysisAgent
    # via FMP now. This is just a lightweight quote-level snapshot.

    def _fetch_fundamentals(self, symbol: str) -> dict:
        fundamentals = {
            "market_cap": None, "52w_high": None, "52w_low": None,
            "avg_volume": None, "exchange": None, "short_name": None,
            "currency": None,
        }
        try:
            resp = requests.get(
                f"{self.base_url}/quote",
                params={"symbol": symbol, "apikey": self.api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") == "error" or data.get("code"):
                self.logger.warning(f"Twelve Data quote failed for {symbol}: {data.get('message')}")
                return fundamentals

            fundamentals.update({
                "market_cap": self._to_float(data.get("market_cap") or data.get("marketCap")),
                "52w_high"  : self._to_float(data.get("fifty_two_week", {}).get("high") if isinstance(data.get("fifty_two_week"), dict) else None),
                "52w_low"   : self._to_float(data.get("fifty_two_week", {}).get("low") if isinstance(data.get("fifty_two_week"), dict) else None),
                "avg_volume": self._to_float(data.get("average_volume")),
                "exchange"  : data.get("exchange"),
                "short_name": data.get("name"),
                "currency"  : data.get("currency"),
            })
        except Exception as e:
            self.logger.warning(f"Twelve Data quote fetch failed for {symbol}, continuing without it: {e}")

        return fundamentals

    @staticmethod
    def _to_float(value):
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None

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