#!/usr/bin/env bash
# check-references-hint.sh <skill_root>
# Sugere mover docs operacionais longas (>200 linhas) para references/.
# Warning, nao fail. Exclui docs de repo (README, RELEASE_NOTES, CHANGELOG,
# CONTRIBUTING, LICENSE, SECURITY, CODE_OF_CONDUCT) que ficam na raiz por
# politica da org QuickClaw.

set -euo pipefail
ROOT="${1:-.}"
THRESHOLD=200

# Padroes de docs de repo (ficam na raiz, nao migrar pra references/)
REPO_DOCS_RE='^(README|RELEASE_NOTES|CHANGELOG|CONTRIBUTING|LICENSE|SECURITY|CODE_OF_CONDUCT|AUTHORS|ROADMAP)(\.md)?$'

found_any=false
while IFS= read -r -d '' file; do
  rel="${file#$ROOT/}"
  basename=$(basename "$file")

  # Skip SKILL.md (validado em outro script)
  [ "$basename" = "SKILL.md" ] && continue

  # Skip se ja esta em references/ ou resources/
  case "$rel" in
    references/*|resources/*) continue ;;
  esac

  # Skip se e doc de repo
  if echo "$basename" | grep -qE "$REPO_DOCS_RE"; then
    continue
  fi

  # Conta linhas
  lines=$(wc -l < "$file" | tr -d ' ')
  if [ "$lines" -gt "$THRESHOLD" ]; then
    echo "::warning file=$rel::doc com $lines linhas (>$THRESHOLD) fora de references/. Considerar mover — SKILL.md deve referenciar sob demanda, nao inline."
    found_any=true
  fi
done < <(find "$ROOT" -type f -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.skill-ci/*" -print0)

if [ "$found_any" = false ]; then
  echo "OK: nenhuma doc operacional longa fora de references/."
fi
exit 0
