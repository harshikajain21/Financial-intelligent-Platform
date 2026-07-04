# fix_database.py

models = """# database/models.py

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    symbol            = Column(String(10), nullable=False, index=True)
    timestamp         = Column(DateTime, default=datetime.utcnow, index=True)
    final_decision    = Column(String(10), nullable=False)
    confidence        = Column(Float, nullable=False)
    recommendation    = Column(Text)
    duration_ms       = Column(Float)
    scores            = Column(JSON)
    errors            = Column(JSON)
    close_price       = Column(Float)
    technical_score   = Column(Float)
    news_score        = Column(Float)
    sentiment_score   = Column(Float)
    macro_score       = Column(Float)
    risk_score        = Column(Float)
    fundamental_score = Column(Float)
    regime_score      = Column(Float)
    anomaly_score     = Column(Float)

    def to_dict(self):
        return {
            "id"             : self.id,
            "symbol"         : self.symbol,
            "timestamp"      : self.timestamp.isoformat() if self.timestamp else None,
            "final_decision" : self.final_decision,
            "confidence"     : self.confidence,
            "recommendation" : self.recommendation,
            "duration_ms"    : self.duration_ms,
            "scores"         : self.scores,
            "errors"         : self.errors,
            "close_price"    : self.close_price,
        }


class SymbolWatchlist(Base):
    __tablename__ = "watchlist"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    symbol   = Column(String(10), nullable=False, unique=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes    = Column(Text)

    def to_dict(self):
        return {
            "id"       : self.id,
            "symbol"   : self.symbol,
            "added_at" : self.added_at.isoformat() if self.added_at else None,
            "notes"    : self.notes,
        }
"""

connection = """# database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from utils.logger import get_logger

logger = get_logger("Database")

DATABASE_URL = "sqlite:///./finplatform.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""

repository = """# database/repository.py

from sqlalchemy.orm import Session
from sqlalchemy import desc
from database.models import AnalysisResult, SymbolWatchlist
from datetime import datetime
from typing import Optional, List
from utils.logger import get_logger

logger = get_logger("Repository")


class AnalysisRepository:

    @staticmethod
    def save_analysis(db: Session, report, close_price: float = None) -> AnalysisResult:
        try:
            scores = report.scores or {}
            record = AnalysisResult(
                symbol            = report.symbol,
                timestamp         = datetime.utcnow(),
                final_decision    = report.final_decision or "UNAVAILABLE",
                confidence        = report.confidence or 0,
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
        return (
            db.query(AnalysisResult)
            .filter(AnalysisResult.symbol == symbol.upper())
            .order_by(desc(AnalysisResult.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_latest(db: Session, symbol: str) -> Optional[AnalysisResult]:
        return (
            db.query(AnalysisResult)
            .filter(AnalysisResult.symbol == symbol.upper())
            .order_by(desc(AnalysisResult.timestamp))
            .first()
        )

    @staticmethod
    def get_all_latest(db: Session, limit: int = 20) -> List[AnalysisResult]:
        return (
            db.query(AnalysisResult)
            .order_by(desc(AnalysisResult.timestamp))
            .limit(limit)
            .all()
        )


class WatchlistRepository:

    @staticmethod
    def add_symbol(db: Session, symbol: str, notes: str = None) -> SymbolWatchlist:
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
        return db.query(SymbolWatchlist).order_by(SymbolWatchlist.added_at).all()

    @staticmethod
    def remove_symbol(db: Session, symbol: str) -> bool:
        record = db.query(SymbolWatchlist).filter(
            SymbolWatchlist.symbol == symbol.upper()
        ).first()
        if record:
            db.delete(record)
            db.commit()
            logger.info(f"Removed {symbol} from watchlist")
            return True
        return False
"""

files = {
    "database/models.py"     : models,
    "database/connection.py" : connection,
    "database/repository.py" : repository,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{path} written successfully")