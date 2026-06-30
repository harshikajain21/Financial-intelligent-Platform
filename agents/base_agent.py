# agents/base_agent.py

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
from utils.logger import get_logger


class AgentStatus:
    """Simple status constants"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

class AgentError(Exception):
    """Custom exception for agent failures"""
    pass

class AgentResult:
    """
    Standardized output from every agent.
    Every agent returns this — makes the Decision Fusion Engine's job easy.
    """
    def __init__(
        self,
        agent_name: str,
        success: bool,
        data: Any = None,
        score: Optional[float] = None,    # -100 to +100
        error: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        self.agent_name = agent_name
        self.success = success
        self.data = data
        self.score = score                 # the key output used by Decision Engine
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "data": self.data,
            "score": self.score,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class BaseAgent(ABC):
    """
    Parent class for all 12 agents.

    Every agent must implement:
        - execute() : the actual work
        - validate_output() : check the result makes sense

    Every agent gets for free:
        - logging
        - status tracking
        - error handling with retries
        - standardized output (AgentResult)
    """

    def __init__(self, name: str, max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries
        self.status = AgentStatus.IDLE
        self.last_run: Optional[datetime] = None
        self.logger = get_logger(name)
        self.logger.info(f"Agent initialized: {self.name}")

    @abstractmethod
    def execute(self, symbol: str = "GLOBAL", **kwargs) -> AgentResult:
        """
        Core logic of the agent. Every agent implements this differently.
        symbol: stock ticker e.g. 'AAPL'
        """
        pass

    @abstractmethod
    def validate_output(self, result: AgentResult) -> bool:
        """
        Sanity check on the result before passing it forward.
        e.g. check score is between -100 and +100
        """
        pass

    def run(self, symbol: str = "GLOBAL", **kwargs) -> AgentResult:
        """
        Public method called by the Orchestrator.
        Wraps execute() with retry logic and error handling.
        You never override this — override execute() instead.
        """
        self.logger.info(f"Starting run for symbol: {symbol}")
        self.status = AgentStatus.RUNNING
        self.last_run = datetime.utcnow()

        for attempt in range(1, self.max_retries + 1):
            try:
                result = self.execute(symbol, **kwargs)

                if self.validate_output(result):
                    self.status = AgentStatus.SUCCESS
                    self.logger.success(
                        f"Completed successfully | Score: {result.score}"
                    )
                    return result
                else:
                    raise ValueError(f"Output validation failed: {result.to_dict()}")

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed: {e}"
                )
                if attempt == self.max_retries:
                    self.status = AgentStatus.FAILED
                    self.logger.error(
                        f"All {self.max_retries} attempts failed for {symbol}"
                    )
                    return AgentResult(
                        agent_name=self.name,
                        success=False,
                        error=str(e)
                    )

    def get_status(self) -> dict:
        """Health check — Orchestrator calls this to monitor agents"""
        return {
            "agent": self.name,
            "status": self.status,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }