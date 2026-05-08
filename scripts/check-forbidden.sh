#!/usr/bin/env bash
# check-forbidden.sh <skill_root>
# Bloqueia arquivos/diretorios que nao devem viver no pacote final.
set -euo pipefail

ROOT="${1:-.}"
FAIL=0

cd "$ROOT"

# Diretorios proibidos
FORBIDDEN_DIRS=(
  "data"
  "tmp"
  "output"
  "node_modules"
  ".venv"
  "venv"
  "agents/main/sessions"
)

for d in "${FORBIDDEN_DIRS[@]}"; do
  if [[ -d "$d" ]]; then
    echo "::error::Diretorio proibido versionado: $d/ (artefato de runtime, nao deve ir no pacote)"
    FAIL=1
  fi
done

# __pycache__ pode estar em qualquer profundidade
PYCACHE=$(find . -type d -name "__pycache__" -not -path "./.git/*" 2>/dev/null || true)
if [[ -n "$PYCACHE" ]]; then
  echo "::error::__pycache__ versionado em:"
  echo "$PYCACHE" | sed 's/^/  /'
  FAIL=1
fi

# Arquivos proibidos (glob)
FORBIDDEN_GLOBS=(
  ".env"
  ".env.local"
  ".env.production"
  "*.bak"
  "*.db"
  "*.sqlite"
  "*.sqlite3"
  "*.pyc"
)

for pattern in "${FORBIDDEN_GLOBS[@]}"; do
  MATCHES=$(find . -name "$pattern" -not -path "./.git/*" -not -path "./.skill-ci/*" 2>/dev/null || true)
  if [[ -n "$MATCHES" ]]; then
    echo "::error::Arquivo proibido versionado ($pattern):"
    echo "$MATCHES" | sed 's/^/  /'
    FAIL=1
  fi
done

if [[ $FAIL -eq 0 ]]; then
  echo "OK: sem arquivos/diretorios proibidos"
fi

exit $FAIL
