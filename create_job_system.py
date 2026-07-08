# create_job_system.py

content = """
# api/job_manager.py

import uuid
import threading
from datetime import datetime
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger("JobManager")


class JobStatus:
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    FAILED     = "failed"


class Job:
    def __init__(self, job_id: str, symbol: str):
        self.job_id     = job_id
        self.symbol     = symbol
        self.status     = JobStatus.PENDING
        self.result     = None
        self.error      = None
        self.created_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None

    def to_dict(self):
        return {
            "job_id"       : self.job_id,
            "symbol"       : self.symbol,
            "status"       : self.status,
            "created_at"   : self.created_at,
            "started_at"   : self.started_at,
            "completed_at" : self.completed_at,
            "error"        : self.error,
            "result"       : self.result,
        }


class JobManager:
    \"\"\"
    Simple in-memory job manager.
    Runs analysis in background thread.
    Stores results in memory (lost on restart).
    Production version would use Redis/Celery.
    \"\"\"

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        logger.info("JobManager initialized")

    def create_job(self, symbol: str) -> str:
        job_id = str(uuid.uuid4())[:8]
        job = Job(job_id, symbol)
        with self._lock:
            self._jobs[job_id] = job
        logger.info(f"Job created: {job_id} for {symbol}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def run_job(self, job_id: str, orchestrator, exchange: str = "NSE"):
        job = self.get_job(job_id)
        if not job:
            return

        job.status     = JobStatus.RUNNING
        job.started_at = datetime.utcnow().isoformat()
        logger.info(f"Job {job_id} starting for {job.symbol}")

        def worker():
            try:
                from data.stock_universe import resolve_symbol
                resolved = resolve_symbol(job.symbol, exchange)
                report   = orchestrator.analyze(resolved)

                # Build result dict
                display_scores = {
                    k: v for k, v in report.scores.items()
                    if k != "MarketDataAgent"
                }

                forecast_data = {}
                forecast_result = report.agent_results.get("ForecastingAgent")
                if forecast_result and forecast_result.success:
                    forecast_data = forecast_result.data.get("forecasts", {})

                explanation_data = {}
                if hasattr(report, 'explanation') and report.explanation:
                    explanation_data = report.explanation

                job.result = {
                    "symbol"         : resolved,
                    "timestamp"      : report.timestamp,
                    "final_decision" : report.final_decision or "UNAVAILABLE",
                    "confidence"     : report.confidence or 0,
                    "scores"         : display_scores,
                    "errors"         : report.errors,
                    "duration_ms"    : report.duration_ms,
                    "forecasts"      : forecast_data,
                    "explanation"    : explanation_data,
                }

                job.status       = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow().isoformat()
                logger.info(f"Job {job_id} completed | Decision: {report.final_decision}")

            except Exception as e:
                job.status       = JobStatus.FAILED
                job.error        = str(e)
                job.completed_at = datetime.utcnow().isoformat()
                logger.error(f"Job {job_id} failed: {e}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def cleanup_old_jobs(self, max_jobs: int = 100):
        \"\"\"Keep only the most recent N jobs in memory.\"\"\"
        with self._lock:
            if len(self._jobs) > max_jobs:
                oldest = sorted(self._jobs.keys())[:-max_jobs]
                for job_id in oldest:
                    del self._jobs[job_id]


# Global job manager instance
job_manager = JobManager()
"""

with open("api/job_manager.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("api/job_manager.py written")

# Add job routes
jobs_route = """
# api/routes/jobs.py

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from api.job_manager import job_manager, JobStatus
from api.limiter import limiter
from api.sanitizer import sanitize_symbol, sanitize_exchange
from database.connection import get_db
from database.repository import AnalysisRepository
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("JobsRouter")


@router.post(
    "/analyze/async/{symbol}",
    summary="Start async analysis — returns job_id immediately"
)
@limiter.limit("5/minute")
async def start_analysis(
    request : Request,
    symbol  : str,
    exchange: str = "NSE",
):
    \"\"\"
    Start analysis in background.
    Returns job_id immediately — poll /jobs/{job_id} for result.
    \"\"\"
    symbol   = sanitize_symbol(symbol)
    exchange = sanitize_exchange(exchange)

    from api.main import orchestrator
    job_id = job_manager.create_job(symbol)
    job_manager.run_job(job_id, orchestrator, exchange)

    logger.info(f"Async job started: {job_id} for {symbol}")

    return {
        "job_id"   : job_id,
        "symbol"   : symbol,
        "status"   : "pending",
        "poll_url" : f"/api/v1/jobs/{job_id}",
        "message"  : "Analysis started. Poll the poll_url for results."
    }


@router.get(
    "/jobs/{job_id}",
    summary="Check job status and get result when complete"
)
@limiter.limit("60/minute")
async def get_job_status(request: Request, job_id: str):
    \"\"\"
    Poll this endpoint to check if analysis is complete.
    Returns result when status is 'completed'.
    \"\"\"
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response = job.to_dict()

    # Add recommendation to completed jobs
    if job.status == JobStatus.COMPLETED and job.result:
        scores   = job.result.get("scores", {})
        decision = job.result.get("final_decision", "HOLD")
        confidence = job.result.get("confidence", 0)

        if scores:
            strongest_positive = max(scores.items(), key=lambda x: x[1])
            strongest_negative = min(scores.items(), key=lambda x: x[1])

            if decision == "BUY":
                rec = f"Strong buy signal with {confidence:.1f}% confidence. Primary driver: {strongest_positive[0]} ({strongest_positive[1]:.1f})."
            elif decision == "SELL":
                rec = f"Sell signal with {confidence:.1f}% confidence. Primary concern: {strongest_negative[0]} ({strongest_negative[1]:.1f})."
            else:
                rec = f"Hold signal with {confidence:.1f}% conviction."

            job.result["recommendation"] = rec

    return response
"""

with open("api/routes/jobs.py", "w", encoding="utf-8") as f:
    f.write(jobs_route.strip())
    print("api/routes/jobs.py written")

print("\nJob system files created!")