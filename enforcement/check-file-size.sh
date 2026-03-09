#!/usr/bin/env bash
set -euo pipefail

MAX_LINES=300  # From harness.yaml enforcement.file_size_limit

VIOLATIONS=0
while IFS= read -r file; do
    [ -z "$file" ] && continue
    LINES=$(wc -l < "$file")
    if [ "$LINES" -gt "$MAX_LINES" ]; then
        echo "ERROR: file-size-limit"
        echo "  ${file} has ${LINES} lines (max ${MAX_LINES})"
        echo "  FIX: Split into smaller, focused modules. One file = one concept."
        echo "  REFERENCE: docs/conventions.md#code-smells"
        echo ""
        VIOLATIONS=1
    fi
done < <(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) \
    -not -path "./.git/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/.venv/*" \
    -not -path "*/build/*" \
    -not -path "*/.next/*" \
    -not -path "*/.dart_tool/*" \
    -not -path "*/alembic/*" 2>/dev/null)

if [ "$VIOLATIONS" -eq 1 ]; then
    echo "Files exceeding ${MAX_LINES} lines detected. Consider splitting."
    exit 1
fi

echo "All files within size limit."
exit 0
