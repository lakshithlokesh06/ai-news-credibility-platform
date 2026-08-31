from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class ComponentStatus(BaseModel):
    status: str
    message: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    service: str
    environment: str
    components: dict[str, ComponentStatus]


class SystemInfoResponse(BaseModel):
    application: str
    version: str
    environment: str
    api_version: str
    capabilities: list[str]
    docs_enabled: bool


class ProcessMetricsResponse(BaseModel):
    request_count: int
    error_count: int
    rate_limited_count: int
    average_duration_ms: float
    status_counts: dict[str, int]
