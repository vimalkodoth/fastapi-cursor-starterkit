"""
Database models using SQLModel.

SQLModel combines SQLAlchemy and Pydantic for type-safe database models.
The sqlalchemy.func import is for server_default/onupdate timestamps; expected with SQLModel.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlmodel import Column, DateTime, Field, SQLModel


class DataProcessingRecord(SQLModel, table=True):
    """
    Model for storing data processing records.
    Tracks all data processing requests and their outcomes.
    """

    __tablename__ = "data_processing_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)
    payload: str
    description: Optional[str] = None
    task_type: str = Field(default="data")
    task_status: str
    outcome: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())
    )


class TaskLog(SQLModel, table=True):
    """
    Model for storing task execution logs.
    Tracks all task executions with correlation IDs for tracing.
    """

    __tablename__ = "task_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True)
    correlation_id: Optional[str] = Field(default=None, index=True)
    queue_name: Optional[str] = None
    service_name: str
    task_type: str
    description: Optional[str] = None
    status: str  # start, end, error
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
