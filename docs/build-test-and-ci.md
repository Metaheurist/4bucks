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

## CI/CD workflows

Workflows are split by category. Each name starts with its category so the Actions sidebar groups them, and each file opens with a header block covering what it runs, when, what fails it, and the local equivalent command.

| Workflow | File | Runs on | Fails when |
|----------|------|---------|------------|
| **Tests · Unit & Coverage** | [`tests.yml`](../.github/workflows/tests.yml) | PRs, release gate, manual | A unit test fails (Linux 3.11/3.12, Windows 3.11); coverage < 70%; a `src` module fails to import |
| **Quality · Lint & Static Checks** | [`quality.yml`](../.github/workflows/quality.yml) | PRs, release gate, manual | Ruff finding; syntax error; invalid workflow (actionlint) |
| **Security · SAST & Secret Scanning** | [`security.yml`](../.github/workflows/security.yml) | PRs, weekly, release gate, manual | Leaked secret (Gitleaks); Bandit medium+ finding; CodeQL alerts land in Security > Code scanning |
| **CVE · Dependency Vulnerability Audit** | [`cve.yml`](../.github/workflows/cve.yml) | PRs, daily, release gate, manual | Known CVE in a pinned dependency (pip-audit: PyPI + OSV); PR adds a moderate+ vulnerable dependency |
| **Benchmark · Save I/O Performance** | [`benchmark.yml`](../.github/workflows/benchmark.yml) | PRs/pushes touching `src/` or deps, manual | PR benchmark mean > 3x the `main` baseline |
| **Build · Windows EXE (x64 + x86)** | [`build.yml`](../.github/workflows/build.yml) | Code PRs, release, manual | `build.ps1` fails; wrong EXE architecture; EXE < 20 MB |
| **Docs · Markdown Link Check** | [`docs.yml`](../.github/workflows/docs.yml) | PRs touching Markdown/docs/assets, manual | Broken repo-relative link or image |
| **Release · Version Bump & Publish** | [`release.yml`](../.github/workflows/release.yml) | Push to `main`, manual on `main` | Any gate fails; version push or publish fails |

[Dependabot](../.github/dependabot.yml) opens weekly grouped PRs for pip packages and GitHub Actions. Those PRs run the workflows above like any other PR.

### Category details

- **Tests** - `tests/unit` runs on three legs. Only the Linux 3.11 leg measures branch coverage (`src/app.py` is excluded because the Flet UI is tested by hand). The coverage table goes to the job summary and `coverage.xml` is uploaded. A separate smoke job imports every `src` module so a broken import fails before the EXE pack does.
- **Quality** - Ruff rules live in [`pyproject.toml`](../pyproject.toml) (`E4`, `E7`, `E9`, `F`, `B`; tests are exempt from `E402` because they edit `sys.path`). actionlint validates these workflow files.
- **Security** - Gitleaks scans the working tree (`--no-git`; README/CHANGELOG/docs allowlisted in [`.gitleaks.toml`](../.gitleaks.toml)). Bandit uploads a full JSON report but gates only on medium+ severity at medium+ confidence. Accepted findings carry an inline `# nosec` with the reason on the line above. CodeQL runs `security-extended` queries. Running it on every `main` push keeps the default-branch baseline current for PR comparisons.
- **CVE** - pip-audit checks both requirement files against two advisory services, so a CVE missing from one database still gets caught. The daily schedule surfaces newly published CVEs even when no code changed. Dependency Review blocks PRs that introduce vulnerable packages.
- **Benchmark** - `tests/benchmarks` measures block parsing, money/weapons/vitality reads, StoredCar reads, safehouse slot mapping, carcols parsing, save inspection, and a set-money write. [`scripts/ci/benchmark_report.py`](../scripts/ci/benchmark_report.py) writes the comparison table. Pushes to `main` store a new baseline in the Actions cache. The 3x gate is loose on purpose because shared runners are noisy.
- **Build** - [`scripts/ci/verify_exe.py`](../scripts/ci/verify_exe.py) checks the PE header and CPU type (`0x8664` x64, `0x014C` x86) and writes a `.sha256` next to each EXE.
- **Docs** - [`scripts/ci/check_md_links.py`](../scripts/ci/check_md_links.py) is offline and deterministic, and skips external URLs.

### Release pipeline (push to `main`)

The category workflows double as reusable workflows (`workflow_call`). On `main`, the release pipeline calls them as gates instead of running them a second time.

```text
Gate · Tests ────┐
Gate · Quality ──┤
Gate · Security ─┼─> Version · Bump patch ─> Build · EXEs ─> Publish · GitHub Release
Gate · CVE ──────┘
```

1. **Version · Bump patch** - bumps `src/__init__.py` and uploads it as the `bumped-version` artifact.
2. **Build · EXEs** - calls `build.yml` with `use-bumped-version: true`, so the packed EXE UI version matches the tag.
3. **Publish · GitHub Release** - downloads the gated EXEs (no rebuild), cross-checks them against `SHA256SUMS.txt`, commits the bump as `[skip ci]`, tags `vX.Y.Z`, and publishes the EXEs plus `SHA256SUMS.txt`.

GitHub skips workflows natively for commits containing `[skip ci]`, so the bot's version commit does not start another release. The publish job rebases and retries the version push if `main` moved during the build. It also re-uploads assets if the tag or release already exists.

Linux jobs run on **ubuntu-24.04**; EXE packing runs on **windows-latest**.

### Version source

App SemVer: [`src/__init__.py`](../src/__init__.py). The release pipeline bumps the patch with [`scripts/ci/bump_version.py`](../scripts/ci/bump_version.py).

Savegame format allowlisting (dword 57 across CE / pre-CE families) is separate - see [versioning.md](versioning.md).

### Permissions

Workflows default to `contents: read`. CodeQL adds `security-events: write`, and the publish job adds `contents: write`. If Actions cannot push to `main`, allow GitHub Actions write access or use a PAT secret.

### Run the CI checks locally

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q --cov --cov-fail-under=70   # Tests
.\.venv\Scripts\python.exe -m ruff check .                                     # Quality
.\.venv\Scripts\python.exe -m bandit -c pyproject.toml -r src save4bucks.py scripts -ll -ii   # Security
.\.venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt                # CVE
.\.venv\Scripts\python.exe -m pytest tests/benchmarks --benchmark-only         # Benchmark
.\.venv\Scripts\python.exe scripts/ci/check_md_links.py                        # Docs
.\build.ps1 -Arch x64                                                          # Build
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Antivirus quarantines exe | Exclusion for `dist\`, or run from source |
| pip-audit fails | Upgrade or pin fixed package versions |
| Bandit flags a reviewed line | Fix it, or add `# nosec BXXX` with the reason on the line above |
| Benchmark regression on PR | Re-run once (runner noise); if it repeats, profile the flagged function |
| Coverage below 70% | Add tests in `tests/unit` for the new save logic |
| No profiles found | Saves under Documents (often OneDrive) |
| Icon missing | Confirm `assets\icon.ico` before build |
| No 32-bit Python | Install Python 3.11 Windows 32-bit, or pass `-PythonX86` |
| `flet pack` / x86 fails | Flet desktop client is primarily x64; try `-Arch x64` first |
| Wrong bitness EXE | Pack with the matching interpreter; `verify_exe.py` reports the PE machine type |
| `flet pack` wipes previous EXE | Pack uses `dist\{arch}\` then copies into `dist\` |
| Release missing EXE | `build.yml` must upload `Save4Bucks-x64` / `Save4Bucks-x86`; publish only downloads those artifacts |
