# Build, test & CI

Local packaging and GitHub Actions for Save 4Bucks.

## Local build (`build.ps1`)

See **[setup-and-usage.md](setup-and-usage.md#nav-installation)** for the one-shot commands.

What the script does:

1. Creates `.venv` (x64) and/or `.venv-x86` as needed
2. Installs `requirements.txt` + `requirements-dev.txt` in each venv
3. Runs **pytest** (`tests/unit`) once
4. Runs **pip-audit** (fails on known CVEs)
5. Ensures `assets\icon.ico`
6. ``flet pack`` (Flutter desktop client + PyInstaller) per arch

Manual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit -q
pip-audit -r requirements.txt
flet pack save4bucks.py -n Save4Bucks-x64 -i assets\icon.ico --distpath dist -y
```

## CI/CD

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

| Event | Jobs |
|-------|------|
| **Pull request** → `main` | Unit tests, Gitleaks + `pip-audit`, Windows EXE builds **x64 + x86** (artifacts) |
| **Push** → `main` | Unit tests, Gitleaks + `pip-audit`, SemVer **patch** bump, both EXEs, tag `vX.Y.Z`, GitHub Release with both artifacts |
| **workflow_dispatch** on `main` | Same as push release path |

Bot version commits use `[skip ci]` so they do not re-trigger another release.

### Version source

App SemVer lives in [`src/__init__.py`](../src/__init__.py) (`__version__`).  
CI bumps the **patch** with [`scripts/ci/bump_version.py`](../scripts/ci/bump_version.py) on each release.

Savegame format allowlisting (v57) is separate - see [versioning.md](versioning.md).

### Permissions

The release job needs `contents: write` (default `GITHUB_TOKEN` is enough unless branch protection blocks the bot). If pushes from Actions fail, allow GitHub Actions to write to `main` or use a PAT secret.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Antivirus quarantines exe | Exclusion for `dist\`, or run from source |
| pip-audit fails | Upgrade/pin fixed package versions |
| “No profiles found” | Saves under Documents (often OneDrive) |
| Icon missing | Confirm `assets\icon.ico` before build |
| No 32-bit Python | Install Python 3.11 Windows **32-bit**, or pass `-PythonX86` |
| Wrong bitness EXE | PyInstaller matches the interpreter - use x86 Python for `-Arch x86` |
