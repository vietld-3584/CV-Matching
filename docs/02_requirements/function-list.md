# Function List

> Functional scope of the CV Matching service. This list defines what the service covers.
> API specifications: [`../03_system-design/api-design/api-list.md`](../03_system-design/api-design/api-list.md).

## 1. Functions

| ID | Function | Description | Priority | Status | Detail |
| --- | --- | --- | --- | --- | --- |
| F-001 | CV text extraction | OCR a PDF / DOCX / image CV into plain text via Azure Document Intelligence | Must | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-002 | Structured CV parsing | Parse the text into structured resume data: contact details, skills, education, work history, projects, tags | Must | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-003 | Criterion scoring | Score the candidate on six criteria against a JD, concurrently, each with its own explanation | Must | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-004 | Weighted total and recommendation | Combine criterion scores into a 0–100 total and a SHORTLIST / REVIEW_CAREFULLY / REJECT recommendation | Must | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-005 | Custom weighting | Accept per-request weight overrides, rescaled to 100%, with unknown keys rejected | Must | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-006 | Insight generation | Produce a summary, strengths, gaps and matched keywords from the CV, JD and scores | Should | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-007 | On-site conflict detection | Flag a genuine location conflict and downgrade an automatic SHORTLIST | Should | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-008 | Extraction-only mode | Return the parsed CV without scoring when no JD is supplied | Must | Done | [API-001](../03_system-design/api-design/api-1-match-cv.md) |
| F-009 | API key authentication | Validate `X-API-Key` in constant time | Must | Done | [api-list.md](../03_system-design/api-design/api-list.md) |
| F-010 | Health, readiness, metrics | Probe endpoints and Prometheus metrics | Must | Done | [api-list.md](../03_system-design/api-design/api-list.md) |

## 2. Out of scope

| Item | Note |
| --- | --- |
| Candidate data storage | The service is stateless; uploaded files are deleted after the response. Persistence is the caller's responsibility |
| Ranking across candidates | One CV per request. Comparing candidates is done by the caller |
| Automatic rejection | `REJECT` is a recommendation for a human, never an automated decision |
| Interview scheduling / ATS integration | Handled by the hiring system |

## 3. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
