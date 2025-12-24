"""Database engine and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from ..config import config


# Create engine with optimized settings
engine = create_engine(
    f"sqlite:///{config.db_path}",
    connect_args={
        "timeout": 30,
        "check_same_thread": False,
    },
    pool_pre_ping=True,
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite for better concurrency."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup.

    Usage:
        with get_db() as db:
            products = db.query(ProductTable).all()
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


def init_db() -> None:
    """Initialize database tables."""
    from .tables import Base
    Base.metadata.create_all(bind=engine)
