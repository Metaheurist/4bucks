# Changelog

Canonical product changelog. Root [`CHANGELOG.md`](../CHANGELOG.md) mirrors this file.

## Unreleased

- Multi-view Flet UI: startup menu (Money / Weapons / Vitality / Settings), outlined panels, fade transitions.
- Weapons and ammo loadout editor; stock vs mod weapon detection (catalog + optional `weaponinfo.xml`).
- Health, armour, max health, and max armour PlayerInfo editors.
- Write technique `PLAYERINFO_INPLACE_V57` with status chip reporting; End-block `GameFamily` (CE / pre-CE) and dword-57 multi-EXE compat matrix.
- Accessibility: keyboard focus rings, contrast, tooltips, Esc and digit menu shortcuts.
- Contributor guide ([CONTRIBUTING.md](../CONTRIBUTING.md)).
- Single-build CI (prepare version → matrix pack once → release downloads artifacts).

## v1.2.x

Automated SemVer patch releases via GitHub Actions (see [Releases](https://github.com/Metaheurist/4bucks/releases)). Includes Flet 1.0 UI packaging (`flet pack`), dual-arch EXEs, Gitleaks/pip-audit gates, and ubuntu-24.04 Linux jobs.

## v1.1.0

- Dual-arch Windows EXE builds (`Save4Bucks-x64.exe`, `Save4Bucks-x86.exe`) via `build.ps1` and CI.
- GitHub Actions: unit tests, Gitleaks, pip-audit, SemVer patch bump, GitHub Release.

## v1.0.0

- Initial offline CE save money editor (tkinter UI, version gate v57, dual Autobackup, CLI).
