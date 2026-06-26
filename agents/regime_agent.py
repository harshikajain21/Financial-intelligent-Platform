"""
Regime Agent — identifies the current market regime (bull / bear / sideways / volatile).

Methods:
  - Hidden Markov Model (hmmlearn)
  - Threshold / rule-based classification
  - Trend-strength via ADX
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from agents.base_agent import BaseAgent, AgentError


Regime = Literal["bull", "bear", "sideways", "volatile"]


class RegimeAgent(BaseAgent):
    """Classifies the current and historical market regimes."""

    agent_name = "RegimeAgent"

    _N_STATES = 3  # bull, bear, sideways

    def __init__(self, method: str = "hmm", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.method = method  # "hmm" | "threshold"

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(self, price_series: pd.Series) -> dict[str, Any]:
        """Detect market regime from a closing price series.

        Args:
            price_series: DatetimeIndex pandas Series of closing prices.

        Returns:
            Dict with per-date regime labels and current regime.
        """
        if len(price_series) < 60:
            raise AgentError("Need at least 60 observations for regime detection.")

        returns = price_series.pct_change().dropna()

        if self.method == "hmm":
            labels = self._hmm_regimes(returns)
        else:
            labels = self._threshold_regimes(price_series, returns)

        regime_series = pd.Series(labels, index=returns.index)
        current = regime_series.iloc[-1]

        transitions = self._count_transitions(labels)
        durations = self._regime_durations(labels)

        return {
            "current_regime": current,
            "history": regime_series.to_dict(),
            "transitions": transitions,
            "avg_durations": durations,
            "method": self.method,
        }

    # ------------------------------------------------------------------
    # Regime detection methods
    # ------------------------------------------------------------------

    def _hmm_regimes(self, returns: pd.Series) -> list[str]:
        try:
            from hmmlearn import hmm  # type: ignore
        except ImportError as exc:
            raise AgentError("hmmlearn not installed. Run: pip install hmmlearn") from exc

        X = returns.values.reshape(-1, 1)
        model = hmm.GaussianHMM(
            n_components=self._N_STATES,
            covariance_type="full",
            n_iter=200,
            random_state=42,
        )
        model.fit(X)
        state_seq = model.predict(X)

        # Assign human labels by sorting states by mean return
        means = {s: returns.values[state_seq == s].mean() for s in range(self._N_STATES)}
        sorted_states = sorted(means, key=means.__getitem__)

        label_map = {
            sorted_states[0]: "bear",
            sorted_states[1]: "sideways",
            sorted_states[2]: "bull",
        }
        return [label_map[s] for s in state_seq]

    @staticmethod
    def _threshold_regimes(prices: pd.Series, returns: pd.Series) -> list[str]:
        sma_50 = prices.rolling(50).mean()
        sma_200 = prices.rolling(200).mean()
        vol_20 = returns.rolling(20).std()
        vol_threshold = vol_20.quantile(0.75)

        labels = []
        for i in range(len(returns)):
            r = returns.iloc[i]
            v = vol_20.iloc[i]
            s50 = sma_50.iloc[i]
            s200 = sma_200.iloc[i]

            if pd.isna(s50) or pd.isna(s200):
                labels.append("sideways")
            elif v > vol_threshold:
                labels.append("volatile")
            elif s50 > s200 and r > 0:
                labels.append("bull")
            elif s50 < s200 and r < 0:
                labels.append("bear")
            else:
                labels.append("sideways")

        return labels

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @staticmethod
    def _count_transitions(labels: list[str]) -> dict[str, int]:
        transitions: dict[str, int] = {}
        for i in range(1, len(labels)):
            if labels[i] != labels[i - 1]:
                key = f"{labels[i-1]}→{labels[i]}"
                transitions[key] = transitions.get(key, 0) + 1
        return transitions

    @staticmethod
    def _regime_durations(labels: list[str]) -> dict[str, float]:
        from collections import defaultdict
        durations: dict[str, list[int]] = defaultdict(list)
        count = 1
        for i in range(1, len(labels)):
            if labels[i] == labels[i - 1]:
                count += 1
            else:
                durations[labels[i - 1]].append(count)
                count = 1
        durations[labels[-1]].append(count)
        return {k: round(float(np.mean(v)), 2) for k, v in durations.items()}
