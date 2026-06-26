"""
Normalizer — standardises raw OHLCV DataFrames to a canonical schema.
"""

from __future__ import annotations

import pandas as pd


_COLUMN_ALIASES: dict[str, list[str]] = {
    "open": ["open", "Open", "1. open"],
    "high": ["high", "High", "2. high"],
    "low": ["low", "Low", "3. low"],
    "close": ["close", "Close", "4. close", "Adj Close", "5. adjusted close"],
    "volume": ["volume", "Volume", "6. volume"],
}


class Normalizer:
    """Normalises raw market data DataFrames to a consistent schema."""

    def normalise_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns, enforce dtypes, sort by date, and drop NaN rows.

        Args:
            df: Raw OHLCV DataFrame from any fetcher.

        Returns:
            Normalised DataFrame with columns [open, high, low, close, volume]
            and a DatetimeIndex named 'date'.
        """
        df = df.copy()

        # Normalise column names
        rename_map: dict[str, str] = {}
        for canonical, aliases in _COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in df.columns and alias != canonical:
                    rename_map[alias] = canonical
        df = df.rename(columns=rename_map)

        # Keep only OHLCV columns
        ohlcv_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        df = df[ohlcv_cols]

        # Enforce numeric dtype
        for col in ohlcv_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Ensure DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.index.name = "date"

        # Sort and drop NaN rows
        df = df.sort_index().dropna(how="all")

        return df
