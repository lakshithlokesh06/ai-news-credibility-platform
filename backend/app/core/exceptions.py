import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette import status

from app.core.config import settings

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_content(
    *,
    code: str,
    message: str,
    request_id: str | None,
    detail=None,
    errors=None,
) -> dict:
    payload = {
        "detail": detail if detail is not None else message,
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        },
        "request_id": request_id,
    }
    if errors is not None:
        payload["errors"] = errors
    return payload


def _sanitize_validation_errors(errors):
    sanitized = []
    for error in errors:
        if isinstance(error, dict):
            sanitized.append(
                {
                    key: _sanitize_validation_errors(value) if isinstance(value, list) else value
                    for key, value in error.items()
                    if key != "input"
                }
            )
        else:
            sanitized.append(error)
    return sanitized


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        request_id = _request_id(request)
        detail = exc.detail
        if isinstance(detail, dict):
            message = str(detail.get("message") or detail.get("error") or "Request failed.")
            code = str(detail.get("error_type") or detail.get("code") or f"http_{exc.status_code}")
        else:
            message = str(detail or "Request failed.")
            code = f"http_{exc.status_code}"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_content(code=code, message=message, request_id=request_id, detail=detail),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = jsonable_encoder(exc.errors())
        errors = _sanitize_validation_errors(errors)
        request_id = _request_id(request)
        logger.info(
            "request_validation_error",
            extra={"path": request.url.path, "errors": errors, "request_id": request_id},
        )
        return JSONResponse(
            status_code=422,
            content=_error_content(
                code="validation_error",
                message="Request validation failed.",
                request_id=request_id,
                detail="Request validation failed.",
                errors=errors,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = _request_id(request)
        logger.exception(
            "unhandled_exception",
            extra={"path": request.url.path, "request_id": request_id},
        )
        message = "Internal server error."
        if settings.app_env != "production" and settings.debug:
            message = f"Internal server error: {type(exc).__name__}"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_content(
                code="internal_server_error",
                message=message,
                request_id=request_id,
                detail=message,
            ),
        )
