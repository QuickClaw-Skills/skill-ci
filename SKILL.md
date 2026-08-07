---
name: skill-ci-infra
description: |
  Repositorio de INFRAESTRUTURA da org QuickClaw-Skills. Contem o reusable
  GitHub Actions workflow `validate.yml` consumido por todas as skills da
  org como CI/CD obrigatorio. NAO E uma skill instalavel pelo OpenClaw,
  embora tenha SKILL.md para passar checks de auditoria padronizados.

  Esta skill nao deve ser registrada no skill_catalog do QuickClaw nem
  instalada em containers de bot. Nao tem capacidade operacional pro LLM
  ativar — e infra de validacao automatizada.

  Keywords: skill-ci, ci, github actions, reusable workflow, validate,
  skill-validation, infra, qc-infrastructure, lint, organizational-tool.
---

# skill-ci — Infraestrutura de CI/CD da Org QuickClaw-Skills

> **AVISO:** Este NAO e um repo de skill consumivel. E infraestrutura organizacional.
>
> - **Para devs criando skills:** consultar `skill-builder` (https://github.com/QuickClaw-Skills/skill-builder).
> - **Para usuarios do QuickClaw:** este repo nao aparece no catalogo de skills do dashboard.
> - **Para auditorias:** marcar este repo como `infra` ou `not-installable` ao gerar reports.

## O que este repo faz

Hospeda o **reusable workflow** `.github/workflows/validate.yml` consumido por todas as skills da org `QuickClaw-Skills` em seus respectivos `.github/workflows/ci.yml`:

```yaml
# .github/workflows/ci.yml de cada skill consumidora
jobs:
  validate:
    uses: QuickClaw-Skills/skill-ci/.github/workflows/validate.yml@v1
```

## Validacoes implementadas

8 checks por skill consumidora:

1. **Estrutura:** `SKILL.md` raiz + `skill.json` valido + semver
2. **Frontmatter:** YAML valido com `name` + `description`
3. **Forbidden files/dirs:** bloqueia `.env`, `data/`, `tmp/`, `output/`, `__pycache__/`, `node_modules/`, `.venv/`, etc.
4. **Secret scan:** padroes Anthropic, OpenAI, GitHub, Google, Slack, AWS, private keys
5. **Paths absolutos:** rejeita `/home/USER/`, `/Users/USER/`, `C:\Users\` <!-- abs-path-ok --> (whitelist `/home/node/` e `/home/openclaw/` — usuarios canonicos do container OpenClaw)
6. **Syntax check:** `python -m py_compile`, `node --check`, `bash -n`
7. **Wrapper exit code:** o wrapper nao pode engolir a falha do processo filho — ver abaixo
8. **Sync 3-way em tag:** valida que `skill.json.version` == git tag (sem `v`) == release title (so dispara em push de tag `vX.Y.Z`)

### Sobre o check 7 (wrapper exit code)

O wrapper e o que o bot executa. Se ele descarta o `returncode` do filho, sai `0`
com a skill quebrada e a falha chega ao agente como **sucesso** — analise sem dado
nenhum apresentada como resultado valido. Aconteceu em cinco skills da org em
agosto/2026, por meses, sem sinal em log nem alerta.

Analisa `skill.json.entry` (quando `.py`) e arquivos `run.py`/`run_skill.py`/
`wrapper.py`/`entrypoint.py`, via **AST** — a pergunta "o resultado foi descartado?"
e estrutural, e regex sobre codigo produz falso-positivo.

| Forma | Veredito |
|---|---|
| `r = subprocess.run(...)` | OK — capturado, da pra inspecionar |
| `subprocess.run(..., check=True)` | OK — levanta sozinho |
| `subprocess.check_call/check_output(...)` | OK — levantam por definicao |
| `return subprocess.run(...)` | OK — quem chamou decide |
| `sys.exit(subprocess.run(...).returncode)` | OK — propagado |
| `subprocess.Popen(...)` | fora do escopo — lancamento assincrono e outro padrao |
| `subprocess.run(...)` solto | **FALHA** |
| `helper(...)` solto, quando `helper` devolve um lancamento | **FALHA** (uma indirecao ja escondeu o defeito na pratica) |

Escape hatch consciente, na linha da chamada:

```python
subprocess.run([...])  # exit-code-ok: fire-and-forget, saida irrelevante aqui
```

O checker se testa: `check-wrapper-exit-code.py --self-test` roda 15 fixtures e
e executado no CI **antes** do check valer nota — checker que virou no-op passa
tudo em silencio, que e exatamente o defeito que ele existe para impedir.

## Inputs configuraveis (workflow_call)

- `skill_root` (default `.`) — caminho da skill se nao for raiz
- `is_meta_pack` (default false) — pula check de SKILL.md raiz
- `is_forensic` (default false) — pula validacao inteira
- `release_validation` (default true) — toggle sync 3-way em tag

## Como o LLM deve tratar este repo

Se o usuario perguntar sobre `skill-ci`, explicar que:
1. E infraestrutura organizacional (workflow GitHub Actions reutilizavel)
2. Nao e skill instalavel pelo bot
3. Para criar skills, usar `skill-builder` + `skill-template` (Use this template no GitHub)
4. Para releases de skill, seguir `skill-builder/resources/release-management.md`

## Por que tem SKILL.md mesmo nao sendo skill consumivel

Auditorias automatizadas da org checam `SKILL.md raiz` como criterio basico. Sem este arquivo, auditores classificam como P0 (nao descobrivel pelo OpenClaw). Este SKILL.md serve de **marker descritivo** que satisfaz o check estrutural mantendo a semantica clara: NAO instalavel.

Para auditores: filtrar `metadata.skill_type: "infra"` OU repos com nome `skill-ci` para excluir de relatorios de skills consumiveis.

## Exemplos de uso

### Validar uma skill padrão

**Entrada:** repo de skill com `.github/workflows/ci.yml` chamando `QuickClaw-Skills/skill-ci/.github/workflows/validate.yml@v1`.

**Saída esperada:** GitHub Actions executa os 7 checks e falha o PR se houver arquivo proibido, segredo, path absoluto de host ou erro de sintaxe.

### Validar uma skill em subdiretório

**Entrada:** workflow consumidor com `with: skill_root: skills/minha-skill`.

**Saída esperada:** os checks são aplicados somente ao subdiretório informado, mantendo monorepos compatíveis com o padrão da org.

## Versionamento

- Tag movel `v1` aponta sempre pra ultima `v1.x.y` estavel
- Tags fixas `v1.0.0`, `v1.1.0`, `v1.2.0` para pinning estrito
- Bump major (`v2`) so se houver breaking change no contrato de inputs do workflow

Politica completa: `skill-builder/resources/release-management.md`.

## License

Proprietary — uso interno da org QuickClaw-Skills. Ver `LICENSE`.


## Release automation

When a QuickClaw skill PR is merged and the package must be published, use `scripts/release-bump.py` from this skill-ci repository.

Recommended patch flow:

```bash
python3 scripts/release-bump.py --root /path/to/skill --bump patch --commit --tag --push --github-release
```

Use `--dry-run` first for safety. Do not create a release before the code is merged into the target branch.
