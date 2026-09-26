"""Shared fixtures for 4Bucks unit tests."""

from __future__ import annotations

import struct
from pathlib import Path


def _pack_stored_car(
    *,
    model: int,
    x: float,
    y: float,
    z: float,
    rot: tuple[int, int, int] = (0, 0, 0),
    colors: tuple[int, int, int, int] = (0, 0, 0, 0),
    flags: int = 1,
) -> bytes:
    from src.save_garage import _pack_car

    return _pack_car(
        model=model,
        x=x,
        y=y,
        z=z,
        rot=rot,
        colors=colors,
        flags=flags,
    )


def make_garages_block(
    cars: list[bytes] | None = None,
    *,
    safehouse_count: int = 5,
) -> bytes:
    """Build Block 4 payload+header sized like CE (StoredCar[20] + Garage[40] pad)."""
    # Payload layout: header through 0x0E, cars @ 0x0F, garages @ 0x05AF
    payload_len = 0x0F + 20 * 72 + 40 * 72  # 0x10EF
    payload = bytearray(payload_len)
    struct.pack_into("<I", payload, 0x0B, safehouse_count)
    if cars:
        for i, raw in enumerate(cars[:20]):
            if len(raw) != 72:
                raise ValueError("each car must be 72 bytes")
            off = 0x0F + i * 72
            payload[off : off + 72] = raw
    block_size = 9 + payload_len  # BLOCK + size + payload
    block = bytearray(block_size)
    block[0:5] = b"BLOCK"
    struct.pack_into("<I", block, 5, block_size)
    block[9:] = payload
    return bytes(block)


def make_minimal_save(
    *,
    version: int = 57,
    money: int = 413_388,
    display: int | None = None,
    playerinfo_const: int = 192,
    magic: bytes = b"SAVE",
    health: float = 200.0,
    armour: float = 50.0,
    max_health: int = 200,
    max_armour: int = 100,
    weapons: list[int] | None = None,
    ammo: list[int] | None = None,
    current_weapon: int = 0,
    with_garages: bool = False,
    garage_cars: list[bytes] | None = None,
) -> bytes:
    """Build a tiny but parseable SGTA4-like buffer (metadata + BLOCKs)."""
    if display is None:
        display = money
    if weapons is None:
        weapons = [0] * 10
        weapons[0] = 0
        weapons[2] = 7  # PISTOL
        weapons[4] = 14  # AK47
    if ammo is None:
        ammo = [0] * 10
        ammo[2] = 50
        ammo[4] = 120
    while len(weapons) < 10:
        weapons.append(0)
    while len(ammo) < 10:
        ammo.append(0)

    b0 = bytearray(0xB9)
    b0[0:5] = b"BLOCK"
    struct.pack_into("<I", b0, 5, 0xB9)

    # Need room through weapon ammo (PlayerInfo+0x84+20)
    b1_size = 0xD4
    b1 = bytearray(b1_size)
    b1[0:5] = b"BLOCK"
    struct.pack_into("<I", b1, 5, b1_size)
    struct.pack_into("<I", b1, 5 + 0x10, playerinfo_const)
    pi = 5 + 0x14
    struct.pack_into("<I", b1, pi + 0x08, money)
    struct.pack_into("<I", b1, pi + 0x10, display)
    struct.pack_into("<H", b1, pi + 0x24, max_health)
    struct.pack_into("<H", b1, pi + 0x26, max_armour)
    struct.pack_into("<f", b1, pi + 0x50, health)
    struct.pack_into("<f", b1, pi + 0x54, armour)
    struct.pack_into("<I", b1, pi + 0x58, current_weapon)
    for i in range(10):
        struct.pack_into("<I", b1, pi + 0x5C + i * 4, weapons[i])
        struct.pack_into("<H", b1, pi + 0x84 + i * 2, ammo[i])

    # Optional stub blocks 2-3 so Garages is index 4
    extra = b""
    if with_garages or garage_cars is not None:
        for _ in range(2):
            stub = bytearray(16)
            stub[0:5] = b"BLOCK"
            struct.pack_into("<I", stub, 5, 16)
            extra += bytes(stub)
        extra += make_garages_block(garage_cars)

    meta = bytearray(0x110)
    struct.pack_into("<I", meta, 0, version)
    total = 0x110 + len(b0) + len(b1) + len(extra)
    struct.pack_into("<I", meta, 4, total)
    meta[0x0C:0x10] = magic
    title = "TEST\x00".encode("utf-16-le")
    meta[0x10 : 0x10 + len(title)] = title

    # CE End marker at EOF (pre-CE fixtures append a GFWL-style trail separately).
    return bytes(meta) + bytes(b0) + bytes(b1) + extra + b"END\x00"


def make_pre_ce_save(**kwargs) -> bytes:
    """Minimal save with a GFWL-style End signature trail (pre-CE family)."""
    return make_minimal_save(**kwargs)[:-4] + b"END\x00" + bytes.fromhex(
        "C5E7F3F3CDCDCDCD08000000"
    )


def write_ce_save(tmp: Path, name: str = "SGTA400", **kwargs) -> Path:
    """Write fixture under a fake CE Profiles path."""
    profile = tmp / "Documents" / "Rockstar Games" / "GTA IV" / "Profiles" / "ABCD1234"
    profile.mkdir(parents=True, exist_ok=True)
    path = profile / name
    path.write_bytes(make_minimal_save(**kwargs))
    return path


def write_pre_ce_save(tmp: Path, name: str = "SGTA400", **kwargs) -> Path:
    """Write a pre-CE-shaped fixture under a fake CE Profiles path."""
    profile = tmp / "Documents" / "Rockstar Games" / "GTA IV" / "Profiles" / "ABCD1234"
    profile.mkdir(parents=True, exist_ok=True)
    path = profile / name
    path.write_bytes(make_pre_ce_save(**kwargs))
    return path
