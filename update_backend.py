# update_backend.py

import os

# 1. Search route
search_route = """# api/routes/search.py

from fastapi import APIRouter
from data.stock_universe import search_stocks, resolve_symbol

router = APIRouter()


@router.get("/search", summary="Search stocks by name or ticker")
async def search(query: str, limit: int = 8):
    if not query or len(query) < 2:
        return {"results": []}
    results = search_stocks(query, limit)
    return {"results": results}


@router.get("/resolve", summary="Resolve company name to ticker symbol")
async def resolve(query: str, exchange: str = "NSE"):
    symbol = resolve_symbol(query, exchange)
    return {"symbol": symbol, "exchange": exchange}
"""

with open("api/routes/search.py", "w", encoding="utf-8") as f:
    f.write(search_route.strip())
    print("api/routes/search.py written")

# 2. Updated main.py with search router
main_content = """# api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from utils.logger import get_logger
from config.settings import settings

logger = get_logger("FastAPI")
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("Starting up Financial Intelligence Platform API...")
    from database.connection import init_db
    init_db()
    from orchestrator.master_orchestrator import MasterOrchestrator
    orchestrator = MasterOrchestrator()
    logger.info("All agents initialized. API ready.")
    yield
    logger.info("Shutting down API...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-agent AI system for real-time stock market intelligence",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router
from api.routes.history import router as history_router
from api.routes.search import router as search_router

app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(health_router,   prefix="/api/v1", tags=["Health"])
app.include_router(history_router,  prefix="/api/v1", tags=["History"])
app.include_router(search_router,   prefix="/api/v1", tags=["Search"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/health"
    }
"""

with open("api/main.py", "w", encoding="utf-8") as f:
    f.write(main_content.strip())
    print("api/main.py updated")

# 3. Updated analysis route with plain English explanations
analysis_content = """# api/routes/analysis.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.models import AnalysisResponse
from database.connection import get_db
from database.repository import AnalysisRepository
from data.stock_universe import resolve_symbol
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


def _plain_english_explanations(scores: dict) -> dict:
    explanations = {}

    tech = scores.get("TechnicalAnalysisAgent")
    if tech is not None:
        if tech >= 40:
            explanations["Technical"] = "Price charts look bullish — strong upward momentum with positive indicators."
        elif tech >= 10:
            explanations["Technical"] = "Charts are mildly positive — some bullish signals but not overwhelming."
        elif tech >= -10:
            explanations["Technical"] = "Mixed chart signals — no clear direction from technical indicators."
        elif tech >= -40:
            explanations["Technical"] = "Charts look weak — bearish signals outweigh bullish ones."
        else:
            explanations["Technical"] = "Strong bearish chart pattern — multiple indicators pointing downward."

    news = scores.get("NewsIntelligenceAgent")
    if news is not None:
        if news >= 30:
            explanations["News"] = "Recent news is very positive — strong positive sentiment in financial media."
        elif news >= 10:
            explanations["News"] = "News sentiment is mostly positive — more good news than bad recently."
        elif news >= -10:
            explanations["News"] = "News is neutral — mix of positive and negative stories recently."
        elif news >= -30:
            explanations["News"] = "Recent news is mostly negative — more concerning stories than positive ones."
        else:
            explanations["News"] = "Very negative news sentiment — significant negative coverage recently."

    sentiment = scores.get("SocialSentimentAgent")
    if sentiment is not None:
        if sentiment >= 30:
            explanations["Social Buzz"] = "Investors on social media are very bullish — strong positive chatter."
        elif sentiment >= 10:
            explanations["Social Buzz"] = "Social media sentiment is leaning positive — more bulls than bears."
        elif sentiment >= -10:
            explanations["Social Buzz"] = "Social media is neutral — mixed opinions among retail investors."
        else:
            explanations["Social Buzz"] = "Social media sentiment is bearish — retail investors are cautious."

    macro = scores.get("MacroeconomicIntelligenceAgent")
    if macro is not None:
        if macro >= 30:
            explanations["Economy"] = "Economic conditions are favorable — low rates, strong growth, low unemployment."
        elif macro >= 0:
            explanations["Economy"] = "Economy is in reasonable shape — conditions are supportive for stocks."
        else:
            explanations["Economy"] = "Economic headwinds present — conditions are challenging for stocks overall."

    risk = scores.get("PortfolioRiskAgent")
    if risk is not None:
        if risk >= 30:
            explanations["Risk"] = "Low risk profile — stock has been stable with good risk-adjusted returns."
        elif risk >= 0:
            explanations["Risk"] = "Moderate risk — some volatility but manageable for most investors."
        elif risk >= -30:
            explanations["Risk"] = "Above average risk — stock has been volatile recently, invest carefully."
        else:
            explanations["Risk"] = "High risk stock — significant volatility and poor risk-adjusted returns lately."

    fundamental = scores.get("FundamentalAnalysisAgent")
    if fundamental is not None:
        if fundamental >= 60:
            explanations["Business Health"] = "Excellent financials — strong profits, healthy balance sheet, growing revenue."
        elif fundamental >= 30:
            explanations["Business Health"] = "Good financial health — solid profits and reasonable debt levels."
        elif fundamental >= 0:
            explanations["Business Health"] = "Average financials — some strengths but also some weaknesses."
        else:
            explanations["Business Health"] = "Weak financials — concerning debt levels or poor profitability."

    regime = scores.get("RegimeDetectionAgent")
    if regime is not None:
        if regime >= 50:
            explanations["Market Trend"] = "Strong bull market — overall market trend is clearly upward."
        elif regime >= 0:
            explanations["Market Trend"] = "Mild uptrend — market is trending positive but not strongly."
        elif regime >= -50:
            explanations["Market Trend"] = "Bearish conditions — market trend is working against this stock."
        else:
            explanations["Market Trend"] = "Strong bear market — overall conditions are very unfavorable."

    anomaly = scores.get("AnomalyDetectionAgent")
    if anomaly is not None:
        if anomaly >= 60:
            explanations["Unusual Activity"] = "No unusual activity detected — trading looks normal and clean."
        elif anomaly >= 20:
            explanations["Unusual Activity"] = "Minor unusual activity — some volume or price spikes recently."
        else:
            explanations["Unusual Activity"] = "Significant unusual activity detected — abnormal trading patterns."

    return explanations


@router.post(
    "/analyze/{symbol}",
    response_model=AnalysisResponse,
    summary="Run full analysis for a stock symbol or company name"
)
async def analyze_symbol(
    symbol: str,
    exchange: str = "NSE",
    db: Session = Depends(get_db)
):
    # Resolve company name to ticker symbol
    resolved = resolve_symbol(symbol.strip(), exchange)
    logger.info(f"API request: analyze {symbol} -> resolved to {resolved}")

    try:
        from api.main import orchestrator
        report = orchestrator.analyze(resolved)
    except Exception as e:
        logger.error(f"Analysis failed for {resolved}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    display_scores = {
        k: v for k, v in report.scores.items()
        if k != "MarketDataAgent"
    }

    recommendation = _generate_recommendation(
        report.final_decision,
        report.confidence or 0,
        display_scores
    )

    explanations = _plain_english_explanations(display_scores)

    # Save to database
    try:
        market_result = report.agent_results.get("MarketDataAgent")
        close_price = None
        if market_result and market_result.success:
            close_price = market_result.data.get("snapshot", {}).get("close")
        db_record = AnalysisRepository.save_analysis(db, report, close_price)
        db_record.recommendation = recommendation
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to save to database: {e}")

    return AnalysisResponse(
        symbol=resolved,
        timestamp=report.timestamp,
        final_decision=report.final_decision or "UNAVAILABLE",
        confidence=report.confidence or 0,
        scores=display_scores,
        errors=report.errors,
        duration_ms=report.duration_ms,
        recommendation=recommendation,
        explanations=explanations
    )
"""

with open("api/routes/analysis.py", "w", encoding="utf-8") as f:
    f.write(analysis_content.strip())
    print("api/routes/analysis.py updated")

print("\nAll backend files updated successfully!")