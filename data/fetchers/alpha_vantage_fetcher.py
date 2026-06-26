"""
Alpha Vantage Fetcher — retrieves OHLCV data from the Alpha Vantage API.
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests


class AlphaVantageFetcher:
    """Fetches OHLCV data from Alpha Vantage REST API."""

    _BASE_URL = "https://www.alphavantage.co/query"
    _INTERVAL_MAP = {
        "1d": ("TIME_SERIES_DAILY_ADJUSTED", "Time Series (Daily)"),
        "1wk": ("TIME_SERIES_WEEKLY_ADJUSTED", "Weekly Adjusted Time Series"),
        "1mo": ("TIME_SERIES_MONTHLY_ADJUSTED", "Monthly Adjusted Time Series"),
    }

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Alpha Vantage API key is required.")
        self.api_key = api_key

    def fetch(
        self,
        ticker: str,
        start: str,
        end: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Alpha Vantage.

        Args:
            ticker:   Ticker symbol.
            start:    ISO-8601 start date (used to filter response).
            end:      ISO-8601 end date.
            interval: "1d" | "1wk" | "1mo".

        Returns:
            OHLCV DataFrame with DatetimeIndex.
        """
        if interval not in self._INTERVAL_MAP:
            raise ValueError(f"Unsupported interval '{interval}'. Use 1d, 1wk, or 1mo.")

        function, series_key = self._INTERVAL_MAP[interval]

        params: dict[str, Any] = {
            "function": function,
            "symbol": ticker,
            "outputsize": "full",
            "apikey": self.api_key,
        }

        resp = requests.get(self._BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            raise RuntimeError(f"Alpha Vantage rate limit: {data['Note']}")

        series = data.get(series_key, {})
        if not series:
            raise ValueError(f"No data returned for {ticker}.")

        records = []
        for date_str, vals in series.items():
            records.append({
                "date": pd.Timestamp(date_str),
                "open": float(vals.get("1. open", vals.get("1. open", 0))),
                "high": float(vals.get("2. high", 0)),
                "low": float(vals.get("3. low", 0)),
                "close": float(vals.get("4. close", vals.get("5. adjusted close", 0))),
                "volume": float(vals.get("6. volume", vals.get("5. volume", 0))),
            })

        df = pd.DataFrame(records).set_index("date").sort_index()
        mask = (df.index >= pd.Timestamp(start)) & (df.index <= pd.Timestamp(end))
        return df.loc[mask]
