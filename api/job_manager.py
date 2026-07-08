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
    """
    Simple in-memory job manager.
    Runs analysis in background thread.
    Stores results in memory (lost on restart).
    Production version would use Redis/Celery.
    """

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
        """Keep only the most recent N jobs in memory."""
        with self._lock:
            if len(self._jobs) > max_jobs:
                oldest = sorted(self._jobs.keys())[:-max_jobs]
                for job_id in oldest:
                    del self._jobs[job_id]


# Global job manager instance
job_manager = JobManager()