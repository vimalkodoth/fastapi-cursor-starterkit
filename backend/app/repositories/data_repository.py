"""
Data repository - Data access for data processing records.
Async implementation using SQLModel AsyncSession (connection-pooled).
"""
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.database import DataProcessingRecord


class DataRepository:
    """
    Repository for data processing records.
    Handles all database operations for DataProcessingRecord (async).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_record(
        self,
        task_id: str,
        payload: str,
        task_status: str,
        description: Optional[str] = None,
        task_type: str = "data",
        outcome: Optional[str] = None,
    ) -> DataProcessingRecord:
        """
        Create a new data processing record.
        """
        record = DataProcessingRecord(
            task_id=task_id,
            payload=payload,
            description=description,
            task_type=task_type,
            task_status=task_status,
            outcome=outcome,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_record_by_id(self, record_id: int) -> Optional[DataProcessingRecord]:
        """
        Get a record by its ID.
        """
        return await self.session.get(DataProcessingRecord, record_id)

    async def get_record_by_task_id(
        self, task_id: str
    ) -> Optional[DataProcessingRecord]:
        """
        Get a record by task ID.
        """
        stmt = select(DataProcessingRecord).where(
            DataProcessingRecord.task_id == task_id
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_records(
        self, limit: int = 10, offset: int = 0
    ) -> List[DataProcessingRecord]:
        """
        Get multiple records with pagination.
        """
        stmt = select(DataProcessingRecord).offset(offset).limit(limit)
        result = await self.session.exec(stmt)
        return list(result.all())

    async def delete_record_by_task_id(self, task_id: str) -> bool:
        """
        Delete a record by task ID.
        """
        record = await self.get_record_by_task_id(task_id)
        if not record:
            return False
        await self.session.delete(record)
        await self.session.commit()
        return True

    async def update_record(
        self,
        task_id: str,
        task_status: Optional[str] = None,
        outcome: Optional[str] = None,
    ) -> Optional[DataProcessingRecord]:
        """
        Update a record.
        """
        record = await self.get_record_by_task_id(task_id)
        if not record:
            return None
        if task_status:
            record.task_status = task_status
        if outcome:
            record.outcome = outcome
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record
