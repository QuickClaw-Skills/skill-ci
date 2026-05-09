## v1.2.0 — 2026-05-09

> Bump: MINOR
> Compatibilidade: nenhuma quebra. Consumidores que apontam para `@v1` recebem automaticamente.

### Added
- Whitelist de path agora aceita `/home/openclaw/` alem de `/home/node/`. Esses sao os dois usuarios canonicos do container OpenClaw em diferentes deployment models (containerizado QuickClaw vs bare-metal/systemd self-hosted).

### Changed
- `scripts/check-abs-paths.sh` — regex de allowed expandida para `/home/(node|openclaw)/`.

### Fixed
- Skills que documentam systemd unit files com `WorkingDirectory=/home/openclaw/...` ou que tem fallback default `/home/openclaw/.npm-global/bin/openclaw` para `OPENCLAW_BIN` agora passam o check sem ajuste manual.

### Security
- (n/a)

### Migration Notes
- Consumidores apontando para `@v1` nao precisam fazer nada — tag movel atualizada.

### Validation
- [x] Workflow YAML inalterado (so script foi tocado)
- [x] Sync 2-way: tag v1.2.0 == release title v1.2.0
- [x] Tag movel v1 atualizada

### Rollback
- Tag anterior estavel: v1.1.0
- Procedimento: `git tag -f v1 v1.1.0 && git push --force origin v1`. Codigo de v1.1.0 continua acessivel via `@v1.1.0`.
