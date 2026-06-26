"""
Sentiment Agent — scores financial text using NLP models.

Supports:
  - FinBERT (via transformers)  for domain-specific financial sentiment
  - VADER                        for lightweight rule-based scoring
  - Aggregation across article corpora
"""

from __future__ import annotations

from typing import Any, Literal

from agents.base_agent import BaseAgent, AgentError


SentimentLabel = Literal["positive", "neutral", "negative"]


class SentimentAgent(BaseAgent):
    """Classifies sentiment of financial news articles or arbitrary text."""

    agent_name = "SentimentAgent"

    _SUPPORTED_MODELS = ("finbert", "vader")

    def __init__(self, model: str = "finbert", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if model not in self._SUPPORTED_MODELS:
            raise ValueError(f"model must be one of {self._SUPPORTED_MODELS}")
        self.model_name = model
        self._pipeline = None  # lazy-loaded on first use

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(self, texts: list[str]) -> dict[str, Any]:
        """Score a list of text snippets.

        Args:
            texts: List of strings (e.g. article headlines/descriptions).

        Returns:
            Dict with per-text scores and an aggregate sentiment summary.
        """
        if not texts:
            raise AgentError("No texts provided for sentiment analysis.")

        self.logger.info(
            "Running sentiment analysis on %d texts using %s.",
            len(texts),
            self.model_name,
        )

        scores = self._score_texts(texts)
        aggregate = self._aggregate(scores)

        return {
            "model": self.model_name,
            "scores": scores,
            "aggregate": aggregate,
        }

    # ------------------------------------------------------------------
    # Scoring back-ends
    # ------------------------------------------------------------------

    def _score_texts(self, texts: list[str]) -> list[dict[str, Any]]:
        if self.model_name == "finbert":
            return self._score_finbert(texts)
        return self._score_vader(texts)

    def _score_finbert(self, texts: list[str]) -> list[dict[str, Any]]:
        """Score texts with FinBERT (transformers)."""
        try:
            from transformers import pipeline  # type: ignore
        except ImportError as exc:
            raise AgentError(
                "transformers package not installed. "
                "Run: pip install transformers torch"
            ) from exc

        if self._pipeline is None:
            self.logger.info("Loading FinBERT pipeline (first call)…")
            self._pipeline = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                top_k=None,
            )

        results = []
        for text, raw in zip(texts, self._pipeline(texts, truncation=True, max_length=512)):
            label_scores = {item["label"].lower(): item["score"] for item in raw}
            dominant = max(label_scores, key=label_scores.__getitem__)
            results.append({
                "text": text[:120],
                "label": dominant,
                "scores": label_scores,
            })
        return results

    def _score_vader(self, texts: list[str]) -> list[dict[str, Any]]:
        """Score texts with VADER (vaderSentiment)."""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
        except ImportError as exc:
            raise AgentError(
                "vaderSentiment not installed. Run: pip install vaderSentiment"
            ) from exc

        analyzer = SentimentIntensityAnalyzer()
        results = []
        for text in texts:
            vs = analyzer.polarity_scores(text)
            compound = vs["compound"]
            if compound >= 0.05:
                label: SentimentLabel = "positive"
            elif compound <= -0.05:
                label = "negative"
            else:
                label = "neutral"
            results.append({"text": text[:120], "label": label, "scores": vs})
        return results

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
        from collections import Counter

        label_counts: Counter[str] = Counter(s["label"] for s in scores)
        total = len(scores)
        return {
            "total": total,
            "positive": label_counts.get("positive", 0),
            "neutral": label_counts.get("neutral", 0),
            "negative": label_counts.get("negative", 0),
            "dominant": label_counts.most_common(1)[0][0] if total else "neutral",
            "positive_pct": round(label_counts.get("positive", 0) / total * 100, 2) if total else 0,
            "negative_pct": round(label_counts.get("negative", 0) / total * 100, 2) if total else 0,
        }
