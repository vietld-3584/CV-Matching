# Database Design

## Not applicable

The CV Matching service holds **no database**. It is stateless by design: every request carries
everything it needs, and nothing is persisted between requests.

| Data | Handling |
| --- | --- |
| Uploaded CV file | Written to a temporary file, read once by the parser, deleted in a background task after the response is sent |
| Extracted CV data | Returned in the response; never stored |
| Matching results | Returned in the response; never stored |
| Credentials | Environment variables from a Kubernetes secret; never written to disk by the service |

Persisting candidates, results or audit history is the responsibility of the calling hiring system.

This is what lets the service scale horizontally without coordination — any replica can serve any
request — and it keeps candidate data out of a store that would otherwise need a retention policy.

See [`architecture.md`](./architecture.md) for the full picture.

## Revision history

| Date | Author | Change |
| --- | --- | --- |
| 2026-08-19 | Le Duc Viet | Initial version — recorded that the service is intentionally stateless |
