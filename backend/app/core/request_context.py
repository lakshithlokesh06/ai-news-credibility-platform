from contextvars import ContextVar

REQUEST_ID_CONTEXT: ContextVar[str | None] = ContextVar("request_id", default=None)


def current_request_id() -> str | None:
    return REQUEST_ID_CONTEXT.get()
