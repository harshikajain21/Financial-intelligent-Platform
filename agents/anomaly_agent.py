# agents/anomaly_agent.py

import numpy as np
import pandas as pd
from agents.base_agent import BaseAgent, AgentResult, AgentError


class AnomalyDetectionAgent(BaseAgent):
    """
    Agent 11: Anomaly Detection Agent

    Detects unusual activity in price and volume data using
    statistical methods. Flags potential insider activity,
    manipulation, or significant market events.

    Score interpretation:
        +100 = no anomalies detected (clean, normal trading)
           0 = mild anomalies present
        -100 = severe anomalies detected (high alert)

    Note: Score is INVERTED vs other agents — high anomaly = negative score
    because anomalies represent risk/uncertainty, not opportunity.
    """

    # Thresholds for anomaly detection
    VOLUME_SPIKE_THRESHOLD   = 2.5   # volume > 2.5x average = spike
    PRICE_GAP_THRESHOLD      = 0.03  # 3% gap between sessions = anomaly
    ZSCORE_THRESHOLD         = 2.5   # return z-score > 2.5 = outlier

    def __init__(self):
        super().__init__(name="AnomalyDetectionAgent", max_retries=2)

    def execute(self, symbol: str, price_history: list = None, **kwargs) -> AgentResult:
        if not price_history:
            raise AgentError(
                "price_history is required. Run MarketDataAgent first."
            )

        self.logger.info(f"Running anomaly detection for {symbol}")

        # --- Step 1: Prepare data ---
        df = pd.DataFrame(price_history)
        df = df.sort_values("date").reset_index(drop=True)

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if len(df) < 20:
            raise AgentError(f"Need at least 20 bars. Got {len(df)}")

        returns = df["close"].pct_change().dropna()

        # --- Step 2: Run all anomaly checks ---
        anomalies = []

        volume_anomalies   = self._check_volume_anomalies(df)
        price_anomalies    = self._check_price_gap_anomalies(df)
        return_anomalies   = self._check_return_anomalies(returns)
        volatility_anomaly = self._check_volatility_anomaly(returns)

        anomalies.extend(volume_anomalies)
        anomalies.extend(price_anomalies)
        anomalies.extend(return_anomalies)
        if volatility_anomaly:
            anomalies.append(volatility_anomaly)

        # --- Step 3: Calculate alert severity ---
        severity_score = self._calculate_severity(anomalies)

        # --- Step 4: Convert to agent score ---
        # No anomalies = +100 (clean), severe anomalies = -100 (alert)
        score = round(max(min(100 - (severity_score * 2), 100), -100), 2)

        self.logger.info(
            f"{symbol} | Anomalies: {len(anomalies)} | "
            f"Severity: {severity_score} | Score: {score}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "anomalies"      : anomalies,
                "anomaly_count"  : len(anomalies),
                "severity_score" : severity_score,
            },
            score=score,
            metadata={"symbol": symbol, "bars_analyzed": len(df)}
        )

    def _check_volume_anomalies(self, df: pd.DataFrame) -> list:
        """
        Detect unusual volume spikes vs 20-day average.
        High volume with price movement = potential insider activity.
        """
        anomalies = []

        avg_volume = df["volume"].rolling(20).mean()
        recent_bars = df.tail(5)

        for idx, row in recent_bars.iterrows():
            if idx < 20:
                continue
            avg = avg_volume.iloc[idx]
            if avg and avg > 0:
                vol_ratio = row["volume"] / avg
                if vol_ratio >= self.VOLUME_SPIKE_THRESHOLD:
                    anomalies.append({
                        "type"     : "VOLUME_SPIKE",
                        "severity" : "HIGH" if vol_ratio >= 4 else "MEDIUM",
                        "date"     : str(row["date"]),
                        "detail"   : f"Volume {vol_ratio:.1f}x above 20-day average",
                        "value"    : round(vol_ratio, 2)
                    })

        return anomalies

    def _check_price_gap_anomalies(self, df: pd.DataFrame) -> list:
        """
        Detect large overnight gaps between sessions.
        Gaps > 3% indicate significant news or manipulation.
        """
        anomalies = []

        recent = df.tail(10).copy()
        recent["prev_close"] = recent["close"].shift(1)
        recent["gap_pct"] = (
            (recent["open"] - recent["prev_close"]) / recent["prev_close"]
        ).abs()

        for _, row in recent.iterrows():
            if pd.isna(row["gap_pct"]):
                continue
            if row["gap_pct"] >= self.PRICE_GAP_THRESHOLD:
                anomalies.append({
                    "type"     : "PRICE_GAP",
                    "severity" : "HIGH" if row["gap_pct"] >= 0.06 else "MEDIUM",
                    "date"     : str(row["date"]),
                    "detail"   : f"Overnight gap of {row['gap_pct']*100:.2f}%",
                    "value"    : round(row["gap_pct"] * 100, 2)
                })

        return anomalies

    def _check_return_anomalies(self, returns: pd.Series) -> list:
        """
        Detect statistically extreme daily returns using z-scores.
        A z-score > 2.5 means the return is very unusual vs recent history.
        """
        anomalies = []

        mean_r = returns.mean()
        std_r  = returns.std()

        if std_r == 0:
            return anomalies

        recent_returns = returns.tail(10)

        for date, ret in recent_returns.items():
            zscore = abs((ret - mean_r) / std_r)
            if zscore >= self.ZSCORE_THRESHOLD:
                anomalies.append({
                    "type"     : "RETURN_OUTLIER",
                    "severity" : "HIGH" if zscore >= 3.5 else "MEDIUM",
                    "date"     : str(date),
                    "detail"   : f"Return z-score: {zscore:.2f} ({ret*100:.2f}%)",
                    "value"    : round(zscore, 2)
                })

        return anomalies

    def _check_volatility_anomaly(self, returns: pd.Series) -> dict:
        """
        Check if recent volatility has spiked vs the longer term.
        Vol spike = market stress or unusual event.
        """
        if len(returns) < 20:
            return None

        recent_vol  = returns.tail(5).std() * np.sqrt(252)
        baseline_vol = returns.tail(20).std() * np.sqrt(252)

        if baseline_vol == 0:
            return None

        vol_ratio = recent_vol / baseline_vol

        if vol_ratio >= 2.0:
            return {
                "type"     : "VOLATILITY_SPIKE",
                "severity" : "HIGH" if vol_ratio >= 3.0 else "MEDIUM",
                "date"     : "recent",
                "detail"   : f"Recent vol {vol_ratio:.1f}x above baseline",
                "value"    : round(vol_ratio, 2)
            }

        return None

    def _calculate_severity(self, anomalies: list) -> float:
        """
        Convert list of anomalies into a single severity score (0-100).
        HIGH severity anomalies count more than MEDIUM ones.
        """
        if not anomalies:
            return 0.0

        severity_map = {"HIGH": 20, "MEDIUM": 10, "LOW": 5}
        total = sum(severity_map.get(a["severity"], 5) for a in anomalies)

        return min(total, 100)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True