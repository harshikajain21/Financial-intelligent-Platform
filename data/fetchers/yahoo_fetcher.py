"""
Yahoo Finance Fetcher — retrieves OHLCV data from Yahoo Finance via yfinance.
"""

from __future__ import annotations

import pandas as pd


class YahooFetcher:
    """Fetches OHLCV price data from Yahoo Finance."""

    def fetch(
        self,
        ticker: str,
        start: str,
        end: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Download historical OHLCV data for a single ticker.

        Args:
            ticker:   Stock ticker symbol.
            start:    ISO-8601 start date string.
            end:      ISO-8601 end date string.
            interval: Data frequency ("1d", "1wk", "1mo").

        Returns:
            DataFrame with columns [open, high, low, close, volume].
        """
        try:
            import yfinance as yf  # type: ignore
        except ImportError as exc:
            raise ImportError("yfinance not installed. Run: pip install yfinance") from exc

        raw = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        if raw.empty:
            raise ValueError(f"No data returned for ticker '{ticker}'.")

        # Normalise column names to lowercase
        raw.columns = [c.lower() for c in raw.columns]
        return raw
