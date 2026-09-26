"""Read/write player health, armour, and max health/armour in CE saves."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .backup import BackupResult, create_dual_backup
from .playerinfo import (
    OFF_ARMOUR,
    OFF_HEALTH,
    OFF_MAX_ARMOUR,
    OFF_MAX_HEALTH,
    playerinfo_loc,
)
from .versioning import WriteCheck, check_write

# Sensible UI defaults for current health/armour floats
UI_CLAMP_MIN = 0.0
UI_CLAMP_MAX = 200.0
# Max health/armour are uint16 in the save
UI_MAX_CLAMP = 65535


@dataclass(frozen=True)
class Vitality:
    health: float
    armour: float
    max_health: int
    max_armour: int


def read_vitality(data: bytes) -> Vitality:
    loc = playerinfo_loc(data)
    health = struct.unpack_from("<f", data, loc.abs(OFF_HEALTH))[0]
    armour = struct.unpack_from("<f", data, loc.abs(OFF_ARMOUR))[0]
    max_health = struct.unpack_from("<H", data, loc.abs(OFF_MAX_HEALTH))[0]
    max_armour = struct.unpack_from("<H", data, loc.abs(OFF_MAX_ARMOUR))[0]
    return Vitality(health, armour, max_health, max_armour)


def read_vitality_file(path: Path) -> Vitality:
    return read_vitality(path.read_bytes())


def set_vitality(
    path: Path,
    health: float,
    armour: float,
    max_health: int,
    max_armour: int,
    *,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> tuple[Vitality, Vitality, BackupResult | None, WriteCheck]:
    """
    Set current health/armour floats and max health/armour uint16s.
    Returns (old, new, backup, write_check).
    """
    if not (health == health) or not (armour == armour):  # NaN check
        raise ValueError("Health and armour must be finite numbers")
    if abs(health) == float("inf") or abs(armour) == float("inf"):
        raise ValueError("Health and armour must be finite numbers")
    if max_health < 0 or max_health > 0xFFFF:
        raise ValueError("Max health must be 0..65535")
    if max_armour < 0 or max_armour > 0xFFFF:
        raise ValueError("Max armour must be 0..65535")

    path = Path(path)
    raw = path.read_bytes()
    check = check_write(path, raw, allow_non_ce_path=allow_non_ce_path)
    if not check.allowed:
        raise RuntimeError(check.reason)

    old = read_vitality(raw)
    data = bytearray(raw)
    loc = playerinfo_loc(bytes(data))

    bak: BackupResult | None = None
    if backup:
        from .save_money import read_money

        old_m, _, _, _ = read_money(raw)
        bak = create_dual_backup(path, old_m, base=app_base)

    struct.pack_into("<H", data, loc.abs(OFF_MAX_HEALTH), int(max_health))
    struct.pack_into("<H", data, loc.abs(OFF_MAX_ARMOUR), int(max_armour))
    struct.pack_into("<f", data, loc.abs(OFF_HEALTH), float(health))
    struct.pack_into("<f", data, loc.abs(OFF_ARMOUR), float(armour))
    path.write_bytes(data)
    new = read_vitality(bytes(data))
    if (
        abs(new.health - health) > 1e-3
        or abs(new.armour - armour) > 1e-3
        or new.max_health != max_health
        or new.max_armour != max_armour
    ):
        raise RuntimeError("Write verification failed")
    return old, new, bak, check
