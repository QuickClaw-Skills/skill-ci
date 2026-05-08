#!/usr/bin/env python3
"""check-frontmatter.py <SKILL.md path>
Valida frontmatter YAML do SKILL.md: presenca, parse, campos obrigatorios.
"""
import sys
import re
import os

if len(sys.argv) < 2:
    print("::error::uso: check-frontmatter.py <path/SKILL.md>")
    sys.exit(2)

path = sys.argv[1]
if not os.path.isfile(path):
    print(f"::error::SKILL.md nao encontrado: {path}")
    sys.exit(1)

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
if not m:
    print(f"::error::SKILL.md sem frontmatter YAML delimitado por '---' no inicio.")
    sys.exit(1)

fm_raw = m.group(1)

# Parse minimo sem PyYAML (evita dependencia). Aceita 'key: value' e blocos
# multi-linha indentados.
fields = {}
current_key = None
for line in fm_raw.splitlines():
    if not line.strip():
        continue
    mm = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", line)
    if mm:
        current_key = mm.group(1)
        fields[current_key] = mm.group(2).strip()
    elif current_key and (line.startswith(" ") or line.startswith("\t")):
        fields[current_key] = (fields[current_key] + " " + line.strip()).strip()

errors = []
if not fields.get("name"):
    errors.append("frontmatter sem campo 'name'.")
if not fields.get("description"):
    errors.append("frontmatter sem campo 'description'.")
else:
    desc_len = len(fields["description"])
    if desc_len < 40:
        print(f"::warning::description curta ({desc_len} chars). Recomendado >=80 para bom matching de trigger.")

# Body length warning
body = content[m.end():]
body_lines = body.count("\n") + 1
if body_lines > 500:
    print(f"::warning::SKILL.md tem {body_lines} linhas (>500). Considerar mover detalhe para references/.")

if errors:
    for e in errors:
        print(f"::error::{e}")
    sys.exit(1)

print(f"OK: frontmatter valido (name={fields['name']!r}, description={len(fields['description'])} chars, body={body_lines} linhas)")
