# agents/risk_agent.py

import numpy as np
import pandas as pd
from agents.base_agent import BaseAgent, AgentResult, AgentError


class PortfolioRiskAgent(BaseAgent):
    """
    Agent 7: Portfolio Risk Agent

    Calculates statistical risk metrics from price history.
    Pure computation — no external API calls needed.

    Score interpretation:
        +100 = excellent risk-adjusted returns, low risk
           0 = average / mixed risk profile
        -100 = poor risk-adjusted returns, high risk
    """

    def __init__(self, risk_free_rate: float = 0.045):
        """
        risk_free_rate: annual risk-free rate (e.g. 10-year treasury yield)
                         used in Sharpe/Sortino calculations.
                         Default 4.5% is a reasonable current approximation.
        """
        super().__init__(name="PortfolioRiskAgent", max_retries=2)
        self.risk_free_rate = risk_free_rate

    def execute(self, symbol: str, price_history: list = None, **kwargs) -> AgentResult:
        if not price_history:
            raise AgentError(
                "price_history is required. Run MarketDataAgent first."
            )

        self.logger.info(f"Calculating risk metrics for {symbol}")

        # --- Step 1: Prepare data ---
        df = pd.DataFrame(price_history)
        df = df.sort_values("date").reset_index(drop=True)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")

        if len(df) < 20:
            raise AgentError(
                f"Not enough data for risk calculation. Got {len(df)} bars, need 20+"
            )

        # Daily returns — the foundation of all risk metrics
        returns = df["close"].pct_change().dropna()

        # --- Step 2: Calculate all metrics ---
        metrics = self._calculate_metrics(returns, df["close"])

        # --- Step 3: Score the overall risk profile ---
        score = self._calculate_risk_score(metrics)

        self.logger.info(
            f"{symbol} | Sharpe: {metrics['sharpe_ratio']} | "
            f"Volatility: {metrics['annualized_volatility']}% | "
            f"Max Drawdown: {metrics['max_drawdown']}% | "
            f"Risk Score: {score}"
        )

        return AgentResult(
            agent_name=self.name,
            success=True,
            data={"metrics": metrics},
            score=score,
            metadata={"symbol": symbol, "bars_used": len(df)}
        )

    def _calculate_metrics(self, returns: pd.Series, prices: pd.Series) -> dict:
        """
        Calculate all risk metrics from daily returns and price series.
        """
        metrics = {}

        # --- Volatility (annualized) ---
        # Daily std dev * sqrt(252 trading days) = annualized volatility
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(252)
        metrics["daily_volatility"] = round(float(daily_vol) * 100, 4)
        metrics["annualized_volatility"] = round(float(annualized_vol) * 100, 2)

        # --- Average Return (annualized) ---
        avg_daily_return = returns.mean()
        annualized_return = avg_daily_return * 252
        metrics["annualized_return"] = round(float(annualized_return) * 100, 2)

        # --- Sharpe Ratio ---
        # (Return - Risk Free Rate) / Volatility
        # Higher = better risk-adjusted return. >1 is good, >2 is excellent.
        if daily_vol > 0:
            sharpe = (annualized_return - self.risk_free_rate) / annualized_vol
        else:
            sharpe = 0
        metrics["sharpe_ratio"] = round(float(sharpe), 3)

        # --- Sortino Ratio ---
        # Like Sharpe, but only counts DOWNSIDE volatility (negative returns)
        # More accurate than Sharpe because upside swings shouldn't be "penalized"
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std() * np.sqrt(252)
            sortino = (annualized_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0
        else:
            sortino = 0
        metrics["sortino_ratio"] = round(float(sortino), 3)

        # --- Maximum Drawdown ---
        # Worst peak-to-trough decline in the period
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        metrics["max_drawdown"] = round(float(max_drawdown) * 100, 2)

        # --- Value at Risk (95% confidence, 1-day) ---
        # "There's a 95% chance daily loss won't exceed this %"
        var_95 = np.percentile(returns, 5)
        metrics["var_95_daily"] = round(float(var_95) * 100, 2)

        # --- Current vs 52-week range position ---
        current_price = float(prices.iloc[-1])
        period_high = float(prices.max())
        period_low = float(prices.min())
        if period_high > period_low:
            range_position = (current_price - period_low) / (period_high - period_low)
        else:
            range_position = 0.5
        metrics["range_position_pct"] = round(range_position * 100, 2)

        return metrics

    def _calculate_risk_score(self, metrics: dict) -> float:
        """
        Combine metrics into a single -100 to +100 score.

        Logic:
            - Good Sharpe ratio = positive contribution
            - Low max drawdown = positive contribution
            - High volatility = negative contribution
            - Position near 52w high with low drawdown = positive (healthy uptrend)
        """
        score = 0.0

        # Sharpe Ratio component (most important — weight 40%)
        # Sharpe > 2 = excellent, 1-2 = good, 0-1 = mediocre, <0 = bad
        sharpe = metrics["sharpe_ratio"]
        if sharpe >= 2:
            score += 40
        elif sharpe >= 1:
            score += 20
        elif sharpe >= 0:
            score += 0
        else:
            score -= 30

        # Max Drawdown component (weight 30%)
        # Smaller (less negative) drawdown = better
        drawdown = metrics["max_drawdown"]  # negative number e.g. -15.0
        if drawdown >= -10:
            score += 30
        elif drawdown >= -20:
            score += 10
        elif drawdown >= -35:
            score -= 10
        else:
            score -= 30

        # Volatility component (weight 20%)
        # Lower volatility = more stable = better (for risk-averse scoring)
        vol = metrics["annualized_volatility"]
        if vol <= 20:
            score += 20
        elif vol <= 35:
            score += 5
        elif vol <= 50:
            score -= 10
        else:
            score -= 20

        # Sortino Ratio component (weight 10%)
        sortino = metrics["sortino_ratio"]
        if sortino >= 2:
            score += 10
        elif sortino >= 1:
            score += 5
        elif sortino < 0:
            score -= 10

        return round(max(min(score, 100), -100), 2)

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        if result.score is None:
            return False
        if not (-100 <= result.score <= 100):
            return False
        return True