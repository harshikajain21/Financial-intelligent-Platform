# fix_connection.py

content = """# database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
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

with open("database/connection.py", "w", encoding="utf-8") as f:
    f.write(content)
    print("database/connection.py fixed")