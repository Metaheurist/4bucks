<a id="nav-installation"></a>

## ⚙️ Installation

### Prerequisites

- Windows 10/11
- Python **3.11+** x64 on PATH (run from source / 64-bit EXE)
- Python **3.11+** x86 for 32-bit EXE (`py -3.11-32` or python.org 32-bit installer)
- GTA IV Complete Edition saves under Documents Profiles

### Run from source

```powershell
cd "C:\Users\OnceU\OneDrive\Documents\GitHub\4bucks"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python -m src
```

### Run the EXE

1. Download **Save4Bucks-x64.exe** / **Save4Bucks-x86.exe** from [GitHub Releases](https://github.com/Metaheurist/4bucks/releases), **or** build locally (below).
2. Launch the EXE matching your Windows architecture.
3. Quit **GTAIV.exe** before writing saves.

### Build EXE (both architectures)

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

| Output | Arch |
|--------|------|
| `dist\Save4Bucks-x64.exe` | 64-bit |
| `dist\Save4Bucks-x86.exe` | 32-bit |

Single arch / custom interpreters:

```powershell
.\build.ps1 -Arch x64
.\build.ps1 -Arch x86
.\build.ps1 -Arch All -PythonX64 "C:\Path\python.exe" -PythonX86 "C:\Path\python.exe"
.\build.ps1 -SkipChecks   # not recommended
```

`build.ps1` creates `.venv` / `.venv-x86`, installs deps, runs **pytest** + **pip-audit**, ensures `assets\icon.ico`, then PyInstaller (`SAVE4BUCKS_ARCH`).

Details: **[build-test-and-ci.md](build-test-and-ci.md)**.

### Notes

- Close `GTAIV.exe` before writing.
- If profiles are missing, launch CE once and save.
- OneDrive may host Documents - that is normal for CE.
- Antivirus may quarantine PyInstaller EXEs; exclude `dist\` if needed.
