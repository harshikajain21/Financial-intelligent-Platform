"""
Database Connection — SQLAlchemy engine and session factory.

Supports PostgreSQL (production) and SQLite (development/testing).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import Settings

_settings = Settings()
_engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=_settings.debug,
)

SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_db_connection():
    """Return the SQLAlchemy engine."""
    return _engine


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context-managed database session.

    Usage::

        with get_db_session() as session:
            result = session.execute(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
