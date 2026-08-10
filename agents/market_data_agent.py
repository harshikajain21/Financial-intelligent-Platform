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


class MarketDataAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MarketDataAgent", max_retries=3)
        self.api_key = settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"

    def execute(self, symbol: str, period: str = "6mo", **kwargs) -> AgentResult:
        self.logger.info(f"Fetching market data for {symbol} | period={period}")

        if not self.api_key:
            raise AgentError("FINNHUB_API_KEY is not configured")

        price_data = self._fetch_candles(symbol, period)
        if not price_data:
            raise AgentError(f"No price data returned for {symbol}")

        profile = self._fetch_company_profile(symbol)
        quote = self._fetch_quote(symbol)
        fundamentals = self._extract_fundamentals(profile, quote)

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

    def _fetch_company_profile(self, symbol: str) -> dict:
        try:
            resp = requests.get(
                f"{self.base_url}/stock/profile2",
                params={"symbol": symbol, "token": self.api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json() or {}
        except Exception:
            return {}

    def _fetch_quote(self, symbol: str) -> dict:
        try:
            resp = requests.get(
                f"{self.base_url}/quote",
                params={"symbol": symbol, "token": self.api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json() or {}
        except Exception:
            return {}

    def _extract_fundamentals(self, profile: dict, quote: dict) -> dict:
        return {
            "market_cap"     : profile.get("marketCapitalization"),
            "pe_ratio"       : None,   # not in free tier basic endpoints
            "forward_pe"     : None,
            "eps"            : None,
            "dividend_yield" : None,
            "beta"           : None,
            "52w_high"       : quote.get("h"),
            "52w_low"        : quote.get("l"),
            "avg_volume"     : None,
            "sector"         : profile.get("finnhubIndustry"),
            "industry"       : profile.get("finnhubIndustry"),
            "country"        : profile.get("country"),
            "employees"      : None,
            "revenue"        : None,
            "profit_margin"  : None,
            "roe"            : None,
            "debt_to_equity" : None,
            "current_ratio"  : None,
            "short_name"     : profile.get("name"),
            "exchange"       : profile.get("exchange"),
        }

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