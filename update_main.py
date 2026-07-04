# update_main.py

content = '''# api/main.py

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

    # Initialize database
    from database.connection import init_db
    init_db()

    # Initialize orchestrator
    from orchestrator.master_orchestrator import MasterOrchestrator
    orchestrator = MasterOrchestrator()

    logger.info("All agents initialized. API ready.")
    yield
    logger.info("Shutting down API...")


app = FastAPI(
    title       = settings.APP_NAME,
    version     = settings.VERSION,
    description = "Multi-agent AI system for real-time stock market intelligence",
    lifespan    = lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

from api.routes.analysis import router as analysis_router
from api.routes.health import router as health_router
from api.routes.history import router as history_router

app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(health_router,   prefix="/api/v1", tags=["Health"])
app.include_router(history_router,  prefix="/api/v1", tags=["History"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name"    : settings.APP_NAME,
        "version" : settings.VERSION,
        "docs"    : "/docs",
        "health"  : "/api/v1/health"
    }
'''

with open("api/main.py", "w") as f:
    f.write(content)
    print("api/main.py updated")