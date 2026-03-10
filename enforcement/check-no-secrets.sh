#!/usr/bin/env bash
set -euo pipefail

PATTERN='(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY)\s*='

FILES=$(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
    -not -path "./.git/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/__pycache__/*" \
    -not -path "*/.venv/*" \
    -not -path "*/build/*" \
    -not -path "*/.next/*" \
    -not -path "*/tests/*" \
    -not -path "*/__tests__/*" \
    -not -path "*/providers/base.py" 2>/dev/null || true)

VIOLATIONS=0
while IFS= read -r file; do
    [ -z "$file" ] && continue
    matches=$(grep -Pn "$PATTERN" "$file" 2>/dev/null || true)
    if [ -n "$matches" ]; then
        while IFS= read -r match; do
            line_num=$(echo "$match" | cut -d: -f1)
            echo "ERROR: no-secrets-in-code"
            echo "  ${file}:${line_num} matches pattern: $(echo "$match" | cut -d: -f2-)"
            echo "  FIX: Move to environment variable. Use os.environ['KEY'] (Python) or process.env.KEY (TypeScript)."
            echo "  REFERENCE: docs/conventions/naming.md"
            echo ""
        done <<< "$matches"
        VIOLATIONS=1
    fi
done <<< "$FILES"

if [ "$VIOLATIONS" -eq 1 ]; then
    echo "Hardcoded secrets detected. Use environment variables instead."
    exit 1
fi

echo "No hardcoded secrets found."
exit 0
