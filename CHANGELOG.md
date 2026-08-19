# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- CV Matching service extracted from the `ai_erp_backend` monorepo as a standalone application
  - `POST /cv-matching/api/v1/match` — CV extraction, and CV/JD matching on six weighted criteria
  - `GET /cv-matching/ready` — readiness probe, separate from liveness
  - `GET /cv-matching/health`, `GET /cv-matching/metrics`
- Vendored the infrastructure previously shared with `doc_analyzer`: `AzureDocumentParser`,
  `FileProcessor`, `AuthenticationService`, and the `verify_api_key` dependency
- Standalone packaging: `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `docker-bake.hcl`,
  `.env.example`
- Helm chart `deploy/charts/cv-matching`
- CI workflows: `Test` (ruff + pytest), `Build Image`, `Publish Chart`
- Documentation: README, architecture, API specifications, requirements, test plan

### Changed
- `FileProcessor` reduced to the two methods this service uses, dropping `pdf2image`, `pillow`,
  `python-docx`, `pypdf2` and the `poppler-utils` system package — Azure Document Intelligence reads
  PDF, DOCX and images directly
- Ruff rule set pinned explicitly so a ruff upgrade cannot turn a clean tree red

### Fixed
- Helm probes now render. The chart this was derived from passed `livenessProbe` / `readinessProbe`
  without the `enabled` key that `tplchart` requires, so both were silently dropped

### Security
- Runs as non-root (uid 1000); credentials supplied only via environment variables

---

## Notes on the migration

The HTTP contract is unchanged from the monorepo: the OpenAPI operation for `/match` and all 16 of
its schemas are byte-identical, and the environment variable names (`AZURE__*`,
`CV_MATCHING_LITELLM__*`, `AUTH__API_KEY`) are unchanged, so existing secrets carry over as-is.

<!-- Link definitions -->
[Unreleased]: https://github.com/vietld-3584/CV-Matching/commits/main
