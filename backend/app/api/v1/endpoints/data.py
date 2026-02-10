"""
Data router - Controller layer for data processing endpoints.
Uses async DB session (connection pool, non-blocking).
"""
from typing import Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.api.v1.deps import get_data_service
from app.models.schemas import DataRequest, TaskResult
from app.services.data_service import DataService

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/process", response_model=TaskResult, status_code=200)
async def process_data(
    request: DataRequest, service: DataService = Depends(get_data_service)
) -> TaskResult:
    """
    Process data synchronously via data service using RabbitMQ.
    Saves the record to database (non-blocking async DB).
    """
    try:
        return await service.process_data_sync_and_save(
            payload=request.payload, description=request.description
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/process-async", response_model=TaskResult, status_code=202)
def process_data_async(
    request: DataRequest, service: DataService = Depends(get_data_service)
) -> TaskResult:
    """
    Process data asynchronously via Celery task.
    Returns a task ID that can be used to check status.
    """
    return service.process_data_async(
        payload=request.payload, description=request.description
    )


@router.get("/process-async/{task_id}", response_model=TaskResult, status_code=200)
def get_data_task_status(
    task_id: str, service: DataService = Depends(get_data_service)
) -> Union[TaskResult, JSONResponse]:
    """
    Get the status of an async data processing task.
    """
    try:
        result = service.get_task_status(task_id)
        if result["task_status"] == "Processing":
            return JSONResponse(status_code=202, content=result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
