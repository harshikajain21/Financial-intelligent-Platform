# api/routes/analysis.py

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from api.models import AnalysisResponse, ErrorResponse
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("AnalysisRouter")


def _generate_recommendation(decision: str, confidence: float, scores: dict) -> str:
    """Generate a human-readable recommendation summary."""

    strongest_positive = max(scores.items(), key=lambda x: x[1], default=None)
    strongest_negative = min(scores.items(), key=lambda x: x[1], default=None)

    if decision == "BUY":
        return (
            f"Strong buy signal with {confidence:.1f}% confidence. "
            f"Primary driver: {strongest_positive[0]} (score: {strongest_positive[1]:.1f}). "
            f"Consider entering a position with appropriate position sizing."
        )
    elif decision == "SELL":
        return (
            f"Sell signal with {confidence:.1f}% confidence. "
            f"Primary concern: {strongest_negative[0]} (score: {strongest_negative[1]:.1f}). "
            f"Consider reducing or exiting position."
        )
    else:
        return (
            f"Hold signal — mixed indicators with {confidence:.1f}% conviction. "
            f"Best signal: {strongest_positive[0]} ({strongest_positive[1]:.1f}). "
            f"Weakest signal: {strongest_negative[0]} ({strongest_negative[1]:.1f}). "
            f"Wait for clearer direction before acting."
        )


@router.post(
    "/analyze/{symbol}",
    response_model=AnalysisResponse,
    summary="Run full analysis pipeline for a stock symbol",
    description="Runs all 9 agents and returns a consolidated investment decision."
)
def analyze_symbol(request: Request, symbol: str):
    """
    Full analysis endpoint.
    Runs all agents and returns BUY/HOLD/SELL with confidence.
    """
    symbol = symbol.upper().strip()

    if not symbol or not symbol.isalpha():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid symbol: '{symbol}'. Must be letters only e.g. AAPL"
        )

    logger.info(f"API request: analyze {symbol}")

    try:
        orchestrator = request.app.state.orchestrator
        report = orchestrator.analyze(symbol)

    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

    # Filter out MarketDataAgent from scores shown to user
    # (its score is data quality, not investment signal)
    display_scores = {
        k: v for k, v in report.scores.items()
        if k != "MarketDataAgent"
    }

    recommendation = _generate_recommendation(
        report.final_decision,
        report.confidence or 0,
        display_scores
    )

    # Extract forecast data if available
    forecast_data = {}
    forecast_result = report.agent_results.get("ForecastingAgent")
    if forecast_result and forecast_result.success:
        forecast_data = forecast_result.data.get("forecasts", {})

    # Extract explanation report
    explanation_data = {}
    if hasattr(report, 'explanation') and report.explanation:
        explanation_data = report.explanation
    return AnalysisResponse(
        symbol         = symbol,
        timestamp      = report.timestamp,
        final_decision = report.final_decision or "UNAVAILABLE",
        confidence     = report.confidence or 0,
        scores         = display_scores,
        errors         = report.errors,
        duration_ms    = report.duration_ms,
        recommendation = recommendation,
        explanations   = {},
        forecasts      = forecast_data,
        explanation    = explanation_data
    )
