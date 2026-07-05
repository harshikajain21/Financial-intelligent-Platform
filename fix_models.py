# fix_models.py

content = """# api/models.py

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
    explanations    : Optional[Dict[str, str]] = {}


class HealthResponse(BaseModel):
    status      : str
    version     : str
    agents      : int
    timestamp   : str


class ErrorResponse(BaseModel):
    error   : str
    detail  : str
    symbol  : Optional[str] = None
"""

with open("api/models.py", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("api/models.py updated")