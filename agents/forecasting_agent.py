"""
Forecasting Agent — generates price / return forecasts using statistical and ML models.

Supported models:
  - ARIMA / SARIMA  (statsmodels)
  - Prophet         (Facebook Prophet)
  - XGBoost         (gradient boosting regression)
  - LSTM            (PyTorch — optional, heavy dependency)
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from agents.base_agent import BaseAgent, AgentError


ForecastModel = Literal["arima", "prophet", "xgboost", "lstm"]


class ForecastingAgent(BaseAgent):
    """Produces price or return forecasts for a given price series."""

    agent_name = "ForecastingAgent"

    _SUPPORTED = ("arima", "prophet", "xgboost", "lstm")

    def __init__(self, model: ForecastModel = "arima", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if model not in self._SUPPORTED:
            raise ValueError(f"model must be one of {self._SUPPORTED}")
        self.model_name = model

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(
        self,
        series: pd.Series,
        horizon: int = 30,
        confidence: float = 0.95,
    ) -> dict[str, Any]:
        """Fit model and forecast `horizon` steps ahead.

        Args:
            series:     Time-indexed pandas Series of closing prices.
            horizon:    Number of periods to forecast.
            confidence: Confidence interval level (e.g. 0.95 → 95% CI).

        Returns:
            Dict with 'forecast', 'lower_bound', 'upper_bound', and 'metrics'.
        """
        self.logger.info(
            "Forecasting %d steps with %s (CI=%.0f%%).",
            horizon,
            self.model_name,
            confidence * 100,
        )

        if len(series) < 30:
            raise AgentError("Need at least 30 observations to fit a forecast model.")

        dispatch = {
            "arima": self._forecast_arima,
            "prophet": self._forecast_prophet,
            "xgboost": self._forecast_xgboost,
            "lstm": self._forecast_lstm,
        }
        return dispatch[self.model_name](series, horizon, confidence)

    # ------------------------------------------------------------------
    # Model back-ends
    # ------------------------------------------------------------------

    def _forecast_arima(
        self, series: pd.Series, horizon: int, confidence: float
    ) -> dict[str, Any]:
        try:
            from pmdarima import auto_arima  # type: ignore
        except ImportError as exc:
            raise AgentError("pmdarima not installed. Run: pip install pmdarima") from exc

        model = auto_arima(series, suppress_warnings=True, error_action="ignore")
        forecast, conf_int = model.predict(n_periods=horizon, return_conf_int=True, alpha=1 - confidence)
        return self._build_result(series, forecast, conf_int[:, 0], conf_int[:, 1], model.aic())

    def _forecast_prophet(
        self, series: pd.Series, horizon: int, confidence: float
    ) -> dict[str, Any]:
        try:
            from prophet import Prophet  # type: ignore
        except ImportError as exc:
            raise AgentError("prophet not installed. Run: pip install prophet") from exc

        df = pd.DataFrame({"ds": series.index, "y": series.values})
        m = Prophet(interval_width=confidence)
        m.fit(df)
        future = m.make_future_dataframe(periods=horizon)
        forecast_df = m.predict(future).tail(horizon)
        return self._build_result(
            series,
            forecast_df["yhat"].values,
            forecast_df["yhat_lower"].values,
            forecast_df["yhat_upper"].values,
            metric=None,
        )

    def _forecast_xgboost(
        self, series: pd.Series, horizon: int, confidence: float
    ) -> dict[str, Any]:
        try:
            import xgboost as xgb  # type: ignore
        except ImportError as exc:
            raise AgentError("xgboost not installed. Run: pip install xgboost") from exc

        lags = min(30, len(series) // 3)
        X, y = self._create_lag_features(series.values, lags)
        model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.05)
        model.fit(X, y)

        preds = []
        window = list(series.values[-lags:])
        for _ in range(horizon):
            x = np.array(window[-lags:]).reshape(1, -1)
            pred = model.predict(x)[0]
            preds.append(float(pred))
            window.append(pred)

        std = np.std(series.values[-60:]) if len(series) >= 60 else np.std(series.values)
        z = 1.96 if confidence >= 0.95 else 1.645
        preds_arr = np.array(preds)
        return self._build_result(series, preds_arr, preds_arr - z * std, preds_arr + z * std, metric=None)

    def _forecast_lstm(
        self, series: pd.Series, horizon: int, confidence: float
    ) -> dict[str, Any]:
        raise AgentError(
            "LSTM forecasting is not yet implemented. "
            "Use 'arima', 'prophet', or 'xgboost' instead."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_lag_features(values: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
        rows = []
        targets = []
        for i in range(lags, len(values)):
            rows.append(values[i - lags: i])
            targets.append(values[i])
        return np.array(rows), np.array(targets)

    @staticmethod
    def _build_result(
        series: pd.Series,
        forecast: np.ndarray,
        lower: np.ndarray,
        upper: np.ndarray,
        metric: float | None,
    ) -> dict[str, Any]:
        last_price = series.iloc[-1]
        return {
            "forecast": forecast.tolist(),
            "lower_bound": lower.tolist(),
            "upper_bound": upper.tolist(),
            "horizon": len(forecast),
            "last_observed_price": float(last_price),
            "expected_return_pct": round((forecast[-1] - last_price) / last_price * 100, 3),
            "aic": metric,
        }
