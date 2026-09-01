# Release Checklist

Use this checklist before tagging or deploying a release.

## Code And Tests

- Run the complete backend test suite.
- Run frontend lint, typecheck, and production build.
- Verify no test failures are skipped or hidden.
- Inspect code comments for stale TODOs or debug notes.
- Confirm no accidental `print()` or `console.log()` output is present.

## Database

- Run `alembic history`.
- Verify exactly one Alembic head.
- Run `alembic upgrade head --sql` or apply migrations in a disposable database.
- Confirm new migrations preserve existing data and foreign keys.

## Configuration

- Review `.env.example` and app-specific examples.
- Confirm production CORS origins are explicit.
- Confirm no secrets are committed.
- Confirm input limits, rate limits, and concurrency settings are documented.

## Frontend

- Smoke-test `/`, `/analyze`, `/data`, `/models`, `/evaluation`, `/history`, `/monitoring`, `/experiments`, `/review`, `/performance`, and `/about`.
- Smoke-test representative dynamic routes for history detail, evidence workspace, experiment detail, and monitoring detail.
- Check mobile, tablet, and desktop navigation.
- Check keyboard focus visibility.
- Confirm long titles, URLs, model names, and notes wrap safely.

## Backend

- Verify app imports and startup.
- Check `/health`, `/api/v1/health`, `/api/v1/readiness`, and `/api/v1/system/info`.
- Confirm startup/readiness does not load transformer weights.
- Confirm evidence URL handling does not fetch, crawl, resolve, or preview remote resources.
- Confirm logs do not include article bodies, reviewer notes, evidence excerpts, raw rows, query strings, or secrets.

## Docker

- Run `docker compose config`.
- Build backend and frontend images when a Docker daemon is available.
- Verify migration service ordering.
- Verify persistent PostgreSQL and model artifact volumes.

## Documentation

- Review README links and project identity.
- Review demo guide.
- Review architecture, security, deployment, evidence, and portfolio notes.
- Update CHANGELOG for the release.
- Add real screenshots only after capturing them from the running app.

## Final Git Review

- Run `git status`.
- Run `git diff --check`.
- Inspect the final diff for generated artifacts, binaries, local databases, model weights, logs, caches, or secrets.
- Do not commit `.env`, `node_modules`, `.next`, virtual environments, downloaded models, trained artifacts, database dumps, or local logs.
