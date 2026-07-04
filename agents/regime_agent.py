# agents/regime_agent.py

import numpy as np
import pandas as pd
from agents.base_agent import BaseAgent, AgentResult, AgentError


class RegimeDetectionAgent(BaseAgent):
    """
    Agent 8: Regime Detection Agent

    Identifies the current market regime from price history.
    Uses trend, momentum, and volatility signals combined.

    Regimes:
        BULL            — strong uptrend, healthy momentum
        BEAR            — strong downtrend, negative momentum
        SIDEWAYS        — no clear direction, low momentum
        HIGH_VOLATILITY — extreme price swings regardless of direction
        BLACK_SWAN      — statistically extreme event detected

    Score interpretation:
        +100 = strong bull regime (very favorable)
           0 = sideways / neutral regime
        -100 = strong bear or black swan (very unfavorable)
    """

    # How many std deviations = black swan
    BLACK_SWAN_THRESHOLD = 3.5

    def __init__(self):
        super().__init__(name="RegimeDetectionAgent", max_retries=2)

    def execute(self, symbol: str, price_history: list = None, **kwargs) -> AgentResult:
        if not price_history:
            raise AgentError(
                "price_history is required. Run MarketDataAgent first."
            )

        self.logger.info(f"Detecting market regime for {symbol}")

        # --- Step 1: Prepare data ---
        df = pd.DataFrame(price_history)
        df = df.sort_values("date").reset_index(drop=True)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        if len(df) < 50:
            raise AgentError(
                f"Need at least 50 bars for regime detection. Got {len(df)}"
            )

        returns = df["close"].pct_change().dropna()

        # --- Step 2: Calculate regime indicators ---
        indicators = self._calculate_regime_indicators(df, returns)

        # --- Step 3: Classify regime ---
        regime, confidence = self._classify_regime(indicators, returns)

        # --- Step 4: Convert to score ---
        score = self._regime_to_score(regime, confidence)

        self.logger.info(
            f"{symbol} | Regime: {regime} | "
            f"Confidence: {confidence}% | Score: {score}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "regime"     : regime,
                "confidence" : confidence,
                "indicators" : indicators,
            },
            score=score,
            metadata={"symbol": symbol, "bars_used": len(df)}
        )

    def _calculate_regime_indicators(self, df: pd.DataFrame,
                                      returns: pd.Series) -> dict:
        """
        Calculate the raw indicators we use to classify regime.
        """
        close = df["close"]
        ind = {}

        # --- Trend indicators ---
        # SMA comparison: where is price relative to its moving averages?
        ind["sma_20"]  = float(close.rolling(20).mean().iloc[-1])
        ind["sma_50"]  = float(close.rolling(50).mean().iloc[-1])
        ind["current_price"] = float(close.iloc[-1])

        # Price position relative to SMAs
        ind["above_sma20"] = ind["current_price"] > ind["sma_20"]
        ind["above_sma50"] = ind["current_price"] > ind["sma_50"]
        ind["sma20_above_sma50"] = ind["sma_20"] > ind["sma_50"]

        # --- Momentum: recent return over different windows ---
        ind["return_5d"]  = float((close.iloc[-1] / close.iloc[-5]  - 1) * 100)
        ind["return_20d"] = float((close.iloc[-1] / close.iloc[-20] - 1) * 100)
        ind["return_50d"] = float((close.iloc[-1] / close.iloc[-50] - 1) * 100)

        # --- Volatility ---
        ind["volatility_20d"] = float(returns.tail(20).std() * np.sqrt(252) * 100)
        ind["volatility_50d"] = float(returns.tail(50).std() * np.sqrt(252) * 100)

        # Is volatility spiking recently vs longer term?
        ind["vol_ratio"] = (
            ind["volatility_20d"] / ind["volatility_50d"]
            if ind["volatility_50d"] > 0 else 1.0
        )

        # --- Black Swan detection ---
        # Is the most recent return an extreme outlier?
        mean_return   = float(returns.mean())
        std_return    = float(returns.std())
        latest_return = float(returns.iloc[-1])

        ind["latest_return"] = round(latest_return * 100, 4)
        ind["return_zscore"]  = (
            (latest_return - mean_return) / std_return
            if std_return > 0 else 0
        )

        # Round for clean display
        for key in ["return_5d", "return_20d", "return_50d",
                    "volatility_20d", "volatility_50d", "vol_ratio",
                    "return_zscore", "sma_20", "sma_50"]:
            ind[key] = round(ind[key], 3)

        return ind

    def _classify_regime(self, ind: dict, returns: pd.Series) -> tuple:
        """
        Classify regime based on indicators.
        Returns (regime_name, confidence_pct)
        """

        # --- Black Swan check first (overrides everything) ---
        if abs(ind["return_zscore"]) >= self.BLACK_SWAN_THRESHOLD:
            confidence = min(abs(ind["return_zscore"]) * 20, 100)
            return "BLACK_SWAN", round(confidence, 1)

        # --- High Volatility check ---
        # Vol ratio > 1.5 means recent volatility is 50% higher than normal
        if ind["vol_ratio"] >= 1.5 and ind["volatility_20d"] >= 40:
            confidence = min(ind["vol_ratio"] * 30, 100)
            return "HIGH_VOLATILITY", round(confidence, 1)

        # --- Bull / Bear / Sideways based on trend + momentum ---
        # Count bullish signals
        bull_signals = 0
        bear_signals = 0

        if ind["above_sma20"]:
            bull_signals += 1
        else:
            bear_signals += 1

        if ind["above_sma50"]:
            bull_signals += 1
        else:
            bear_signals += 1

        if ind["sma20_above_sma50"]:
            bull_signals += 1
        else:
            bear_signals += 1

        if ind["return_20d"] > 2:
            bull_signals += 1
        elif ind["return_20d"] < -2:
            bear_signals += 1

        if ind["return_50d"] > 5:
            bull_signals += 1
        elif ind["return_50d"] < -5:
            bear_signals += 1

        total = bull_signals + bear_signals
        if total == 0:
            return "SIDEWAYS", 50.0

        bull_pct = (bull_signals / (bull_signals + bear_signals)) * 100

        if bull_pct >= 70:
            return "BULL", round(bull_pct, 1)
        elif bull_pct <= 30:
            return "BEAR", round(100 - bull_pct, 1)
        else:
            return "SIDEWAYS", round(50 + abs(bull_pct - 50), 1)

    def _regime_to_score(self, regime: str, confidence: float) -> float:
        """
        Convert regime + confidence into a -100 to +100 score.
        Confidence scales the magnitude.
        """
        regime_base = {
            "BULL"            :  80,
            "SIDEWAYS"        :   0,
            "HIGH_VOLATILITY" : -40,
            "BEAR"            : -80,
            "BLACK_SWAN"      : -100,
        }

        base = regime_base.get(regime, 0)
        # Scale by confidence (confidence 50% = half the base score)
        score = base * (confidence / 100)
        return round(max(min(score, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        if result.data.get("regime") not in [
            "BULL", "BEAR", "SIDEWAYS", "HIGH_VOLATILITY", "BLACK_SWAN"
        ]:
            return False
        return True