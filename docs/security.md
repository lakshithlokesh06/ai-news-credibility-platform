# Security Notes

This platform is currently a single-user/local architecture. It has production-oriented safeguards, but it does not include authentication or multi-user authorization.

## Boundaries

- Dataset imports accept CSV filenames only from the configured raw-data directory.
- Import paths reject absolute paths, parent-directory traversal, unsupported extensions, symlink escapes, and oversized files.
- Model artifacts are loaded only from controlled training-run metadata under the configured model directory.
- Artifact loaders reject traversal and validate checksums before use.
- Transformer artifact readiness checks validate metadata and checksums without loading model weights.

## Input Limits

Article title, article content, combined article input, dataset import size, monitoring windows, explanation limits, pagination, experiment comparison count, and tags are bounded through central configuration and Pydantic validation.

Oversized article inputs are rejected with validation errors. Validation responses do not echo raw article bodies.

Human review notes are bounded plain-text fields. The frontend renders them as text, not raw HTML.

## Observability

The backend returns an `X-Request-ID` header for every request, accepts bounded incoming request IDs, and logs method, path, status, duration, and request ID. Request logs do not include query strings or bodies.

Do not log full article bodies, raw dataset rows, secrets, database credentials, model binaries, SHAP arrays, or future authorization headers.

## Rate Limits And Capacity

The app includes in-process rate limits and bounded semaphores for expensive operations such as training and explainability. These controls are suitable for a single backend process and are not distributed across multiple replicas.

Use external infrastructure-aware controls before exposing this service broadly.

## CORS And Headers

Development CORS defaults allow local Next.js origins. Production configuration must provide explicit origins and cannot use wildcard CORS. The API also returns basic security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.

A strict Content Security Policy is not added yet because it requires coordinated Next.js runtime and deployment testing.

## Data Privacy

Saved analysis content resides in PostgreSQL. History detail endpoints return saved article content; history summaries, review queue responses, reviewed-performance APIs, calibration APIs, error-analysis APIs, and monitoring endpoints avoid full article bodies. Monitoring remains aggregate-only.

Human-verified labels must be explicitly entered. They are not inferred from predictions, confidence, explanations, source metadata, training labels, web results, or external APIs. Review notes are not returned by aggregate metrics endpoints.

## Deployment Limitations

Do not expose mutation, history, or model-management endpoints to untrusted users without authentication, authorization, HTTPS termination at a reverse proxy or deployment platform, distributed rate limiting, backups, and stronger operational controls.
