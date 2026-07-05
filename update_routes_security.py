# update_routes_security.py

analysis = """
# api/routes/analysis.py

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from api.models import AnalysisResponse
from api.limiter import limiter
from api.sanitizer import sanitize_symbol, sanitize_exchange
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
        if tech >= 40: explanations["Technical"] = "Price charts look bullish with strong upward momentum."
        elif tech >= 10: explanations["Technical"] = "Charts are mildly positive with some bullish signals."
        elif tech >= -10: explanations["Technical"] = "Mixed chart signals with no clear direction."
        elif tech >= -40: explanations["Technical"] = "Charts look weak with bearish signals outweighing bullish ones."
        else: explanations["Technical"] = "Strong bearish chart pattern with multiple indicators pointing down."
    news = scores.get("NewsIntelligenceAgent")
    if news is not None:
        if news >= 30: explanations["News"] = "Recent news is very positive with strong media sentiment."
        elif news >= 10: explanations["News"] = "News sentiment is mostly positive recently."
        elif news >= -10: explanations["News"] = "News is neutral with a mix of positive and negative stories."
        elif news >= -30: explanations["News"] = "Recent news is mostly negative."
        else: explanations["News"] = "Very negative news sentiment with significant negative coverage."
    sentiment = scores.get("SocialSentimentAgent")
    if sentiment is not None:
        if sentiment >= 30: explanations["Social Buzz"] = "Investors on social media are very bullish."
        elif sentiment >= 10: explanations["Social Buzz"] = "Social media sentiment is leaning positive."
        elif sentiment >= -10: explanations["Social Buzz"] = "Social media is neutral with mixed opinions."
        else: explanations["Social Buzz"] = "Social media sentiment is bearish."
    macro = scores.get("MacroeconomicIntelligenceAgent")
    if macro is not None:
        if macro >= 30: explanations["Economy"] = "Economic conditions are favorable for stocks."
        elif macro >= 0: explanations["Economy"] = "Economy is in reasonable shape and supportive for stocks."
        else: explanations["Economy"] = "Economic headwinds present, challenging conditions for stocks."
    risk = scores.get("PortfolioRiskAgent")
    if risk is not None:
        if risk >= 30: explanations["Risk"] = "Low risk profile with stable and good risk-adjusted returns."
        elif risk >= 0: explanations["Risk"] = "Moderate risk with some volatility but manageable."
        elif risk >= -30: explanations["Risk"] = "Above average risk, stock has been volatile recently."
        else: explanations["Risk"] = "High risk stock with significant volatility and poor returns lately."
    fundamental = scores.get("FundamentalAnalysisAgent")
    if fundamental is not None:
        if fundamental >= 60: explanations["Business Health"] = "Excellent financials with strong profits and growing revenue."
        elif fundamental >= 30: explanations["Business Health"] = "Good financial health with solid profits and reasonable debt."
        elif fundamental >= 0: explanations["Business Health"] = "Average financials with some strengths and weaknesses."
        else: explanations["Business Health"] = "Weak financials with concerning debt or poor profitability."
    regime = scores.get("RegimeDetectionAgent")
    if regime is not None:
        if regime >= 50: explanations["Market Trend"] = "Strong bull market with clearly upward overall trend."
        elif regime >= 0: explanations["Market Trend"] = "Mild uptrend with market trending positive but not strongly."
        elif regime >= -50: explanations["Market Trend"] = "Bearish conditions working against this stock."
        else: explanations["Market Trend"] = "Strong bear market with very unfavorable overall conditions."
    anomaly = scores.get("AnomalyDetectionAgent")
    if anomaly is not None:
        if anomaly >= 60: explanations["Unusual Activity"] = "No unusual activity detected, trading looks normal."
        elif anomaly >= 20: explanations["Unusual Activity"] = "Minor unusual activity with some volume or price spikes."
        else: explanations["Unusual Activity"] = "Significant unusual activity detected with abnormal trading patterns."
    return explanations


@router.post(
    "/analyze/{symbol}",
    response_model=AnalysisResponse,
    summary="Run full analysis for a stock symbol or company name"
)
@limiter.limit("5/minute")
async def analyze_symbol(
    request: Request,
    symbol: str,
    exchange: str = "NSE",
    db: Session = Depends(get_db)
):
    # Sanitize inputs
    symbol   = sanitize_symbol(symbol)
    exchange = sanitize_exchange(exchange)

    # Resolve company name to ticker
    resolved = resolve_symbol(symbol.strip(), exchange)
    logger.info(f"API request: analyze {symbol} -> {resolved}")

    try:
        from api.main import orchestrator
        report = orchestrator.analyze(resolved)
    except Exception as e:
        logger.error(f"Analysis failed for {resolved}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Please try again with a valid stock symbol."
        )

    display_scores = {k: v for k, v in report.scores.items() if k != "MarketDataAgent"}
    recommendation = _generate_recommendation(report.final_decision, report.confidence or 0, display_scores)
    explanations   = _plain_english_explanations(display_scores)

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
        symbol         = resolved,
        timestamp      = report.timestamp,
        final_decision = report.final_decision or "UNAVAILABLE",
        confidence     = report.confidence or 0,
        scores         = display_scores,
        errors         = report.errors,
        duration_ms    = report.duration_ms,
        recommendation = recommendation,
        explanations   = explanations
    )
"""

search = """
# api/routes/search.py

from fastapi import APIRouter, Request
from api.limiter import limiter
from api.sanitizer import sanitize_query
from data.stock_universe import search_stocks, resolve_symbol

router = APIRouter()


@router.get("/search", summary="Search stocks by name or ticker")
@limiter.limit("30/minute")
async def search(request: Request, query: str, limit: int = 8):
    query = sanitize_query(query)
    if not query or len(query) < 2:
        return {"results": []}
    if limit > 20:
        limit = 20
    results = search_stocks(query, limit)
    return {"results": results}


@router.get("/resolve", summary="Resolve company name to ticker symbol")
@limiter.limit("30/minute")
async def resolve(request: Request, query: str, exchange: str = "NSE"):
    query    = sanitize_query(query)
    symbol   = resolve_symbol(query, exchange)
    return {"symbol": symbol, "exchange": exchange}
"""

prices = """
# api/routes/prices.py

from fastapi import APIRouter, HTTPException, Request
from api.limiter import limiter
from api.sanitizer import sanitize_symbol
import yfinance as yf
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("PricesRouter")

ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y"}


@router.get("/prices/{symbol}", summary="Get price history for a stock symbol")
@limiter.limit("20/minute")
async def get_prices(request: Request, symbol: str, period: str = "6mo"):
    symbol = sanitize_symbol(symbol)

    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period. Allowed: {ALLOWED_PERIODS}")

    try:
        logger.info(f"Fetching price history for {symbol}")
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")

        hist = hist.reset_index()
        data = []
        for _, row in hist.iterrows():
            data.append({
                "date"  : str(row["Date"])[:10],
                "close" : round(float(row["Close"]), 2),
                "open"  : round(float(row["Open"]), 2),
                "high"  : round(float(row["High"]), 2),
                "low"   : round(float(row["Low"]), 2),
                "volume": int(row["Volume"]),
            })

        closes      = [d["close"] for d in data]
        start_price = closes[0] if closes else 0
        end_price   = closes[-1] if closes else 0
        change_pct  = round(((end_price - start_price) / start_price) * 100, 2) if start_price else 0

        return {
            "symbol"      : symbol,
            "period"      : period,
            "data"        : data,
            "current"     : end_price,
            "change_pct"  : change_pct,
            "period_high" : round(max(closes), 2) if closes else 0,
            "period_low"  : round(min(closes), 2) if closes else 0,
            "bars"        : len(data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price data. Please try again.")
"""

health = """
# api/routes/health.py

from fastapi import APIRouter, Request
from api.limiter import limiter
from api.models import HealthResponse
from datetime import datetime
from config.settings import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="API health check")
@limiter.limit("60/minute")
async def health_check(request: Request):
    return HealthResponse(
        status    = "healthy",
        version   = settings.VERSION,
        agents    = 9,
        timestamp = datetime.utcnow().isoformat()
    )


@router.get("/agents", summary="List all agents and their status")
@limiter.limit("30/minute")
async def list_agents(request: Request):
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
"""

files = {
    "api/routes/analysis.py" : analysis,
    "api/routes/search.py"   : search,
    "api/routes/prices.py"   : prices,
    "api/routes/health.py"   : health,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("\nAll routes updated with security!")