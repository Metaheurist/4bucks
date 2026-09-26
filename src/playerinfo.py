"""Shared PlayerInfo (Block 1) offset helpers for CE saves."""

from __future__ import annotations

import struct
from dataclasses import dataclass

PLAYERINFO_SIZE = 192

# Offsets relative to PlayerInfo start (after BLOCK + 0x14)
OFF_MONEY = 0x08
OFF_DISPLAY_MONEY = 0x10
OFF_MAX_HEALTH = 0x24
OFF_MAX_ARMOUR = 0x26
OFF_HEALTH = 0x50
OFF_ARMOUR = 0x54
OFF_CURRENT_WEAPON = 0x58
OFF_WEAPON_SLOTS = 0x5C
OFF_WEAPON_AMMO = 0x84
WEAPON_SLOT_COUNT = 10


@dataclass(frozen=True)
class PlayerInfoLoc:
    """Absolute file offsets for the PlayerInfo region."""

    block_offset: int
    base: int  # absolute offset of PlayerInfo start

    def abs(self, rel: int) -> int:
        return self.base + rel


def parse_blocks(data: bytes) -> list[tuple[int, int, int]]:
    """Return list of (index, offset, size) for BLOCK chunks."""
    off = 0x110
    blocks: list[tuple[int, int, int]] = []
    for i in range(40):
        if off + 9 > len(data):
            break
        if data[off : off + 5] != b"BLOCK":
            break
        size = struct.unpack_from("<I", data, off + 5)[0]
        if size < 9 or off + size > len(data):
            break
        blocks.append((i, off, size))
        off += size
    return blocks


def playerinfo_loc(data: bytes) -> PlayerInfoLoc:
    """Locate PlayerInfo start; raise if Block 1 / size marker is wrong."""
    blocks = parse_blocks(data)
    if len(blocks) < 2:
        raise RuntimeError(f"Expected PlayerInfo as block 1, got {len(blocks)} blocks")
    _, bo, bs = blocks[1]
    block = data[bo : bo + bs]
    if len(block) < 5 + 0x14 + OFF_WEAPON_AMMO + WEAPON_SLOT_COUNT * 2:
        raise RuntimeError(f"PlayerInfo block too short ({len(block)} bytes)")
    const = struct.unpack_from("<I", block, 5 + 0x10)[0]
    if const != PLAYERINFO_SIZE:
        raise RuntimeError(
            f"Unexpected PlayerInfo size marker {const} (expected {PLAYERINFO_SIZE})"
        )
    return PlayerInfoLoc(block_offset=bo, base=bo + 5 + 0x14)
