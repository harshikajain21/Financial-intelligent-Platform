"""
Fundamental Agent — analyses company fundamentals from financial statements.

Data sourced from:
  - Yahoo Finance (yfinance) for income statement, balance sheet, cash flow
  - Computed derived metrics: P/E, P/B, EV/EBITDA, DCF estimate, etc.
"""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent, AgentError


class FundamentalAgent(BaseAgent):
    """Retrieves and scores fundamental financial metrics for a given ticker."""

    agent_name = "FundamentalAgent"

    # Sector-adjusted fair P/E benchmarks (simplified)
    _SECTOR_PE = {
        "Technology": 30,
        "Healthcare": 25,
        "Financials": 15,
        "Energy": 12,
        "Utilities": 18,
        "Consumer Discretionary": 22,
        "default": 20,
    }

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(self, ticker: str) -> dict[str, Any]:
        """Fetch and analyse fundamental data for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g. "AAPL").

        Returns:
            Dict with financial statements, key ratios, and a valuation score.
        """
        try:
            import yfinance as yf  # type: ignore
        except ImportError as exc:
            raise AgentError("yfinance not installed. Run: pip install yfinance") from exc

        self.logger.info("Fetching fundamentals for %s.", ticker)
        stock = yf.Ticker(ticker)

        try:
            info = stock.info
            income_stmt = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
        except Exception as exc:  # noqa: BLE001
            raise AgentError(f"Failed to retrieve data for {ticker}: {exc}") from exc

        ratios = self._compute_ratios(info)
        dcf = self._simple_dcf(info, cash_flow)
        score = self._valuation_score(ratios, info.get("sector", "default"))

        return {
            "ticker": ticker,
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "ratios": ratios,
            "dcf_estimate": dcf,
            "valuation_score": score,
            "income_statement": income_stmt.to_dict() if income_stmt is not None else {},
            "balance_sheet": balance_sheet.to_dict() if balance_sheet is not None else {},
            "cash_flow": cash_flow.to_dict() if cash_flow is not None else {},
        }

    # ------------------------------------------------------------------
    # Ratio computation
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_ratios(info: dict[str, Any]) -> dict[str, Any]:
        return {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "ps_ratio": info.get("priceToSalesTrailing12Months"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "dividend_yield": info.get("dividendYield"),
            "peg_ratio": info.get("pegRatio"),
            "beta": info.get("beta"),
        }

    @staticmethod
    def _simple_dcf(info: dict[str, Any], cash_flow: Any) -> dict[str, Any] | None:
        """Simplified two-stage DCF using free cash flow."""
        try:
            import pandas as pd  # noqa: F401

            fcf_series = cash_flow.loc["Free Cash Flow"] if "Free Cash Flow" in cash_flow.index else None
            if fcf_series is None or fcf_series.empty:
                return None

            latest_fcf = float(fcf_series.iloc[0])
            shares = info.get("sharesOutstanding", 1)
            wacc = 0.10
            g_high = 0.15
            g_terminal = 0.03
            years_high = 5

            pv = 0.0
            for yr in range(1, years_high + 1):
                pv += latest_fcf * (1 + g_high) ** yr / (1 + wacc) ** yr

            terminal_value = (
                latest_fcf * (1 + g_high) ** years_high * (1 + g_terminal)
                / (wacc - g_terminal)
            )
            pv += terminal_value / (1 + wacc) ** years_high

            intrinsic_per_share = pv / shares if shares else None
            return {
                "intrinsic_value_per_share": round(intrinsic_per_share, 2) if intrinsic_per_share else None,
                "assumptions": {
                    "wacc": wacc,
                    "growth_rate_high": g_high,
                    "terminal_growth": g_terminal,
                },
            }
        except Exception:  # noqa: BLE001
            return None

    def _valuation_score(self, ratios: dict[str, Any], sector: str) -> dict[str, Any]:
        """Score -10 (very overvalued) to +10 (very undervalued)."""
        fair_pe = self._SECTOR_PE.get(sector, self._SECTOR_PE["default"])
        score = 0
        reasons = []

        pe = ratios.get("pe_ratio")
        if pe and pe > 0:
            if pe < fair_pe * 0.8:
                score += 2
                reasons.append("P/E below sector fair value")
            elif pe > fair_pe * 1.5:
                score -= 2
                reasons.append("P/E significantly above sector fair value")

        roe = ratios.get("roe")
        if roe and roe > 0.15:
            score += 1
            reasons.append("Strong ROE (>15%)")

        debt_eq = ratios.get("debt_to_equity")
        if debt_eq is not None:
            if debt_eq < 0.5:
                score += 1
                reasons.append("Low leverage")
            elif debt_eq > 2.0:
                score -= 1
                reasons.append("High leverage risk")

        return {"score": score, "interpretation": reasons}
