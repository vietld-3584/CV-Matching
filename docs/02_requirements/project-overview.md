# Project Overview

> Business and product overview of the CV Matching service. Roles: [`role-list.md`](./role-list.md).
> Terminology: [`glossary.md`](./glossary.md). Scope: [`function-list.md`](./function-list.md).

## 1. Service summary

| Item | Detail |
| --- | --- |
| Service name | CV Matching API |
| Platform | Internal backend service (REST API), consumed by the hiring frontend |
| Summary | Extracts structured data from candidate CVs and scores them against a job description on six weighted, individually explained criteria |

## 2. Background and problem

- **As-Is:** Recruiters read every incoming CV by hand to decide who moves to interview. For a single
  posting that can mean dozens of CVs in inconsistent formats — PDF, DOCX, scanned images — in
  Vietnamese and English, with the strongest evidence often buried in a projects section rather than
  the job history.
- **Problem:** Screening is slow and inconsistent. Two recruiters shortlist differently from the same
  CV, and there is no record of *why* a candidate was passed over.
- **Cost of inaction:** Screening stays the bottleneck in the hiring funnel, strong candidates are
  missed through fatigue or formatting, and shortlisting decisions cannot be audited or improved.

## 3. Purpose and value

- **Purpose:** Give recruiters a consistent, defensible first-pass ranking of candidates against a
  job description, with the reasoning attached.
- **Value:**
  - **Speed.** Six criteria are scored concurrently, so a full match returns in seconds rather than
    the minutes a careful manual read takes.
  - **Consistency.** The same CV and JD produce the same score on re-run — the model was chosen
    specifically for that property.
  - **Explainability.** Every criterion carries its own score, weight and written justification. The
    service is a screening aid that shows its work, not an automatic reject switch.
  - **Adjustability.** Teams can re-weight criteria per role without a code change or redeploy.
- **Deliberate limits.** The service ranks and explains; a human decides. `REJECT` is a
  recommendation, never an automated rejection.

## 4. Related documents

| Document | Content |
| --- | --- |
| [`function-list.md`](./function-list.md) | Functional scope |
| [`non-function-list.md`](./non-function-list.md) | Non-functional requirements |
| [`glossary.md`](./glossary.md) | Terminology |
| [`../03_system-design/architecture.md`](../03_system-design/architecture.md) | System architecture |
| [`../03_system-design/api-design/api-list.md`](../03_system-design/api-design/api-list.md) | API inventory |

## 5. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
