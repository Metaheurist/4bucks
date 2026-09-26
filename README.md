# Save 4Bucks

Windows tool that edits **cash in Grand Theft Auto IV Complete Edition save files** (`SGTA4xx`).

It is an **offline save editor only** — no process memory, no injection, no live godmode/weapons.

Close **GTAIV.exe** before applying changes, then load the edited slot in-game.

Supported: CE with `SAVEGAME_VERSION_NUMBER` **57** (e.g. `1.2.0.59`). See [docs/VERSIONING.md](docs/VERSIONING.md).

## Quick start

### Run from source

```powershell
cd "C:\Users\OnceU\OneDrive\Documents\GitHub\4bucks"
python -m src
```

### Run the EXE

Build once (see [BUILD.md](BUILD.md)), then launch `dist\Save4Bucks-x64.exe` or `dist\Save4Bucks-x86.exe`.

## How to use

1. Quit GTA IV completely.
2. Open **Save 4Bucks**.
3. Pick your Rockstar **Profile**.
4. Select a slot — status chip shows save version / path / OK to edit.
5. Enter an amount → **Set money** or **Add money**.
6. Optional: Autobackup (default on), Also apply to autosave (SGTA412).
7. Start the game and load that save.

## Autobackup

When enabled, each write snapshots the save to:

| Location | Pattern |
|----------|---------|
| Beside the save | `SGTA4xx.backup` |
| App folder | `backups/{profile}_{SGTA4xx}_{timestamp}_m{old}.backup` |

If either copy fails, the money write is **aborted**.

## Docs

| Doc | Topic |
|-----|-------|
| [docs/SETUP.md](docs/SETUP.md) | Install / venv |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Module map |
| [docs/SAVE_FORMAT.md](docs/SAVE_FORMAT.md) | BLOCK / money offsets |
| [docs/VERSIONING.md](docs/VERSIONING.md) | Allowlist / refuse rules |
| [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) | Forum / Steam pitfalls |
| [docs/TESTING.md](docs/TESTING.md) | pytest / audit |
| [docs/CI.md](docs/CI.md) | GitHub Actions / releases |
| [SECURITY.md](SECURITY.md) | CVE / offline policy |
| [BUILD.md](BUILD.md) | PyInstaller |

## Save locations (CE)

```text
%USERPROFILE%\OneDrive\Documents\Rockstar Games\GTA IV\Profiles\<ID>\
%USERPROFILE%\Documents\Rockstar Games\GTA IV\Profiles\<ID>\
```

| File | Meaning |
|------|---------|
| `SGTA400` | Manual slot 1 |
| `SGTA401`–`SGTA411` | Slots 2–12 |
| `SGTA412` | Autosave (IV) |
| `SGTA413` / `SGTA414` | TLAD / TBoGT autosave |

## CLI

```powershell
python -m src.save_money "PATH\TO\SGTA412" --read-only
python -m src.save_money "PATH\TO\SGTA412" --amount 500000
```

## Safety

- Warns if `GTAIV.exe` is running.
- Version gate + PlayerInfo checks before write.
- Dual Autobackup by default.
- Verified money layout on CE `1.2.0.59` (save version 57).
