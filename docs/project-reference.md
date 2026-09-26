# Project reference

Tree, dependencies, and troubleshooting for contributors.

## Repository tree (high level)

```text
4bucks/
  assets/           App icons (png/ico)
  docs/             Long-form docs + GTA IV-style icons/
  scripts/ci/       Version bump for Actions
  src/              Application package (Flet UI in app.py)
  tests/unit/       pytest suite
  .github/workflows CI (ubuntu-24.04 + windows dual-arch release)
  build.ps1         Dual-arch flet pack
  save4bucks.spec   Legacy PyInstaller spec (optional / reference)
  save4bucks.py     EXE / flet pack entry
  requirements*.txt
```

## Dependencies

| File | Role |
|------|------|
| `requirements.txt` | **Flet 1.0.1**, PyInstaller, Pillow (UI + packaging) |
| `requirements-dev.txt` | pytest, pip-audit (+ runtime via `-r`) |

UI uses **Flet** (Flutter for Python). Save editing modules (`detect`, `versioning`, `save_money`, `backup`, `settings`) stay stdlib-only aside from the frozen UI/packaging stack.

## Troubleshooting

| Issue | Where to look |
|-------|----------------|
| Profiles missing | [setup-and-usage.md](setup-and-usage.md), [known-issues.md](known-issues.md) |
| Write refused | [versioning.md](versioning.md) |
| Build / CI | [build-test-and-ci.md](build-test-and-ci.md) |
| Security / antivirus | [SECURITY.md](SECURITY.md) |

<a id="nav-security-notes"></a>

## Security notes

See **[SECURITY.md#nav-security-notes](SECURITY.md#nav-security-notes)**.
