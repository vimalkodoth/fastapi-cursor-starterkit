"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.database import init_db
from app.core.idempotency import IdempotencyMiddleware
from app.observability import init_observability

# OpenTelemetry: set tracer provider (no-op if OTEL_EXPORTER_OTLP_ENDPOINT not set)
init_observability()

app = FastAPI(
    title="FastAPI Starter Kit",
    description="A production-ready FastAPI starter kit for large-scale applications",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# Idempotency: optional Idempotency-Key header, Redis 1h TTL (no change to services/repos)
app.add_middleware(IdempotencyMiddleware)

# OpenTelemetry: auto-instrument FastAPI (traces for HTTP requests)
init_observability(app)


@app.on_event("startup")
def on_startup():
    """Initialize database on application startup."""
    init_db()


# Include API routers
app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "FastAPI Starter Kit API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
