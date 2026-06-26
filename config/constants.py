"""
Constants — static application-wide constants.

These are non-environment-dependent values that define default
behaviours, thresholds, and lookup tables.
"""

from __future__ import annotations

# ------------------------------------------------------------------
# Signal fusion weights (must sum to 1.0)
# ------------------------------------------------------------------
SIGNAL_WEIGHTS: dict[str, float] = {
    "technical": 0.25,
    "fundamental": 0.20,
    "regime": 0.20,
    "risk": 0.15,
    "sentiment": 0.10,
    "macro": 0.10,
}

assert abs(sum(SIGNAL_WEIGHTS.values()) - 1.0) < 1e-9, "Signal weights must sum to 1.0"

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
LOG_LEVELS: dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# ------------------------------------------------------------------
# Technical analysis defaults
# ------------------------------------------------------------------
TECHNICAL_DEFAULTS: dict[str, int | float] = {
    "sma_short": 20,
    "sma_medium": 50,
    "sma_long": 200,
    "ema_fast": 12,
    "ema_slow": 26,
    "macd_signal": 9,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "bb_window": 20,
    "bb_std": 2.0,
    "atr_period": 14,
}

# ------------------------------------------------------------------
# Risk defaults
# ------------------------------------------------------------------
RISK_DEFAULTS: dict[str, float] = {
    "confidence_level": 0.95,
    "risk_free_rate": 0.05,
    "trading_days": 252,
}

# ------------------------------------------------------------------
# Forecasting
# ------------------------------------------------------------------
FORECAST_DEFAULTS: dict[str, int | float] = {
    "horizon_days": 30,
    "confidence_interval": 0.95,
}

# ------------------------------------------------------------------
# Market regime labels
# ------------------------------------------------------------------
REGIME_LABELS: list[str] = ["bull", "bear", "sideways", "volatile"]

# ------------------------------------------------------------------
# Alert severity levels
# ------------------------------------------------------------------
ALERT_SEVERITIES: list[str] = ["INFO", "WARNING", "CRITICAL"]

# ------------------------------------------------------------------
# Supported data intervals
# ------------------------------------------------------------------
SUPPORTED_INTERVALS: list[str] = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]

# ------------------------------------------------------------------
# FRED series map (kept here for reference; also used in MacroAgent)
# ------------------------------------------------------------------
FRED_SERIES: dict[str, str] = {
    "gdp_growth": "A191RL1Q225SBEA",
    "cpi": "CPIAUCSL",
    "core_cpi": "CPILFESL",
    "unemployment": "UNRATE",
    "fed_funds_rate": "FEDFUNDS",
    "treasury_10y": "GS10",
    "consumer_confidence": "UMCSENT",
}
