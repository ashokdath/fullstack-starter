#!/usr/bin/env bash

set -e
set -x

ENVIRONMENT=development coverage run -m pytest tests/
coverage report
coverage html --title "${@-coverage}"
