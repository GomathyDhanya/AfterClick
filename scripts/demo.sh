#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up -d --wait db
uv sync --frozen
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
uv run playwright install chromium
uv run python -m afterclick.replay.demo --output "${1:-artifacts/demo}"
