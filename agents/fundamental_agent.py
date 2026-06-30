# agents/fundamental_agent.py

import yfinance as yf
import pandas as pd
from agents.base_agent import BaseAgent, AgentResult, AgentError


class FundamentalAnalysisAgent(BaseAgent):
    """
    Agent 9: Fundamental Analysis Agent

    Analyzes a company's financial statements to assess business health.
    Independent of price action — purely about the company's financials.

    Score interpretation:
        +100 = excellent financial health
           0 = average / mixed fundamentals
        -100 = poor financial health, red flags present
    """

    def __init__(self):
        super().__init__(name="FundamentalAnalysisAgent", max_retries=2)

    def execute(self, symbol: str, **kwargs) -> AgentResult:
        self.logger.info(f"Running fundamental analysis for {symbol}")

        ticker = yf.Ticker(symbol)

        # --- Step 1: Fetch financial statements ---
        try:
            info = ticker.info
            balance_sheet = ticker.balance_sheet
            income_stmt = ticker.income_stmt
            cash_flow = ticker.cashflow
        except Exception as e:
            raise AgentError(f"Failed to fetch financial statements: {e}")

        if not info or balance_sheet.empty:
            raise AgentError(f"No fundamental data available for {symbol}")

        # --- Step 2: Calculate key ratios ---
        ratios = self._calculate_ratios(info, balance_sheet, income_stmt, cash_flow)

        # --- Step 3: Score each ratio ---
        sub_scores = self._score_ratios(ratios)

        # --- Step 4: Combine into overall score ---
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
            data={
                "ratios": ratios,
                "sub_scores": sub_scores,
            },
            score=score,
            metadata={"symbol": symbol}
        )

    def _safe_get(self, df: pd.DataFrame, row_name: str, col_index: int = 0):
        """
        Safely extract a value from a financial statement DataFrame.
        Returns None if the row doesn't exist or data is missing.
        """
        try:
            if row_name in df.index:
                value = df.loc[row_name].iloc[col_index]
                return float(value) if pd.notna(value) else None
        except Exception:
            pass
        return None

    def _calculate_ratios(self, info: dict, balance_sheet: pd.DataFrame,
                           income_stmt: pd.DataFrame, cash_flow: pd.DataFrame) -> dict:
        """
        Calculate fundamental ratios from financial statements + info dict.
        Uses .get() and safe extraction everywhere — financial data is
        notoriously inconsistent across companies.
        """
        ratios = {}

        # --- From the info dict (pre-calculated by Yahoo) ---
        ratios["roe"] = self._pct(info.get("returnOnEquity"))
        ratios["roa"] = self._pct(info.get("returnOnAssets"))
        ratios["profit_margin"] = self._pct(info.get("profitMargins"))
        ratios["operating_margin"] = self._pct(info.get("operatingMargins"))
        ratios["debt_to_equity"] = self._round(info.get("debtToEquity"))
        ratios["current_ratio"] = self._round(info.get("currentRatio"))
        ratios["quick_ratio"] = self._round(info.get("quickRatio"))
        ratios["pe_ratio"] = self._round(info.get("trailingPE"))
        ratios["peg_ratio"] = self._round(info.get("pegRatio"))
        ratios["revenue_growth"] = self._pct(info.get("revenueGrowth"))
        ratios["earnings_growth"] = self._pct(info.get("earningsGrowth"))
        ratios["free_cashflow"] = info.get("freeCashflow")

        # --- Manual calculation from raw statements (backup/cross-check) ---
        total_revenue = self._safe_get(income_stmt, "Total Revenue")
        net_income = self._safe_get(income_stmt, "Net Income")
        total_assets = self._safe_get(balance_sheet, "Total Assets")
        total_debt = self._safe_get(balance_sheet, "Total Debt")
        stockholders_equity = self._safe_get(balance_sheet, "Stockholders Equity")

        ratios["net_margin_calculated"] = (
            self._round((net_income / total_revenue) * 100)
            if net_income and total_revenue else None
        )

        return ratios

    def _pct(self, value):
        """Convert a decimal ratio to a percentage, rounded."""
        if value is None:
            return None
        return round(float(value) * 100, 2)

    def _round(self, value, decimals=2):
        if value is None:
            return None
        return round(float(value), decimals)

    def _score_ratios(self, ratios: dict) -> dict:
        """
        Score each fundamental ratio individually.
        Thresholds based on general value-investing heuristics.
        """
        scores = {}

        # --- ROE (Return on Equity) ---
        # >20% excellent, 10-20% good, 0-10% mediocre, <0% bad
        roe = ratios.get("roe")
        if roe is not None:
            if roe >= 20:
                scores["roe"] = 30
            elif roe >= 10:
                scores["roe"] = 15
            elif roe >= 0:
                scores["roe"] = -5
            else:
                scores["roe"] = -30
        else:
            scores["roe"] = 0

        # --- Debt to Equity ---
        # Lower is generally safer. <50 = conservative, >150 = highly leveraged
        de = ratios.get("debt_to_equity")
        if de is not None:
            if de < 50:
                scores["debt_to_equity"] = 25
            elif de < 100:
                scores["debt_to_equity"] = 10
            elif de < 200:
                scores["debt_to_equity"] = -15
            else:
                scores["debt_to_equity"] = -35
        else:
            scores["debt_to_equity"] = 0

        # --- Current Ratio ---
        # >1.5 = healthy liquidity, <1.0 = potential liquidity issues
        cr = ratios.get("current_ratio")
        if cr is not None:
            if cr >= 1.5:
                scores["current_ratio"] = 20
            elif cr >= 1.0:
                scores["current_ratio"] = 5
            else:
                scores["current_ratio"] = -25
        else:
            scores["current_ratio"] = 0

        # --- Profit Margin ---
        pm = ratios.get("profit_margin")
        if pm is not None:
            if pm >= 20:
                scores["profit_margin"] = 25
            elif pm >= 10:
                scores["profit_margin"] = 10
            elif pm >= 0:
                scores["profit_margin"] = -5
            else:
                scores["profit_margin"] = -25
        else:
            scores["profit_margin"] = 0

        # --- PEG Ratio ---
        # ~1.0 = fairly valued relative to growth, <1 = undervalued, >2 = overvalued
        peg = ratios.get("peg_ratio")
        if peg is not None and peg > 0:
            if peg < 1:
                scores["peg_ratio"] = 20
            elif peg < 2:
                scores["peg_ratio"] = 5
            else:
                scores["peg_ratio"] = -15
        else:
            scores["peg_ratio"] = 0

        # --- Revenue Growth ---
        rg = ratios.get("revenue_growth")
        if rg is not None:
            if rg >= 15:
                scores["revenue_growth"] = 20
            elif rg >= 5:
                scores["revenue_growth"] = 10
            elif rg >= 0:
                scores["revenue_growth"] = 0
            else:
                scores["revenue_growth"] = -20
        else:
            scores["revenue_growth"] = 0

        return scores

    def _calculate_fundamental_score(self, sub_scores: dict) -> float:
        """
        Sum all sub-scores (they're already weighted via their point ranges above)
        and clamp to -100 to +100.
        """
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