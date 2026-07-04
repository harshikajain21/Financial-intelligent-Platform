# api/models.py

from pydantic import BaseModel
from typing import Optional, Dict, List


class AnalysisResponse(BaseModel):
    symbol          : str
    timestamp       : str
    final_decision  : str
    confidence      : float
    scores          : Dict[str, float]
    errors          : List[str]
    duration_ms     : Optional[float]
    recommendation  : str


class HealthResponse(BaseModel):
    status      : str
    version     : str
    agents      : int
    timestamp   : str


class ErrorResponse(BaseModel):
    error   : str
    detail  : str
    symbol  : Optional[str] = None
