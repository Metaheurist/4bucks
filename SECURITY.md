# Security — Save 4Bucks

## Threat model

Save 4Bucks is an **offline**, local Windows tool. It reads/writes your own `SGTA4xx` save files. It does **not** open network sockets for gameplay, inject into `GTAIV.exe`, or ship remote update channels.

## Dependencies / CVE

- Runtime deps are pinned in `requirements.txt`.
- Dev/audit deps in `requirements-dev.txt`.
- `build.ps1` runs **`pip-audit`** against installed packages and fails the build on known CVEs.
- CI also runs **Gitleaks** (secret scan) and **`pip-audit`** before every release — see [docs/CI.md](docs/CI.md).

```powershell
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\.venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt
```

## Privileges

- No admin required for normal CE Profiles under Documents.
- OneDrive / Controlled Folder Access may block writes — fix folder permissions rather than disabling security wholesale.
- Antivirus may flag PyInstaller EXEs; exclude `dist\` if needed.

## Backups

Autobackup writes copies beside the save (`.backup`) and under `backups\` next to the app (or EXE). Treat those files as sensitive save data.

## What we do not do

- Process memory read/write
- DLL injection / ASI trainers
- Shipping third-party offset dumps for live cheats
