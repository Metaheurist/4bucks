# Testing

## Unit tests

```powershell
cd "C:\Users\OnceU\OneDrive\Documents\GitHub\4bucks"
.\.venv\Scripts\python.exe -m pytest tests/unit -q
```

Covers:

- parse / read / set / add money on synthetic CE fixtures  
- version gate (bad version, magic, PlayerInfo)  
- dual Autobackup paths + fail-closed abort  
- slot listing skips `*.backup`

## Manual checklist

1. Quit GTA IV.  
2. Note HUD money on a manual slot.  
3. Set money in Save 4Bucks; confirm chip `v57 · OK to edit`.  
4. Confirm `SGTA4xx.backup` beside save and a file under `backups\`.  
5. Load slot in-game; verify cash.  

## pip-audit

```powershell
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
```

`build.ps1` runs pytest + pip-audit before packing.
