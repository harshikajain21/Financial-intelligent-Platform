# update_analysis_route.py

content = '''# api/routes/analysis.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.models import AnalysisResponse
from database.connection import get_db
from database.repository import AnalysisRepository
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
async def analyze_symbol(symbol: str, db: Session = Depends(get_db)):
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

    # Save to database
    try:
        market_result = report.agent_results.get("MarketDataAgent")
        close_price = None
        if market_result and market_result.success:
            close_price = market_result.data.get("snapshot", {}).get("close")

        db_record = AnalysisRepository.save_analysis(db, report, close_price)
        db_record.recommendation = recommendation
        db.commit()
        logger.info(f"Analysis saved to database with id: {db_record.id}")
    except Exception as e:
        logger.warning(f"Failed to save to database: {e}")

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

with open("api/routes/analysis.py", "w") as f:
    f.write(content)
    print("api/routes/analysis.py updated")