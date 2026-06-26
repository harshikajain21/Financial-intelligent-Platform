"""
Decision Fusion Engine — combines signals from all agents into a unified
buy / hold / sell recommendation with a confidence score.

Signal weighting is configurable; defaults are set in config/constants.py.
"""

from __future__ import annotations

from typing import Any

from config.settings import Settings
from config.constants import SIGNAL_WEIGHTS
from utils.logger import get_logger

logger = get_logger("DecisionFusion")

# Valid recommendation labels
_LABELS = ("strong_buy", "buy", "hold", "sell", "strong_sell")


class DecisionFusion:
    """Fuses multi-agent signals into a final investment recommendation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.weights = SIGNAL_WEIGHTS

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fuse(
        self,
        per_ticker: dict[str, Any],
        sentiment: dict[str, Any],
        macro: dict[str, Any],
    ) -> dict[str, Any]:
        """Fuse all agent outputs into a per-ticker recommendation.

        Args:
            per_ticker: Dict mapping ticker → dict of agent results.
            sentiment:  Aggregate sentiment result envelope.
            macro:      Macro agent result envelope.

        Returns:
            Dict mapping ticker → {recommendation, confidence, signal_breakdown}.
        """
        logger.info("Fusing signals for %d ticker(s).", len(per_ticker))
        output: dict[str, Any] = {}

        sentiment_score = self._sentiment_to_score(sentiment)
        macro_score = self._macro_to_score(macro)

        for ticker, results in per_ticker.items():
            score = self._compute_score(results, sentiment_score, macro_score)
            rec, confidence = self._score_to_recommendation(score)
            output[ticker] = {
                "recommendation": rec,
                "confidence": confidence,
                "composite_score": round(score, 4),
                "signal_breakdown": self._build_breakdown(results, sentiment_score, macro_score),
            }

        return output

    # ------------------------------------------------------------------
    # Signal extractors
    # ------------------------------------------------------------------

    def _compute_score(
        self,
        results: dict[str, Any],
        sentiment_score: float,
        macro_score: float,
    ) -> float:
        """Compute a composite score in [-1, +1] from all signals."""
        score = 0.0
        total_weight = 0.0

        # Technical signals
        tech_score = self._technical_score(results.get("TechnicalAnalysisAgent", {}))
        if tech_score is not None:
            w = self.weights.get("technical", 0.25)
            score += tech_score * w
            total_weight += w

        # Risk-adjusted score
        risk_score = self._risk_score(results.get("RiskAgent", {}))
        if risk_score is not None:
            w = self.weights.get("risk", 0.15)
            score += risk_score * w
            total_weight += w

        # Regime
        regime_score = self._regime_score(results.get("RegimeAgent", {}))
        if regime_score is not None:
            w = self.weights.get("regime", 0.20)
            score += regime_score * w
            total_weight += w

        # Fundamental
        fund_score = self._fundamental_score(results.get("FundamentalAgent", {}))
        if fund_score is not None:
            w = self.weights.get("fundamental", 0.20)
            score += fund_score * w
            total_weight += w

        # Sentiment
        w = self.weights.get("sentiment", 0.10)
        score += sentiment_score * w
        total_weight += w

        # Macro
        w = self.weights.get("macro", 0.10)
        score += macro_score * w
        total_weight += w

        return score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _technical_score(tech_result: dict[str, Any]) -> float | None:
        data = tech_result.get("data", {})
        if not data:
            return None
        signals = data.get("signals", {})
        s = 0.0
        count = 0
        for key, val in signals.items():
            if val in ("bullish", "oversold"):
                s += 1.0
                count += 1
            elif val in ("bearish", "overbought"):
                s -= 1.0
                count += 1
        return s / count if count > 0 else 0.0

    @staticmethod
    def _risk_score(risk_result: dict[str, Any]) -> float | None:
        data = risk_result.get("data", {})
        if not data:
            return None
        per_asset = data.get("per_asset", {})
        sharpes = [v.get("sharpe", 0) for v in per_asset.values() if isinstance(v, dict)]
        if not sharpes:
            return None
        avg_sharpe = sum(sharpes) / len(sharpes)
        # Normalise to [-1, +1] roughly: sharpe 2 → +1, -2 → -1
        return max(-1.0, min(1.0, avg_sharpe / 2.0))

    @staticmethod
    def _regime_score(regime_result: dict[str, Any]) -> float | None:
        data = regime_result.get("data", {})
        if not data:
            return None
        regime_map = {"bull": 1.0, "sideways": 0.0, "bear": -1.0, "volatile": -0.5}
        return regime_map.get(data.get("current_regime", "sideways"), 0.0)

    @staticmethod
    def _fundamental_score(fund_result: dict[str, Any]) -> float | None:
        data = fund_result.get("data", {})
        if not data:
            return None
        raw_score = data.get("valuation_score", {}).get("score", 0)
        return max(-1.0, min(1.0, raw_score / 5.0))

    @staticmethod
    def _sentiment_to_score(sentiment_result: dict[str, Any]) -> float:
        data = sentiment_result.get("data", {})
        if not data:
            return 0.0
        agg = data.get("aggregate", {})
        total = agg.get("total", 1) or 1
        return (agg.get("positive", 0) - agg.get("negative", 0)) / total

    @staticmethod
    def _macro_to_score(macro_result: dict[str, Any]) -> float:
        """Simplified macro score: +0.2 for accommodative, -0.2 for restrictive."""
        data = macro_result.get("data", {})
        if not data:
            return 0.0
        interpretation = data.get("interpretation", {})
        ffr = interpretation.get("fed_funds_rate", "")
        if "Accommodative" in ffr:
            return 0.3
        elif "Restrictive" in ffr:
            return -0.3
        return 0.0

    @staticmethod
    def _score_to_recommendation(score: float) -> tuple[str, float]:
        """Convert composite score to label and confidence."""
        confidence = min(1.0, abs(score))
        if score >= 0.6:
            return "strong_buy", confidence
        elif score >= 0.2:
            return "buy", confidence
        elif score <= -0.6:
            return "strong_sell", confidence
        elif score <= -0.2:
            return "sell", confidence
        return "hold", confidence

    def _build_breakdown(
        self,
        results: dict[str, Any],
        sentiment_score: float,
        macro_score: float,
    ) -> dict[str, Any]:
        return {
            "technical": self._technical_score(results.get("TechnicalAnalysisAgent", {})),
            "risk": self._risk_score(results.get("RiskAgent", {})),
            "regime": self._regime_score(results.get("RegimeAgent", {})),
            "fundamental": self._fundamental_score(results.get("FundamentalAgent", {})),
            "sentiment": sentiment_score,
            "macro": macro_score,
            "weights": self.weights,
        }
