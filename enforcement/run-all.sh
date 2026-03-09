#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED=0

# Run all check-*.sh scripts in this directory
for script in "$SCRIPT_DIR"/check-*.sh; do
  [ -f "$script" ] || continue
  echo "Running: $(basename "$script")"
  if ! bash "$script"; then
    FAILED=1
  fi
  echo ""
done

if [ "$FAILED" -ne 0 ]; then
  echo "ENFORCEMENT FAILED: one or more rules violated."
  echo "Fix the issues above and retry."
  exit 1
fi

echo "All enforcement rules passed."
exit 0
