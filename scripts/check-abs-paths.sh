#!/usr/bin/env bash
# check-abs-paths.sh <skill_root>
# Detecta paths absolutos do host em arquivos versionados.
# Permite paths em strings de exemplo dentro de docs com marcador <!-- abs-path-ok -->.
set -euo pipefail

ROOT="${1:-.}"
FAIL=0

cd "$ROOT"

# Paths que indicam ambiente especifico do host.
# Nota: /home/node/ e o usuario canonico do container OpenClaw e e permitido
# (filtrado abaixo). /Users/ e C:\Users\ sao paths de host por definicao.
PATTERNS=(
  '/home/[a-zA-Z0-9_-]+/'
  '/Users/[a-zA-Z0-9_-]+/'
  'C:\\\\Users\\\\'
  'C:/Users/'
)

# Whitelist de paths de container/sistema legitimos (regex).
# /home/node/ e /home/openclaw/ sao usuarios canonicos do container OpenClaw
# em diferentes deployment models (containerizado QuickClaw vs bare-metal/systemd).
ALLOWED='/home/(node|openclaw)/'

EXCLUDES=(
  "--exclude-dir=.git"
  "--exclude-dir=.skill-ci"
  "--exclude-dir=node_modules"
  "--exclude-dir=.venv"
  "--exclude-dir=venv"
  "--exclude-dir=__pycache__"
  "--exclude=*.lock"
  "--exclude=package-lock.json"
  "--exclude=*.pyc"
)

for pattern in "${PATTERNS[@]}"; do
  HITS=$(grep -rEn "${EXCLUDES[@]}" "$pattern" . 2>/dev/null || true)
  if [[ -n "$HITS" ]]; then
    # Filtra linhas marcadas com <!-- abs-path-ok --> e paths de container permitidos
    FILTERED=$(echo "$HITS" | grep -v 'abs-path-ok' | grep -Ev "$ALLOWED" || true)
    if [[ -n "$FILTERED" ]]; then
      echo "::error::Path absoluto do host detectado [$pattern]:"
      echo "$FILTERED" | sed 's/^/  /'
      FAIL=1
    fi
  fi
done

if [[ $FAIL -eq 0 ]]; then
  echo "OK: sem paths absolutos do host"
fi

exit $FAIL
