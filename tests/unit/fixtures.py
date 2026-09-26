"""Shared fixtures for Save 4Bucks unit tests."""

from __future__ import annotations

import struct
from pathlib import Path


def make_minimal_save(
    *,
    version: int = 57,
    money: int = 413_388,
    display: int | None = None,
    playerinfo_const: int = 192,
    magic: bytes = b"SAVE",
) -> bytes:
    """Build a tiny but parseable SGTA4-like buffer (metadata + 2 BLOCKs)."""
    if display is None:
        display = money

    b0 = bytearray(0xB9)
    b0[0:5] = b"BLOCK"
    struct.pack_into("<I", b0, 5, 0xB9)

    b1 = bytearray(0xD4)
    b1[0:5] = b"BLOCK"
    struct.pack_into("<I", b1, 5, 0xD4)
    struct.pack_into("<I", b1, 5 + 0x10, playerinfo_const)
    struct.pack_into("<I", b1, 5 + 0x14 + 0x08, money)
    struct.pack_into("<I", b1, 5 + 0x14 + 0x10, display)

    meta = bytearray(0x110)
    struct.pack_into("<I", meta, 0, version)
    total = 0x110 + len(b0) + len(b1)
    struct.pack_into("<I", meta, 4, total)
    meta[0x0C:0x10] = magic
    title = "TEST\x00".encode("utf-16-le")
    meta[0x10 : 0x10 + len(title)] = title

    return bytes(meta) + bytes(b0) + bytes(b1)


def write_ce_save(tmp: Path, name: str = "SGTA400", **kwargs) -> Path:
    """Write fixture under a fake CE Profiles path."""
    profile = tmp / "Documents" / "Rockstar Games" / "GTA IV" / "Profiles" / "ABCD1234"
    profile.mkdir(parents=True, exist_ok=True)
    path = profile / name
    path.write_bytes(make_minimal_save(**kwargs))
    return path
