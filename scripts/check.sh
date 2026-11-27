#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync --frozen --group research
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
bash scripts/test.sh
