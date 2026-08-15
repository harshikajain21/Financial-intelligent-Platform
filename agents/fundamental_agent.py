# agents/fundamental_agent.py

import requests
from agents.base_agent import BaseAgent, AgentResult, AgentError
from config.settings import settings


class FundamentalAnalysisAgent(BaseAgent):
    """
    Agent 9: Fundamental Analysis Agent
    Now sourced from Financial Modeling Prep (FMP) instead of yfinance.
    Score interpretation unchanged: +100 excellent, 0 mixed, -100 poor.
    """

    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self):
        super().__init__(name="FundamentalAnalysisAgent", max_retries=2)
        self.api_key = settings.FMP_API_KEY

    def execute(self, symbol: str, **kwargs) -> AgentResult:
        self.logger.info(f"Running fundamental analysis for {symbol}")

        if not self.api_key:
            raise AgentError("FMP_API_KEY is not configured")

        ratios_ttm = self._fetch_json("ratios-ttm", symbol)
        key_metrics_ttm = self._fetch_json("key-metrics-ttm", symbol)

        if not ratios_ttm and not key_metrics_ttm:
            raise AgentError(f"No fundamental data available for {symbol}")

        ratios = self._calculate_ratios(ratios_ttm, key_metrics_ttm)
        sub_scores = self._score_ratios(ratios)
        score = self._calculate_fundamental_score(sub_scores)

        self.logger.info(
            f"{symbol} | ROE: {ratios.get('roe')}% | "
            f"D/E: {ratios.get('debt_to_equity')} | "
            f"Current Ratio: {ratios.get('current_ratio')} | "
            f"Fundamental Score: {score}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={"ratios": ratios, "sub_scores": sub_scores},
            score=score,
            metadata={"symbol": symbol}
        )

    def _fetch_json(self, endpoint: str, symbol: str) -> dict:
        try:
            resp = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                params={"symbol": symbol, "apikey": self.api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            # FMP returns a list of period rows — first entry is TTM/most recent
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict) and data.get("Error Message"):
                self.logger.warning(f"FMP error on {endpoint} for {symbol}: {data['Error Message']}")
                return {}
            return {}
        except Exception as e:
            self.logger.warning(f"FMP {endpoint} fetch failed for {symbol}: {e}")
            return {}

    def _first(self, d: dict, *keys):
        """Try several candidate field names — FMP's field naming shifts between endpoint versions."""
        for k in keys:
            if k in d and d[k] is not None:
                return d[k]
        return None

    def _calculate_ratios(self, ratios_ttm: dict, key_metrics_ttm: dict) -> dict:
        r, k = ratios_ttm, key_metrics_ttm
        ratios = {}

        roe = self._first(r, "returnOnEquityTTM") or self._first(k, "returnOnEquityTTM")
        ratios["roe"] = self._pct(roe)

        roa = self._first(r, "returnOnAssetsTTM") or self._first(k, "returnOnAssetsTTM")
        ratios["roa"] = self._pct(roa)

        ratios["profit_margin"] = self._pct(self._first(r, "netProfitMarginTTM"))
        ratios["operating_margin"] = self._pct(self._first(r, "operatingProfitMarginTTM"))

        de = self._first(r, "debtToEquityRatioTTM", "debtEquityRatioTTM", "debtToEquityTTM")
        ratios["debt_to_equity"] = self._round(de * 100 if de is not None and de < 5 else de)  # normalize ratio→%

        ratios["current_ratio"] = self._round(self._first(r, "currentRatioTTM"))
        ratios["quick_ratio"] = self._round(self._first(r, "quickRatioTTM"))
        ratios["pe_ratio"] = self._round(self._first(r, "priceToEarningsRatioTTM", "peRatioTTM"))
        ratios["peg_ratio"] = self._round(self._first(r, "priceEarningsToGrowthRatioTTM", "pegRatioTTM"))
        ratios["revenue_growth"] = self._pct(self._first(k, "revenueGrowthTTM"))
        ratios["earnings_growth"] = self._pct(self._first(k, "epsgrowthTTM", "netIncomeGrowthTTM"))
        ratios["free_cashflow"] = self._first(k, "freeCashFlowTTM", "freeCashFlowPerShareTTM")

        return ratios

    def _pct(self, value):
        if value is None:
            return None
        try:
            v = float(value)
        except (ValueError, TypeError):
            return None
        # FMP TTM ratios are often already decimals like 0.23 for 23% — normalize
        return round(v * 100, 2) if abs(v) < 5 else round(v, 2)

    def _round(self, value, decimals=2):
        if value is None:
            return None
        try:
            return round(float(value), decimals)
        except (ValueError, TypeError):
            return None

    def _score_ratios(self, ratios: dict) -> dict:
        scores = {}

        roe = ratios.get("roe")
        if roe is not None:
            scores["roe"] = 30 if roe >= 20 else 15 if roe >= 10 else -5 if roe >= 0 else -30
        else:
            scores["roe"] = 0

        de = ratios.get("debt_to_equity")
        if de is not None:
            scores["debt_to_equity"] = 25 if de < 50 else 10 if de < 100 else -15 if de < 200 else -35
        else:
            scores["debt_to_equity"] = 0

        cr = ratios.get("current_ratio")
        if cr is not None:
            scores["current_ratio"] = 20 if cr >= 1.5 else 5 if cr >= 1.0 else -25
        else:
            scores["current_ratio"] = 0

        pm = ratios.get("profit_margin")
        if pm is not None:
            scores["profit_margin"] = 25 if pm >= 20 else 10 if pm >= 10 else -5 if pm >= 0 else -25
        else:
            scores["profit_margin"] = 0

        peg = ratios.get("peg_ratio")
        if peg is not None and peg > 0:
            scores["peg_ratio"] = 20 if peg < 1 else 5 if peg < 2 else -15
        else:
            scores["peg_ratio"] = 0

        rg = ratios.get("revenue_growth")
        if rg is not None:
            scores["revenue_growth"] = 20 if rg >= 15 else 10 if rg >= 5 else 0 if rg >= 0 else -20
        else:
            scores["revenue_growth"] = 0

        return scores

    def _calculate_fundamental_score(self, sub_scores: dict) -> float:
        total = sum(v for v in sub_scores.values() if v is not None)
        return round(max(min(total, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True