"""
FastAPI application entry point — Financial Intelligence Platform REST API.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import analysis, health, alerts, backtesting
from config.settings import Settings
from utils.logger import get_logger

logger = get_logger("API")
settings = Settings()


# ------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Financial Intelligence Platform API starting up.")
    yield
    logger.info("Financial Intelligence Platform API shutting down.")


# ------------------------------------------------------------------
# Application factory
# ------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="Financial Intelligence Platform",
        description=(
            "Multi-agent financial analysis API. "
            "Provides market data, sentiment, technical & fundamental analysis, "
            "risk metrics, forecasting, and investment recommendations."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
    app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
    app.include_router(backtesting.router, prefix="/api/v1/backtest", tags=["Backtesting"])

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )
