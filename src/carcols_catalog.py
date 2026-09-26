"""Paint swatch names from carcols.dat ``col`` tables (CE merge order)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_INDEX_RE = re.compile(r"^\s*(\d+)\s*(.*)$")


@dataclass(frozen=True)
class PaintColor:
    index: int
    r: int
    g: int
    b: int
    prefix: str
    scanner: str
    label: str


# Minimal labels when no install / carcols.dat is available.
_FALLBACK: dict[int, PaintColor] = {
    0: PaintColor(0, 10, 10, 10, "-", "black", "Black"),
    1: PaintColor(1, 37, 37, 39, "-", "black", "Black Poly"),
    27: PaintColor(27, 162, 20, 20, "-", "red", "Very Red"),
    34: PaintColor(34, 88, 104, 144, "-", "blue", "Bright Blue Poly"),
    89: PaintColor(89, 255, 255, 255, "-", "white", "White"),
    133: PaintColor(133, 255, 255, 255, "-", "white", "Very White"),
}


def _pretty(text: str) -> str:
    return text.replace("_", " ").strip().title() if text else "Unknown"


def _label_from(prefix: str, scanner: str, comment_rest: str) -> str:
    rest = comment_rest.strip()
    if rest:
        # Preserve author casing when present (e.g. SuperD); title-case plain comments.
        if rest == rest.lower():
            return _pretty(rest)
        return rest
    bits: list[str] = []
    if prefix and prefix != "-":
        bits.append(prefix)
    if scanner:
        bits.append(scanner)
    return _pretty(" ".join(bits)) if bits else "Unknown"


def _carcols_paths(install: Path) -> list[Path]:
    """CE-ish merge order: base IV, then TLAD, then TBoGT."""
    root = install
    if (root / "GTAIV").is_dir():
        root = root / "GTAIV"
    return [
        root / "common" / "data" / "carcols.dat",
        root / "update" / "common" / "data" / "carcols.dat",
        root / "TLAD" / "common" / "data" / "carcols.dat",
        root / "update" / "TLAD" / "common" / "data" / "carcols.dat",
        root / "TBoGT" / "common" / "data" / "carcols.dat",
        root / "update" / "TBoGT" / "common" / "data" / "carcols.dat",
    ]


def parse_col_table(text: str) -> dict[int, PaintColor]:
    """Parse one or more ``col`` … ``end`` blocks from a carcols.dat body."""
    out: dict[int, PaintColor] = {}
    in_col = False
    next_idx = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low == "col":
            in_col = True
            continue
        if low == "end":
            in_col = False
            continue
        if not in_col or line.startswith("#"):
            continue

        comment = ""
        body = line
        if "#" in line:
            body, comment = line.split("#", 1)

        parts = [p.strip() for p in body.split(",")]
        if len(parts) < 5:
            continue
        try:
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            continue
        prefix = parts[3] or "-"
        scanner = parts[4] or ""

        idx = next_idx
        comment_rest = comment
        m = _INDEX_RE.match(comment)
        if m:
            idx = int(m.group(1))
            comment_rest = m.group(2)

        label = _label_from(prefix, scanner, comment_rest)
        out[idx] = PaintColor(idx, r, g, b, prefix, scanner, label)
        next_idx = max(next_idx, idx + 1)
    return out


def _merge_tables(paths: list[Path]) -> dict[int, PaintColor]:
    merged: dict[int, PaintColor] = {}
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Later files may add higher indices (e.g. TBoGT 134–136) or override.
        merged.update(parse_col_table(text))
    return merged


@lru_cache(maxsize=8)
def load_color_table(install_key: str) -> dict[int, PaintColor]:
    """Index → paint swatch from merged carcols.dat files."""
    if not install_key:
        return dict(_FALLBACK)
    merged = _merge_tables(_carcols_paths(Path(install_key)))
    return merged if merged else dict(_FALLBACK)


def paint_label(index: int, install: Path | None = None) -> str:
    """Display label including index, e.g. ``27 · Very Red``."""
    key = str(install.resolve()) if install else ""
    table = load_color_table(key)
    swatch = table.get(int(index))
    if swatch:
        return f"{swatch.index} · {swatch.label}"
    return f"{int(index)} · Color {int(index)}"


def list_paint_colors(install: Path | None = None) -> list[tuple[int, str]]:
    """Sorted ``(index, label)`` rows for paint dropdowns."""
    key = str(install.resolve()) if install else ""
    table = load_color_table(key)
    items = [(i, f"{c.index} · {c.label}") for i, c in table.items()]
    items.sort(key=lambda t: t[0])
    return items


def clear_carcols_cache() -> None:
    load_color_table.cache_clear()
