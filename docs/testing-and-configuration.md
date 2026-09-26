# Testing and configuration

## Unit tests

```powershell
cd path\to\4bucks
.\.venv\Scripts\python.exe -m pytest tests/unit -q
```

Coverage:

- Parse / read / set / add money on synthetic CE fixtures
- Weapons loadout and ammo round-trip; stock vs mod classification
- Health / armour / max health / max armour round-trip
- Write profile (`PLAYERINFO_INPLACE_V57`) and version gate refusals
- Dual Autobackup paths and fail-closed abort
- Slot listing skips `*.backup`

Unit tests do not drive the Flet UI; they cover save, backup, and version logic only.

## Manual checklist

1. Quit GTA IV.
2. Note HUD money (and optionally health/weapons) on a manual slot.
3. Edit in Save 4Bucks; confirm chip `v57 · CE · … · PlayerInfo in-place · OK`.
4. Confirm `SGTA4xx.backup` beside the save and a file under `backups\`.
5. Load the slot in-game and verify values.

## pip-audit

```powershell
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\.venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt
```

`build.ps1` runs pytest and pip-audit before packing. CI also runs Gitleaks - see [build-test-and-ci.md](build-test-and-ci.md).
