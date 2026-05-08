#!/usr/bin/env bash
# check-syntax.sh <skill_root>
# Roda syntax check em python/node/bash.
set -euo pipefail

ROOT="${1:-.}"
FAIL=0

cd "$ROOT"

# Python
PY_FILES=$(find . -name "*.py" -not -path "./.git/*" -not -path "./.skill-ci/*" -not -path "*/__pycache__/*" -not -path "*/.venv/*" 2>/dev/null || true)
if [[ -n "$PY_FILES" ]]; then
  while IFS= read -r f; do
    if ! python3 -m py_compile "$f" 2>&1; then
      echo "::error file=$f::Python syntax error"
      FAIL=1
    fi
  done <<< "$PY_FILES"
  echo "Python: $(echo "$PY_FILES" | wc -l) arquivo(s) checados"
fi

# Node (.js, .mjs, .cjs)
JS_FILES=$(find . \( -name "*.js" -o -name "*.mjs" -o -name "*.cjs" \) -not -path "./.git/*" -not -path "./.skill-ci/*" -not -path "*/node_modules/*" 2>/dev/null || true)
if [[ -n "$JS_FILES" ]]; then
  while IFS= read -r f; do
    if ! node --check "$f" 2>&1; then
      echo "::error file=$f::JS syntax error"
      FAIL=1
    fi
  done <<< "$JS_FILES"
  echo "Node: $(echo "$JS_FILES" | wc -l) arquivo(s) checados"
fi

# Bash
SH_FILES=$(find . -name "*.sh" -not -path "./.git/*" -not -path "./.skill-ci/*" 2>/dev/null || true)
if [[ -n "$SH_FILES" ]]; then
  while IFS= read -r f; do
    if ! bash -n "$f" 2>&1; then
      echo "::error file=$f::Bash syntax error"
      FAIL=1
    fi
  done <<< "$SH_FILES"
  echo "Bash: $(echo "$SH_FILES" | wc -l) arquivo(s) checados"
fi

if [[ $FAIL -eq 0 ]]; then
  echo "OK: syntax check passou"
fi

exit $FAIL
