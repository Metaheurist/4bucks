# Building Save 4Bucks

## Requirements

- Windows
- Python **3.11+ x64** on PATH (for 64-bit EXE)
- Python **3.11+ x86** for 32-bit EXE (python.org Windows installer → “Windows installer (32-bit)”, or `py -3.11-32`)
- Network once for `pip install` / `pip-audit` advisory DB

## One-shot build (both architectures)

```powershell
cd "C:\Users\OnceU\OneDrive\Documents\GitHub\4bucks"
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Outputs:

| File | Arch |
|------|------|
| `dist\Save4Bucks-x64.exe` | 64-bit |
| `dist\Save4Bucks-x86.exe` | 32-bit |

Single arch:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Arch x64
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Arch x86
```

Optional interpreters:

```powershell
.\build.ps1 -Arch All -PythonX64 "C:\Path\python.exe" -PythonX86 "C:\Path\python.exe"
```

## What the script does

1. Creates `.venv` (x64) and/or `.venv-x86` as needed  
2. Installs `requirements.txt` + `requirements-dev.txt` in each venv  
3. Runs **pytest** (`tests/unit`) once  
4. Runs **pip-audit** (fails on known CVEs)  
5. Ensures `assets\icon.ico`  
6. PyInstaller via `save4bucks.spec` per arch (`SAVE4BUCKS_ARCH=x64|x86`)

Skip tests/audit (not recommended):

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -SkipChecks
```

## Manual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/unit -q
pip-audit -r requirements.txt
$env:SAVE4BUCKS_ARCH = 'x64'
pyinstaller --noconfirm save4bucks.spec
```

## CI / automated release

On every push to `main`, GitHub Actions runs tests + security scans, bumps the patch version in `src/__init__.py`, builds **both** `Save4Bucks-x64.exe` and `Save4Bucks-x86.exe`, and publishes a GitHub Release (`vX.Y.Z`) with both artifacts.

Details: [docs/CI.md](docs/CI.md).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Antivirus quarantines exe | Exclusion for `dist\`, or run from source |
| pip-audit fails | Upgrade/pin fixed package versions |
| “No profiles found” | Saves under Documents (often OneDrive) |
| Icon missing | Confirm `assets\icon.ico` before build |
| No 32-bit Python | Install Python 3.11 Windows **32-bit**, or pass `-PythonX86` |
| Wrong bitness EXE | PyInstaller matches the interpreter — use x86 Python for `-Arch x86` |
