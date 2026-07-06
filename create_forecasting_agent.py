# create_forecasting_agent.py

content = """
# agents/forecasting_agent.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent, AgentResult, AgentError


class ForecastingAgent(BaseAgent):
    \"\"\"
    Agent 6: Forecasting Agent

    Predicts future stock prices using ensemble of 3 models:
        - Prophet  (trend + seasonality)
        - ARIMA    (statistical time series)
        - Linear   (simple trend baseline)

    Output score reflects predicted direction and confidence:
        +100 = strong predicted uptrend
           0 = flat / uncertain prediction
        -100 = strong predicted downtrend
    \"\"\"

    def __init__(self):
        super().__init__(name="ForecastingAgent", max_retries=2)

    def execute(self, symbol: str, price_history: list = None, **kwargs) -> AgentResult:
        if not price_history:
            raise AgentError("price_history is required. Run MarketDataAgent first.")

        self.logger.info(f"Running price forecasting for {symbol}")

        df = pd.DataFrame(price_history)
        df = df.sort_values("date").reset_index(drop=True)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["date"]  = pd.to_datetime(df["date"].astype(str).str[:10])
        df = df.dropna(subset=["close"])

        if len(df) < 30:
            raise AgentError(f"Need at least 30 bars for forecasting. Got {len(df)}")

        current_price = float(df["close"].iloc[-1])

        # Run all 3 models
        forecasts = {}

        prophet_result = self._run_prophet(df)
        if prophet_result:
            forecasts["prophet"] = prophet_result

        arima_result = self._run_arima(df)
        if arima_result:
            forecasts["arima"] = arima_result

        linear_result = self._run_linear(df)
        if linear_result:
            forecasts["linear"] = linear_result

        if not forecasts:
            raise AgentError("All forecasting models failed")

        # Ensemble: average predictions across models
        ensemble = self._ensemble(forecasts, current_price)

        # Score based on 30-day prediction direction and magnitude
        score = self._calculate_score(ensemble, current_price)

        self.logger.info(
            f"{symbol} | Current: {current_price:.2f} | "
            f"7d: {ensemble['7d']['price']:.2f} | "
            f"30d: {ensemble['30d']['price']:.2f} | "
            f"Score: {score}"
        )

        return AgentResult(
            agent_name = self.name,
            success    = True,
            data       = {
                "current_price" : current_price,
                "forecasts"     : ensemble,
                "models_used"   : list(forecasts.keys()),
            },
            score    = score,
            metadata = {"symbol": symbol, "bars_used": len(df)}
        )

    def _run_prophet(self, df: pd.DataFrame) -> dict:
        \"\"\"Facebook Prophet — best for trend + seasonality detection.\"\"\"
        try:
            from prophet import Prophet
            import warnings
            warnings.filterwarnings("ignore")

            prophet_df = df[["date", "close"]].rename(
                columns={"date": "ds", "close": "y"}
            )

            model = Prophet(
                daily_seasonality  = False,
                weekly_seasonality = True,
                yearly_seasonality = True,
                changepoint_prior_scale = 0.05,
                interval_width = 0.80
            )
            model.fit(prophet_df)

            future = model.make_future_dataframe(periods=90)
            forecast = model.predict(future)

            last_date = df["date"].iloc[-1]
            results = {}

            for days, key in [(7, "7d"), (30, "30d"), (90, "90d")]:
                target_date = last_date + timedelta(days=days)
                row = forecast[forecast["ds"] >= target_date].head(1)
                if not row.empty:
                    results[key] = {
                        "price" : round(float(row["yhat"].iloc[0]), 2),
                        "lower" : round(float(row["yhat_lower"].iloc[0]), 2),
                        "upper" : round(float(row["yhat_upper"].iloc[0]), 2),
                    }

            return results if results else None

        except Exception as e:
            self.logger.warning(f"Prophet failed: {e}")
            return None

    def _run_arima(self, df: pd.DataFrame) -> dict:
        \"\"\"ARIMA — classical statistical time series model.\"\"\"
        try:
            from statsmodels.tsa.arima.model import ARIMA
            import warnings
            warnings.filterwarnings("ignore")

            prices = df["close"].values

            model  = ARIMA(prices, order=(5, 1, 0))
            fitted = model.fit()

            forecast_90 = fitted.forecast(steps=90)

            results = {}
            for days, key in [(7, "7d"), (30, "30d"), (90, "90d")]:
                idx = min(days - 1, len(forecast_90) - 1)
                price = float(forecast_90[idx])
                results[key] = {
                    "price" : round(price, 2),
                    "lower" : round(price * 0.95, 2),
                    "upper" : round(price * 1.05, 2),
                }

            return results

        except Exception as e:
            self.logger.warning(f"ARIMA failed: {e}")
            return None

    def _run_linear(self, df: pd.DataFrame) -> dict:
        \"\"\"Linear regression on recent trend — simple but robust baseline.\"\"\"
        try:
            from sklearn.linear_model import LinearRegression

            # Use last 30 days for trend
            recent = df.tail(30).copy()
            X = np.arange(len(recent)).reshape(-1, 1)
            y = recent["close"].values

            model = LinearRegression()
            model.fit(X, y)

            last_idx = len(recent) - 1
            results = {}

            for days, key in [(7, "7d"), (30, "30d"), (90, "90d")]:
                future_idx = last_idx + days
                price = float(model.predict([[future_idx]])[0])
                results[key] = {
                    "price" : round(price, 2),
                    "lower" : round(price * 0.93, 2),
                    "upper" : round(price * 1.07, 2),
                }

            return results

        except Exception as e:
            self.logger.warning(f"Linear regression failed: {e}")
            return None

    def _ensemble(self, forecasts: dict, current_price: float) -> dict:
        \"\"\"
        Average predictions from all models.
        Weight: Prophet 50%, ARIMA 30%, Linear 20%
        \"\"\"
        weights = {"prophet": 0.5, "arima": 0.3, "linear": 0.2}
        ensemble = {}

        for horizon in ["7d", "30d", "90d"]:
            total_weight = 0
            weighted_price = 0
            weighted_lower = 0
            weighted_upper = 0

            for model_name, model_results in forecasts.items():
                if horizon in model_results:
                    w = weights.get(model_name, 0.33)
                    weighted_price += model_results[horizon]["price"] * w
                    weighted_lower += model_results[horizon]["lower"] * w
                    weighted_upper += model_results[horizon]["upper"] * w
                    total_weight   += w

            if total_weight > 0:
                price = weighted_price / total_weight
                lower = weighted_lower / total_weight
                upper = weighted_upper / total_weight
                change_pct = ((price - current_price) / current_price) * 100

                ensemble[horizon] = {
                    "price"      : round(price, 2),
                    "lower"      : round(lower, 2),
                    "upper"      : round(upper, 2),
                    "change_pct" : round(change_pct, 2),
                }

        return ensemble

    def _calculate_score(self, ensemble: dict, current_price: float) -> float:
        \"\"\"
        Score based on 30-day predicted change.
        +10% predicted gain = ~+60 score
        -10% predicted loss = ~-60 score
        \"\"\"
        if "30d" not in ensemble:
            return 0.0

        change_pct = ensemble["30d"]["change_pct"]

        # Scale: every 1% predicted change = ~6 score points
        score = change_pct * 6

        return round(max(min(score, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True
"""

with open("agents/forecasting_agent.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("agents/forecasting_agent.py written successfully")