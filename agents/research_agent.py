"""
Research Agent — orchestrates deep-dive research on a ticker or sector.

Coordinates outputs from multiple sub-agents (fundamental, technical,
macro, news, sentiment) and synthesises them into a structured research
report, optionally using an LLM to generate narrative commentary.
"""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent, AgentError


class ResearchAgent(BaseAgent):
    """Produces a comprehensive research dossier for a given asset."""

    agent_name = "ResearchAgent"

    def __init__(self, llm_enabled: bool = False, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.llm_enabled = llm_enabled

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(
        self,
        ticker: str,
        agent_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Synthesise research from collected agent results.

        Args:
            ticker:        Target ticker symbol.
            agent_results: Dict keyed by agent_name → result envelope.

        Returns:
            Structured research report dict.
        """
        self.logger.info("Synthesising research report for %s.", ticker)

        sections = {
            "fundamental": self._extract(agent_results, "FundamentalAgent"),
            "technical": self._extract(agent_results, "TechnicalAnalysisAgent"),
            "sentiment": self._extract(agent_results, "SentimentAgent"),
            "macro": self._extract(agent_results, "MacroAgent"),
            "risk": self._extract(agent_results, "RiskAgent"),
            "forecast": self._extract(agent_results, "ForecastingAgent"),
            "regime": self._extract(agent_results, "RegimeAgent"),
        }

        summary = self._build_summary(ticker, sections)

        if self.llm_enabled:
            narrative = self._generate_narrative(ticker, sections)
        else:
            narrative = None

        return {
            "ticker": ticker,
            "summary": summary,
            "sections": sections,
            "narrative": narrative,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract(results: dict[str, Any], agent_name: str) -> Any:
        envelope = results.get(agent_name, {})
        if envelope.get("status") == "ok":
            return envelope.get("data")
        return {"error": envelope.get("error", "Not available")}

    @staticmethod
    def _build_summary(ticker: str, sections: dict[str, Any]) -> dict[str, Any]:
        """Derive a concise multi-signal summary."""
        signals: list[str] = []

        # Sentiment signal
        if isinstance(sections.get("sentiment"), dict):
            dominant = sections["sentiment"].get("aggregate", {}).get("dominant", "neutral")
            signals.append(f"Market sentiment: {dominant}")

        # Regime signal
        if isinstance(sections.get("regime"), dict):
            regime = sections["regime"].get("current_regime", "unknown")
            signals.append(f"Market regime: {regime}")

        # Technical signals
        if isinstance(sections.get("technical"), dict):
            tech_signals = sections["technical"].get("signals", {})
            for ind, sig in tech_signals.items():
                signals.append(f"{ind.upper()}: {sig}")

        # Risk signal
        if isinstance(sections.get("risk"), dict):
            per_asset = sections["risk"].get("per_asset", {})
            if ticker in per_asset:
                sharpe = per_asset[ticker].get("sharpe")
                if sharpe is not None:
                    signals.append(f"Sharpe ratio: {sharpe:.2f}")

        return {"ticker": ticker, "signals": signals}

    def _generate_narrative(self, ticker: str, sections: dict[str, Any]) -> str:
        """Optional: Generate LLM-based narrative commentary."""
        try:
            import openai  # type: ignore
        except ImportError:
            return "OpenAI package not installed. Narrative unavailable."

        client = openai.OpenAI(api_key=self.settings.openai_api_key)
        prompt = (
            f"You are a senior financial analyst. Write a concise investment research summary "
            f"for {ticker} based on the following data:\n\n"
            f"Signals: {sections.get('summary', {})}\n"
            f"Regime: {sections.get('regime', {}).get('current_regime')}\n"
            f"Forecast return: {sections.get('forecast', {}).get('expected_return_pct')}%\n"
            f"Risk (Sharpe): {sections.get('risk', {})}\n\n"
            f"Provide a 3-paragraph analysis covering outlook, risks, and recommendation."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("LLM narrative generation failed: %s", exc)
            return f"LLM narrative unavailable: {exc}"
