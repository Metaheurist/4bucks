# Setup

## Requirements

- Windows 10/11
- Python 3.11+
- GTA IV Complete Edition saves under Documents Profiles

## From source

```powershell
cd "C:\Users\OnceU\OneDrive\Documents\GitHub\4bucks"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python -m src
```

## EXE

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
.\dist\Save4Bucks.exe
```

## Notes

- Close `GTAIV.exe` before writing.
- If profiles are missing, launch CE once and save.
- OneDrive may host Documents — that is normal for CE.
