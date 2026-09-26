# Architecture

## Module map

```text
UI (app.py - Flet multi-view)
  → detect.py            Profiles / slots / game running
  → versioning.py        WriteTechnique / SaveWriteProfile / gates
  → playerinfo.py        BLOCK parse + PlayerInfo locator
  → save_money.py        money + display money
  → save_weapons.py      weapon IDs + ammo
  → save_vitality.py     health / armour floats + max uint16s
  → weapons_catalog.py   stock / episodic IDs
  → weapon_detect.py     Stock vs Mod (+ optional weaponinfo.xml)
  → backup.py            dual Autobackup
  → settings.py          Autobackup / also-autosave
```

```mermaid
flowchart LR
  menu[Startup menu]
  select[Profile + slot]
  chip[Status chip + technique]
  gate[Refuse if game or version fail]
  bak[Dual Autobackup fail-closed]
  patch[PlayerInfo in-place patch]
  menu --> select --> chip --> gate --> bak --> patch
```

## Data flow

1. Startup menu → Money / Weapons / Vitality / Settings.
2. User selects profile and slot.
3. Status chip from `inspect_save` / `check_write` / `resolve_write_profile`.
4. On apply: refuse if the game is running or the write technique is unsupported.
5. Optional confirm for non-CE path warnings.
6. If Autobackup: copy beside the save and under `app/backups/` (fail closed).
7. Patch PlayerInfo fields; re-read to verify.

## App directory

- Frozen EXE: folder containing `Save4Bucks-x64.exe` / `Save4Bucks-x86.exe`
- Source: repository root

Used for `backups/` and `save4bucks_settings.json`.

## UI stack

Flet app (`ft.run` in `src/app.py`): outlined Liberty City panels, `AnimatedSwitcher` transitions, theme focus colour, focusable menu buttons, Esc and digit shortcuts, selectable status text. Save logic remains in pure Python modules so CLI and tests do not require Flet.
