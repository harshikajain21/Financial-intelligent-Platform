"""
Database Models — SQLAlchemy ORM models for persisting analysis results.
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    JSON,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PriceRecord(Base):
    """Stores daily OHLCV price records."""

    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    source = Column(String(50), default="yahoo")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_price_ticker_date"),
        Index("ix_price_ticker_date", "ticker", "date"),
    )

    def __repr__(self) -> str:
        return f"<PriceRecord ticker={self.ticker} date={self.date}>"


class AnalysisResult(Base):
    """Stores the full analysis envelope for a ticker run."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    run_id = Column(String(64), nullable=False, unique=True, index=True)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    data = Column(JSON)
    error = Column(Text)
    elapsed_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<AnalysisResult ticker={self.ticker} agent={self.agent_name} "
            f"status={self.status}>"
        )


class NewsArticle(Base):
    """Stores fetched news articles."""

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, nullable=False, unique=True)
    title = Column(Text)
    description = Column(Text)
    published_at = Column(DateTime)
    source_name = Column(String(200))
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        return f"<NewsArticle title={str(self.title)[:50]}>"


class Alert(Base):
    """Stores triggered alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), index=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), default="INFO")
    message = Column(Text, nullable=False)
    metadata = Column(JSON)
    dispatched = Column(Integer, default=0)  # 0=pending, 1=dispatched
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Alert ticker={self.ticker} type={self.alert_type} severity={self.severity}>"
