"""
Macro Agent — monitors macroeconomic indicators via FRED and other sources.

Key data series fetched:
  - GDP growth rate
  - CPI / Core CPI (inflation)
  - Unemployment rate
  - Federal Funds Rate
  - 10-Year Treasury Yield
  - PMI (manufacturing & services)
  - Consumer Confidence Index
"""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent, AgentError
from data.fetchers.fred_fetcher import FREDFetcher


# FRED series IDs
_SERIES = {
    "gdp_growth": "A191RL1Q225SBEA",
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "unemployment": "UNRATE",
    "fed_funds_rate": "FEDFUNDS",
    "treasury_10y": "GS10",
    "pmi_manufacturing": "MANEMP",
    "consumer_confidence": "UMCSENT",
}


class MacroAgent(BaseAgent):
    """Fetches and interprets macroeconomic indicator data."""

    agent_name = "MacroAgent"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._fetcher = FREDFetcher(api_key=self.settings.fred_api_key)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(
        self,
        series_ids: list[str] | None = None,
        observation_start: str = "2020-01-01",
        observation_end: str | None = None,
    ) -> dict[str, Any]:
        """Fetch macroeconomic series from FRED.

        Args:
            series_ids:        Subset of keys from the internal _SERIES map.
                               None → fetch all.
            observation_start: ISO-8601 start date.
            observation_end:   ISO-8601 end date. None → latest available.

        Returns:
            Dict mapping series key → list of {date, value} observations,
            plus a brief macro interpretation summary.
        """
        target = {k: v for k, v in _SERIES.items() if series_ids is None or k in (series_ids or [])}

        self.logger.info(
            "Fetching %d FRED series from %s.", len(target), observation_start
        )

        data: dict[str, Any] = {}
        errors: dict[str, str] = {}

        for key, series_id in target.items():
            try:
                observations = self._fetcher.fetch_series(
                    series_id,
                    observation_start=observation_start,
                    observation_end=observation_end,
                )
                data[key] = observations
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to fetch %s (%s): %s", key, series_id, exc)
                errors[key] = str(exc)

        if not data:
            raise AgentError(f"All FRED series failed: {errors}")

        return {
            "series": data,
            "errors": errors,
            "interpretation": self._interpret(data),
        }

    # ------------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------------

    @staticmethod
    def _interpret(data: dict[str, Any]) -> dict[str, str]:
        """Generate simple textual interpretation of latest values."""
        interpretations: dict[str, str] = {}

        if "fed_funds_rate" in data and data["fed_funds_rate"]:
            rate = data["fed_funds_rate"][-1]["value"]
            interpretations["fed_funds_rate"] = (
                "Restrictive monetary policy" if float(rate) > 4.0 else "Accommodative monetary policy"
            )

        if "unemployment" in data and data["unemployment"]:
            unemp = float(data["unemployment"][-1]["value"])
            interpretations["unemployment"] = (
                "Tight labor market" if unemp < 4.5 else "Slack in labor market"
            )

        if "cpi" in data and len(data["cpi"]) >= 13:
            # YoY inflation proxy
            latest = float(data["cpi"][-1]["value"])
            year_ago = float(data["cpi"][-13]["value"])
            yoy = (latest - year_ago) / year_ago * 100
            interpretations["inflation_yoy"] = f"{yoy:.2f}% YoY — {'elevated' if yoy > 3 else 'moderate'}"

        return interpretations
