import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _normalize_database_url(url: str) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy.

    - Heroku commonly provides postgres://
    - SQLAlchemy's default postgresql:// dialect maps to psycopg2 unless specified
    - This app uses psycopg v3, so we force postgresql+psycopg:// when no driver is specified
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # If caller already specified a driver (postgresql+psycopg://, postgresql+psycopg2://, etc.), keep it.
    if url.startswith("postgresql+"):
        return url

    # Force psycopg v3 driver
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    return _normalize_database_url(url)


_ENGINE = None
_SessionLocal = None


def get_engine():
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        _ENGINE = create_engine(get_database_url(), pool_pre_ping=True, future=True)
        _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)
    return _ENGINE


@contextmanager
def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        get_engine()
    session = _SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


