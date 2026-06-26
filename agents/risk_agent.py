"""
Risk Agent — quantifies portfolio and position risk.

Metrics computed:
  - Value at Risk (VaR): historical, parametric, Monte Carlo
  - Conditional VaR (CVaR / Expected Shortfall)
  - Maximum Drawdown
  - Sharpe, Sortino, Calmar ratios
  - Beta vs. benchmark
  - Volatility (rolling & realised)
  - Correlation matrix
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from agents.base_agent import BaseAgent, AgentError


class RiskAgent(BaseAgent):
    """Computes comprehensive risk metrics for a portfolio or single asset."""

    agent_name = "RiskAgent"

    _TRADING_DAYS = 252

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(
        self,
        returns: pd.DataFrame | pd.Series,
        benchmark_returns: pd.Series | None = None,
        confidence_level: float = 0.95,
        risk_free_rate: float = 0.05,
    ) -> dict[str, Any]:
        """Compute risk metrics.

        Args:
            returns:           Daily return series / DataFrame (one column per asset).
            benchmark_returns: Benchmark returns for beta calculation.
            confidence_level:  VaR / CVaR confidence (e.g. 0.95 → 95%).
            risk_free_rate:    Annual risk-free rate for ratio calculations.

        Returns:
            Nested dict of risk metrics.
        """
        if isinstance(returns, pd.Series):
            returns = returns.to_frame(name=returns.name or "portfolio")

        if returns.empty:
            raise AgentError("Returns DataFrame is empty.")

        results: dict[str, Any] = {}

        for col in returns.columns:
            r = returns[col].dropna()
            results[col] = {
                "var": self._var(r, confidence_level),
                "cvar": self._cvar(r, confidence_level),
                "max_drawdown": self._max_drawdown(r),
                "sharpe": self._sharpe(r, risk_free_rate),
                "sortino": self._sortino(r, risk_free_rate),
                "annualised_volatility": self._annualised_vol(r),
                "skewness": float(r.skew()),
                "kurtosis": float(r.kurtosis()),
                "beta": (
                    self._beta(r, benchmark_returns)
                    if benchmark_returns is not None
                    else None
                ),
                "monte_carlo_var": self._monte_carlo_var(r, confidence_level),
            }

        corr = returns.corr().to_dict() if returns.shape[1] > 1 else {}
        return {"per_asset": results, "correlation_matrix": corr}

    # ------------------------------------------------------------------
    # Metric implementations
    # ------------------------------------------------------------------

    def _var(self, returns: pd.Series, confidence: float) -> float:
        """Historical VaR (negative = loss)."""
        return float(np.percentile(returns, (1 - confidence) * 100))

    def _cvar(self, returns: pd.Series, confidence: float) -> float:
        """Conditional VaR / Expected Shortfall."""
        var = self._var(returns, confidence)
        tail = returns[returns <= var]
        return float(tail.mean()) if not tail.empty else var

    @staticmethod
    def _max_drawdown(returns: pd.Series) -> float:
        """Maximum peak-to-trough drawdown."""
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative - rolling_max) / rolling_max
        return float(drawdown.min())

    def _sharpe(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Annualised Sharpe ratio."""
        excess = returns.mean() * self._TRADING_DAYS - risk_free_rate
        vol = returns.std() * np.sqrt(self._TRADING_DAYS)
        return float(excess / vol) if vol > 0 else 0.0

    def _sortino(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Annualised Sortino ratio (downside deviation)."""
        excess = returns.mean() * self._TRADING_DAYS - risk_free_rate
        downside = returns[returns < 0].std() * np.sqrt(self._TRADING_DAYS)
        return float(excess / downside) if downside > 0 else 0.0

    def _annualised_vol(self, returns: pd.Series) -> float:
        return float(returns.std() * np.sqrt(self._TRADING_DAYS))

    @staticmethod
    def _beta(returns: pd.Series, benchmark: pd.Series) -> float:
        aligned = pd.concat([returns, benchmark], axis=1).dropna()
        if aligned.shape[0] < 2:
            return float("nan")
        cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
        return float(cov_matrix[0, 1] / cov_matrix[1, 1]) if cov_matrix[1, 1] != 0 else 0.0

    @staticmethod
    def _monte_carlo_var(
        returns: pd.Series, confidence: float, n_simulations: int = 10_000
    ) -> float:
        """Monte Carlo VaR using normally distributed return simulations."""
        mu, sigma = returns.mean(), returns.std()
        simulated = np.random.normal(mu, sigma, n_simulations)
        return float(np.percentile(simulated, (1 - confidence) * 100))
