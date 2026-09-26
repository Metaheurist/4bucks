# Project reference

Tree, dependencies, and troubleshooting for contributors.

## Repository tree (high level)

```text
4bucks/
  assets/           App icons (png/ico)
  docs/             Long-form documentation + icons/
  scripts/ci/       Version bump for Actions
  src/              Application package
  tests/unit/       pytest suite
  .github/workflows CI
  build.ps1         Dual-arch PyInstaller
  save4bucks.spec
  save4bucks.py     EXE entry
  requirements*.txt
```

## Dependencies

| File | Role |
|------|------|
| `requirements.txt` | PyInstaller, Pillow (packaging) |
| `requirements-dev.txt` | pytest, pip-audit (+ runtime via `-r`) |

UI uses the Python stdlib (`tkinter`). Runtime editing code has no third-party imports beyond the frozen build toolchain.

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
