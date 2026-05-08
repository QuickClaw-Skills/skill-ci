#!/usr/bin/env bash
# check-structure.sh <skill_root> <is_meta_pack>
# Valida presenca de SKILL.md (exceto meta-pack) e skill.json valido.
set -euo pipefail

ROOT="${1:-.}"
IS_META="${2:-false}"
FAIL=0

cd "$ROOT"

if [[ "$IS_META" != "true" ]]; then
  if [[ ! -f SKILL.md ]]; then
    echo "::error::SKILL.md ausente na raiz ($ROOT). Skills OpenClaw exigem SKILL.md raiz para serem descobertas pelo runtime."
    FAIL=1
  else
    echo "OK: SKILL.md presente"
  fi
fi

if [[ ! -f skill.json ]]; then
  echo "::error::skill.json ausente na raiz ($ROOT)."
  FAIL=1
else
  if ! python3 -c "import json,sys; json.load(open('skill.json'))" 2>/dev/null; then
    echo "::error::skill.json nao e JSON valido."
    FAIL=1
  else
    NAME=$(python3 -c "import json; print(json.load(open('skill.json')).get('name',''))")
    VERSION=$(python3 -c "import json; print(json.load(open('skill.json')).get('version',''))")
    if [[ -z "$NAME" ]]; then
      echo "::error::skill.json sem campo 'name'."
      FAIL=1
    fi
    if [[ -z "$VERSION" ]]; then
      echo "::error::skill.json sem campo 'version'."
      FAIL=1
    fi
    if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.+-]+)?$ ]]; then
      echo "::error::skill.json.version='$VERSION' nao e semver valido (X.Y.Z)."
      FAIL=1
    fi
    echo "OK: skill.json valido (name=$NAME version=$VERSION)"
  fi
fi

if [[ ! -f LICENSE ]]; then
  echo "::warning::LICENSE ausente na raiz (recomendado)."
fi

if [[ ! -f README.md ]]; then
  echo "::warning::README.md ausente na raiz (obrigatorio em skills QuickClaw — ver skill-builder/resources/skill-standards.md)."
fi

exit $FAIL
