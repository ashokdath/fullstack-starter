#! /usr/bin/env bash

set -e
set -x

cd backend
ENVIRONMENT=development uv run python manage.py export_openapi_schema --api app.api.api --output ../frontend/openapi.json
cd ..
bun run --filter frontend generate-client
bun run lint
