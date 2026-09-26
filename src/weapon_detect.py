"""Detect stock vs mod weapon IDs in a save loadout."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .weapons_catalog import STOCK_WEAPONS, is_stock_id, stock_name


@dataclass(frozen=True)
class DetectedWeapon:
    weapon_id: int
    name: str
    kind: str  # "stock" | "mod" | "empty"
    source: str  # "catalog" | "weaponinfo" | "unknown"


def _parse_weaponinfo(path: Path) -> dict[int, str]:
    """Best-effort parse of weaponinfo.xml style entries."""
    found: dict[int, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return found
    # Prefer ElementTree; fall back to regex for messy mod XML
    try:
        root = ET.fromstring(text)
        for el in root.iter():
            wid = el.attrib.get("type") or el.attrib.get("id") or el.attrib.get("slot")
            name = el.attrib.get("name") or el.attrib.get("weaponName") or el.tag
            if wid is None:
                continue
            try:
                iid = int(wid)
            except ValueError:
                continue
            if iid not in STOCK_WEAPONS:
                found[iid] = str(name)
    except ET.ParseError:
        for m in re.finditer(
            r'(?:type|id)\s*=\s*["\']?(\d+)["\']?[^>]*?(?:name\s*=\s*["\']([^"\']+)["\'])?',
            text,
            re.I,
        ):
            iid = int(m.group(1))
            if iid not in STOCK_WEAPONS:
                found[iid] = m.group(2) or f"MOD_{iid}"
    return found


def find_gtaiv_install() -> Path | None:
    """Locate a GTA IV install with common/data (Steam / common paths)."""
    candidates: list[Path] = []
    # Steam library default + known local path from research notes
    candidates.extend(
        [
            Path(r"D:\SteamLibrary\steamapps\common\Grand Theft Auto IV"),
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto IV"),
            Path(r"C:\Program Files\Rockstar Games\Grand Theft Auto IV"),
            Path(r"C:\Program Files (x86)\Rockstar Games\Grand Theft Auto IV"),
        ]
    )
    try:
        import winreg

        for root_key, sub in (
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Rockstar Games\Grand Theft Auto IV"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Rockstar Games\Grand Theft Auto IV"),
        ):
            try:
                with winreg.OpenKey(root_key, sub) as key:
                    val, _ = winreg.QueryValueEx(key, "InstallFolder")
                    if val:
                        candidates.insert(0, Path(val))
            except OSError:
                pass
    except ImportError:
        pass

    for c in candidates:
        if (c / "common" / "data").is_dir() or (c / "GTAIV.exe").is_file():
            return c
    return None


@lru_cache(maxsize=1)
def load_mod_weapon_names(install: Path | None = None) -> dict[int, str]:
    """Merge weaponinfo.xml (+ common mod overlay paths) for non-stock IDs."""
    root = install or find_gtaiv_install()
    if root is None:
        return {}
    merged: dict[int, str] = {}
    search_paths = [
        root / "common" / "data" / "weaponinfo.xml",
        root / "update" / "common" / "data" / "weaponinfo.xml",
        root / "modloader",
        root / "plugins",
    ]
    for p in search_paths:
        if p.is_file() and p.suffix.lower() == ".xml":
            merged.update(_parse_weaponinfo(p))
        elif p.is_dir():
            for xml in p.rglob("weaponinfo*.xml"):
                merged.update(_parse_weaponinfo(xml))
    return merged


def classify_weapon(
    weapon_id: int, *, mod_names: dict[int, str] | None = None
) -> DetectedWeapon:
    if weapon_id == 0:
        return DetectedWeapon(0, "UNARMED", "empty", "catalog")
    if is_stock_id(weapon_id):
        return DetectedWeapon(
            weapon_id, stock_name(weapon_id) or f"ID_{weapon_id}", "stock", "catalog"
        )
    mods = mod_names if mod_names is not None else load_mod_weapon_names()
    if weapon_id in mods:
        return DetectedWeapon(weapon_id, mods[weapon_id], "mod", "weaponinfo")
    return DetectedWeapon(weapon_id, f"Mod / unknown (0x{weapon_id:X})", "mod", "unknown")


def classify_loadout(
    weapon_ids: list[int], *, refresh_install: bool = False
) -> list[DetectedWeapon]:
    if refresh_install:
        load_mod_weapon_names.cache_clear()
    mods = load_mod_weapon_names()
    return [classify_weapon(wid, mod_names=mods) for wid in weapon_ids]
