# Test Case List

> Automated cases in `tests/test_match_cv.py`. Strategy:
> [`../test-plan.md`](../test-plan.md). Run with `pytest -q`.

## 1. Weighting (F-005)

| ID | Case | Expected |
| --- | --- | --- |
| TC-001 | Default weighting | Matches `DEFAULT_WEIGHTS`, sums to 100 |
| TC-002 | Partial override rescaled | Untouched criteria keep relative weighting; total stays 100 |
| TC-003 | Location defaults to zero | `location` weight is 0 |
| TC-004 | Location can be weighted back up | Cross-region hiring override works; total stays 100 |
| TC-005 | A criterion can be switched off | Setting a weight to 0 is accepted; total stays 100 |
| TC-006 | Misspelled criterion rejected | `InvalidWeightsError`, not silently ignored |
| TC-007 | Negative weight / all-zero set rejected | `InvalidWeightsError` (parametrised, 2 cases) |

## 2. Experience arithmetic (F-002)

| ID | Case | Expected |
| --- | --- | --- |
| TC-010 | End month counts as worked | 2024-01 → 2024-12 is 1.0 year |
| TC-011 | Overlapping roles counted once | A day job plus a concurrent contract is 1.0 year, not 2.0 |
| TC-012 | Separate periods summed | Two distinct years total 2.0 |
| TC-013 | "Present" read as today | Ongoing role measured to the current month |
| TC-014 | Undatable entries skipped | Unparseable dates contribute 0.0, never a guess (parametrised, 2 cases) |
| TC-015 | Latest title by date, not list order | Returns the most recent role even when the CV is out of order |

## 3. Skills and prompt rendering (F-002, F-003)

| ID | Case | Expected |
| --- | --- | --- |
| TC-020 | Listed and mentioned skills merged | Skills named only inside an achievement are collected; no duplicates |
| TC-021 | Projects section read for skills | Tech stack from a dedicated projects section reaches the scorer |
| TC-022 | Projects prompt covers both sources | Job history and projects section both rendered |
| TC-023 | Projects reported without job history | A fresher's projects still appear |
| TC-024 | Neither present | Explicit "no work experience or projects" message |
| TC-025 | Every achievement kept | No cap — capping hid technologies from the skills scorer |

## 4. Use case orchestration (F-003, F-004, F-006, F-008)

| ID | Case | Expected |
| --- | --- | --- |
| TC-030 | Full match | All six criteria scored, total and recommendation produced |
| TC-031 | Custom weights applied | `match_score` reflects the overridden weighting |
| TC-032 | Bad weights rejected before any LLM call | Raises without spending a call |
| TC-033 | No JD → extraction only | `cv_data` returned, `matching` is `None` |
| TC-034 | Blank JD read as no JD | Whitespace-only `jd_text` behaves as absent |
| TC-035 | Bad weights rejected even without a JD | A typo is reported, not silently accepted |
| TC-036 | Extraction-only still reports gaps | Missing-work-history warning survives |
| TC-037 | Empty CV rejected | `MatchCvError` when OCR yields nothing |
| TC-038 | Warning when no work experience | Warning added to the result |

## 5. Failure handling (NFR-014)

| ID | Case | Expected |
| --- | --- | --- |
| TC-040 | Criterion scorer fails | Fails loudly — never scored as 0, which would read as a genuine rejection |
| TC-041 | Insights call fails | Scores preserved, downgraded to a warning |

## 6. On-site conflict (F-007)

| ID | Case | Expected |
| --- | --- | --- |
| TC-050 | Conflict blocks automatic shortlist | SHORTLIST downgraded to REVIEW_CAREFULLY with a warning |
| TC-051 | Matching location leaves shortlist alone | No downgrade when locations agree |
| TC-052 | Conflict does not promote a weak candidate | A REJECT is not lifted to REVIEW_CAREFULLY |
| TC-053 | Reason ignores zero-weight criteria | Only criteria that affect the score are cited |

## 7. API contract (F-001, F-004)

| ID | Case | Expected |
| --- | --- | --- |
| TC-060 | Result serialises to the response DTO | `MatchingResultDTO` validates from the domain result |
| TC-061 | Extracted CV serialises with every section | All sections survive the DTO boundary |

## 8. Manual verification

| ID | Case | Expected |
| --- | --- | --- |
| TC-070 | Missing API key | `401` |
| TC-071 | Invalid API key | `401` |
| TC-072 | Unsupported file type | `400` listing allowed types |
| TC-073 | Empty file upload | `400` |
| TC-074 | Malformed `weights` JSON | `400` with an example |
| TC-075 | Real CV + JD against live services | `200` with a plausible, explained score |
| TC-076 | Health / readiness / metrics | `200` on all three |

## 9. Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version, extracted from the `ai_erp_backend` monorepo |
