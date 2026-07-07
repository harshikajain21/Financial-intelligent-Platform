# create_explainability_agent.py

content = """
# agents/explainability_agent.py

from agents.base_agent import BaseAgent, AgentResult, AgentError
from datetime import datetime


class ExplainabilityAgent(BaseAgent):
    \"\"\"
    Agent 12: Explainability Agent

    Generates a detailed human-readable investment report
    from all other agents' outputs.

    Does NOT call external APIs — works purely from
    the data already collected by other agents.

    Output score is always 0 — this agent explains,
    it does not contribute to the BUY/HOLD/SELL decision.
    \"\"\"

    def __init__(self):
        super().__init__(name="ExplainabilityAgent", max_retries=1)

    def execute(self, symbol: str, report_data: dict = None, **kwargs) -> AgentResult:
        \"\"\"
        Args:
            symbol      : stock ticker
            report_data : dict containing all agent results from orchestrator
        \"\"\"
        if not report_data:
            raise AgentError("report_data is required")

        self.logger.info(f"Generating explanation report for {symbol}")

        scores       = report_data.get("scores", {})
        decision     = report_data.get("final_decision", "UNKNOWN")
        confidence   = report_data.get("confidence", 0)
        errors       = report_data.get("errors", [])
        agent_results = report_data.get("agent_results", {})

        # Generate each section of the report
        report = {
            "symbol"           : symbol,
            "generated_at"     : datetime.utcnow().isoformat(),
            "decision"         : decision,
            "confidence"       : confidence,
            "executive_summary": self._executive_summary(symbol, decision, confidence, scores),
            "signal_analysis"  : self._signal_analysis(scores),
            "agreement_map"    : self._agreement_map(scores, decision),
            "key_risks"        : self._key_risks(scores, agent_results),
            "what_would_change": self._what_would_change(scores, decision),
            "data_quality"     : self._data_quality(scores, errors),
            "disclaimer"       : self._disclaimer(),
        }

        self.logger.info(f"Explanation report generated for {symbol}")

        return AgentResult(
            agent_name = self.name,
            success    = True,
            data       = {"report": report},
            score      = 0.0,  # explainability never affects decision
            metadata   = {"symbol": symbol}
        )

    def _executive_summary(self, symbol, decision, confidence, scores) -> str:
        \"\"\"One paragraph plain English summary of the decision.\"\"\"

        # Count positive vs negative signals
        positive = sum(1 for s in scores.values() if s > 20)
        negative = sum(1 for s in scores.values() if s < -20)
        neutral  = len(scores) - positive - negative

        if decision == "BUY":
            strength = "strong" if confidence > 50 else "moderate" if confidence > 25 else "weak"
            return (
                f"Our AI system recommends BUYING {symbol} with {strength} conviction "
                f"({confidence:.1f}% confidence). "
                f"Out of {len(scores)} analytical signals evaluated, {positive} are positive, "
                f"{neutral} are neutral, and {negative} are negative. "
                f"The bullish case is supported by multiple independent signals "
                f"across technical, fundamental, and macro dimensions."
            )
        elif decision == "SELL":
            strength = "strong" if confidence > 50 else "moderate" if confidence > 25 else "weak"
            return (
                f"Our AI system recommends SELLING {symbol} with {strength} conviction "
                f"({confidence:.1f}% confidence). "
                f"Out of {len(scores)} analytical signals evaluated, {negative} are negative, "
                f"{neutral} are neutral, and {positive} are positive. "
                f"The bearish case is driven by deteriorating signals across multiple dimensions."
            )
        else:
            return (
                f"Our AI system recommends HOLDING {symbol} — the evidence is mixed "
                f"({confidence:.1f}% conviction). "
                f"Out of {len(scores)} signals, {positive} are positive, {negative} are negative, "
                f"and {neutral} are neutral. "
                f"The conflicting signals suggest waiting for clearer direction before acting."
            )

    def _signal_analysis(self, scores: dict) -> list:
        \"\"\"Detailed breakdown of each agent signal.\"\"\"
        signal_map = {
            "TechnicalAnalysisAgent": {
                "name": "Technical Analysis",
                "description": "Price chart patterns, momentum indicators (RSI, MACD, EMA, Bollinger Bands)"
            },
            "NewsIntelligenceAgent": {
                "name": "News Sentiment",
                "description": "AI analysis of recent financial news and media coverage"
            },
            "SocialSentimentAgent": {
                "name": "Social Sentiment",
                "description": "Retail investor sentiment from social media and trading forums"
            },
            "MacroeconomicIntelligenceAgent": {
                "name": "Macroeconomic Conditions",
                "description": "Interest rates, inflation, GDP growth, unemployment data"
            },
            "PortfolioRiskAgent": {
                "name": "Risk Assessment",
                "description": "Volatility, Sharpe ratio, maximum drawdown, Value at Risk"
            },
            "FundamentalAnalysisAgent": {
                "name": "Business Fundamentals",
                "description": "Revenue growth, profit margins, debt levels, return on equity"
            },
            "RegimeDetectionAgent": {
                "name": "Market Regime",
                "description": "Overall market environment — bull, bear, sideways, or high volatility"
            },
            "AnomalyDetectionAgent": {
                "name": "Anomaly Detection",
                "description": "Unusual volume, price gaps, statistical outliers in trading activity"
            },
            "ForecastingAgent": {
                "name": "Price Forecast",
                "description": "AI price predictions using Prophet, ARIMA, and Linear ensemble models"
            },
        }

        signals = []
        for agent_key, score in scores.items():
            if agent_key == "MarketDataAgent":
                continue
            info = signal_map.get(agent_key, {"name": agent_key, "description": ""})

            if score >= 40:
                verdict = "STRONGLY BULLISH"
                color   = "green"
            elif score >= 10:
                verdict = "MILDLY BULLISH"
                color   = "light_green"
            elif score >= -10:
                verdict = "NEUTRAL"
                color   = "gray"
            elif score >= -40:
                verdict = "MILDLY BEARISH"
                color   = "light_red"
            else:
                verdict = "STRONGLY BEARISH"
                color   = "red"

            signals.append({
                "agent"      : info["name"],
                "score"      : round(score, 2),
                "verdict"    : verdict,
                "color"      : color,
                "description": info["description"],
            })

        # Sort by score descending
        return sorted(signals, key=lambda x: x["score"], reverse=True)

    def _agreement_map(self, scores: dict, decision: str) -> dict:
        \"\"\"Which agents agree with the decision, which disagree.\"\"\"
        filtered = {k: v for k, v in scores.items() if k != "MarketDataAgent"}

        agreeing    = []
        disagreeing = []
        neutral     = []

        for agent, score in filtered.items():
            name = agent.replace("Agent","").replace("Intelligence","").strip()
            if decision == "BUY":
                if score > 10:
                    agreeing.append(name)
                elif score < -10:
                    disagreeing.append(name)
                else:
                    neutral.append(name)
            elif decision == "SELL":
                if score < -10:
                    agreeing.append(name)
                elif score > 10:
                    disagreeing.append(name)
                else:
                    neutral.append(name)
            else:
                neutral.append(name)

        return {
            "agreeing"    : agreeing,
            "disagreeing" : disagreeing,
            "neutral"     : neutral,
        }

    def _key_risks(self, scores: dict, agent_results: dict) -> list:
        \"\"\"Identify the top risks regardless of overall decision.\"\"\"
        risks = []

        risk_score = scores.get("PortfolioRiskAgent", 0)
        if risk_score < -30:
            risks.append("HIGH VOLATILITY: This stock has shown significant price swings recently. Position sizing should be conservative.")

        tech_score = scores.get("TechnicalAnalysisAgent", 0)
        if tech_score < -30:
            risks.append("BEARISH TECHNICALS: Price chart patterns are weak. Short-term downside pressure may continue.")

        news_score = scores.get("NewsIntelligenceAgent", 0)
        if news_score < -20:
            risks.append("NEGATIVE NEWS FLOW: Recent media coverage is unfavorable. Monitor for further negative developments.")

        regime_score = scores.get("RegimeDetectionAgent", 0)
        if regime_score < -30:
            risks.append("BEAR MARKET CONDITIONS: The overall market environment is unfavorable. Even good stocks struggle in bear markets.")

        forecast_score = scores.get("ForecastingAgent", 0)
        if forecast_score < -30:
            risks.append("NEGATIVE PRICE FORECAST: AI models predict downside over the next 30 days based on current trends.")

        anomaly_score = scores.get("AnomalyDetectionAgent", 0)
        if anomaly_score < 40:
            risks.append("UNUSUAL TRADING ACTIVITY: Abnormal volume or price patterns detected. Exercise caution.")

        if not risks:
            risks.append("No major risk flags detected at this time. Standard market risks still apply.")

        return risks

    def _what_would_change(self, scores: dict, decision: str) -> list:
        \"\"\"What signals would need to change to flip the decision.\"\"\"
        changes = []

        if decision == "BUY":
            if scores.get("TechnicalAnalysisAgent", 0) < 0:
                changes.append("A breakdown below key moving averages would weaken the technical case.")
            if scores.get("NewsIntelligenceAgent", 0) < 0:
                changes.append("Significantly negative news (earnings miss, regulatory action) could shift sentiment.")
            changes.append("A deterioration in macroeconomic conditions (rate hikes, recession signals) would reduce the bullish case.")

        elif decision == "SELL":
            if scores.get("FundamentalAnalysisAgent", 0) > 50:
                changes.append("Strong earnings beat or positive guidance could reverse the bearish trend.")
            changes.append("A confirmed technical breakout above resistance levels would improve the outlook.")
            changes.append("Broader market recovery (bull regime) would provide tailwinds even for weak stocks.")

        else:  # HOLD
            changes.append("A clear technical breakout with volume confirmation would trigger a BUY signal.")
            changes.append("Breakdown below key support levels would trigger a SELL signal.")
            changes.append("Strong earnings report would likely push this to BUY territory.")

        return changes

    def _data_quality(self, scores: dict, errors: list) -> dict:
        \"\"\"Report on data completeness.\"\"\"
        total_agents  = 9
        failed_agents = len(errors)
        success_rate  = round(((total_agents - failed_agents) / total_agents) * 100, 1)

        quality = "EXCELLENT" if success_rate == 100 else \\
                  "GOOD"      if success_rate >= 78  else \\
                  "FAIR"      if success_rate >= 56  else "POOR"

        return {
            "success_rate"  : success_rate,
            "quality"       : quality,
            "agents_used"   : total_agents - failed_agents,
            "agents_failed" : failed_agents,
            "failed_list"   : [e.replace("Agent","") for e in errors],
            "note"          : "Higher success rate = more reliable decision" if failed_agents > 0
                              else "All data sources available — maximum reliability"
        }

    def _disclaimer(self) -> str:
        return (
            "This report is generated by an AI system for informational purposes only. "
            "It does not constitute financial advice. Past performance does not guarantee "
            "future results. Always consult a qualified financial advisor before making "
            "investment decisions. The AI system may be wrong."
        )

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if not result.data.get("report"):
            return False
        return True
"""

with open("agents/explainability_agent.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("agents/explainability_agent.py written successfully")