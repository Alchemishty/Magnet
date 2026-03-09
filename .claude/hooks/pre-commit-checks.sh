#!/bin/bash
# Only run enforcement checks when the Bash command is a git commit
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

if ! echo "$COMMAND" | grep -q 'git commit'; then
  exit 0
fi

CWD=$(echo "$INPUT" | jq -r '.session.cwd // "."')
cd "$CWD" || exit 2

if ! (bash enforcement/run-all.sh && \
  cd packages/api && ruff check . && pytest -x && \
  cd ../../packages/web && npx eslint . && npx vitest run); then
  echo "Pre-commit checks failed" >&2
  exit 2
fi
