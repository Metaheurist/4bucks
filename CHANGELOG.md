# Changelog

Canonical notes: **[docs/CHANGELOG.md](docs/CHANGELOG.md)**.

## v1.2.0

- UI redesigned on **Flet 1.0** (Flutter for Python) with the Liberty City dark/gold theme.
- Packaging via **`flet pack`** (PyInstaller under the hood) for `Save4Bucks-x64.exe` / `Save4Bucks-x86.exe`.
- Docs hub + tech-stack category icons in **GTA IV phone-menu** style (dark tile + gold SVGs); no emoji category labels.
- First-person wording ("I") across README/docs; ASCII hyphens instead of em dashes.
- CI hardening: Gitleaks allowlist for README/docs false positives; Linux jobs on **ubuntu-24.04**; release job rebases/retries version-bump push and tolerates existing tags/releases.

## v1.1.0

- Dual-arch Windows EXE builds (`Save4Bucks-x64.exe`, `Save4Bucks-x86.exe`) via `build.ps1` and CI.
- GitHub Actions pipeline: unit tests, Gitleaks, pip-audit, SemVer patch bump, GitHub Release with both EXEs.
- Documentation hub aligned with Rianell-style README + `docs/` layout.

## v1.0.0

- Initial offline CE save money editor (tkinter UI, version gate v57, dual Autobackup, CLI).
