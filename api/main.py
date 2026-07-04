# api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from utils.logger import get_logger
from config.settings import settings

logger = get_logger("FastAPI")

# Global orchestrator instance — initialized once on startup
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown logic.
    Orchestrator is initialized ONCE when the server starts —
    this means FinBERT loads once, agents initialize once.
    All requests share the same orchestrator instance.
    """
    global orchestrator
    logger.info("Starting up Financial Intelligence Platform API...")

    from orchestrator.master_orchestrator import MasterOrchestrator
    orchestrator = MasterOrchestrator()

    logger.info("All agents initialized. API ready.")
    yield

    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title       = settings.APP_NAME,
    version     = settings.VERSION,
    description = "Multi-agent AI system for real-time stock market intelligence",
    lifespan    = lifespan
)

# CORS — allows the React dashboard to call this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Register routers
from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router

app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(health_router,   prefix="/api/v1", tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name"    : settings.APP_NAME,
        "version" : settings.VERSION,
        "docs"    : "/docs",
        "health"  : "/api/v1/health"
    }