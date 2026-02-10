"""
API v1 endpoints.
"""
from fastapi import APIRouter

from .endpoints import data, database, metrics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(data.router)
api_router.include_router(database.router)
api_router.include_router(metrics.router)
