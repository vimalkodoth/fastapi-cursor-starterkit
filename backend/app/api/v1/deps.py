"""
Shared FastAPI dependencies for API v1.
Import these in endpoint modules instead of redefining.
"""
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_async_session
from app.repositories.task_repository import TaskRepository
from app.services.data_service import DataService


def get_data_service(
    session: AsyncSession = Depends(get_async_session),
) -> DataService:
    """Dependency that returns a DataService instance (async session)."""
    return DataService(session)


def get_task_repository(
    session: AsyncSession = Depends(get_async_session),
) -> TaskRepository:
    """Dependency that returns a TaskRepository instance (async session)."""
    return TaskRepository(session)
