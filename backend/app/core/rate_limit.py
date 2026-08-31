from collections import defaultdict, deque
from time import monotonic
from typing import Literal

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings

RateLimitName = Literal["prediction", "explanation", "training", "mutation", "monitoring"]


class InMemoryRateLimiter:
    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, int]:
        now = monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()
        if len(hits) >= self.limit:
            retry_after = max(1, int(self.window_seconds - (now - hits[0]))) if hits else self.window_seconds
            return False, retry_after
        hits.append(now)
        return True, 0


def _limit_for(name: RateLimitName) -> int:
    return {
        "prediction": settings.prediction_rate_limit,
        "explanation": settings.explanation_rate_limit,
        "training": settings.training_rate_limit,
        "mutation": settings.mutation_rate_limit,
        "monitoring": settings.monitoring_rate_limit,
    }[name]


def _client_key(request: Request, name: RateLimitName) -> str:
    client_host = request.client.host if request.client else "unknown"
    if settings.trusted_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        client_host = forwarded_for or client_host
    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)
    return f"{name}:{client_host}:{route_path}"


def rate_limit(name: RateLimitName):
    async def dependency(request: Request) -> None:
        limiters = getattr(request.app.state, "rate_limiters", None)
        if limiters is None:
            limiters = {}
            request.app.state.rate_limiters = limiters
        limiter = limiters.setdefault(
            name,
            InMemoryRateLimiter(limit=_limit_for(name), window_seconds=settings.rate_limit_window_seconds),
        )
        allowed, retry_after = limiter.check(_client_key(request, name))
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Rate limit exceeded. Try again later.",
                    "error_type": "rate_limited",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

    return Depends(dependency)
