# Build, test, and CI

Local packaging and GitHub Actions for 4Bucks.

## Local build (`build.ps1`)

See [setup-and-usage.md](setup-and-usage.md) for one-shot commands.

1. Creates `.venv` (x64) and/or `.venv-x86` as needed
2. Installs `requirements.txt` + `requirements-dev.txt` (includes Flet 1.0.1)
3. Runs pytest (`tests/unit`) once
4. Runs pip-audit (fails on known CVEs)
5. Ensures `assets\icon.ico`
6. Runs `flet pack` per arch into `dist\Save4Bucks-{x64|x86}.exe`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit -q
pip-audit -r requirements.txt
flet pack save4bucks.py -n Save4Bucks-x64 -i assets\icon.ico --distpath dist -y `
  --hidden-import src --hidden-import src.app --hidden-import src.detect `
  --hidden-import src.save_money --hidden-import src.save_weapons `
  --hidden-import src.save_vitality --hidden-import src.save_garage `
  --hidden-import src.safehouse_parking --hidden-import src.vehicles_catalog `
  --hidden-import src.carcols_catalog `
  --hidden-import src.playerinfo `
  --hidden-import src.weapons_catalog --hidden-import src.weapon_detect `
  --hidden-import src.versioning --hidden-import src.backup --hidden-import src.settings
```

## CI/CD

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

| Event | Jobs |
|-------|------|
| Pull request → `main` | Unit tests, Gitleaks + pip-audit, EXE matrix x64 + x86 (checkout version) |
| Push → `main` | Gates → prepare SemVer bump → matrix packs once with bumped `__init__.py` → release downloads EXEs, commits bump, tags, publishes |
| workflow_dispatch on `main` | Same as push release path |

### Single-build release path

EXEs are packed only in the matrix job. The release job does not rebuild.

```text
unit-tests + security-audit
        ↓
prepare_version   (main only: bump src/__init__.py → artifact bumped-version)
        ↓
build-exe x64/x86 (apply bumped file if present → flet pack → Save4Bucks-{arch})
        ↓
release           (download EXEs + bumped file → commit [skip ci] → tag → gh release)
```

Released EXE UI version matches the tag because prepare bumps before the matrix pack.

Linux jobs run on **ubuntu-24.04**. Gitleaks allowlists `README.md`, `CHANGELOG.md`, and `docs/` for badge/doc false positives (see [`.gitleaks.toml`](../.gitleaks.toml)).

Bot version commits use `[skip ci]` so they do not re-trigger a release. The release job rebases/retries the version-bump push if `main` moved during the matrix build, and re-uploads assets if the tag/release already exists.

### Version source

App SemVer: [`src/__init__.py`](../src/__init__.py). CI bumps the patch with [`scripts/ci/bump_version.py`](../scripts/ci/bump_version.py) in the prepare job.

Savegame format allowlisting (dword 57 across CE / pre-CE families) is separate - see [versioning.md](versioning.md).

### Permissions

The release job needs `contents: write`. If Actions cannot push to `main`, allow GitHub Actions write access or use a PAT secret.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Antivirus quarantines exe | Exclusion for `dist\`, or run from source |
| pip-audit fails | Upgrade or pin fixed package versions |
| No profiles found | Saves under Documents (often OneDrive) |
| Icon missing | Confirm `assets\icon.ico` before build |
| No 32-bit Python | Install Python 3.11 Windows 32-bit, or pass `-PythonX86` |
| `flet pack` / x86 fails | Flet desktop client is primarily x64; try `-Arch x64` first |
| Wrong bitness EXE | Pack with the matching interpreter |
| `flet pack` wipes previous EXE | Pack uses `dist\{arch}\` then copies into `dist\` |
| Release missing EXE | Matrix must upload `Save4Bucks-x64` / `Save4Bucks-x86`; release only downloads those artifacts |
