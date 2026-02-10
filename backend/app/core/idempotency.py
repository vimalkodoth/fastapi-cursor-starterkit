"""
Idempotency layer: optional Idempotency-Key header, Redis storage, 1h TTL.
Sits in front of route handlers; no changes to services or repositories.
"""
import json
import os
from typing import Callable, Optional

from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Paths that support idempotency (POST only)
IDEMPOTENT_PATHS = frozenset({"/api/v1/data/process", "/api/v1/data/process-async"})

IDEMPOTENCY_HEADER = "idempotency-key"
IDEMPOTENCY_TTL_SECONDS = 3600  # 1 hour
REDIS_KEY_PREFIX = "idempotency:"


async def _get_stored(redis, key: str) -> Optional[dict]:
    """Return stored {status_code, body} or None."""
    try:
        raw = await redis.get(key)
    except Exception:
        return None
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


async def _set_stored(redis, key: str, status_code: int, body: bytes) -> None:
    """Store response in Redis with TTL."""
    try:
        payload = json.dumps({"status_code": status_code, "body": body.decode("utf-8")})
        await redis.setex(key, IDEMPOTENCY_TTL_SECONDS, payload.encode("utf-8"))
    except Exception:
        pass


class IdempotencyMiddleware:
    """
    ASGI middleware: optional Idempotency-Key header.
    On hit: return stored response. On miss: run app, capture response, store, return.
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self._redis: Optional[object] = None

    def _get_redis_url(self) -> str:
        return os.getenv("IDEMPOTENCY_REDIS_URL") or os.getenv(
            "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )

    def _get_redis(self):
        if self._redis is None:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(
                self._get_redis_url(),
                decode_responses=False,
            )
        return self._redis

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")
        if method != "POST" or path not in IDEMPOTENT_PATHS:
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        key = headers.get(IDEMPOTENCY_HEADER) or headers.get(
            "Idempotency-Key"
        )  # allow both
        if not key or not key.strip():
            await self.app(scope, receive, send)
            return

        key = key.strip()
        redis_key = f"{REDIS_KEY_PREFIX}{path}:{key}"

        try:
            redis = self._get_redis()
        except Exception:
            await self.app(scope, receive, send)
            return

        stored = await _get_stored(redis, redis_key)
        if stored is not None:
            status_code = stored.get("status_code", 200)
            body = stored.get("body", "{}")
            if isinstance(body, str):
                body = body.encode("utf-8")
            response = Response(
                content=body,
                status_code=status_code,
                media_type="application/json",
            )
            await response(scope, receive, send)
            return

        # Capture response by wrapping send
        status_code: int = 200
        body_chunks: list = []

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            elif message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                if chunk:
                    body_chunks.append(chunk)
            await send(message)

        await self.app(scope, receive, send_wrapper)
        full_body = b"".join(body_chunks)
        await _set_stored(redis, redis_key, status_code, full_body)
