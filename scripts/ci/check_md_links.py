#!/usr/bin/env python3
"""Fail when a Markdown file links or embeds a repo-relative path that does not exist.

External URLs (http/https/mailto) and pure in-page anchors are skipped so the check is
offline and deterministic. Run from anywhere: python scripts/ci/check_md_links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".venv", ".venv-x86", "build", "dist", "backups", "node_modules", ".pytest_cache"}

MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_ATTR = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
FENCE = re.compile(r"^\s*(```|~~~)")


def markdown_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(ROOT).parts))


def targets(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"`[^`]*`", "", line)
        for rx in (MD_LINK, HTML_ATTR):
            found.extend((lineno, m.group(1)) for m in rx.finditer(line))
    return found


def is_external(link: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*:", link, re.IGNORECASE)) or link.startswith("//")


def main() -> int:
    broken: list[str] = []
    checked = 0
    for md in markdown_files():
        for lineno, link in targets(md.read_text(encoding="utf-8", errors="replace")):
            if is_external(link) or link.startswith("#"):
                continue
            path_part = unquote(link.split("#", 1)[0].split("?", 1)[0])
            if not path_part:
                continue
            base = ROOT if path_part.startswith("/") else md.parent
            resolved = (base / path_part.lstrip("/")).resolve()
            checked += 1
            if not resolved.exists():
                broken.append(f"{md.relative_to(ROOT)}:{lineno}: {link}")

    print(f"Checked {checked} relative links across {len(markdown_files())} Markdown files.")
    if broken:
        print("Broken links:", *broken, sep="\n  ")
        return 1
    print("All relative links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
