# Project reference

Repository layout, dependencies, and troubleshooting pointers.

## Tree

```text
4bucks/
  assets/             App icons (png/ico)
  docs/               Documentation + icons/
  scripts/ci/         Version bump for Actions
  src/                Application package
  tests/unit/         pytest suite
  .github/workflows   CI
  CONTRIBUTING.md
  build.ps1           Dual-arch flet pack
  save4bucks.spec     Optional PyInstaller reference
  save4bucks.py       EXE / flet pack entry
  requirements*.txt
```

## Dependencies

| File | Role |
|------|------|
| `requirements.txt` | Flet 1.0.1, PyInstaller, Pillow |
| `requirements-dev.txt` | pytest, pip-audit (+ runtime via `-r`) |

UI: Flet. Save modules (`detect`, `versioning`, `playerinfo`, `save_money`, `save_weapons`, `save_vitality`, `weapon_detect`, `weapons_catalog`, `backup`, `settings`) are stdlib aside from the frozen packaging stack.

## Troubleshooting

| Issue | Doc |
|-------|-----|
| Profiles missing | [setup-and-usage.md](setup-and-usage.md), [known-issues.md](known-issues.md) |
| Write refused | [versioning.md](versioning.md) |
| Build / CI | [build-test-and-ci.md](build-test-and-ci.md) |
| Security / antivirus | [SECURITY.md](SECURITY.md) |
| Contributing | [CONTRIBUTING.md](../CONTRIBUTING.md) |

<a id="nav-security-notes"></a>

## Security notes

See **[SECURITY.md#nav-security-notes](SECURITY.md#nav-security-notes)**.
