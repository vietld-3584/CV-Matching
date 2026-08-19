# Role List

> Consumers of the CV Matching service and what they are permitted to do.
> Functions: [`function-list.md`](./function-list.md).

## 1. Roles

This is a machine-to-machine API. It has **no per-user identity model**: authentication is a single
shared API key, so the service authenticates the *calling system*, not the person behind the request.
The roles below describe who is served through those systems.

| ID | Role | Description | Access |
| --- | --- | --- | --- |
| ROLE-001 | Hiring system / frontend | The application that uploads CVs and displays results. Holds the API key | Full API access via `X-API-Key` |
| ROLE-002 | Recruiter (indirect) | Screens candidates through the hiring frontend. Never calls this API directly | Whatever the frontend exposes |
| ROLE-003 | Platform operator | Deploys and operates the service | Health, readiness, metrics; secrets via Kubernetes |
| ROLE-004 | Monitoring system | Scrapes metrics and probes | `/health`, `/ready`, `/metrics` — unauthenticated |

## 2. Permission matrix

| Function ID | Function | ROLE-001 | ROLE-003 | ROLE-004 |
| --- | --- | --- | --- | --- |
| F-001–F-008 | CV extraction and matching | ✅ | — | — |
| F-009 | API key authentication | Holds the key | Rotates the key | — |
| F-010 | Health / readiness / metrics | ✅ | ✅ | ✅ |

## 3. Notes on authorisation

- The API key is compared in constant time and grants all-or-nothing access; there is no scoping or
  rate limiting inside the service.
- Because the service authenticates a system rather than a person, any per-recruiter audit trail must
  be kept by the caller. This service stores nothing.

## 4. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
