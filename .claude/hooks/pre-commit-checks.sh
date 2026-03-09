#!/bin/bash
# Only run enforcement checks when the Bash command is a git commit
COMMAND=$(jq -r '.tool_input.command // ""')

if ! echo "$COMMAND" | grep -q 'git commit'; then
  exit 0
fi

cd "$(jq -r '.session.cwd // "."')" || exit 1
bash enforcement/run-all.sh && \
  cd packages/api && ruff check . && pytest -x && \
  cd ../../packages/web && npx eslint . && npx vitest run
