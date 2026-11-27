#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --frozen --group research python -m research_ops.publication.program verify-data
uv run --frozen --group research ruff check afterclick tests migrations research_ops archive paper/*.py
uv run --frozen --group research ruff format --check afterclick tests migrations research_ops archive paper/*.py
uv run --frozen --group research pytest -q --junitxml="${AFTERCLICK_TEST_REPORT:-artifacts/tests.xml}"
