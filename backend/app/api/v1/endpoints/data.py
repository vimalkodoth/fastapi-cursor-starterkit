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

_ENDPOINT_PROCESS = "/process"
_ENDPOINT_PROCESS_ASYNC = "/process-async"


def _api_emit_log(body: str, **attrs):
    try:
        from app.observability import emit_log

        emit_log(body, attributes={**attrs, "layer": "api"})
    except Exception:
        pass


@router.post("/process", response_model=TaskResult, status_code=200)
async def process_data(
    request: DataRequest, service: DataService = Depends(get_data_service)
) -> TaskResult:
    """
    Process data synchronously via data service using RabbitMQ.
    Saves the record to database (non-blocking async DB).
    """
    _api_emit_log("api sync request start", endpoint=_ENDPOINT_PROCESS, method="POST")
    try:
        result = await service.process_data_sync_and_save(
            payload=request.payload, description=request.description
        )
        _api_emit_log(
            "api sync request end", endpoint=_ENDPOINT_PROCESS, status="success"
        )
        return result
    except ValueError as e:
        _api_emit_log(
            "api sync request end",
            endpoint=_ENDPOINT_PROCESS,
            status="error",
            error=str(e),
        )
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/process-async", response_model=TaskResult, status_code=202)
def process_data_async(
    request: DataRequest, service: DataService = Depends(get_data_service)
) -> TaskResult:
    """
    Process data asynchronously via Celery task.
    Returns a task ID that can be used to check status.
    """
    _api_emit_log(
        "api async request start", endpoint=_ENDPOINT_PROCESS_ASYNC, method="POST"
    )
    result = service.process_data_async(
        payload=request.payload, description=request.description
    )
    _api_emit_log(
        "api async request end",
        endpoint=_ENDPOINT_PROCESS_ASYNC,
        status="accepted",
        task_id=result.get("task_id", ""),
    )
    return result


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
