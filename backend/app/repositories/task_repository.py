"""
Task repository - Data access for task logs.
Async implementation using SQLModel AsyncSession (connection-pooled).
"""
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.database import TaskLog


class TaskRepository:
    """
    Repository for task logs.
    Handles all database operations for TaskLog (async).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_log(
        self,
        task_id: str,
        service_name: str,
        task_type: str,
        status: str,
        correlation_id: Optional[str] = None,
        queue_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> TaskLog:
        """
        Create a new task log.
        """
        log = TaskLog(
            task_id=task_id,
            correlation_id=correlation_id,
            queue_name=queue_name,
            service_name=service_name,
            task_type=task_type,
            description=description,
            status=status,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_logs_by_correlation_id(
        self, correlation_id: str, limit: int = 10, offset: int = 0
    ) -> List[TaskLog]:
        """
        Get logs by correlation ID.
        """
        stmt = (
            select(TaskLog)
            .where(TaskLog.correlation_id == correlation_id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def get_logs(self, limit: int = 10, offset: int = 0) -> List[TaskLog]:
        """
        Get multiple logs with pagination.
        """
        stmt = select(TaskLog).offset(offset).limit(limit)
        result = await self.session.exec(stmt)
        return list(result.all())
