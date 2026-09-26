"""Vehicle display names from vehicles.ide (CE load order)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def _cars_section(ide: Path) -> list[str]:
    if not ide.is_file():
        return []
    names: list[str] = []
    in_cars = False
    try:
        text = ide.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    for line in text.splitlines():
        s = line.strip()
        low = s.lower()
        if low == "cars":
            in_cars = True
            continue
        if low == "end":
            in_cars = False
            continue
        if not in_cars or not s or s.startswith("#") or "," not in s:
            continue
        names.append(s.split(",", 1)[0].strip())
    return names


def _ide_paths(install: Path) -> list[Path]:
    """CE-ish merge order: base IV, then TLAD, then TBoGT (unique names)."""
    root = install
    if (root / "GTAIV").is_dir():
        root = root / "GTAIV"
    return [
        root / "common" / "data" / "vehicles.ide",
        root / "update" / "common" / "data" / "vehicles.ide",
        root / "TLAD" / "common" / "data" / "vehicles.ide",
        root / "update" / "TLAD" / "common" / "data" / "vehicles.ide",
        root / "TBoGT" / "common" / "data" / "vehicles.ide",
        root / "update" / "TBoGT" / "common" / "data" / "vehicles.ide",
    ]


# Minimal fallback when no install is selected (common IV indices).
_FALLBACK: dict[int, str] = {
    0: "admiral",
    3: "banshee",
    92: "taxi",
    95: "turismo",
}


def _pretty(name: str) -> str:
    return name.replace("_", " ").strip().title() if name else "Unknown"


@lru_cache(maxsize=8)
def load_vehicle_index_map(install_key: str) -> dict[int, str]:
    """Map stream model index to internal name from IDE merge order."""
    if not install_key:
        return dict(_FALLBACK)
    install = Path(install_key)
    merged: list[str] = []
    seen: set[str] = set()
    for ide in _ide_paths(install):
        for name in _cars_section(ide):
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(name)
    if not merged:
        return dict(_FALLBACK)
    return {i: n for i, n in enumerate(merged)}


def vehicle_name(model_index: int, install: Path | None = None) -> str:
    key = str(install.resolve()) if install else ""
    mapping = load_vehicle_index_map(key)
    raw = mapping.get(int(model_index))
    if raw:
        return _pretty(raw)
    return f"Model {int(model_index)}"


def list_vehicles(install: Path | None = None) -> list[tuple[int, str]]:
    """Sorted (index, display name) for pickers."""
    key = str(install.resolve()) if install else ""
    mapping = load_vehicle_index_map(key)
    items = [(i, _pretty(n)) for i, n in mapping.items()]
    items.sort(key=lambda t: t[1].lower())
    return items


def clear_vehicle_cache() -> None:
    load_vehicle_index_map.cache_clear()


def livery_label(index: int) -> str:
    """
    Display label for a StoredCar livery byte.

    GTA IV has no global livery name table in common/data (unlike carcols.dat).
    Indices map to per-model texture slots; 255 is the usual unused/None marker
    (``0xFFFFFFFF & 0xFF``).
    """
    i = int(index) & 0xFF
    if i == 255:
        return "None"
    return f"Style {i}"


def list_livery_options(*extra: int) -> list[tuple[int, str]]:
    """Dropdown rows: None (255) plus Style 0–15 and any current value."""
    vals = {255, *range(16)}
    for e in extra:
        if e >= 0:
            vals.add(int(e) & 0xFF)
    items = [(i, livery_label(i)) for i in vals]
    # None first, then ascending indices
    items.sort(key=lambda t: (-1 if t[0] == 255 else t[0]))
    return items
