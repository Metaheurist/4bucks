"""Edit player money in a GTA IV Complete Edition save (SGTA4xx)."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path

from .backup import BackupResult, create_dual_backup
from .versioning import WriteCheck, check_write


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


def read_money(data: bytes) -> tuple[int, int, int, int]:
    """Return money, display_money, money_abs_off, display_abs_off."""
    blocks = parse_blocks(data)
    if len(blocks) < 2:
        raise RuntimeError(f"Expected PlayerInfo as block 1, got {len(blocks)} blocks")
    _, bo, bs = blocks[1]
    block = data[bo : bo + bs]
    # After "BLOCK" (5 bytes), wiki PlayerInfo table:
    # +0x00 size, +0x04 float[3] coords, +0x10 = 192, +0x14 = PlayerInfo
    # money at PlayerInfo+0x08, display at +0x10
    base = 5
    const = struct.unpack_from("<I", block, base + 0x10)[0]
    if const != 192:
        raise RuntimeError(f"Unexpected PlayerInfo size marker {const} (expected 192)")
    money_rel = base + 0x14 + 0x08
    disp_rel = base + 0x14 + 0x10
    money = struct.unpack_from("<I", block, money_rel)[0]
    disp = struct.unpack_from("<I", block, disp_rel)[0]
    return money, disp, bo + money_rel, bo + disp_rel


def read_money_file(path: Path) -> tuple[int, int]:
    money, disp, _, _ = read_money(path.read_bytes())
    return money, disp


def set_money(
    path: Path,
    amount: int,
    *,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> tuple[int, int, BackupResult | None, WriteCheck]:
    """
    Set money and display money.
    Returns (old_money, new_money, backup_result_or_None, write_check).
    """
    if amount < 0 or amount > 0xFFFFFFFF:
        raise ValueError("Amount must be between 0 and 4294967295")

    path = Path(path)
    raw = path.read_bytes()
    check = check_write(path, raw, allow_non_ce_path=allow_non_ce_path)
    if not check.allowed:
        raise RuntimeError(check.reason)

    data = bytearray(raw)
    old_m, old_d, m_off, d_off = read_money(bytes(data))

    bak: BackupResult | None = None
    if backup:
        bak = create_dual_backup(path, old_m, base=app_base)

    struct.pack_into("<I", data, m_off, amount)
    struct.pack_into("<I", data, d_off, amount)
    path.write_bytes(data)
    new_m, new_d, _, _ = read_money(bytes(data))
    if new_m != amount or new_d != amount:
        raise RuntimeError("Write verification failed")
    return old_m, new_m, bak, check


def add_money(
    path: Path,
    delta: int,
    *,
    backup: bool = True,
    allow_non_ce_path: bool = False,
    app_base: Path | None = None,
) -> tuple[int, int, BackupResult | None, WriteCheck]:
    current, _ = read_money_file(path)
    target = max(0, min(0xFFFFFFFF, current + delta))
    return set_money(
        path,
        target,
        backup=backup,
        allow_non_ce_path=allow_non_ce_path,
        app_base=app_base,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Save 4Bucks CLI")
    ap.add_argument("save", type=Path)
    ap.add_argument("--amount", type=int, default=500_000)
    ap.add_argument("--read-only", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--allow-non-ce-path", action="store_true")
    args = ap.parse_args()
    if args.read_only:
        from .versioning import inspect_save, status_chip

        data = args.save.read_bytes()
        ident = inspect_save(args.save, data)
        m, d, mo, do = read_money(data)
        print(status_chip(ident))
        print(f"money={m} display={d} @ 0x{mo:X} / 0x{do:X}")
        return
    old, new, bak, check = set_money(
        args.save,
        args.amount,
        backup=not args.no_backup,
        allow_non_ce_path=args.allow_non_ce_path,
    )
    print(f"{args.save.name}: {old} -> {new}")
    if bak:
        print(f"backup beside: {bak.beside}")
        print(f"backup app:    {bak.app_copy}")
    if check.warnings:
        for w in check.warnings:
            print(f"warning: {w}")


if __name__ == "__main__":
    main()
