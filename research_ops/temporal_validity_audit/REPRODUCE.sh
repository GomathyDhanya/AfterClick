#!/usr/bin/env bash
# No model endpoints, cloud jobs, GPUs, or paid tools are invoked.
set -euo pipefail
AUDIT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$AUDIT_DIR/../.." && pwd)"
AUDIT_PYTHON="${AUDIT_PYTHON:-$REPO_DIR/.venv/bin/python}"
cd "$REPO_DIR"
mode="${1:---full}"
if [[ "$mode" == "--plots-only" ]]; then
  "$AUDIT_PYTHON" "$AUDIT_DIR/plot.py"
  exit 0
fi
if [[ "$mode" != "--full" && "$mode" != "--saved-only" ]]; then
  echo 'Usage: REPRODUCE.sh [--full|--saved-only|--plots-only]' >&2
  exit 2
fi
mkdir -p "$AUDIT_DIR/provenance"
if [[ ! -f "$AUDIT_DIR/provenance/historical/README.md" ]]; then
  python3 archive/restore.py --output "$AUDIT_DIR/provenance/historical" \
    > "$AUDIT_DIR/provenance/source_only_restoration.log" 2>&1
fi
if [[ "$mode" == "--full" || ! -f "$AUDIT_DIR/integrity_report.json" ]]; then
  "$AUDIT_PYTHON" "$AUDIT_DIR/integrity.py"
fi
"$AUDIT_PYTHON" "$AUDIT_DIR/analyze.py"
"$AUDIT_PYTHON" "$AUDIT_DIR/analyze.py" --all-policies --output "$AUDIT_DIR/all_valid_internal"
if [[ "$mode" == "--full" ]]; then
  "$AUDIT_PYTHON" "$AUDIT_DIR/positive_controls.py"
  "$AUDIT_PYTHON" "$AUDIT_DIR/positive_controls.py" --ticket-window
fi
"$AUDIT_PYTHON" "$AUDIT_DIR/enrich.py"
"$AUDIT_PYTHON" "$AUDIT_DIR/supplementary.py"
"$AUDIT_PYTHON" "$AUDIT_DIR/audit_invalid.py"
"$AUDIT_PYTHON" "$AUDIT_DIR/write_reports.py"
"$AUDIT_PYTHON" "$AUDIT_DIR/plot.py"
"$AUDIT_PYTHON" -m pytest -q "$AUDIT_DIR/tests" \
  --junitxml="$AUDIT_DIR/provenance/audit_tests.xml"
"$AUDIT_PYTHON" -m pytest -q tests \
  --junitxml="$AUDIT_DIR/provenance/active_tests.xml"
(
  cd "$AUDIT_DIR/provenance/historical"
  "$AUDIT_PYTHON" -m pytest -q \
    tests/completion_v12/benchmark/test_native_conversation.py \
    tests/completion_v12/benchmark/test_program_safety.py \
    tests/completion_v12/benchmark/test_oracle_alternatives.py \
    tests/completion_v12/benchmark/test_scientific_estimators.py \
    --junitxml="$AUDIT_DIR/provenance/historical_relevant_tests.xml"
)
"$AUDIT_PYTHON" -m ruff check "$AUDIT_DIR"
"$AUDIT_PYTHON" -m ruff format --check "$AUDIT_DIR"
"$AUDIT_PYTHON" "$AUDIT_DIR/verify.py"
