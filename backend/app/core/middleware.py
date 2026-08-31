import logging
import re
import time
from collections import defaultdict
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import REQUEST_ID_CONTEXT

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
logger = logging.getLogger("app.requests")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming and REQUEST_ID_RE.fullmatch(incoming) else uuid4().hex
        token = REQUEST_ID_CONTEXT.set(request_id)
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            metrics = getattr(request.app.state, "process_metrics", None)
            if metrics is not None:
                metrics.record(status_code=status_code, duration_ms=duration_ms)
            if not request.url.path.endswith("/health"):
                logger.info(
                    "request_completed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "duration_ms": duration_ms,
                    },
                )
            REQUEST_ID_CONTEXT.reset(token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault(REQUEST_ID_HEADER, getattr(request.state, "request_id", ""))
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


class ProcessMetrics:
    def __init__(self) -> None:
        self.request_count = 0
        self.error_count = 0
        self.rate_limited_count = 0
        self.total_duration_ms = 0.0
        self.status_counts: dict[str, int] = defaultdict(int)

    def record(self, *, status_code: int, duration_ms: float) -> None:
        self.request_count += 1
        self.total_duration_ms += duration_ms
        self.status_counts[str(status_code)] += 1
        if status_code >= 500:
            self.error_count += 1
        if status_code == 429:
            self.rate_limited_count += 1

    def snapshot(self) -> dict:
        average = self.total_duration_ms / self.request_count if self.request_count else 0.0
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "rate_limited_count": self.rate_limited_count,
            "average_duration_ms": round(average, 3),
            "status_counts": dict(self.status_counts),
        }
