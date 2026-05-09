## v1.1.0 — 2026-05-09

> Bump: MINOR
> Compatibilidade: nenhuma quebra. Consumidores que apontam para `@v1` recebem automaticamente.

### Added
- `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` no job `validate` — forca runtime das actions JS (checkout, setup-node, setup-python) para Node.js 24 antes do deprecation default em 2026-06-02.

### Changed
- (nenhuma mudanca de contrato/inputs)

### Fixed
- Warnings de deprecation Node.js 20 que apareciam em todo run de CI dos consumidores.

### Security
- (n/a)

### Migration Notes
- Consumidores que usam `uses: QuickClaw-Skills/skill-ci/.github/workflows/validate.yml@v1` nao precisam fazer nada. A tag movel `v1` foi atualizada para apontar pra `v1.1.0`.
- Quem pinou em `@v1.0.0` continua funcionando (com warnings) ate atualizar o pin.

### Validation
- [x] skill.json nao se aplica (skill-ci nao e skill OpenClaw — e um workflow reusable)
- [x] Workflow YAML valido
- [x] Sync 2-way: tag v1.1.0 == release title v1.1.0
- [x] Tag movel v1 atualizada

### Rollback
- Tag anterior estavel: v1.0.0
- Procedimento: `git tag -f v1 v1.0.0 && git push --force origin v1` (mover v1 de volta) e `gh release edit v1.1.0 --prerelease` para sumir do canal default. Codigo de v1.0.0 continua acessivel via `@v1.0.0`.
