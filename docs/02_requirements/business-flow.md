# Business Flow

> How the CV Matching service fits into the screening process. Background:
> [`project-overview.md`](./project-overview.md).

## 1. Screening flow

```mermaid
flowchart TD
    A[Job posting opens] --> B[Candidates apply<br/>CVs arrive]
    B --> C[Recruiter uploads CV + JD<br/>via the hiring frontend]
    C --> D[CV Matching API]
    D --> E[Structured CV + score<br/>+ per-criterion reasoning]
    E --> F{Recommendation}
    F -->|SHORTLIST ≥70| G[Move to interview]
    F -->|REVIEW_CAREFULLY ≥40| H[Recruiter reads<br/>the reasoning and decides]
    F -->|REJECT <40| H
    G --> I[Interview process]
    H --> I
    H --> J[Pass, with a recorded reason]
```

The recommendation is an input to a human decision, never a gate. Even a `REJECT` reaches a recruiter
with its per-criterion explanations attached — the point is to order and justify the queue, not to
close it.

## 2. Where the value lands

| Step | Before | With the service |
| --- | --- | --- |
| Reading a CV | Manual, minutes per candidate, formats vary | Seconds, normalised into one structure |
| Ranking | Recruiter judgement, varies by reader and by fatigue | Consistent weighted score, reproducible on re-run |
| Justification | Held in the recruiter's head | Per-criterion score, weight and written reason |
| Adjusting priorities | Re-read everything with new emphasis | Re-weight criteria per request |

## 3. Extraction-only flow

Uploading a CV without a job description returns just the structured data — used to populate a
candidate record when there is no specific posting to match against yet.

```mermaid
flowchart LR
    A[CV file] --> B[CV Matching API<br/>no jd_text]
    B --> C[Structured CV data]
    C --> D[Talent pool record]
```

## 4. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
