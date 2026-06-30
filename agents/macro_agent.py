# agents/macro_agent.py

from fredapi import Fred
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent, AgentResult, AgentError


class MacroeconomicIntelligenceAgent(BaseAgent):
    """
    Agent 5: Macroeconomic Intelligence Agent

    Fetches key macroeconomic indicators from FRED (Federal Reserve
    Economic Data) and produces an overall "economic outlook" score.

    Unlike other agents, this score is NOT stock-specific — it reflects
    the broader environment all stocks operate in.

    Score interpretation:
        +100 = very favorable macro environment for stocks
           0 = neutral / mixed conditions
        -100 = very unfavorable (recession risk, high rates, high inflation)
    """

    # FRED series codes — these are fixed identifiers for each economic metric
    SERIES = {
        "fed_funds_rate"  : "FEDFUNDS",     # interest rate set by the Fed
        "cpi"             : "CPIAUCSL",     # inflation (Consumer Price Index)
        "unemployment"    : "UNRATE",       # unemployment rate
        "gdp_growth"      : "A191RL1Q225SBEA",  # real GDP growth rate
        "treasury_10y"    : "DGS10",        # 10-year treasury yield
    }

    def __init__(self):
        super().__init__(name="MacroeconomicIntelligenceAgent", max_retries=2)

        from config.settings import settings
        if not settings.FRED_API_KEY:
            raise AgentError("FRED_API_KEY is not set in .env")

        self.fred = Fred(api_key=settings.FRED_API_KEY)

    def execute(self, symbol: str = None, **kwargs) -> AgentResult:
        """
        Note: symbol is accepted for interface consistency with other agents
        but not actually used — macro data applies to the whole market.
        """
        self.logger.info("Fetching macroeconomic indicators")

        # --- Step 1: Fetch each indicator ---
        indicators = self._fetch_all_indicators()

        # --- Step 2: Score each indicator individually ---
        sub_scores = self._score_indicators(indicators)

        # --- Step 3: Combine into overall macro score ---
        score = self._calculate_macro_score(sub_scores)

        self.logger.info(
            f"Macro Score: {score} | "
            f"Fed Funds: {indicators['fed_funds_rate']}% | "
            f"Unemployment: {indicators['unemployment']}% | "
            f"10Y Yield: {indicators['treasury_10y']}%"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={
                "indicators": indicators,
                "sub_scores": sub_scores,
            },
            score=score,
            metadata={"as_of": datetime.utcnow().isoformat()}
        )

    def _fetch_all_indicators(self) -> dict:
        """
        Fetch the latest value for each macro indicator.
        FRED returns a time series — we take the most recent value.
        """
        indicators = {}

        for name, series_code in self.SERIES.items():
            try:
                data = self.fred.get_series(
                    series_code,
                    observation_start=datetime.now() - timedelta(days=400)
                )
                # Drop missing values, take the latest
                data = data.dropna()
                if len(data) == 0:
                    indicators[name] = None
                else:
                    indicators[name] = round(float(data.iloc[-1]), 3)
            except Exception as e:
                self.logger.warning(f"Failed to fetch {name} ({series_code}): {e}")
                indicators[name] = None

        if all(v is None for v in indicators.values()):
            raise AgentError("Failed to fetch any macroeconomic data from FRED")

        return indicators

    def _score_indicators(self, ind: dict) -> dict:
        """
        Convert each raw indicator into a -100 to +100 sub-score.
        These thresholds are based on general macro/market theory:
            - Moderate inflation (~2%) is healthy, high inflation is bad
            - Low-moderate interest rates support stock valuations
            - Low unemployment is generally good, but extremely low can mean overheating
            - Positive GDP growth is good, contraction is bad
        """
        scores = {}

        # --- Fed Funds Rate ---
        # Lower rates = cheaper borrowing = good for stocks
        # Above 5% = restrictive, below 2% = very accommodative
        rate = ind.get("fed_funds_rate")
        if rate is not None:
            if rate < 2:
                scores["fed_funds_rate"] = 60
            elif rate < 4:
                scores["fed_funds_rate"] = 20
            elif rate < 5.5:
                scores["fed_funds_rate"] = -20
            else:
                scores["fed_funds_rate"] = -60
        else:
            scores["fed_funds_rate"] = 0

        # --- Unemployment Rate ---
        # Healthy range is roughly 3.5%-5%. Too high = recession risk.
        # Too low (<3%) can signal overheating / wage inflation pressure
        unemployment = ind.get("unemployment")
        if unemployment is not None:
            if unemployment < 3.5:
                scores["unemployment"] = 20   # mild concern, overheating
            elif unemployment <= 5.0:
                scores["unemployment"] = 60   # healthy
            elif unemployment <= 6.5:
                scores["unemployment"] = -20
            else:
                scores["unemployment"] = -70  # recession territory
        else:
            scores["unemployment"] = 0

        # --- GDP Growth ---
        # Positive growth = good. Negative = recession risk.
        gdp = ind.get("gdp_growth")
        if gdp is not None:
            if gdp >= 3:
                scores["gdp_growth"] = 70
            elif gdp >= 1:
                scores["gdp_growth"] = 30
            elif gdp >= 0:
                scores["gdp_growth"] = -10
            else:
                scores["gdp_growth"] = -70   # contraction
        else:
            scores["gdp_growth"] = 0

        # --- 10-Year Treasury Yield ---
        # Higher yields make bonds more attractive vs stocks (competition for capital)
        # Also raises borrowing costs for companies
        treasury = ind.get("treasury_10y")
        if treasury is not None:
            if treasury < 3:
                scores["treasury_10y"] = 50
            elif treasury < 4.5:
                scores["treasury_10y"] = 10
            else:
                scores["treasury_10y"] = -50
        else:
            scores["treasury_10y"] = 0

        return scores

    def _calculate_macro_score(self, sub_scores: dict) -> float:
        """
        Weighted average of all sub-scores.
        Fed Funds Rate and GDP Growth weighted slightly higher —
        they tend to have the biggest direct market impact.
        """
        weights = {
            "fed_funds_rate" : 0.3,
            "unemployment"   : 0.2,
            "gdp_growth"     : 0.3,
            "treasury_10y"   : 0.2,
        }

        weighted_sum = sum(
            sub_scores[k] * weights[k] for k in weights if k in sub_scores
        )

        return round(max(min(weighted_sum, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True