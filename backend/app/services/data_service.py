"""
Data processing service - Business logic for data operations.
Uses async DB (connection-pooled) for non-blocking requests.
Blocking RabbitMQ RPC is run in a thread pool so the event loop is not blocked.
"""
import asyncio
import json
from typing import Any, Dict, List, Optional

from celery.result import AsyncResult
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.dependencies import call_service, get_queue_name
from app.repositories.data_repository import DataRepository
from app.repositories.task_repository import TaskRepository
from app.tasks.data import process_data_task


class DataService:
    """
    Service for handling data processing business logic.
    Uses AsyncSession for non-blocking database access.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.data_repo = DataRepository(session)
        self.task_repo = TaskRepository(session)

    def process_data_sync(
        self, payload: Any, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process data synchronously via data service using RabbitMQ.
        (RabbitMQ call is blocking; DB write is async and invoked by caller.)
        """
        queue_name = get_queue_name("data")
        request_payload = {
            "payload": payload,
            "description": description,
            "task_type": "data",
        }
        response = call_service(
            queue_name=queue_name, payload=request_payload, use_rabbitmq=True
        )
        return {"task_id": "-", "task_status": "Success", "outcome": response}

    async def process_data_sync_and_save(
        self, payload: Any, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process via RabbitMQ RPC (in thread pool) and save result to DB (async).
        Does not block the event loop: blocking RPC runs in asyncio.to_thread().
        """
        result = await asyncio.to_thread(
            self.process_data_sync, payload=payload, description=description
        )
        outcome_str = (
            json.dumps(result["outcome"])
            if isinstance(result["outcome"], dict)
            else str(result["outcome"])
        )
        await self.data_repo.create_record(
            task_id="-",
            payload=str(payload),
            description=description,
            task_type="data",
            task_status="Success",
            outcome=outcome_str,
        )
        return result

    def process_data_async(
        self, payload: Any, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process data asynchronously via Celery task (no DB in request path).
        Propagates trace context in the task payload so the worker continues the same trace
        (API → Celery worker → data-service in one trace). See backend celery.py task_prerun.
        """
        request_payload = {"payload": payload, "description": description}
        try:
            from app.observability import inject_trace_context

            carrier = {}
            inject_trace_context(carrier)
            if carrier:
                request_payload["_trace_context"] = carrier
        except Exception:  # pylint: disable=broad-except
            pass
        # headers={} allows instrumentor to inject too; worker prefers payload for reliability.
        task = process_data_task.apply_async(
            args=[json.dumps(request_payload)],
            headers={},
        )
        return {
            "task_id": str(task.id),
            "task_status": "Processing",
            "outcome": None,
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of an async data processing task (Redis/Celery).
        """
        task = AsyncResult(task_id)
        if not task.ready():
            return {"task_id": task_id, "task_status": "Processing", "outcome": None}
        if task.failed():
            raise ValueError(f"Task failed: {task.info}")
        result = task.get()
        return {"task_id": task_id, "task_status": "Success", "outcome": result}

    async def get_processing_records(
        self, limit: int = 10, offset: int = 0
    ) -> List[Any]:
        """
        Get data processing records (async DB).
        """
        records = await self.data_repo.get_records(limit=limit, offset=offset)
        return records

    async def get_processing_record(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific processing record by task_id (async DB).
        """
        record = await self.data_repo.get_record_by_task_id(task_id)
        return record.model_dump() if record else None

    async def delete_processing_record(self, task_id: str) -> bool:
        """
        Delete a processing record (async DB).
        """
        return await self.data_repo.delete_record_by_task_id(task_id)
