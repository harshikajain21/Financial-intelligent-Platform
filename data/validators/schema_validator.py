"""
Schema Validator — validates DataFrames and dicts against expected schemas.
"""

from __future__ import annotations

import pandas as pd


class SchemaValidator:
    """Validates data structures against predefined schemas."""

    _OHLCV_REQUIRED = {"open", "high", "low", "close", "volume"}

    def validate_ohlcv(self, df: pd.DataFrame) -> None:
        """Assert that a DataFrame conforms to the OHLCV schema.

        Args:
            df: DataFrame to validate.

        Raises:
            ValueError: If required columns are missing or data is empty.
        """
        if df is None or df.empty:
            raise ValueError("OHLCV DataFrame is empty or None.")

        cols = {c.lower() for c in df.columns}
        missing = self._OHLCV_REQUIRED - cols
        if missing:
            raise ValueError(f"OHLCV DataFrame missing required columns: {missing}")

        # Check for at least one non-NaN row
        numeric_cols = list(self._OHLCV_REQUIRED & cols)
        if df[numeric_cols].dropna(how="all").empty:
            raise ValueError("OHLCV DataFrame contains no valid (non-NaN) rows.")

    def validate_returns(self, series: pd.Series) -> None:
        """Assert a return series is valid.

        Args:
            series: Pandas Series of returns.

        Raises:
            ValueError: If empty, all-NaN, or non-numeric.
        """
        if series is None or series.empty:
            raise ValueError("Returns series is empty or None.")

        if series.isna().all():
            raise ValueError("Returns series contains only NaN values.")

        if not pd.api.types.is_numeric_dtype(series):
            raise ValueError("Returns series must be numeric.")

    def validate_dict_keys(self, data: dict, required_keys: set[str], name: str = "dict") -> None:
        """Assert that a dictionary contains required keys.

        Args:
            data:          Dictionary to validate.
            required_keys: Set of required key names.
            name:          Human-readable name for error messages.

        Raises:
            ValueError: If any required keys are missing.
        """
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(f"{name} is missing required keys: {missing}")
