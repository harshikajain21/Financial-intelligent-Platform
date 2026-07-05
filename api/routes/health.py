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