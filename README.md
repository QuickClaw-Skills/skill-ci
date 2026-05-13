# skill-ci

Reusable GitHub Actions workflow para validar skills da org `QuickClaw-Skills` contra o padrao normativo definido em [`skill-builder`](https://github.com/QuickClaw-Skills/skill-builder) (`resources/skill-standards.md` + `resources/release-management.md`).

## Como usar (consumidor)

Crie `.github/workflows/ci.yml` na raiz do repo da skill:

```yaml
name: CI
on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  validate:
    uses: QuickClaw-Skills/skill-ci/.github/workflows/validate.yml@v1
```

Pronto. Em todo push/PR/tag, a skill e validada.

### Auto-release em push de tag (recomendado)

Adicione tambem `.github/workflows/release.yml`:

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    uses: QuickClaw-Skills/skill-ci/.github/workflows/auto-release.yml@v1
```

Em todo `git push --tags`, o workflow valida tag vs `skill.json.version` e cria a GitHub Release com release notes auto-geradas. Idempotente (skip se Release ja existe). Defesa contra o padrao "taggeei mas esqueci de criar release", que deixava versoes invisiveis pro cron `check-skills-updates`.

## Inputs (validate.yml)

| Input | Tipo | Default | Quando usar |
|---|---|---|---|
| `skill_root` | string | `.` | Skill nao mora na raiz (ex: monorepo de subskills) |
| `is_meta_pack` | bool | `false` | Bundle/installer sem `SKILL.md` raiz (ex: `skill-personal-assistant`). Pula check de SKILL.md mas mantem outros |
| `is_forensic` | bool | `false` | Repo forense que nunca deve ser publicado como skill (ex: `backup-forense-meu-brother`). Pula validacao inteira |
| `release_validation` | bool | `true` | Roda sync 3-way em push de tag `vX.Y.Z` |

Exemplo meta-pack:

```yaml
jobs:
  validate:
    uses: QuickClaw-Skills/skill-ci/.github/workflows/validate.yml@v1
    with:
      is_meta_pack: true
```

## O que valida

| Check | Falha CI? | Detalhe |
|---|---|---|
| `SKILL.md` na raiz | sim (exceto meta-pack) | Runtime OpenClaw exige |
| Frontmatter YAML (`name`, `description`) | sim | Description curta gera warning |
| `skill.json` valido + semver | sim | `name` e `version` obrigatorios |
| `LICENSE` / `README.md` | warning | Recomendado mas nao bloqueia |
| Diretorios proibidos: `data/`, `tmp/`, `output/`, `node_modules/`, `.venv/`, `__pycache__/`, `agents/main/sessions/` | sim | Artefatos de runtime |
| Arquivos proibidos: `.env*`, `*.bak`, `*.db`, `*.sqlite`, `*.pyc` | sim | |
| Padroes de segredo: `sk-ant-*`, `sk-*` (OpenAI), `ghp_*`/`gho_*`, `AIza*`, `xox[baprs]-*`, RSA/EC/OPENSSH/PGP private key, `AKIA*` | sim | |
| Paths absolutos: `/home/*/`, `/Users/*/`, `C:\Users\` | sim | Use `<!-- abs-path-ok -->` na linha para ignorar (apenas docs) |
| Syntax: `python -m py_compile`, `node --check`, `bash -n` | sim | |
| Release sync 3-way (`skill.json.version` == tag (sem `v`) == release title) | sim | So roda em push de tag `vX.Y.Z` |

## Versionamento

- `v1` — tag movel, sempre aponta pra ultima `v1.x.y` estavel. **Use isso.**
- `v1.0.0`, `v1.1.0`, ... — tags fixas. Use se quiser pinning estrito.
- `v2`, ... — bump major se houver breaking change no contrato de inputs/outputs do workflow.

Politica detalhada: `resources/release-management.md` no skill-builder.

## Desenvolvimento local

Os scripts em `scripts/` rodam standalone:

```bash
cd /path/to/uma-skill
SKILL_ROOT=. bash /path/to/skill-ci/scripts/check-structure.sh "$SKILL_ROOT" false
bash /path/to/skill-ci/scripts/check-forbidden.sh "$SKILL_ROOT"
# etc.
```

## License

Proprietary — uso interno QuickClaw.
