# Security

Authoritative security guide for this repository.

## Threat model

4Bucks is an offline, local Windows tool. It reads and writes the user's own `SGTA4xx` save files. It does not open network sockets for gameplay, inject into `GTAIV.exe`, or ship remote update channels.

## Dependencies / CVE

- Runtime dependencies are pinned in `requirements.txt` (includes Flet for the desktop UI).
- Dev/audit dependencies are in `requirements-dev.txt`.
- `build.ps1` runs `pip-audit` and fails the build on known CVEs.
- CI runs Gitleaks (secret scan; README/docs allowlisted for badge false positives) and `pip-audit` before every release - see [build-test-and-ci.md](build-test-and-ci.md).

```powershell
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\.venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt
```

## Privileges

- Admin rights are not required for CE Profiles under Documents.
- OneDrive or Controlled Folder Access may block writes; adjust folder permissions rather than disabling security wholesale.
- Antivirus may flag `flet pack` / PyInstaller EXEs; exclude `dist\` if needed.

## Backups

Autobackup writes copies beside the save (`.backup`) and under `backups\` next to the app or EXE. Treat those files as sensitive save data.

## Out of scope

- Process memory read/write
- DLL injection / ASI trainers
- Shipping third-party offset dumps for live cheats

<a id="nav-security-notes"></a>

## Notes

- Do not commit secrets (none are required for this offline tool).
- Prefer CE Profiles paths; GFWL paths are refused by the version gate.
- Keep Autobackup enabled unless another backup strategy is in place.
