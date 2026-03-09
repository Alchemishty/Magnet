#!/usr/bin/env bash
set -euo pipefail

# Import direction enforcement for Magnet monorepo
# API (Python): models → schemas → repositories → services → agents → routes
# Web (TypeScript): models → lib → components → app

VIOLATIONS=0

# --- Python (packages/api/) ---

# Layer order (index = rank, lower = deeper)
declare -A PY_LAYER_RANK
PY_LAYER_RANK[models]=0
PY_LAYER_RANK[schemas]=1
PY_LAYER_RANK[repositories]=2
PY_LAYER_RANK[services]=3
PY_LAYER_RANK[agents]=4
PY_LAYER_RANK[routes]=5

get_py_layer() {
  local file="$1"
  for layer in models schemas repositories services agents routes; do
    if echo "$file" | grep -q "app/${layer}/"; then
      echo "$layer"
      return
    fi
  done
  echo ""
}

get_imported_py_layer() {
  local import_line="$1"
  for layer in models schemas repositories services agents routes; do
    if echo "$import_line" | grep -q "app\.${layer}"; then
      echo "$layer"
      return
    fi
  done
  echo ""
}

# Scan Python files
while IFS= read -r file; do
  [ -z "$file" ] && continue
  src_layer=$(get_py_layer "$file")
  [ -z "$src_layer" ] && continue
  src_rank=${PY_LAYER_RANK[$src_layer]}

  while IFS= read -r line; do
    imported_layer=$(get_imported_py_layer "$line")
    [ -z "$imported_layer" ] && continue
    imported_rank=${PY_LAYER_RANK[$imported_layer]}

    if [ "$imported_rank" -gt "$src_rank" ]; then
      line_num=$(grep -n "$line" "$file" | head -1 | cut -d: -f1)
      echo "ERROR: import-direction"
      echo "  ${file}:${line_num} — ${src_layer} imports from ${imported_layer}"
      echo "  FIX: ${src_layer} (rank ${src_rank}) must not import from ${imported_layer} (rank ${imported_rank}). Import from a lower layer instead."
      echo "  REFERENCE: docs/architecture.md#dependency-rules-summary"
      echo ""
      VIOLATIONS=1
    fi
  done < <(grep -E "^(from|import) app\." "$file" 2>/dev/null || true)
done < <(find packages/api -name "*.py" -not -path "*/__pycache__/*" -not -path "*/tests/*" -not -path "*/alembic/*" 2>/dev/null)

# --- TypeScript (packages/web/) ---

declare -A TS_LAYER_RANK
TS_LAYER_RANK[models]=0
TS_LAYER_RANK[lib]=1
TS_LAYER_RANK[components]=2
TS_LAYER_RANK[app]=3

get_ts_layer() {
  local file="$1"
  for layer in models lib components app; do
    if echo "$file" | grep -q "/${layer}/"; then
      echo "$layer"
      return
    fi
  done
  echo ""
}

get_imported_ts_layer() {
  local import_line="$1"
  for layer in models lib components app; do
    if echo "$import_line" | grep -qE "from ['\"]@/${layer}/"; then
      echo "$layer"
      return
    fi
  done
  echo ""
}

# Scan TypeScript files
while IFS= read -r file; do
  [ -z "$file" ] && continue
  src_layer=$(get_ts_layer "$file")
  [ -z "$src_layer" ] && continue
  src_rank=${TS_LAYER_RANK[$src_layer]}

  while IFS= read -r line; do
    imported_layer=$(get_imported_ts_layer "$line")
    [ -z "$imported_layer" ] && continue
    imported_rank=${TS_LAYER_RANK[$imported_layer]}

    if [ "$imported_rank" -gt "$src_rank" ]; then
      line_num=$(grep -n "$line" "$file" | head -1 | cut -d: -f1)
      echo "ERROR: import-direction"
      echo "  ${file}:${line_num} — ${src_layer} imports from ${imported_layer}"
      echo "  FIX: ${src_layer} (rank ${src_rank}) must not import from ${imported_layer} (rank ${imported_rank}). Import from a lower layer instead."
      echo "  REFERENCE: docs/architecture.md#dependency-rules-summary"
      echo ""
      VIOLATIONS=1
    fi
  done < <(grep -E "^import .* from '@/" "$file" 2>/dev/null || true)
done < <(find packages/web -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v __tests__ 2>/dev/null)

if [ "$VIOLATIONS" -eq 1 ]; then
  echo "Import direction violations detected."
  exit 1
fi

echo "Import direction: all clear."
exit 0
