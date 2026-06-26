# agents/technical_analysis_agent.py

import pandas as pd
import ta
from agents.base_agent import BaseAgent, AgentResult, AgentError


class TechnicalAnalysisAgent(BaseAgent):
    """
    Agent 4: Technical Analysis Agent

    Consumes price history from MarketDataAgent and calculates
    technical indicators, then produces a single strength score.

    Score interpretation:
        +100 = extremely bullish signals
           0 = neutral / mixed signals
        -100 = extremely bearish signals
    """

    def __init__(self):
        super().__init__(name="TechnicalAnalysisAgent", max_retries=2)

    def execute(self, symbol: str, price_history: list = None, **kwargs) -> AgentResult:
        """
        Args:
            symbol        : stock ticker e.g. 'AAPL'
            price_history : list of dicts from MarketDataAgent output
                            if None, raises error (we need data first)
        """
        if not price_history:
            raise AgentError(
                "price_history is required. Run MarketDataAgent first."
            )

        self.logger.info(f"Running technical analysis for {symbol}")

        # --- Step 1: Convert to DataFrame ---
        df = pd.DataFrame(price_history)
        df = df.sort_values("date").reset_index(drop=True)

        # Ensure correct types
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if len(df) < 30:
            raise AgentError(
                f"Not enough data to calculate indicators. Got {len(df)} bars, need 30+"
            )

        # --- Step 2: Calculate indicators ---
        indicators = self._calculate_indicators(df)

        # --- Step 3: Generate signals from indicators ---
        signals = self._generate_signals(indicators, df)

        # --- Step 4: Combine signals into one score ---
        score = self._calculate_score(signals)

        self.logger.info(
            f"{symbol} | Technical Score: {score} | "
            f"Bullish signals: {signals['bullish']} | "
            f"Bearish signals: {signals['bearish']}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "indicators": indicators,
                "signals": signals,
            },
            score=score,
            metadata={"symbol": symbol, "bars_used": len(df)}
        )

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """
        Calculate all technical indicators.
        Using the 'ta' library — each function takes a pandas Series.
        """
        close = df["close"]
        high  = df["high"]
        low   = df["low"]
        volume = df["volume"]

        indicators = {}

        # --- RSI (Relative Strength Index) ---
        # Measures momentum. >70 = overbought, <30 = oversold
        rsi = ta.momentum.RSIIndicator(close=close, window=14)
        indicators["rsi"] = round(float(rsi.rsi().iloc[-1]), 2)

        # --- MACD (Moving Average Convergence Divergence) ---
        # Trend following. Signal line crossover = buy/sell signal
        macd = ta.trend.MACD(close=close)
        indicators["macd"]        = round(float(macd.macd().iloc[-1]), 4)
        indicators["macd_signal"] = round(float(macd.macd_signal().iloc[-1]), 4)
        indicators["macd_hist"]   = round(float(macd.macd_diff().iloc[-1]), 4)

        # --- EMA (Exponential Moving Average) ---
        # 20-day and 50-day. Price above EMA = bullish
        ema20 = ta.trend.EMAIndicator(close=close, window=20)
        ema50 = ta.trend.EMAIndicator(close=close, window=50)
        indicators["ema20"] = round(float(ema20.ema_indicator().iloc[-1]), 4)
        indicators["ema50"] = round(float(ema50.ema_indicator().iloc[-1]), 4)

        # --- SMA (Simple Moving Average) ---
        sma20 = ta.trend.SMAIndicator(close=close, window=20)
        indicators["sma20"] = round(float(sma20.sma_indicator().iloc[-1]), 4)

        # --- Bollinger Bands ---
        # Volatility bands. Price near upper = overbought, lower = oversold
        bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
        indicators["bb_upper"]  = round(float(bb.bollinger_hband().iloc[-1]), 4)
        indicators["bb_middle"] = round(float(bb.bollinger_mavg().iloc[-1]), 4)
        indicators["bb_lower"]  = round(float(bb.bollinger_lband().iloc[-1]), 4)
        indicators["bb_pct"]    = round(float(bb.bollinger_pband().iloc[-1]), 4)

        # --- ATR (Average True Range) ---
        # Measures volatility. Higher = more volatile
        atr = ta.volatility.AverageTrueRange(high=high, low=low, close=close)
        indicators["atr"] = round(float(atr.average_true_range().iloc[-1]), 4)

        # --- ADX (Average Directional Index) ---
        # Measures trend strength. >25 = strong trend
        adx = ta.trend.ADXIndicator(high=high, low=low, close=close)
        indicators["adx"]    = round(float(adx.adx().iloc[-1]), 2)
        indicators["adx_pos"] = round(float(adx.adx_pos().iloc[-1]), 2)
        indicators["adx_neg"] = round(float(adx.adx_neg().iloc[-1]), 2)

        # --- Volume SMA ---
        # Is current volume above average?
        indicators["volume_sma20"] = round(float(volume.rolling(20).mean().iloc[-1]), 0)
        indicators["current_volume"] = int(volume.iloc[-1])
        indicators["current_close"]  = round(float(close.iloc[-1]), 4)

        return indicators

    def _generate_signals(self, ind: dict, df: pd.DataFrame) -> dict:
        """
        Convert raw indicator values into BUY/SELL/NEUTRAL signals.
        Each signal is scored: +1 bullish, -1 bearish, 0 neutral
        """
        signals = {
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
            "details": {}
        }

        def record(name, value, bullish_condition, bearish_condition):
            if bullish_condition:
                signals["bullish"] += 1
                signals["details"][name] = {"value": value, "signal": "BULLISH"}
            elif bearish_condition:
                signals["bearish"] += 1
                signals["details"][name] = {"value": value, "signal": "BEARISH"}
            else:
                signals["neutral"] += 1
                signals["details"][name] = {"value": value, "signal": "NEUTRAL"}

        close = ind["current_close"]

        # RSI signal
        record("RSI", ind["rsi"],
               bullish_condition = ind["rsi"] < 35,       # oversold = buy opportunity
               bearish_condition = ind["rsi"] > 65)       # overbought = sell signal

        # MACD signal
        record("MACD", ind["macd_hist"],
               bullish_condition = ind["macd_hist"] > 0,  # histogram above zero = bullish
               bearish_condition = ind["macd_hist"] < 0)

        # Price vs EMA20
        record("EMA20", ind["ema20"],
               bullish_condition = close > ind["ema20"],
               bearish_condition = close < ind["ema20"])

        # Price vs EMA50
        record("EMA50", ind["ema50"],
               bullish_condition = close > ind["ema50"],
               bearish_condition = close < ind["ema50"])

        # EMA crossover (20 above 50 = golden cross = bullish)
        record("EMA_Cross", f"{ind['ema20']:.2f} vs {ind['ema50']:.2f}",
               bullish_condition = ind["ema20"] > ind["ema50"],
               bearish_condition = ind["ema20"] < ind["ema50"])

        # Bollinger Band position
        record("BollingerBand", ind["bb_pct"],
               bullish_condition = ind["bb_pct"] < 0.2,   # near lower band = oversold
               bearish_condition = ind["bb_pct"] > 0.8)   # near upper band = overbought

        # ADX trend strength + direction
        if ind["adx"] > 25:   # strong trend exists
            record("ADX", ind["adx"],
                   bullish_condition = ind["adx_pos"] > ind["adx_neg"],
                   bearish_condition = ind["adx_neg"] > ind["adx_pos"])
        else:
            signals["neutral"] += 1
            signals["details"]["ADX"] = {"value": ind["adx"], "signal": "NEUTRAL (weak trend)"}

        # Volume confirmation
        record("Volume", ind["current_volume"],
               bullish_condition = ind["current_volume"] > ind["volume_sma20"] * 1.2,
               bearish_condition = ind["current_volume"] < ind["volume_sma20"] * 0.8)

        return signals

    def _calculate_score(self, signals: dict) -> float:
        """
        Convert bullish/bearish signal counts into a -100 to +100 score.

        Formula:
            net = bullish - bearish
            total = bullish + bearish + neutral
            score = (net / total) * 100
        """
        total = signals["bullish"] + signals["bearish"] + signals["neutral"]
        if total == 0:
            return 0.0
        net = signals["bullish"] - signals["bearish"]
        return round((net / total) * 100, 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True