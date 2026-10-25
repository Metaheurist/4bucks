#!/usr/bin/env python3
"""Sanity-check a packed Save4Bucks EXE: PE header, CPU architecture, and size.

Usage: python scripts/ci/verify_exe.py dist/Save4Bucks-x64.exe --arch x64 [--min-mb 20]
Writes a SHA-256 line to stdout so CI can publish checksums.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

MACHINE = {"x64": 0x8664, "x86": 0x014C}


def pe_machine(blob: bytes) -> int:
    if blob[:2] != b"MZ":
        raise ValueError("missing MZ header")
    pe_off = struct.unpack_from("<I", blob, 0x3C)[0]
    if blob[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise ValueError("missing PE signature")
    return struct.unpack_from("<H", blob, pe_off + 4)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("--arch", choices=sorted(MACHINE), required=True)
    parser.add_argument("--min-mb", type=float, default=20.0)
    args = parser.parse_args()

    if not args.exe.is_file():
        print(f"ERROR: {args.exe} not found", file=sys.stderr)
        return 1

    data = args.exe.read_bytes()
    size_mb = len(data) / (1024 * 1024)
    try:
        machine = pe_machine(data)
    except ValueError as exc:
        print(f"ERROR: {args.exe.name}: {exc}", file=sys.stderr)
        return 1

    problems = []
    if machine != MACHINE[args.arch]:
        problems.append(f"machine 0x{machine:04X}, expected 0x{MACHINE[args.arch]:04X} ({args.arch})")
    if size_mb < args.min_mb:
        problems.append(f"size {size_mb:.1f} MB below {args.min_mb:g} MB - Flet client likely missing")

    digest = hashlib.sha256(data).hexdigest()
    print(f"{args.exe.name}: {size_mb:.1f} MB, machine 0x{machine:04X}")
    print(f"{digest}  {args.exe.name}")
    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
