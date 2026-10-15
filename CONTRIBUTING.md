# Contributing

This repository is the standard template for new projects. Changes here flow into every project created from it afterwards, so keep it minimal and general.

## Guidelines

- **Project-specific features stay in projects.** SSO, Celery, S3 storage, history tracking and similar belong in the projects that need them, not in the template.
- **Keep the API contract.** Follow the API Contract Rules in the [README](./README.md) and regenerate the frontend client after API changes (`bash scripts/generate-client.sh`).
- **Tests and coverage.** Backend changes need tests; CI requires 90% coverage. UI changes need Playwright coverage in `frontend/tests`.
- **Dependencies.** Prefer the standard library, Django and the existing dependencies. Explain any new dependency in the pull request.

## Development Setup

See [development.md](./development.md). Install the Git hooks once:

```bash
uv run prek install -f
```

## Pull Requests

- Keep each pull request focused on one change.
- Make sure all GitHub Actions checks pass: backend tests, Playwright, Docker Compose, pre-commit, client check and zizmor.
