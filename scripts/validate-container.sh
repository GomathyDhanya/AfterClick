#!/usr/bin/env bash
set -euo pipefail
cd /workspace
git config --global --add safe.directory /workspace
test -z "$(git status --porcelain)"
mkdir -p artifacts
git rev-parse HEAD > artifacts/validated-revision.txt
npm ci --prefix apps/flowboard-web
npm run build --prefix apps/flowboard-web
python -m ruff check afterclick tests migrations
python -m ruff format --check afterclick tests migrations
python -m pytest -q --junitxml=artifacts/tests.xml
python -m research_ops.publication.program demo --output artifacts/demo
python -m research_ops.publication.program verify-data
test -z "$(git status --porcelain)"
