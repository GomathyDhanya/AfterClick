#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "$(git status --porcelain)" ]; then
  echo 'Commit the source before clean-clone validation.' >&2
  exit 1
fi
validation_repo="$PWD"
validation_root=$(mktemp -d "${TMPDIR:-/tmp}/afterclick-validation.XXXXXX")
validation_project="ac-validation-$(date +%s)-$$"
validation_revision=$(git rev-parse --short HEAD)
validation_output="$validation_repo/artifacts/isolated-$validation_project"
mkdir -p "$validation_output"
git clone --quiet --no-hardlinks "$validation_repo" "$validation_root/source"
export VALIDATION_SOURCE="$validation_root/source"
validation_compose="$VALIDATION_SOURCE/compose.validation.yaml"
cleanup() {
  result=$?
  trap - EXIT
  docker compose -p "$validation_project" -f "$validation_compose" ps -a --format json \
    > "$validation_output/containers.json" || true
  if [ -d "$VALIDATION_SOURCE/artifacts" ]; then
    cp -R "$VALIDATION_SOURCE/artifacts/." "$validation_output/"
  fi
  docker compose -p "$validation_project" -f "$validation_compose" down --volumes || true
  echo "Validation revision $validation_revision; exit $result; evidence: $validation_output"
  # Retain the temporary clone on failure for diagnosis; successful clones can be removed later.
  echo "Isolated source clone: $VALIDATION_SOURCE"
  exit "$result"
}
trap cleanup EXIT
docker compose -p "$validation_project" -f "$validation_compose" up \
  --build --abort-on-container-exit --exit-code-from validation 2>&1 | tee "$validation_output/run.log"
