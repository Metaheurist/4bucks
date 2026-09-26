#!/usr/bin/env python3
"""Bump patch SemVer in src/__init__.py and print the new version."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "src" / "__init__.py"
VERSION_RE = re.compile(r'^(__version__\s*=\s*")(\d+)\.(\d+)\.(\d+)(")', re.MULTILINE)


def bump_patch(text: str) -> tuple[str, str]:
    match = VERSION_RE.search(text)
    if not match:
        raise SystemExit(f"Could not find __version__ in {INIT}")
    major, minor, patch = (int(match.group(2)), int(match.group(3)), int(match.group(4)))
    new_version = f"{major}.{minor}.{patch + 1}"
    new_text = VERSION_RE.sub(rf"\g<1>{new_version}\g<5>", text, count=1)
    return new_text, new_version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-github-output",
        action="store_true",
        help="Also append version=... to $GITHUB_OUTPUT",
    )
    args = parser.parse_args()

    text = INIT.read_text(encoding="utf-8")
    new_text, new_version = bump_patch(text)
    INIT.write_text(new_text, encoding="utf-8", newline="\n")
    print(new_version)

    if args.write_github_output:
        out = Path(__import__("os").environ.get("GITHUB_OUTPUT", ""))
        if not out.name:
            raise SystemExit("GITHUB_OUTPUT is not set")
        with out.open("a", encoding="utf-8") as fh:
            fh.write(f"version={new_version}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
