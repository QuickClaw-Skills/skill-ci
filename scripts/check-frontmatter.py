#!/usr/bin/env python3
"""check-frontmatter.py <SKILL.md path>
Valida frontmatter YAML do SKILL.md: presenca, parse, campos obrigatorios,
formato do name, cross-check com skill.json.name e tamanho do body.
"""
import json
import os
import re
import sys

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

# Format check: kebab-case lowercase (warning, nao fail — exceções legitimas existem)
if fields.get("name"):
    name = fields["name"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        print(f"::warning::frontmatter.name={name!r} nao segue kebab-case lowercase (regex: [a-z0-9]+(-[a-z0-9]+)*). Padrao QuickClaw e kebab-case lowercase. Skills infra/legacy podem ter excecao documentada.")

# Cross-check com skill.json.name (mesmo dir do SKILL.md)
skill_dir = os.path.dirname(path) or "."
skill_json_path = os.path.join(skill_dir, "skill.json")
if os.path.isfile(skill_json_path) and fields.get("name"):
    try:
        with open(skill_json_path, "r", encoding="utf-8") as f:
            sj = json.load(f)
        sj_name = sj.get("name")
        # Em skills infra (skill-builder, skill-ci, skill-template), skill.json.name pode
        # diferir do frontmatter.name (skill-ci-infra vs n/a). NAO falhar nesse caso.
        skill_type = (sj.get("metadata") or {}).get("skill_type", "")
        if skill_type != "infra" and sj_name and sj_name != fields["name"]:
            errors.append(
                f"frontmatter.name={fields['name']!r} != skill.json.name={sj_name!r}. "
                f"Invariant: SKILL.md.frontmatter.name == skill.json.name == slug instalado."
            )
        elif skill_type == "infra" and sj_name and sj_name != fields["name"]:
            print(f"::warning::frontmatter.name={fields['name']!r} != skill.json.name={sj_name!r} (relaxado por skill_type=infra).")
    except (json.JSONDecodeError, OSError) as e:
        print(f"::warning::nao consegui ler skill.json para cross-check de name: {e}")

# Body length: warning >500, fail >1000
body = content[m.end():]
body_lines = body.count("\n") + 1
if body_lines > 1000:
    errors.append(f"SKILL.md tem {body_lines} linhas (>1000). Excessivo — mover detalhe para references/.")
elif body_lines > 500:
    print(f"::warning::SKILL.md tem {body_lines} linhas (>500). Considerar mover detalhe operacional para references/.")

if errors:
    for e in errors:
        print(f"::error::{e}")
    sys.exit(1)

print(f"OK: frontmatter valido (name={fields['name']!r}, description={len(fields['description'])} chars, body={body_lines} linhas)")
