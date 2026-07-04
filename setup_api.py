# setup_api.py - run this once to create API route files

analysis_content = '''# api/routes/analysis.py

from fastapi import APIRouter, HTTPException
from api.models import AnalysisResponse
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("AnalysisRouter")


def _generate_recommendation(decision, confidence, scores):
    if not scores:
        return "Insufficient data for recommendation."
    strongest_positive = max(scores.items(), key=lambda x: x[1])
    strongest_negative = min(scores.items(), key=lambda x: x[1])
    if decision == "BUY":
        return (
            f"Strong buy signal with {confidence:.1f}% confidence. "
            f"Primary driver: {strongest_positive[0]} ({strongest_positive[1]:.1f})."
        )
    elif decision == "SELL":
        return (
            f"Sell signal with {confidence:.1f}% confidence. "
            f"Primary concern: {strongest_negative[0]} ({strongest_negative[1]:.1f})."
        )
    else:
        return (
            f"Hold signal with {confidence:.1f}% conviction. "
            f"Best signal: {strongest_positive[0]} ({strongest_positive[1]:.1f}). "
            f"Weakest: {strongest_negative[0]} ({strongest_negative[1]:.1f})."
        )


@router.post(
    "/analyze/{symbol}",
    response_model=AnalysisResponse,
    summary="Run full analysis for a stock symbol"
)
async def analyze_symbol(symbol: str):
    symbol = symbol.upper().strip()

    if not symbol or not symbol.isalpha():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid symbol: {symbol}. Must be letters only e.g. AAPL"
        )

    logger.info(f"API request: analyze {symbol}")

    try:
        from api.main import orchestrator
        report = orchestrator.analyze(symbol)
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

    display_scores = {
        k: v for k, v in report.scores.items()
        if k != "MarketDataAgent"
    }

    recommendation = _generate_recommendation(
        report.final_decision,
        report.confidence or 0,
        display_scores
    )

    return AnalysisResponse(
        symbol         = symbol,
        timestamp      = report.timestamp,
        final_decision = report.final_decision or "UNAVAILABLE",
        confidence     = report.confidence or 0,
        scores         = display_scores,
        errors         = report.errors,
        duration_ms    = report.duration_ms,
        recommendation = recommendation
    )
'''

health_content = '''# api/routes/health.py

from fastapi import APIRouter
from api.models import HealthResponse
from datetime import datetime
from config.settings import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="API health check")
async def health_check():
    return HealthResponse(
        status    = "healthy",
        version   = settings.VERSION,
        agents    = 9,
        timestamp = datetime.utcnow().isoformat()
    )


@router.get("/agents", summary="List all agents and their status")
async def list_agents():
    agents = [
        {"name": "MarketDataAgent",               "stage": "1",  "type": "data"},
        {"name": "TechnicalAnalysisAgent",         "stage": "2",  "type": "analysis"},
        {"name": "NewsIntelligenceAgent",          "stage": "2b", "type": "analysis"},
        {"name": "SocialSentimentAgent",           "stage": "2c", "type": "analysis"},
        {"name": "PortfolioRiskAgent",             "stage": "2d", "type": "analysis"},
        {"name": "FundamentalAnalysisAgent",       "stage": "2e", "type": "analysis"},
        {"name": "RegimeDetectionAgent",           "stage": "2f", "type": "analysis"},
        {"name": "AnomalyDetectionAgent",          "stage": "2g", "type": "analysis"},
        {"name": "MacroeconomicIntelligenceAgent", "stage": "0",  "type": "macro"},
    ]
    return {"total_agents": len(agents), "agents": agents}
'''

with open("api/routes/analysis.py", "w") as f:
    f.write(analysis_content)
    print("analysis.py written successfully")

with open("api/routes/health.py", "w") as f:
    f.write(health_content)
    print("health.py written successfully")