#!/usr/bin/env bash

# Run the test suite with coverage. Extra arguments are passed to pytest,
# e.g. `bash scripts/test.sh -x -k login`.
# Set COVERAGE_TITLE to change the title of the HTML coverage report.

set -e
set -x

ENVIRONMENT=development coverage run -m pytest tests/ "$@"
coverage report
coverage html --title "${COVERAGE_TITLE:-coverage}"
