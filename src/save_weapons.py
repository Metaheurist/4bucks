"""Read/write player weapon slots and ammo in CE saves."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .backup import BackupResult, create_dual_backup
from .playerinfo import (
    OFF_CURRENT_WEAPON,
    OFF_WEAPON_AMMO,
    OFF_WEAPON_SLOTS,
    WEAPON_SLOT_COUNT,
    playerinfo_loc,
)
from .versioning import WriteCheck, check_write
from .weapon_detect import DetectedWeapon, classify_loadout


@dataclass(frozen=True)
class Loadout:
    current_slot: int
    weapon_ids: tuple[int, ...]
    ammo: tuple[int, ...]
    detected: tuple[DetectedWeapon, ...]


def read_loadout(data: bytes) -> Loadout:
    loc = playerinfo_loc(data)
    current = struct.unpack_from("<I", data, loc.abs(OFF_CURRENT_WEAPON))[0]
    weapons: list[int] = []
    ammo: list[int] = []
    for i in range(WEAPON_SLOT_COUNT):
        weapons.append(struct.unpack_from("<I", data, loc.abs(OFF_WEAPON_SLOTS) + i * 4)[0])
        ammo.append(struct.unpack_from("<H", data, loc.abs(OFF_WEAPON_AMMO) + i * 2)[0])
    detected = tuple(classify_loadout(weapons))
    return Loadout(current, tuple(weapons), tuple(ammo), detected)


def read_loadout_file(path: Path) -> Loadout:
    return read_loadout(path.read_bytes())


def write_loadout(
    path: Path,
    weapon_ids: list[int] | tuple[int, ...],
    ammo: list[int] | tuple[int, ...],
    *,
    current_slot: int | None = None,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> tuple[Loadout, Loadout, BackupResult | None, WriteCheck]:
    """
    Write 10 weapon IDs + ammo. Returns (old, new, backup, write_check).
    """
    if len(weapon_ids) != WEAPON_SLOT_COUNT or len(ammo) != WEAPON_SLOT_COUNT:
        raise ValueError(f"Need exactly {WEAPON_SLOT_COUNT} weapons and ammo values")
    for a in ammo:
        if a < 0 or a > 0xFFFF:
            raise ValueError("Ammo must be 0..65535")
    for w in weapon_ids:
        if w < 0 or w > 0xFFFFFFFF:
            raise ValueError("Weapon id out of range")

    path = Path(path)
    raw = path.read_bytes()
    check = check_write(path, raw, allow_non_ce_path=allow_non_ce_path)
    if not check.allowed:
        raise RuntimeError(check.reason)

    old = read_loadout(raw)
    data = bytearray(raw)
    loc = playerinfo_loc(bytes(data))

    bak: BackupResult | None = None
    if backup:
        from .save_money import read_money

        old_m, _, _, _ = read_money(raw)
        bak = create_dual_backup(path, old_m, base=app_base)

    if current_slot is not None:
        if current_slot < 0 or current_slot > 0xFFFFFFFF:
            raise ValueError("current_slot out of range")
        struct.pack_into("<I", data, loc.abs(OFF_CURRENT_WEAPON), current_slot)

    for i in range(WEAPON_SLOT_COUNT):
        struct.pack_into("<I", data, loc.abs(OFF_WEAPON_SLOTS) + i * 4, int(weapon_ids[i]))
        struct.pack_into("<H", data, loc.abs(OFF_WEAPON_AMMO) + i * 2, int(ammo[i]))

    path.write_bytes(data)
    new = read_loadout(bytes(data))
    if new.weapon_ids != tuple(weapon_ids) or new.ammo != tuple(ammo):
        raise RuntimeError("Write verification failed")
    return old, new, bak, check
