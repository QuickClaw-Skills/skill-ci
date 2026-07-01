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
