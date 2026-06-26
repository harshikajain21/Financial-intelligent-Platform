"""
Anomaly Agent — detects statistical anomalies in price, volume, and returns.

Detection methods:
  - Z-score threshold
  - Interquartile Range (IQR)
  - Isolation Forest (sklearn)
  - CUSUM (cumulative sum control chart)
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from agents.base_agent import BaseAgent, AgentError


class AnomalyAgent(BaseAgent):
    """Detects statistical anomalies and outliers in financial time series."""

    agent_name = "AnomalyAgent"

    _METHODS = ("zscore", "iqr", "isolation_forest", "cusum")

    def __init__(self, method: str = "zscore", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if method not in self._METHODS:
            raise ValueError(f"method must be one of {self._METHODS}")
        self.method = method

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(
        self,
        series: pd.Series,
        threshold: float = 3.0,
        contamination: float = 0.05,
    ) -> dict[str, Any]:
        """Detect anomalies in a univariate time series.

        Args:
            series:        DatetimeIndex Series (e.g. closing prices or returns).
            threshold:     Z-score or CUSUM threshold.
            contamination: Expected fraction of anomalies (Isolation Forest).

        Returns:
            Dict with anomaly indices, values, and summary stats.
        """
        if series.empty:
            raise AgentError("Input series is empty.")

        self.logger.info(
            "Detecting anomalies via %s on %d observations.", self.method, len(series)
        )

        if self.method == "zscore":
            flags = self._zscore(series, threshold)
        elif self.method == "iqr":
            flags = self._iqr(series)
        elif self.method == "isolation_forest":
            flags = self._isolation_forest(series, contamination)
        else:
            flags = self._cusum(series, threshold)

        anomaly_dates = series.index[flags].tolist()
        anomaly_values = series[flags].tolist()

        return {
            "method": self.method,
            "total_observations": len(series),
            "anomaly_count": int(flags.sum()),
            "anomaly_rate_pct": round(flags.mean() * 100, 3),
            "anomalies": [
                {"date": str(d), "value": float(v)}
                for d, v in zip(anomaly_dates, anomaly_values)
            ],
        }

    # ------------------------------------------------------------------
    # Detection methods
    # ------------------------------------------------------------------

    @staticmethod
    def _zscore(series: pd.Series, threshold: float) -> pd.Series:
        z = (series - series.mean()) / series.std()
        return z.abs() > threshold

    @staticmethod
    def _iqr(series: pd.Series) -> pd.Series:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        return (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)

    @staticmethod
    def _isolation_forest(series: pd.Series, contamination: float) -> pd.Series:
        try:
            from sklearn.ensemble import IsolationForest  # type: ignore
        except ImportError as exc:
            raise AgentError("scikit-learn not installed. Run: pip install scikit-learn") from exc

        X = series.values.reshape(-1, 1)
        clf = IsolationForest(contamination=contamination, random_state=42)
        preds = clf.fit_predict(X)
        return pd.Series(preds == -1, index=series.index)

    @staticmethod
    def _cusum(series: pd.Series, threshold: float) -> pd.Series:
        """CUSUM control chart."""
        mu = series.mean()
        sigma = series.std()
        if sigma == 0:
            return pd.Series([False] * len(series), index=series.index)

        cusum_pos = np.zeros(len(series))
        cusum_neg = np.zeros(len(series))
        k = 0.5  # allowable slack

        for i in range(1, len(series)):
            z = (series.iloc[i] - mu) / sigma
            cusum_pos[i] = max(0, cusum_pos[i - 1] + z - k)
            cusum_neg[i] = max(0, cusum_neg[i - 1] - z - k)

        flags = (cusum_pos > threshold) | (cusum_neg > threshold)
        return pd.Series(flags, index=series.index)
