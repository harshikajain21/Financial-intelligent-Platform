# create_db.py

content = '''# database/models.py

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class AnalysisResult(Base):
    """
    Stores every analysis run permanently.
    One row = one full analysis of one stock symbol.
    """
    __tablename__ = "analysis_results"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    symbol          = Column(String(10), nullable=False, index=True)
    timestamp       = Column(DateTime, default=datetime.utcnow, index=True)
    final_decision  = Column(String(10), nullable=False)   # BUY / HOLD / SELL
    confidence      = Column(Float, nullable=False)
    recommendation  = Column(Text)
    duration_ms     = Column(Float)

    # Agent scores stored as JSON
    scores          = Column(JSON)
    errors          = Column(JSON)

    # Key metrics snapshot
    close_price     = Column(Float)
    technical_score = Column(Float)
    news_score      = Column(Float)
    sentiment_score = Column(Float)
    macro_score     = Column(Float)
    risk_score      = Column(Float)
    fundamental_score = Column(Float)
    regime_score    = Column(Float)
    anomaly_score   = Column(Float)

    def to_dict(self):
        return {
            "id"              : self.id,
            "symbol"          : self.symbol,
            "timestamp"       : self.timestamp.isoformat() if self.timestamp else None,
            "final_decision"  : self.final_decision,
            "confidence"      : self.confidence,
            "recommendation"  : self.recommendation,
            "duration_ms"     : self.duration_ms,
            "scores"          : self.scores,
            "errors"          : self.errors,
            "close_price"     : self.close_price,
        }


class SymbolWatchlist(Base):
    """
    Stores symbols the user wants to track regularly.
    """
    __tablename__ = "watchlist"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    symbol      = Column(String(10), nullable=False, unique=True)
    added_at    = Column(DateTime, default=datetime.utcnow)
    notes       = Column(Text)

    def to_dict(self):
        return {
            "id"        : self.id,
            "symbol"    : self.symbol,
            "added_at"  : self.added_at.isoformat() if self.added_at else None,
            "notes"     : self.notes,
        }
'''

with open("database/models.py", "w") as f:
    f.write(content)
    print("database/models.py written")

connection_content = '''# database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base
from utils.logger import get_logger
import os

logger = get_logger("Database")

# SQLite database file — stored in project root
DATABASE_URL = "sqlite:///./finplatform.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # needed for SQLite
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Create all tables if they don\'t exist.
    Called once on API startup.
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_db() -> Session:
    """
    FastAPI dependency — provides a database session per request.
    Automatically closes session when request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

with open("database/connection.py", "w") as f:
    f.write(connection_content)
    print("database/connection.py written")

repository_content = '''# database/repository.py

from sqlalchemy.orm import Session
from sqlalchemy import desc
from database.models import AnalysisResult, SymbolWatchlist
from datetime import datetime
from typing import Optional, List
from utils.logger import get_logger

logger = get_logger("Repository")


class AnalysisRepository:
    """
    Handles all database operations for analysis results.
    The API and orchestrator never touch the DB directly — they use this.
    """

    @staticmethod
    def save_analysis(db: Session, report, close_price: float = None) -> AnalysisResult:
        """Save a completed analysis report to the database."""
        try:
            scores = report.scores or {}
            record = AnalysisResult(
                symbol            = report.symbol,
                timestamp         = datetime.utcnow(),
                final_decision    = report.final_decision or "UNAVAILABLE",
                confidence        = report.confidence or 0,
                recommendation    = None,
                duration_ms       = report.duration_ms,
                scores            = scores,
                errors            = report.errors or [],
                close_price       = close_price,
                technical_score   = scores.get("TechnicalAnalysisAgent"),
                news_score        = scores.get("NewsIntelligenceAgent"),
                sentiment_score   = scores.get("SocialSentimentAgent"),
                macro_score       = scores.get("MacroeconomicIntelligenceAgent"),
                risk_score        = scores.get("PortfolioRiskAgent"),
                fundamental_score = scores.get("FundamentalAnalysisAgent"),
                regime_score      = scores.get("RegimeDetectionAgent"),
                anomaly_score     = scores.get("AnomalyDetectionAgent"),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info(f"Saved analysis for {report.symbol} | Decision: {report.final_decision}")
            return record
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save analysis: {e}")
            raise

    @staticmethod
    def get_history(db: Session, symbol: str, limit: int = 10) -> List[AnalysisResult]:
        """Get recent analysis history for a symbol."""
        return (
            db.query(AnalysisResult)
            .filter(AnalysisResult.symbol == symbol.upper())
            .order_by(desc(AnalysisResult.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_latest(db: Session, symbol: str) -> Optional[AnalysisResult]:
        """Get most recent analysis for a symbol."""
        return (
            db.query(AnalysisResult)
            .filter(AnalysisResult.symbol == symbol.upper())
            .order_by(desc(AnalysisResult.timestamp))
            .first()
        )

    @staticmethod
    def get_all_latest(db: Session, limit: int = 20) -> List[AnalysisResult]:
        """Get latest analysis for all symbols — for dashboard overview."""
        return (
            db.query(AnalysisResult)
            .order_by(desc(AnalysisResult.timestamp))
            .limit(limit)
            .all()
        )


class WatchlistRepository:
    """Handles watchlist database operations."""

    @staticmethod
    def add_symbol(db: Session, symbol: str, notes: str = None) -> SymbolWatchlist:
        """Add a symbol to the watchlist."""
        existing = db.query(SymbolWatchlist).filter(
            SymbolWatchlist.symbol == symbol.upper()
        ).first()

        if existing:
            return existing

        record = SymbolWatchlist(symbol=symbol.upper(), notes=notes)
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Added {symbol} to watchlist")
        return record

    @staticmethod
    def get_watchlist(db: Session) -> List[SymbolWatchlist]:
        """Get all watchlist symbols."""
        return db.query(SymbolWatchlist).order_by(SymbolWatchlist.added_at).all()

    @staticmethod
    def remove_symbol(db: Session, symbol: str) -> bool:
        """Remove a symbol from watchlist."""
        record = db.query(SymbolWatchlist).filter(
            SymbolWatchlist.symbol == symbol.upper()
        ).first()
        if record:
            db.delete(record)
            db.commit()
            logger.info(f"Removed {symbol} from watchlist")
            return True
        return False
'''

with open("database/repository.py", "w") as f:
    f.write(repository_content)
    print("database/repository.py written")