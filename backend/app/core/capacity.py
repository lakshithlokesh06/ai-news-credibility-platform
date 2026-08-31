from threading import BoundedSemaphore
from typing import Literal

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings

CapacityName = Literal["training", "explanation"]


def _limit_for(name: CapacityName) -> int:
    return settings.training_concurrency_limit if name == "training" else settings.explanation_concurrency_limit


def _semaphore(request: Request, name: CapacityName) -> BoundedSemaphore:
    semaphores = getattr(request.app.state, "capacity_semaphores", None)
    if semaphores is None:
        semaphores = {}
        request.app.state.capacity_semaphores = semaphores
    return semaphores.setdefault(name, BoundedSemaphore(_limit_for(name)))


def capacity_guard(name: CapacityName):
    async def dependency(request: Request):
        semaphore = _semaphore(request, name)
        acquired = semaphore.acquire(blocking=False)
        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": f"{name.capitalize()} capacity is currently exhausted. Try again later.",
                    "error_type": f"{name}_capacity_exhausted",
                },
            )
        try:
            yield
        finally:
            semaphore.release()

    return Depends(dependency)
