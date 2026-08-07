## v1.5.0 - 2026-08-07

## Check novo: wrapper nao pode engolir a falha do processo filho

> Bump: MINOR
> Compatibilidade: adicao retrocompativel. Nenhum repo da org fica vermelho — ver Validation.

### Added
- `scripts/check-wrapper-exit-code.py` — reprova wrapper de skill que lanca um processo filho e **descarta o resultado** (sem captura e sem `check=True`). O wrapper e o que o bot executa: descartar o `returncode` faz a skill sair `0` quebrada, e a falha chega ao agente como sucesso. Aconteceu em **cinco** skills da org em agosto/2026 — analise sem dado nenhum reportada como execucao bem-sucedida, por meses, sem sinal em log nem em alerta.
- Analise por **AST**, nao regex: "o resultado foi descartado?" e uma pergunta estrutural (o `Call` e filho direto de um `Expr`). Regex sobre codigo produz falso-positivo, e a org ja pagou por detector fragil duas vezes.
- Cobre **uma indirecao**: `helper(...)` solto tambem reprova quando `helper` devolve um lancamento. Sem isso o checker teria ponto cego — foi o caso real do `crypto-divergence-rsi`, que passaria batido.
- Escape hatch consciente por linha: `# exit-code-ok: <motivo>`, na convencao do `abs-path-ok` ja existente.
- `--self-test` com 15 fixtures, rodado no CI **antes** do check valer nota. Checker que virou no-op passa tudo em silencio — que e o defeito que ele existe para impedir.

### Changed
- `validate.yml` ganha os dois passos (self-test + check). Agora sao **8** validacoes por skill consumidora.
- `SKILL.md`: tabela do que o check aceita e rejeita.

### Validation
- **Dry-run contra os 22 repos da org antes de publicar:** 13 verdes, **0 acusados**, 9 sem wrapper Python (skip). Nenhum repo existente fica vermelho com este check.
- Detecta o defeito real nos 5 casos conhecidos: rodado contra o estado **pre-fix** de crypto-assets-analytics, crypto-divergence-rsi, funding-rate-monitor, squeeze-monitor e daily-briefing — acusou os 5; contra o estado corrigido, aceitou os 5.
- Falso-positivo encontrado e corrigido no dry-run: `subprocess.check_call/check_output` levantam por definicao (a checagem esta no NOME, nao num kwarg) — sem esse ajuste o `skill-delta-neutral-nado-kraken`, que esta correto, ficaria vermelho. `Popen` ficou de fora de proposito: lancamento assincrono e outro padrao.

### Notes
- **A tag `v1` estava parada em v1.4.0.** As releases v1.4.1 e v1.4.2 sairam mas o ref que todo repo consome (`@v1`) nunca foi movido — entao o CI da org rodava codigo de duas releases atras. Esta release move o `v1`, o que tambem passa a valer o fix de falso-positivo do `check-abs-paths` (v1.4.1). Ao publicar skill-ci, mover o `v1` faz parte da release, nao e passo opcional.

### Rollback
- Tag anterior estavel: v1.4.2
- Procedimento: reapontar `v1` para `v1.4.2` (`git tag -f v1 v1.4.2 && git push -f origin v1`).

Version bump: v1.4.2 -> v1.5.0.

## v1.4.2 - 2026-07-01

Add canonical release-bump automation for QuickClaw Skills.

## v1.4.1 - 2026-07-01

## CI/audit fixes

- Fixed absolute-path checker self-match false positives.
- Standardized metadata/docs according to the audit findings.

Version bump: v1.4.0 -> v1.4.1.

## v1.2.2 — 2026-05-09

> Bump: PATCH
> Compatibilidade: nenhuma quebra. Apenas sync de version.

### Fixed
- Sync 3-way: skill.json.version 1.2.0 -> 1.2.2 alinha com tag git e release title.
  v1.2.1 anterior teve skill.json.version=1.2.0 por engano (foi adicionado SKILL.md+skill.json novos sem bumpar). Agora coerente.

### Validation
- [x] tag v1.2.2 == release title v1.2.2 == skill.json.version 1.2.2
