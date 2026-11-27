#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv run --frozen --group research python -m research_ops.publication.program generate-paper \
  --tex-engine "${TECTONIC:-tectonic}"
