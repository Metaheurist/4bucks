# CI/CD

GitHub Actions workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## What runs

| Event | Jobs |
|-------|------|
| **Pull request** → `main` | Unit tests, Gitleaks + `pip-audit`, Windows EXE builds **x64 + x86** (artifacts) |
| **Push** → `main` | Unit tests, Gitleaks + `pip-audit`, SemVer **patch** bump, both EXEs, tag `vX.Y.Z`, GitHub Release with both artifacts |
| **workflow_dispatch** on `main` | Same as push release path |

Bot version commits use `[skip ci]` so they do not re-trigger another release.

## Version source

App SemVer lives in [`src/__init__.py`](../src/__init__.py) (`__version__`).  
CI bumps the **patch** with [`scripts/ci/bump_version.py`](../scripts/ci/bump_version.py) on each release.

Savegame format allowlisting (v57) is separate — see [VERSIONING.md](VERSIONING.md).

## Local equivalents

```powershell
python -m pytest tests/unit -q
python -m pip_audit -r requirements.txt
python -m pip_audit -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\build.ps1
# → dist\Save4Bucks-x64.exe and dist\Save4Bucks-x86.exe
```

## Permissions

The release job needs `contents: write` (default `GITHUB_TOKEN` is enough unless branch protection blocks the bot). If pushes from Actions fail, allow GitHub Actions to write to `main` or use a PAT secret.
