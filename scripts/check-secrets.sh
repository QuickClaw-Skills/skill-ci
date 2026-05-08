#!/usr/bin/env bash
# check-secrets.sh <skill_root>
# Grep de padroes de segredo conhecidos.
set -euo pipefail

ROOT="${1:-.}"
FAIL=0

cd "$ROOT"

# Padroes (regex BRE/ERE compativeis com grep -E)
declare -A PATTERNS
PATTERNS[anthropic]='sk-ant-api[0-9]{2}-[A-Za-z0-9_-]{20,}'
PATTERNS[openai]='sk-(proj-)?[A-Za-z0-9]{20,}'
PATTERNS[github_token]='gh[pousr]_[A-Za-z0-9]{36,}'
PATTERNS[google_api]='AIza[0-9A-Za-z_-]{35}'
PATTERNS[slack]='xox[baprs]-[A-Za-z0-9-]{10,}'
PATTERNS[private_key]='-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY'
PATTERNS[aws_access]='AKIA[0-9A-Z]{16}'

EXCLUDES=(
  "--exclude-dir=.git"
  "--exclude-dir=.skill-ci"
  "--exclude-dir=node_modules"
  "--exclude-dir=.venv"
  "--exclude-dir=venv"
  "--exclude=*.lock"
  "--exclude=package-lock.json"
)

for label in "${!PATTERNS[@]}"; do
  pattern="${PATTERNS[$label]}"
  HITS=$(grep -rEn "${EXCLUDES[@]}" "$pattern" . 2>/dev/null || true)
  if [[ -n "$HITS" ]]; then
    echo "::error::Padrao de segredo detectado [$label]:"
    echo "$HITS" | sed 's/^/  /'
    FAIL=1
  fi
done

if [[ $FAIL -eq 0 ]]; then
  echo "OK: sem padroes de segredo"
fi

exit $FAIL
