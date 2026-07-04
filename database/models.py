# database/models.py

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
