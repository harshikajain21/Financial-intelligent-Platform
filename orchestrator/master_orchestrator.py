# orchestrator/master_orchestrator.py

from typing import Optional
from datetime import datetime
from utils.logger import get_logger
from agents.base_agent import AgentResult
from agents.market_data_agent import MarketDataAgent
from agents.technical_analysis_agent import TechnicalAnalysisAgent
from agents.news_agent import NewsIntelligenceAgent
from agents.sentiment_agent import SocialSentimentAgent
from agents.macro_agent import MacroeconomicIntelligenceAgent
from agents.risk_agent import PortfolioRiskAgent
from agents.fundamental_agent import FundamentalAnalysisAgent
from agents.regime_agent import RegimeDetectionAgent
from agents.anomaly_agent import AnomalyDetectionAgent


class AnalysisReport:
    """
    The final output of one full orchestrator run.
    Contains results from every agent + a final decision.
    """

    def __init__(self, symbol: str):
        self.symbol          = symbol
        self.timestamp       = datetime.utcnow().isoformat()
        self.agent_results   = {}
        self.scores          = {}
        self.final_decision  = None
        self.confidence      = None
        self.errors          = []
        self.duration_ms     = None

    def add_result(self, agent_name: str, result: AgentResult):
        self.agent_results[agent_name] = result
        if result.success and result.score is not None:
            self.scores[agent_name] = result.score
        else:
            self.errors.append(agent_name)

    def to_dict(self) -> dict:
        return {
            "symbol"         : self.symbol,
            "timestamp"      : self.timestamp,
            "final_decision" : self.final_decision,
            "confidence"     : self.confidence,
            "scores"         : self.scores,
            "errors"         : self.errors,
            "duration_ms"    : self.duration_ms,
            "agent_results"  : {
                name: result.to_dict()
                for name, result in self.agent_results.items()
            }
        }


class MasterOrchestrator:
    """
    Master Orchestrator — coordinates all agents.

    Currently wired agents:
        Stage 1 — Data Collection  : MarketDataAgent
        Stage 2 — Analysis         : TechnicalAnalysisAgent
                                      NewsIntelligenceAgent
                                      SocialSentimentAgent
        Stage 0 — Macro (cached)   : MacroeconomicIntelligenceAgent
    """

    # How long to cache macro data before refetching (in seconds)
    MACRO_CACHE_SECONDS = 3600   # 1 hour — macro data doesn't change fast

    def __init__(self):
        self.logger = get_logger("MasterOrchestrator")

        self.market_agent    = MarketDataAgent()
        self.tech_agent      = TechnicalAnalysisAgent()
        self.news_agent      = NewsIntelligenceAgent()
        self.sentiment_agent = SocialSentimentAgent(
            finbert_pipeline=self.news_agent.finbert
        )
        self.macro_agent     = MacroeconomicIntelligenceAgent()
        self.risk_agent = PortfolioRiskAgent()
        self.fundamental_agent = FundamentalAnalysisAgent()
        self.regime_agent = RegimeDetectionAgent()
        self.anomaly_agent = AnomalyDetectionAgent()


        # Macro cache — shared across all symbols in this session
        self._macro_cache: Optional[AgentResult] = None
        self._macro_cache_time: Optional[datetime] = None

        self.logger.info("MasterOrchestrator initialized with 9 agents")

    def analyze(self, symbol: str) -> AnalysisReport:
        self.logger.info(f"Starting full analysis for {symbol}")
        start_time = datetime.utcnow()

        report = AnalysisReport(symbol)

        # ── Stage 0: Macro (cached, not stock-specific) ───────────
        macro_result = self._get_macro_data()
        report.add_result("MacroeconomicIntelligenceAgent", macro_result)

        # ── Stage 1: Data Collection ──────────────────────────────
        market_result = self._run_market_data(symbol)
        report.add_result("MarketDataAgent", market_result)

        if not market_result.success:
            self.logger.error(f"Market data failed for {symbol} — aborting")
            report.final_decision = "UNAVAILABLE"
            report.confidence = 0
            return report

        # ── Stage 2: Analysis Agents ──────────────────────────────
        price_history = market_result.data["price_history"]

        tech_result = self._run_technical_analysis(symbol, price_history)
        report.add_result("TechnicalAnalysisAgent", tech_result)

        news_result = self._run_news_analysis(symbol)
        report.add_result("NewsIntelligenceAgent", news_result)

        sentiment_result = self._run_sentiment_analysis(symbol)
        report.add_result("SocialSentimentAgent", sentiment_result)

        risk_result = self._run_risk_analysis(symbol, price_history)
        report.add_result("PortfolioRiskAgent", risk_result)

        fundamental_result = self._run_fundamental_analysis(symbol)
        report.add_result("FundamentalAnalysisAgent", fundamental_result)

        regime_result = self._run_regime_detection(symbol,price_history)
        report.add_result("RegimeDetectionAgent", regime_result)

        anomaly_result = self._run_anomaly_detection(symbol, price_history)
        report.add_result("AnomalyDetectionAgent", anomaly_result)



        # ── Stage 3: Decision Fusion ──────────────────────────────
        self._make_decision(report)

        # ── Finalize ──────────────────────────────────────────────
        end_time = datetime.utcnow()
        report.duration_ms = round(
            (end_time - start_time).total_seconds() * 1000, 2
        )

        self.logger.info(
            f"{symbol} analysis complete | "
            f"Decision: {report.final_decision} | "
            f"Confidence: {report.confidence}% | "
            f"Duration: {report.duration_ms}ms"
        )

        return report

    # ── Private runner methods ────────────────────────────────────

    def _get_macro_data(self) -> AgentResult:
        """
        Returns cached macro data if still fresh, otherwise fetches new.
        Macro conditions don't change minute to minute, so we avoid
        hammering the FRED API unnecessarily.
        """
        now = datetime.utcnow()

        if (self._macro_cache is not None and self._macro_cache_time is not None):
            age_seconds = (now - self._macro_cache_time).total_seconds()
            if age_seconds < self.MACRO_CACHE_SECONDS:
                self.logger.info(f"Using cached macro data (age: {int(age_seconds)}s)")
                return self._macro_cache

        self.logger.info("Stage 0: Running MacroeconomicIntelligenceAgent (fresh fetch)")
        result = self.macro_agent.run()

        self._macro_cache = result
        self._macro_cache_time = now

        return result

    def _run_market_data(self, symbol: str) -> AgentResult:
        self.logger.info(f"Stage 1: Running MarketDataAgent for {symbol}")
        return self.market_agent.run(symbol)

    def _run_technical_analysis(self, symbol: str, price_history: list) -> AgentResult:
        self.logger.info(f"Stage 2: Running TechnicalAnalysisAgent for {symbol}")
        return self.tech_agent.run(symbol, price_history=price_history)

    def _run_news_analysis(self, symbol: str) -> AgentResult:
        self.logger.info(f"Stage 2b: Running NewsIntelligenceAgent for {symbol}")
        return self.news_agent.run(symbol)

    def _run_sentiment_analysis(self, symbol: str) -> AgentResult:
        self.logger.info(f"Stage 2c: Running SocialSentimentAgent for {symbol}")
        return self.sentiment_agent.run(symbol)

    def _run_risk_analysis(self, symbol: str, price_history: list) -> AgentResult:
        self.logger.info(f"Stage 2d: Running PortfolioRiskAgent for {symbol}")
        return self.risk_agent.run(symbol, price_history=price_history)

    def _run_fundamental_analysis(self, symbol: str) -> AgentResult:
        self.logger.info(f"Stage 2e: Running FundamentalAnalysisAgent for {symbol}")
        return self.fundamental_agent.run(symbol)
    
    def _run_regime_detection(self, symbol: str, price_history: list) -> AgentResult:
        self.logger.info(f"Stage 2f: Running RegimeDetectionAgent for {symbol}")
        return self.regime_agent.run(symbol, price_history=price_history)
    
    def _run_anomaly_detection(self, symbol: str, price_history: list) -> AgentResult:
        self.logger.info(f"Stage 2g: Running AnomalyDetectionAgent for {symbol}")
        return self.anomaly_agent.run(symbol, price_history=price_history)

    # ── Decision Fusion ───────────────────────────────────────────

    def _make_decision(self, report: AnalysisReport):
        """
        Combine all agent scores into a final BUY / HOLD / SELL decision.
        """
        weights = {
    "TechnicalAnalysisAgent"          : 0.20,
    "NewsIntelligenceAgent"           : 0.10,
    "SocialSentimentAgent"            : 0.10,
    "MacroeconomicIntelligenceAgent"  : 0.15,
    "PortfolioRiskAgent"              : 0.15,
    "FundamentalAnalysisAgent"        : 0.10,
    "RegimeDetectionAgent"            : 0.10,
    "AnomalyDetectionAgent"           : 0.10,
}
        if not report.scores:
            report.final_decision = "HOLD"
            report.confidence = 0
            return

        weighted_sum = 0.0
        total_weight = 0.0

        for agent_name, weight in weights.items():
            if agent_name in report.scores:
                weighted_sum += report.scores[agent_name] * weight
                total_weight += weight

        if total_weight == 0:
            report.final_decision = "HOLD"
            report.confidence = 0
            return

        final_score = weighted_sum / total_weight

        if final_score >= 20:
            report.final_decision = "BUY"
        elif final_score <= -20:
            report.final_decision = "SELL"
        else:
            report.final_decision = "HOLD"

        report.confidence = round(min(abs(final_score), 100), 2)

        self.logger.info(
            f"Decision fusion | Score: {final_score:.2f} | "
            f"Decision: {report.final_decision} | "
            f"Confidence: {report.confidence}%"
        )