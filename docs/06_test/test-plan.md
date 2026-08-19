# Test Plan

> Test strategy for the CV Matching service. Cases:
> [`testcase/testcase-list.md`](./testcase/testcase-list.md).

## 1. Scope

| In scope | Out of scope |
| --- | --- |
| Weight resolution and rescaling | Azure Document Intelligence OCR accuracy (third-party) |
| Experience arithmetic and profile helpers | LLM output quality (evaluated separately by benchmark, not unit tests) |
| Prompt rendering — what the scorers actually see | Frontend integration |
| Use-case orchestration and failure handling | Load and stress testing |
| DTO serialisation and the API contract | |
| Auth, file validation, error mapping | |

## 2. Test levels

| Level | Coverage | Tooling | Where |
| --- | --- | --- | --- |
| Unit | Domain logic: weighting, date arithmetic, prompt formatting | pytest | `tests/test_match_cv.py` |
| Integration (in-process) | Use case wired to fake LLM and parser doubles | pytest | `tests/test_match_cv.py` |
| Contract | OpenAPI schema for `/match` | FastAPI `app.openapi()` | Manual / CI |
| Manual E2E | Real CV + JD against live Azure and LiteLLM | curl / Swagger UI | Pre-release |

**Deliberately no live-LLM tests in CI.** The suite runs with fakes, so it needs no credentials, no
network, and finishes in under a second. LLM behaviour is non-deterministic and belongs in a
benchmark, not in a gate that must be green to merge.

## 3. Environment

| Item | Value |
| --- | --- |
| Python | 3.10+ (3.13 in CI and the container) |
| Command | `pytest -q` |
| Credentials | Not required |
| Network | Not required |
| Runtime | < 1 second |

## 4. Entry and exit criteria

- **Entry:** code compiles, dependencies install, `ruff check` clean.
- **Exit:** all 38 tests pass, `ruff check .` and `ruff format --check .` clean, container builds and
  answers both probes, Helm chart lints and renders.

## 5. CI

The `Test` workflow runs on every push to `main` and every pull request: install → `ruff check` →
`ruff format --check` → `pytest -q`. `OSV-Scanner` and `Scorecard` cover dependency and supply-chain
posture.

## 6. Regression baseline for the monorepo split

This service was extracted from `ai_erp_backend`. The migration was verified by:

1. Running the test suite **unmodified** — the file is byte-identical to the monorepo's, so a pass
   proves the logic did not change in transit.
2. Diffing `app.openapi()` between the two services: the `/match` operation and all 16 of its schemas
   are byte-identical.
3. Confirming the moved source files are byte-identical apart from the six deliberately edited ones.

## 7. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
