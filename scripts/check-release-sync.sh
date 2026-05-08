#!/usr/bin/env bash
# check-release-sync.sh <skill_root> <ref_name>
# Valida sync 3-way: skill.json.version == ref_name (sem 'v') == release title.
# Roda apenas em push de tag vX.Y.Z.
set -euo pipefail

ROOT="${1:-.}"
REF="${2:-}"

if [[ -z "$REF" ]]; then
  echo "::error::ref_name ausente"
  exit 2
fi

cd "$ROOT"

# Tag deve seguir vX.Y.Z (com sufixo opcional pre-release)
if [[ ! "$REF" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.+-]+)?$ ]]; then
  echo "::error::Tag '$REF' nao segue padrao 'vX.Y.Z'."
  exit 1
fi

EXPECTED_VERSION="${REF#v}"
ACTUAL_VERSION=$(python3 -c "import json; print(json.load(open('skill.json'))['version'])")

if [[ "$EXPECTED_VERSION" != "$ACTUAL_VERSION" ]]; then
  echo "::error::Sync 3-way quebrado: tag=$REF (=> $EXPECTED_VERSION) != skill.json.version=$ACTUAL_VERSION"
  echo "Bumpar skill.json.version para $EXPECTED_VERSION ANTES de criar a tag."
  exit 1
fi

# Tentar validar release title (se a release ja existe — pode ainda nao existir nesse momento)
if command -v gh >/dev/null 2>&1; then
  if RELEASE_TITLE=$(gh release view "$REF" --json name -q .name 2>/dev/null); then
    if [[ "$RELEASE_TITLE" != "$REF" ]]; then
      echo "::error::Sync 3-way quebrado: release title='$RELEASE_TITLE' != tag='$REF'"
      exit 1
    fi
    echo "OK: sync 3-way (skill.json=$ACTUAL_VERSION, tag=$REF, release=$RELEASE_TITLE)"
  else
    echo "::warning::Release '$REF' ainda nao existe no GitHub. Sync 2-way OK (skill.json=$ACTUAL_VERSION, tag=$REF). Criar release com 'gh release create $REF --notes-file RELEASE_NOTES.md'."
  fi
else
  echo "OK: sync 2-way (skill.json=$ACTUAL_VERSION, tag=$REF). gh CLI ausente, skip release title check."
fi
