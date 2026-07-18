# api/main.py

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from api.limiter import limiter
from utils.logger import get_logger
from config.settings import settings
from api.routes.jobs import router as jobs_router

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
    title       = settings.APP_NAME,
    version     = settings.VERSION,
    description = "Multi-agent AI system for real-time stock market intelligence",
    lifespan    = lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — restrict to known origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods     = ["GET", "POST", "DELETE"],
    allow_headers     = ["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


# Global error handler — never leak internal details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": "Something went wrong. Please try again."}
    )


# Register routers
from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router
from api.routes.history import router as history_router
from api.routes.search import router as search_router
from api.routes.prices import router as prices_router
from api.routes.auth import router as auth_router

app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(health_router,   prefix="/api/v1", tags=["Health"])
app.include_router(history_router,  prefix="/api/v1", tags=["History"])
app.include_router(search_router,   prefix="/api/v1", tags=["Search"])
app.include_router(prices_router,   prefix="/api/v1", tags=["Prices"])
app.include_router(auth_router,     prefix="/api/v1", tags=["Auth"])
app.include_router(jobs_router, prefix="/api/v1", tags=["Jobs"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name"    : settings.APP_NAME,
        "version" : settings.VERSION,
        "docs"    : "/docs",
        "health"  : "/api/v1/health"
    }