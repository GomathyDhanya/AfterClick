#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --frozen
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run ruff check afterclick tests migrations
uv run ruff format --check afterclick tests migrations
uv run pytest -q --junitxml=artifacts/tests.xml
