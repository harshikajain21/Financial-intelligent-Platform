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
    """
    Start analysis in background.
    Returns job_id immediately — poll /jobs/{job_id} for result.
    """
    symbol   = sanitize_symbol(symbol)
    exchange = sanitize_exchange(exchange)

    orchestrator = request.app.state.orchestrator
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
    """
    Poll this endpoint to check if analysis is complete.
    Returns result when status is 'completed'.
    """
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