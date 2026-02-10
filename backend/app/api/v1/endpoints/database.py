"""
Database router - Controller layer for database query endpoints.
Uses async DB session (connection pool, non-blocking).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.deps import get_data_service, get_task_repository
from app.models.schemas import RecordResponse, TaskLogResponse
from app.repositories.task_repository import TaskRepository
from app.services.data_service import DataService

router = APIRouter(prefix="/database", tags=["database"])


@router.get("/records", response_model=List[RecordResponse])
async def get_processing_records(
    limit: int = 10,
    offset: int = 0,
    service: DataService = Depends(get_data_service),
) -> List[RecordResponse]:
    """
    Get data processing records from database (non-blocking async).
    """
    records = await service.get_processing_records(limit=limit, offset=offset)
    return [RecordResponse.model_validate(r) for r in records]


@router.get("/records/{task_id}", response_model=RecordResponse)
async def get_processing_record(
    task_id: str, service: DataService = Depends(get_data_service)
) -> RecordResponse:
    """
    Get a specific data processing record by task_id (non-blocking async).
    """
    record = await service.get_processing_record(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return RecordResponse(**record)


@router.get("/logs", response_model=List[TaskLogResponse])
async def get_task_logs(
    correlation_id: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    task_repo: TaskRepository = Depends(get_task_repository),
) -> List[TaskLogResponse]:
    """
    Get task logs from database (non-blocking async).
    Optionally filter by correlation_id.
    """
    if correlation_id:
        logs = await task_repo.get_logs_by_correlation_id(
            correlation_id=correlation_id, limit=limit, offset=offset
        )
    else:
        logs = await task_repo.get_logs(limit=limit, offset=offset)
    return [TaskLogResponse.model_validate(log) for log in logs]


@router.delete("/records/{task_id}", status_code=204)
async def delete_processing_record(
    task_id: str, service: DataService = Depends(get_data_service)
) -> None:
    """
    Delete a data processing record (non-blocking async).
    """
    deleted = await service.delete_processing_record(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return None
