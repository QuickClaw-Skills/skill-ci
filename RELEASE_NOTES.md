## v1.2.1 — 2026-05-09

> Bump: PATCH
> Compatibilidade: nenhuma quebra. Adiciona apenas markers descritivos.

### Added
- `SKILL.md` na raiz — marker descritivo declarando que skill-ci e INFRAESTRUTURA, NAO skill instalavel. Elimina falso positivo P0 em auditorias automatizadas (que checam presenca de SKILL.md raiz como criterio basico).
- `skill.json` na raiz — manifest com `metadata.skill_type: "infra"` e `metadata.installable: false`. Auditores futuros podem filtrar por esses campos pra excluir skill-ci de reports de skills consumiveis.

### Changed
- (nenhum codigo modificado)

### Fixed
- Reaudit do bot QuickClaw (09/05/2026) classificou skill-ci como P0 "sem SKILL.md raiz: nao descobrivel pelo OpenClaw". Verdadeiro mas intencional. Agora skill-ci tem SKILL.md descritivo deixando claro que e infra nao consumivel.

### Security
- N/A

### Migration Notes
- Consumidores apontando `@v1` continuam recebendo automaticamente. Workflow `.github/workflows/validate.yml` inalterado.

### Validation
- [x] SKILL.md frontmatter declara explicitamente `name: skill-ci-infra` (nao skill-ci) pra deixar diferenca clara entre o repo e qualquer hipotetica skill consumivel
- [x] skill.json.version 1.2.0 -> 1.2.1
- [x] Sync 2-way: tag v1.2.1 == release title

### Rollback
- Tag anterior: v1.2.0. Procedimento: `git tag -f v1 v1.2.0 && git push -f origin v1`. SKILL.md/skill.json novos ficam orfaos mas nao quebram nada.
