"""
Pydantic models for API request/response validation.
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


# Data Service Models
class DataRequest(BaseModel):
    """
    Request model for data processing endpoints.

    Attributes:
        payload: The data to process (can be string, number, list, dict, etc.)
        description: Optional description or processing hint (e.g., "uppercase", "reverse", "square")
    """

    payload: Any
    description: Optional[str] = None


# Task Models
class TaskResponse(BaseModel):
    """
    Response model for task creation (returns task ID).

    Attributes:
        task_id: Unique identifier for the task
        task_status: Current status of the task
    """

    task_id: str
    task_status: str


class TaskResult(BaseModel):
    """
    Response model for task results.

    Attributes:
        task_id: Unique identifier for the task (or "-" for synchronous tasks)
        task_status: Current status of the task (e.g., "Processing", "Success", "Failed")
        outcome: The result of the task processing (None if still processing)
    """

    task_id: str
    task_status: str
    outcome: Optional[Any] = None


# Database query response models (Pydantic; use response_model in endpoints)
class RecordResponse(BaseModel):
    """Response model for a single data processing record."""

    id: Optional[int] = None
    task_id: str
    payload: str
    description: Optional[str] = None
    task_type: str = "data"
    task_status: str
    outcome: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskLogResponse(BaseModel):
    """Response model for a single task log entry."""

    id: Optional[int] = None
    task_id: str
    correlation_id: Optional[str] = None
    queue_name: Optional[str] = None
    service_name: str
    task_type: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
