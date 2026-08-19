# Glossary

> Terminology used across the CV Matching documentation and code.

## Domain terms

| Term | Definition |
| --- | --- |
| CV / Resume | The candidate's document. Modelled as `ResumeData` |
| JD (Job Description) | Free text describing the role, passed as `jd_text`. The service does not parse it into a structure — each scorer reads it directly |
| Criterion | One of six dimensions a candidate is scored on. The enum value (e.g. `skills`) is the stable key clients send weights under |
| Weight | A criterion's percentage contribution to the total. Defaults sum to 100; overrides are rescaled so they always do |
| `match_score` | Weighted sum of the six criterion scores, 0–100 |
| `weighted_score` | One criterion's contribution: `score * weight / 100` |
| Recommendation | `SHORTLIST` (≥70), `REVIEW_CAREFULLY` (≥40), or `REJECT` |
| On-site conflict | The JD requires a named location, the candidate is elsewhere, and nothing suggests relocation. Downgrades SHORTLIST rather than subtracting points |
| Tags | Location codes (HN, HCM, DN, JP) and university codes (hust, uit, fpt…) inferred from the CV |
| Insights | The narrative half of the report: summary, strengths, gaps, matched keywords |
| Extraction-only mode | A request without `jd_text`: the CV is parsed and returned, no scoring |

## The six criteria

| Key | Display name | Default weight |
| --- | --- | ---: |
| `skills` | Skills | 40% |
| `relevant_project_count` | Relevant Project Count | 25% |
| `years_of_experience` | Years of Experience | 15% |
| `background` | Background (University) | 10% |
| `title_role` | Title/Role | 10% |
| `location` | Location | 0% |

## Technical terms

| Term | Definition |
| --- | --- |
| Port | An abstract interface in the domain layer (`IDocumentParser`, `ILLMService`, `IFileProcessor`) |
| Adapter | An infrastructure implementation of a port (`AzureDocumentParser`, `LiteLLMService`, `FileProcessor`) |
| Use case | Application-layer orchestration of one operation — here, `MatchCvUseCase` |
| DTO | Request/response model at the API boundary, kept separate from domain entities |
| Container | The dependency-injector wiring of adapters to ports (`CvMatchingContainer`) |
| Structured output | Constraining the LLM to return JSON matching a Pydantic schema |
| Azure DI | Azure Document Intelligence, the OCR service (`prebuilt-read` model) |
| LiteLLM | The OpenAI-compatible proxy the service calls for all LLM work |
| `ROOT_PATH` | Prefix the ingress strips before forwarding (`/ai`). The app itself serves `/cv-matching/...` |

## Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
