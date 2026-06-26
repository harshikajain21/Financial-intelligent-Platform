"""
Backtesting Engine — event-driven backtesting framework.

Supported built-in strategies:
  - sma_crossover   (50/200 SMA golden/death cross)
  - rsi_mean_revert (RSI < 30 buy, RSI > 70 sell)
  - macd_signal     (MACD line crosses signal line)
  - buy_and_hold    (benchmark)

Custom strategies can be registered via BacktestEngine.register_strategy().
"""

from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np
import pandas as pd

from data.fetchers.yahoo_fetcher import YahooFetcher
from data.processors.normalizer import Normalizer
from utils.logger import get_logger

logger = get_logger("BacktestEngine")

StrategyFn = Callable[[pd.DataFrame], pd.Series]  # returns signal Series (-1/0/+1)


class BacktestEngine:
    """Event-driven backtesting engine with portfolio simulation."""

    _STRATEGIES: dict[str, StrategyFn] = {}

    def __init__(self) -> None:
        self._fetcher = YahooFetcher()
        self._normalizer = Normalizer()
        self._register_builtin_strategies()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(
        self,
        ticker: str,
        strategy_name: str,
        start: str,
        end: str,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        strategy_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a backtest and return performance metrics.

        Args:
            ticker:          Ticker symbol.
            strategy_name:   Registered strategy identifier.
            start:           ISO-8601 start date.
            end:             ISO-8601 end date.
            initial_capital: Starting portfolio value.
            commission:      Commission rate per trade (e.g. 0.001 = 0.1%).
            strategy_params: Strategy-specific parameter overrides.

        Returns:
            Dict with equity curve, trades, and performance statistics.
        """
        if strategy_name not in self._STRATEGIES:
            raise ValueError(
                f"Unknown strategy '{strategy_name}'. "
                f"Available: {list(self._STRATEGIES)}"
            )

        logger.info("Backtesting %s with strategy '%s' [%s → %s].", ticker, strategy_name, start, end)

        # Fetch & normalise data
        raw = self._fetcher.fetch(ticker, start, end)
        df = self._normalizer.normalise_ohlcv(raw)

        # Generate signals
        strategy_fn = self._STRATEGIES[strategy_name]
        signals = strategy_fn(df)

        # Simulate portfolio
        equity_curve, trades = self._simulate(df, signals, initial_capital, commission)

        # Compute metrics
        metrics = self._compute_metrics(equity_curve, initial_capital)

        return {
            "ticker": ticker,
            "strategy": strategy_name,
            "start": start,
            "end": end,
            "initial_capital": initial_capital,
            "final_capital": equity_curve.iloc[-1],
            "equity_curve": equity_curve.to_dict(),
            "trades": trades,
            "metrics": metrics,
        }

    def register_strategy(self, name: str, fn: StrategyFn) -> None:
        """Register a custom strategy function.

        Args:
            name: Unique strategy identifier.
            fn:   Callable taking OHLCV DataFrame, returning signal Series.
        """
        self._STRATEGIES[name] = fn
        logger.info("Registered custom strategy '%s'.", name)

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    @staticmethod
    def _simulate(
        df: pd.DataFrame,
        signals: pd.Series,
        initial_capital: float,
        commission: float,
    ) -> tuple[pd.Series, list[dict[str, Any]]]:
        """Simulate portfolio returns based on daily signals."""
        cash = initial_capital
        shares = 0.0
        equity: list[float] = []
        trades: list[dict[str, Any]] = []

        for date, row in df.iterrows():
            price = row["close"]
            signal = signals.get(date, 0)

            if signal == 1 and shares == 0:
                # Buy
                cost = cash * (1 - commission)
                shares = cost / price
                cash = 0.0
                trades.append({"date": str(date), "action": "buy", "price": price, "shares": shares})

            elif signal == -1 and shares > 0:
                # Sell
                proceeds = shares * price * (1 - commission)
                cash = proceeds
                trades.append({"date": str(date), "action": "sell", "price": price, "shares": shares})
                shares = 0.0

            portfolio_value = cash + shares * price
            equity.append(portfolio_value)

        return pd.Series(equity, index=df.index), trades

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_metrics(equity: pd.Series, initial_capital: float) -> dict[str, Any]:
        returns = equity.pct_change().dropna()
        total_return = (equity.iloc[-1] / initial_capital - 1) * 100
        ann_return = ((equity.iloc[-1] / initial_capital) ** (252 / len(equity)) - 1) * 100
        ann_vol = returns.std() * math.sqrt(252) * 100
        sharpe = (ann_return - 5.0) / ann_vol if ann_vol > 0 else 0.0
        max_dd = ((equity / equity.cummax()) - 1).min() * 100
        calmar = ann_return / abs(max_dd) if max_dd != 0 else 0.0

        return {
            "total_return_pct": round(total_return, 3),
            "annualised_return_pct": round(ann_return, 3),
            "annualised_volatility_pct": round(ann_vol, 3),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown_pct": round(max_dd, 3),
            "calmar_ratio": round(calmar, 3),
            "num_trades": None,  # filled by caller
        }

    # ------------------------------------------------------------------
    # Built-in strategies
    # ------------------------------------------------------------------

    @classmethod
    def _register_builtin_strategies(cls) -> None:
        cls._STRATEGIES["buy_and_hold"] = cls._strategy_buy_and_hold
        cls._STRATEGIES["sma_crossover"] = cls._strategy_sma_crossover
        cls._STRATEGIES["rsi_mean_revert"] = cls._strategy_rsi_mean_revert
        cls._STRATEGIES["macd_signal"] = cls._strategy_macd_signal

    @staticmethod
    def _strategy_buy_and_hold(df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(0, index=df.index)
        signals.iloc[0] = 1
        return signals

    @staticmethod
    def _strategy_sma_crossover(df: pd.DataFrame) -> pd.Series:
        sma_50 = df["close"].rolling(50).mean()
        sma_200 = df["close"].rolling(200).mean()
        signal = pd.Series(0, index=df.index)
        signal[(sma_50 > sma_200) & (sma_50.shift(1) <= sma_200.shift(1))] = 1   # golden cross
        signal[(sma_50 < sma_200) & (sma_50.shift(1) >= sma_200.shift(1))] = -1  # death cross
        return signal

    @staticmethod
    def _strategy_rsi_mean_revert(df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        signal = pd.Series(0, index=df.index)
        signal[rsi < 30] = 1
        signal[rsi > 70] = -1
        return signal

    @staticmethod
    def _strategy_macd_signal(df: pd.DataFrame) -> pd.Series:
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        signal = pd.Series(0, index=df.index)
        signal[(macd > signal_line) & (macd.shift(1) <= signal_line.shift(1))] = 1
        signal[(macd < signal_line) & (macd.shift(1) >= signal_line.shift(1))] = -1
        return signal
