#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run --group research ruff check afterclick tests migrations
uv run --group research ruff format --check afterclick tests migrations
uv run --group research pytest -q --junitxml="${AFTERCLICK_TEST_REPORT:-artifacts/tests.xml}"
