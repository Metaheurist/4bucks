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
  → save_garage.py       Block 4 StoredCar (safehouse parking)
  → safehouse_parking.py curated IV parking poses
  → vehicles_catalog.py  vehicles.ide index → name
  → carcols_catalog.py   carcols.dat col table → paint swatch names
  → weapons_catalog.py   stock / episodic IDs
  → weapon_detect.py     Stock vs Mod (+ optional weaponinfo.xml)
  → backup.py            dual Autobackup
  → settings.py          Autobackup / also-autosave
```

```mermaid
flowchart LR
  menu[Radial menu]
  select[Profile + slot]
  chip[Status chip + technique]
  gate[Refuse if game or version fail]
  bak[Dual Autobackup fail-closed]
  patch[In-place PlayerInfo or Garages patch]
  menu --> select --> chip --> gate --> bak --> patch
```

## Data flow

1. Radial home menu → Money / Weapons / Vitality / Garage (ring) or Settings (center).
2. User selects profile and slot.
3. Status chip from `inspect_save` / `check_write` / `resolve_write_profile`.
4. On apply: refuse if the game is running or the write technique is unsupported.
5. Optional confirm for non-CE path warnings.
6. If Autobackup: copy beside the save and under `app/backups/` (fail closed).
7. Patch PlayerInfo or Block 4 StoredCar fields; re-read to verify.

## App directory

- Frozen EXE: folder containing `Save4Bucks-x64.exe` / `Save4Bucks-x86.exe`
- Source: repository root

Used for `backups/` and `save4bucks_settings.json`.

## UI stack

Flet app (`ft.run` in `src/app.py`): outlined Liberty City panels, `AnimatedSwitcher` transitions, theme focus colour, radial menu with hover scale, Esc and digit shortcuts, selectable status text. Save logic remains in pure Python modules so CLI and tests do not require Flet.
