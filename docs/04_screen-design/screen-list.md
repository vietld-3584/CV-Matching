# Screen List

## Not applicable

The CV Matching service is a headless REST API with no user interface. It is consumed by the hiring
frontend, which owns all screen design.

The only browser-facing pages the service exposes are the auto-generated API docs, which are
developer tooling rather than product screens:

| Path | Purpose |
| --- | --- |
| `/docs` | Swagger UI — interactive API explorer |
| `/redoc` | ReDoc — reference rendering of the same schema |
| `/openapi.json` | Raw OpenAPI schema |

For the API itself see
[`../03_system-design/api-design/api-list.md`](../03_system-design/api-design/api-list.md).

## Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Recorded that the service has no UI |
