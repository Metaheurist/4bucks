"""Read/write GTA IV Block 4 StoredCar garage slots (safehouse parking)."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .backup import BackupResult, create_dual_backup
from .playerinfo import parse_blocks
from .safehouse_parking import (
    SAFEHOUSE_BY_ID,
    SAFEHOUSES,
    ParkingPose,
    nearest_safehouse,
    spot_occupied,
)
from .versioning import WriteCheck, WriteTechnique, check_write

STORED_CAR_SIZE = 72
STORED_CAR_COUNT = 20
OFF_STORED_CARS = 0x0F
# Observed on valid CE cars; wiki flags@0x48 do not fit in 72 bytes.
OFF_SLOT_MARK = 0x30  # uint16, typically 0x0011 when occupied
OFF_MODEL = 0x10
OFF_COLORS = 0x32
OFF_EXTRAS = 0x38
OFF_LIVERY = 0x3C
OFF_ROT = 0x43
OFF_FLAGS = 0x46  # uint16: Valid + proof bits (editor-managed)

FLAG_VALID = 0x0001
FLAG_BULLET = 0x0008
FLAG_FIRE = 0x0010
FLAG_EXPLOSION = 0x0020
FLAG_COLLISION = 0x0040
FLAG_MELEE = 0x0080

SLOT_MARK_OCCUPIED = 0x0011


@dataclass(frozen=True)
class StoredCar:
    index: int
    model: int
    x: float
    y: float
    z: float
    handling: int
    colors: tuple[int, int, int, int]
    extras: int
    livery: int
    rot: tuple[int, int, int]
    flags: int
    raw: bytes

    @property
    def valid(self) -> bool:
        return self.model != 0 or bool(self.flags & FLAG_VALID)

    @property
    def bullet_proof(self) -> bool:
        return bool(self.flags & FLAG_BULLET)

    @property
    def fire_proof(self) -> bool:
        return bool(self.flags & FLAG_FIRE)

    @property
    def explosion_proof(self) -> bool:
        return bool(self.flags & FLAG_EXPLOSION)

    @property
    def collision_proof(self) -> bool:
        return bool(self.flags & FLAG_COLLISION)

    @property
    def melee_proof(self) -> bool:
        return bool(self.flags & FLAG_MELEE)


@dataclass(frozen=True)
class GarageLoc:
    block_offset: int
    payload_offset: int
    block_size: int

    def car_abs(self, index: int) -> int:
        return self.payload_offset + OFF_STORED_CARS + index * STORED_CAR_SIZE


@dataclass(frozen=True)
class SafehouseSlot:
    """One curated parking spot at a safehouse (empty or occupied)."""

    safehouse_id: str
    safehouse_name: str
    spot_index: int
    pose: ParkingPose
    car: StoredCar | None


def garages_loc(data: bytes) -> GarageLoc:
    blocks = parse_blocks(data)
    if len(blocks) <= 4:
        raise RuntimeError(f"Expected Garages as block 4, got {len(blocks)} blocks")
    _, bo, bs = blocks[4]
    # BLOCK (5) + size dword (4)
    payload = bo + 9
    need = OFF_STORED_CARS + STORED_CAR_COUNT * STORED_CAR_SIZE
    if bs < 9 + need:
        raise RuntimeError(f"Garages block too short (size 0x{bs:X})")
    return GarageLoc(bo, payload, bs)


def _unpack_car(index: int, raw: bytes) -> StoredCar:
    if len(raw) != STORED_CAR_SIZE:
        raise ValueError("StoredCar must be 72 bytes")
    x, y, z = struct.unpack_from("<fff", raw, 0)
    handling = struct.unpack_from("<I", raw, 0x0C)[0]
    model = struct.unpack_from("<H", raw, OFF_MODEL)[0]
    colors = tuple(raw[OFF_COLORS : OFF_COLORS + 4])  # type: ignore[assignment]
    extras = struct.unpack_from("<I", raw, OFF_EXTRAS)[0]
    livery = struct.unpack_from("<I", raw, OFF_LIVERY)[0]
    rot = (raw[OFF_ROT], raw[OFF_ROT + 1], raw[OFF_ROT + 2])
    flags = struct.unpack_from("<H", raw, OFF_FLAGS)[0]
    return StoredCar(
        index=index,
        model=model,
        x=x,
        y=y,
        z=z,
        handling=handling,
        colors=(colors[0], colors[1], colors[2], colors[3]),
        extras=extras,
        livery=livery,
        rot=rot,
        flags=flags,
        raw=bytes(raw),
    )


def _pack_car(
    *,
    model: int,
    x: float,
    y: float,
    z: float,
    handling: int = 0,
    colors: tuple[int, int, int, int] = (0, 0, 0, 0),
    extras: int = 0,
    livery: int = 0,
    rot: tuple[int, int, int] = (0, 0, 0),
    flags: int = FLAG_VALID,
    template: bytes | None = None,
) -> bytes:
    buf = bytearray(template if template and len(template) == STORED_CAR_SIZE else bytes(STORED_CAR_SIZE))
    struct.pack_into("<fff", buf, 0, float(x), float(y), float(z))
    struct.pack_into("<I", buf, 0x0C, int(handling) & 0xFFFFFFFF)
    struct.pack_into("<H", buf, OFF_MODEL, int(model) & 0xFFFF)
    struct.pack_into("<H", buf, OFF_SLOT_MARK, SLOT_MARK_OCCUPIED if model else 0)
    for i, c in enumerate(colors[:4]):
        buf[OFF_COLORS + i] = int(c) & 0xFF
    struct.pack_into("<I", buf, OFF_EXTRAS, int(extras) & 0xFFFFFFFF)
    struct.pack_into("<I", buf, OFF_LIVERY, int(livery) & 0xFFFFFFFF)
    buf[OFF_ROT] = int(rot[0]) & 0xFF
    buf[OFF_ROT + 1] = int(rot[1]) & 0xFF
    buf[OFF_ROT + 2] = int(rot[2]) & 0xFF
    f = int(flags) & 0xFFFF
    if model:
        f |= FLAG_VALID
    else:
        f &= ~FLAG_VALID
    struct.pack_into("<H", buf, OFF_FLAGS, f)
    return bytes(buf)


def read_stored_cars(data: bytes) -> list[StoredCar]:
    loc = garages_loc(data)
    out: list[StoredCar] = []
    for i in range(STORED_CAR_COUNT):
        abs_off = loc.car_abs(i)
        raw = data[abs_off : abs_off + STORED_CAR_SIZE]
        out.append(_unpack_car(i, raw))
    return out


def read_stored_cars_file(path: Path) -> list[StoredCar]:
    return read_stored_cars(Path(path).read_bytes())


def list_safehouse_slots(data: bytes) -> list[SafehouseSlot]:
    """Curated spots per safehouse with occupying car if present."""
    cars = [c for c in read_stored_cars(data) if c.valid]
    occupied_xy = [(c.x, c.y) for c in cars]
    # Map car -> nearest spot
    car_at: dict[tuple[str, int], StoredCar] = {}
    for c in cars:
        hit = nearest_safehouse(c.x, c.y)
        if hit is None:
            continue
        sh, spot_i = hit
        key = (sh.id, spot_i)
        # Keep first if two claim same spot
        if key not in car_at:
            car_at[key] = c

    slots: list[SafehouseSlot] = []
    for sh in SAFEHOUSES:
        for i, pose in enumerate(sh.spots):
            slots.append(
                SafehouseSlot(
                    safehouse_id=sh.id,
                    safehouse_name=sh.name,
                    spot_index=i,
                    pose=pose,
                    car=car_at.get((sh.id, i)),
                )
            )
    return slots


def proofs_to_flags(
    *,
    bullet: bool = False,
    fire: bool = False,
    explosion: bool = False,
    collision: bool = False,
    melee: bool = False,
    valid: bool = True,
) -> int:
    f = FLAG_VALID if valid else 0
    if bullet:
        f |= FLAG_BULLET
    if fire:
        f |= FLAG_FIRE
    if explosion:
        f |= FLAG_EXPLOSION
    if collision:
        f |= FLAG_COLLISION
    if melee:
        f |= FLAG_MELEE
    return f


def _write_car_bytes(data: bytearray, loc: GarageLoc, index: int, raw: bytes) -> None:
    if not (0 <= index < STORED_CAR_COUNT):
        raise ValueError("StoredCar index out of range")
    if len(raw) != STORED_CAR_SIZE:
        raise ValueError("StoredCar must be 72 bytes")
    abs_off = loc.car_abs(index)
    data[abs_off : abs_off + STORED_CAR_SIZE] = raw


def update_stored_car(
    path: Path,
    index: int,
    *,
    model: int | None = None,
    colors: tuple[int, int, int, int] | None = None,
    extras: int | None = None,
    livery: int | None = None,
    flags: int | None = None,
    clear: bool = False,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> tuple[StoredCar, StoredCar, BackupResult | None, WriteCheck]:
    """Patch one StoredCar in place; preserve pose unless clearing."""
    path = Path(path)
    raw = path.read_bytes()
    check = check_write(path, raw, allow_non_ce_path=allow_non_ce_path)
    if not check.allowed:
        raise RuntimeError(check.reason)

    loc = garages_loc(raw)
    cars = read_stored_cars(raw)
    old = cars[index]
    bak: BackupResult | None = None
    if backup:
        from .save_money import read_money

        old_m, _, _, _ = read_money(raw)
        bak = create_dual_backup(path, old_m, base=app_base)

    data = bytearray(raw)
    if clear:
        packed = bytes(STORED_CAR_SIZE)
    else:
        packed = _pack_car(
            model=old.model if model is None else int(model),
            x=old.x,
            y=old.y,
            z=old.z,
            handling=old.handling,
            colors=old.colors if colors is None else colors,
            extras=old.extras if extras is None else int(extras),
            livery=old.livery if livery is None else int(livery),
            rot=old.rot,
            flags=old.flags if flags is None else int(flags),
            template=old.raw,
        )
    _write_car_bytes(data, loc, index, packed)
    path.write_bytes(data)
    new = read_stored_cars(bytes(data))[index]
    # Annotate technique for callers / status
    check = WriteCheck(
        identity=check.identity,
        allowed=check.allowed,
        reason=check.reason,
        warnings=check.warnings,
        profile=check.profile,
    )
    _ = WriteTechnique.GARAGES_INPLACE_V57  # documented technique used here
    return old, new, bak, check


def spawn_at_safehouse(
    path: Path,
    safehouse_id: str,
    *,
    model: int,
    colors: tuple[int, int, int, int] = (0, 0, 0, 0),
    extras: int = 0,
    livery: int = 0,
    flags: int = FLAG_VALID,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> tuple[StoredCar, BackupResult | None, WriteCheck]:
    """Spawn into the first free curated spot at a safehouse."""
    path = Path(path)
    sh = SAFEHOUSE_BY_ID.get(safehouse_id)
    if sh is None:
        raise ValueError(f"Unknown safehouse id: {safehouse_id}")
    if model <= 0:
        raise ValueError("Model index must be positive")

    raw = path.read_bytes()
    check = check_write(path, raw, allow_non_ce_path=allow_non_ce_path)
    if not check.allowed:
        raise RuntimeError(check.reason)

    cars = read_stored_cars(raw)
    free_global = next((c.index for c in cars if not c.valid), None)
    if free_global is None:
        raise RuntimeError("No free StoredCar slots (20/20 used)")

    occupied = [(c.x, c.y) for c in cars if c.valid]
    free_spot: ParkingPose | None = None
    for pose in sh.spots:
        if not spot_occupied(pose, occupied):
            free_spot = pose
            break
    if free_spot is None:
        raise RuntimeError(f"{sh.name} parking is full")

    bak: BackupResult | None = None
    if backup:
        from .save_money import read_money

        old_m, _, _, _ = read_money(raw)
        bak = create_dual_backup(path, old_m, base=app_base)

    loc = garages_loc(raw)
    data = bytearray(raw)
    packed = _pack_car(
        model=int(model),
        x=free_spot.x,
        y=free_spot.y,
        z=free_spot.z,
        colors=colors,
        extras=extras,
        livery=livery,
        rot=free_spot.rot,
        flags=flags | FLAG_VALID,
    )
    _write_car_bytes(data, loc, free_global, packed)
    path.write_bytes(data)
    new = read_stored_cars(bytes(data))[free_global]
    if not new.valid or new.model != model:
        raise RuntimeError("Spawn write verification failed")
    return new, bak, check


def write_garage_state(
    path: Path,
    cars: list[StoredCar | None],
    *,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> WriteCheck:
    """
    Apply a full 20-slot snapshot.

    Each entry is either a StoredCar to write, or None to clear that index.
    Used by the UI Apply path after in-memory edits.
    """
    path = Path(path)
    if len(cars) != STORED_CAR_COUNT:
        raise ValueError(f"Need exactly {STORED_CAR_COUNT} slots")
    raw = path.read_bytes()
    check = check_write(path, raw, allow_non_ce_path=allow_non_ce_path)
    if not check.allowed:
        raise RuntimeError(check.reason)

    if backup:
        from .save_money import read_money

        old_m, _, _, _ = read_money(raw)
        create_dual_backup(path, old_m, base=app_base)

    loc = garages_loc(raw)
    data = bytearray(raw)
    for i, car in enumerate(cars):
        if car is None or not car.valid:
            packed = bytes(STORED_CAR_SIZE)
        else:
            packed = _pack_car(
                model=car.model,
                x=car.x,
                y=car.y,
                z=car.z,
                handling=car.handling,
                colors=car.colors,
                extras=car.extras,
                livery=car.livery,
                rot=car.rot,
                flags=car.flags | FLAG_VALID,
                template=car.raw,
            )
        _write_car_bytes(data, loc, i, packed)
    path.write_bytes(data)
    return check
