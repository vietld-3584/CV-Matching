# API List

> Endpoint inventory for the CV Matching service. Detailed specifications live in the per-API files
> linked below. Architecture context: [`../architecture.md`](../architecture.md).

## 1. Common

- **Base URL (deployed):** `https://<host>/ai/cv-matching`
- **Base URL (local):** `http://localhost:8000/cv-matching`

The `/ai` segment is added by the ingress (`ROOT_PATH`); the application itself serves
`/cv-matching/...`. Both prefixes are configurable by environment variable.

- **Authentication:** `X-API-Key: <key>` header on business endpoints. Compared in constant time
  against `AUTH__API_KEY`. Health, readiness and metrics are unauthenticated.
- **Content type:** requests are `multipart/form-data`; responses are `application/json`.
- **Interactive docs:** `/docs` (Swagger UI), `/redoc`, raw schema at `/openapi.json`.

## 2. Endpoints

| ID | Method | Path | Name | Auth | Detail |
| --- | --- | --- | --- | :---: | --- |
| API-001 | `POST` | `/api/v1/match` | Extract and match a CV | ✅ | [api-1-match-cv.md](./api-1-match-cv.md) |
| API-002 | `GET` | `/health` | Liveness check | | — |
| API-003 | `GET` | `/ready` | Readiness check | | — |
| API-004 | `GET` | `/metrics` | Prometheus metrics | | — |

### API-002 / API-003 — health and readiness

Both return `200` with `{"status": "healthy"|"ready", "service": "cv-matching"}`.

They are separate so a liveness failure (restart the pod) is never triggered by something that only
means "not ready yet". Neither probes Azure or LiteLLM: those are per-request external calls, and
checking them here would pull the pod out of rotation during someone else's outage.

### API-004 — metrics

Prometheus text exposition format. Excluded from the OpenAPI schema.

## 3. Common error format

All errors return a JSON body with a `detail` string:

```json
{ "detail": "Missing API Key. Provide X-API-Key header." }
```

Unhandled exceptions return `500` with a generic message, plus the `request_id` echoed back when the
caller supplied an `X-Request-ID` header. Internal detail is never leaked to the client; the full
traceback goes to the service log.

## 4. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
