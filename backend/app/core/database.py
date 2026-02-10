"""
Database configuration and session management using SQLModel.

Supports both sync (Celery worker, init) and async (FastAPI) with connection pooling.
ORM: SQLModel (0.0.32+). Async: SQLModel's AsyncSession + SQLAlchemy async engine.

SQLAlchemy imports (create_async_engine, async_sessionmaker) are intentional:
SQLModel is built on SQLAlchemy and does not provide async engine creation.
"""
import os
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# Import all models so they're registered with SQLModel
from app.models.database import DataProcessingRecord, TaskLog  # noqa: F401

# Sync URL (psycopg2) - for init_db and Celery worker
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://fastapi:fastapi@localhost:5432/fastapi_db"
)

# Async URL (asyncpg) - for FastAPI non-blocking requests
# Replace postgresql:// with postgresql+asyncpg://
ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1),
)

# Sync engine: connection pool for Celery and init_db
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async engine: connection pool for non-blocking FastAPI requests
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session factory (one session per request, from pool)
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


def init_db() -> None:
    """
    Initialize database - create all tables.
    Uses sync engine (Celery/init). Call on application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Sync dependency for database session (e.g. Celery worker).
    Prefer get_async_session for FastAPI routes.
    """
    with Session(engine) as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for non-blocking database sessions.
    Uses connection pool; one session per request.
    Repositories call commit/rollback as needed.
    """
    async with async_session_factory() as session:
        yield session
