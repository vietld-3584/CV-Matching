# Non-Functional Requirements

> Non-functional requirements for the CV Matching service. Architecture:
> [`../03_system-design/architecture.md`](../03_system-design/architecture.md).

## 1. Performance

| ID | Requirement | Target | Notes |
| --- | --- | --- | --- |
| NFR-001 | Full match latency | ~5–15s typical | 8 LLM calls; the six scorers run concurrently, so they cost roughly one round trip, not six |
| NFR-002 | Extraction-only latency | ~3–5s typical | 1 OCR call + 1 LLM call |
| NFR-003 | LLM call timeout | 90s | Deliberately under the proxy's 120s Cloudflare read cut-off so a slow call fails as our timeout, which retries can act on |
| NFR-004 | LLM retries | 2 per call | Configurable 0–5 |
| NFR-005 | Event loop | Never blocked | The Azure SDK is synchronous, so OCR runs on a worker thread |

## 2. Availability and scalability

| ID | Requirement | Detail |
| --- | --- | --- |
| NFR-010 | Stateless | No database, no session state; any replica serves any request |
| NFR-011 | Horizontal scaling | Scale by replica count; anti-affinity is set to `soft` |
| NFR-012 | Liveness | `/cv-matching/health`, 30s interval |
| NFR-013 | Readiness | `/cv-matching/ready`, 10s interval. Deliberately does not probe Azure or LiteLLM — that would remove the pod from rotation during a third-party outage |
| NFR-014 | Graceful degradation | A failed insights call becomes a warning; the scores are still returned. A failed criterion scorer does not — Skills alone is 40%, so a silent 0 would read as a genuine rejection |

## 3. Security

| ID | Requirement | Detail |
| --- | --- | --- |
| NFR-020 | Authentication | `X-API-Key` header, compared with `hmac.compare_digest` in constant time |
| NFR-021 | Secret management | All credentials via environment variables from a Kubernetes secret; none baked into the image; `.env` is git-ignored |
| NFR-022 | Container hardening | Runs as non-root uid 1000, `runAsNonRoot: true` |
| NFR-023 | Error disclosure | Internal errors return a generic message; tracebacks go to logs only |
| NFR-024 | Data retention | Uploaded CVs are written to a temp file, read once, and deleted in a background task. Nothing is persisted |
| NFR-025 | Dependency scanning | OSV-Scanner and OpenSSF Scorecard run in CI; Dependabot tracks updates |

## 4. Maintainability

| ID | Requirement | Detail |
| --- | --- | --- |
| NFR-030 | Architecture | Clean architecture; the domain layer imports no framework, no SDK and does no I/O |
| NFR-031 | Testability | External systems sit behind ports; the suite runs with fakes, needing no credentials and no network |
| NFR-032 | Test coverage | 38 tests over weighting, experience arithmetic, prompt rendering and failure handling |
| NFR-033 | Lint | `ruff check` and `ruff format --check` clean; rule set pinned so a ruff upgrade cannot turn the tree red |
| NFR-034 | API contract | Published as OpenAPI at `/openapi.json`, generated from the same Pydantic models used for validation, so docs cannot drift from behaviour |

## 5. Observability

| ID | Requirement | Detail |
| --- | --- | --- |
| NFR-040 | Metrics | Prometheus endpoint at `/cv-matching/metrics` |
| NFR-041 | Logging | Structured stdout logging; each match logs elapsed time, candidate, score and recommendation |
| NFR-042 | Request tracing | An `X-Request-ID` header is echoed back in error responses |

## 6. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
