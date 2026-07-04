# database/repository.py

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
