# fix_yfinance_docker.py

content = """
# agents/market_data_agent.py

import yfinance as yf
import pandas as pd
import requests
from agents.base_agent import BaseAgent, AgentResult, AgentError


# Fix for Docker environments — Yahoo Finance blocks default user agent
yf.utils.requests.Session = lambda: requests.Session()


class MarketDataAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MarketDataAgent", max_retries=3)

    def execute(self, symbol: str, period: str = "6mo", **kwargs) -> AgentResult:
        self.logger.info(f"Fetching market data for {symbol} | period={period}")

        # Create session with browser-like headers
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        ticker = yf.Ticker(symbol, session=session)
        hist = ticker.history(period=period)

        if hist.empty:
            raise AgentError(f"No price data returned for {symbol}")

        hist = hist.reset_index()
        hist.columns = [c.lower() for c in hist.columns]
        price_data = hist[["date", "open", "high", "low", "close", "volume"]].copy()
        price_data["date"] = price_data["date"].astype(str)

        info = ticker.info
        fundamentals = self._extract_fundamentals(info)

        latest = price_data.iloc[-1]
        snapshot = {
            "symbol" : symbol,
            "date"   : str(latest["date"]),
            "open"   : round(float(latest["open"]), 4),
            "high"   : round(float(latest["high"]), 4),
            "low"    : round(float(latest["low"]), 4),
            "close"  : round(float(latest["close"]), 4),
            "volume" : int(latest["volume"]),
        }

        output_data = {
            "snapshot"      : snapshot,
            "fundamentals"  : fundamentals,
            "price_history" : price_data.to_dict(orient="records"),
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

    def _extract_fundamentals(self, info: dict) -> dict:
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
"""

with open("agents/market_data_agent.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("agents/market_data_agent.py updated with Docker-compatible session")