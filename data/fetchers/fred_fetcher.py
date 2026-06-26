"""
FRED Fetcher — retrieves macroeconomic time series from the Federal Reserve (FRED).

Requires a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
"""

from __future__ import annotations

from typing import Any

import requests


class FREDFetcher:
    """Fetches economic data series from the FRED API."""

    _BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("FRED API key is required.")
        self.api_key = api_key

    def fetch_series(
        self,
        series_id: str,
        observation_start: str = "2000-01-01",
        observation_end: str | None = None,
        frequency: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch observations for a FRED series.

        Args:
            series_id:         FRED series identifier (e.g. "CPIAUCSL").
            observation_start: ISO-8601 start date.
            observation_end:   ISO-8601 end date. None → latest.
            frequency:         Optional aggregation frequency code (e.g. "m", "q", "a").

        Returns:
            List of {"date": str, "value": str} observation dicts.
        """
        params: dict[str, Any] = {
            "series_id": series_id,
            "observation_start": observation_start,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if observation_end:
            params["observation_end"] = observation_end
        if frequency:
            params["frequency"] = frequency

        resp = requests.get(self._BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        if "error_message" in data:
            raise ValueError(f"FRED API error: {data['error_message']}")

        return [
            {"date": obs["date"], "value": obs["value"]}
            for obs in data.get("observations", [])
            if obs["value"] != "."
        ]
