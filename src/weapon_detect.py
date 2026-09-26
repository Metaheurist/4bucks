"""Detect stock vs mod weapon IDs and locate GTA IV installs."""

from __future__ import annotations

import os
import re
import string
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .weapons_catalog import STOCK_WEAPONS, is_stock_id, stock_name

# Well-known ASI / framework markers for a short "modded" summary.
_MOD_MARKERS: tuple[tuple[str, str], ...] = (
    ("GTAIV.EFLC.FusionFix.ini", "FusionFix"),
    ("FusionFix.asi", "FusionFix"),
    ("IVSDK", "IVSDK"),
    ("IVSDKDotNet", "IVSDK.NET"),
    ("ScriptHook.dll", "ScriptHook"),
    ("dsound.dll", "ASI loader"),
    ("dinput8.dll", "ASI loader"),
    ("modloader", "ModLoader"),
    ("plugins", "plugins"),
    ("update", "update"),
)

# Steam AppID 12210 — folder names under steamapps/common (PCGamingWiki / Steam).
_GAME_FOLDER_NAMES: tuple[str, ...] = (
    "Grand Theft Auto IV",
    "Grand Theft Auto IV Complete Edition",
    "GTAIV",
)

# Relative Steam client / library roots to probe on every drive letter.
# Sources: PCGamingWiki Glossary:Game data + common community install layouts.
_STEAM_ROOT_REL: tuple[str, ...] = (
    "Steam",
    "SteamLibrary",
    r"Program Files\Steam",
    r"Program Files (x86)\Steam",
    r"Program Files\SteamLibrary",
    r"Program Files (x86)\SteamLibrary",
    r"Games\Steam",
    r"Games\SteamLibrary",
    r"Games\Steam Games",
)

# Rockstar / retail defaults (Windows). Linux/macOS Steam homes checked separately.
_ROCKSTAR_INSTALL_REL: tuple[str, ...] = (
    r"Program Files\Rockstar Games\Grand Theft Auto IV",
    r"Program Files (x86)\Rockstar Games\Grand Theft Auto IV",
    r"Rockstar Games\Grand Theft Auto IV",
    r"Games\Rockstar Games\Grand Theft Auto IV",
    r"Games\Grand Theft Auto IV",
)


@dataclass(frozen=True)
class DetectedWeapon:
    weapon_id: int
    name: str
    kind: str  # "stock" | "mod" | "empty"
    source: str  # "catalog" | "weaponinfo" | "unknown"


@dataclass(frozen=True)
class GameInstall:
    path: Path
    version: str
    edition: str
    modded: bool
    asi_count: int
    mod_weapon_count: int
    markers: tuple[str, ...]

    @property
    def label(self) -> str:
        return str(self.path)

    @property
    def status_line(self) -> str:
        parts = [self.version or "version ?", self.edition]
        if self.modded:
            bits: list[str] = []
            if self.asi_count:
                bits.append(f"{self.asi_count} ASI")
            bits.extend(list(self.markers[:3]))
            if self.mod_weapon_count:
                bits.append(f"{self.mod_weapon_count} mod guns")
            parts.append("Modded")
            if bits:
                parts.append(" · ".join(bits))
        else:
            parts.append("Vanilla")
        return " · ".join(p for p in parts if p)


def _parse_weaponinfo(path: Path) -> dict[int, str]:
    """Best-effort parse of weaponinfo.xml style entries."""
    found: dict[int, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return found
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
            r"(?:type|id)\s*=\s*[\"']?(\d+)[\"']?[^>]*?(?:name\s*=\s*[\"']([^\"']+)[\"'])?",
            text,
            re.I,
        ):
            iid = int(m.group(1))
            if iid not in STOCK_WEAPONS:
                found[iid] = m.group(2) or f"MOD_{iid}"
    return found


def _looks_like_install(root: Path) -> bool:
    return (root / "GTAIV.exe").is_file() or (root / "common" / "data").is_dir()


def _normalize_install(candidate: Path) -> Path | None:
    """Accept CE root or nested GTAIV/ folder."""
    try:
        c = candidate.expanduser().resolve()
    except OSError:
        return None
    for root in (c, c / "GTAIV"):
        if _looks_like_install(root):
            return root
    return None


def _windows_drives() -> list[Path]:
    """Existing drive roots on Windows (C:\\, D:\\, …)."""
    drives: list[Path] = []
    for letter in string.ascii_uppercase:
        root = Path(f"{letter}:/")
        try:
            if root.exists():
                drives.append(root)
        except OSError:
            continue
    return drives


def _parse_libraryfolders_vdf(vdf: Path) -> list[Path]:
    """Return Steam library roots listed in libraryfolders.vdf."""
    try:
        text = vdf.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    libs: list[Path] = []
    for m in re.finditer(r'"path"\s+"([^"]+)"', text):
        raw = m.group(1).replace("\\\\", "\\")
        try:
            libs.append(Path(raw))
        except (OSError, ValueError):
            continue
    # Parent of steamapps/ is also a library root when vdf lives there.
    if vdf.parent.name.lower() == "steamapps":
        libs.append(vdf.parent.parent)
    return libs


def _gta_under_steam_library(lib: Path) -> list[Path]:
    common = lib / "steamapps" / "common"
    return [common / name for name in _GAME_FOLDER_NAMES]


def _steam_roots_on_drive(drive: Path) -> list[Path]:
    roots: list[Path] = []
    for rel in _STEAM_ROOT_REL:
        cand = drive / rel
        steamapps = cand / "steamapps"
        try:
            if steamapps.is_dir() or (cand / "steam.exe").is_file():
                roots.append(cand)
        except OSError:
            continue
    return roots


def _registry_paths() -> list[Path]:
    found: list[Path] = []
    try:
        import winreg
    except ImportError:
        return found

    def _read(root_key: object, sub: str, names: tuple[str, ...]) -> None:
        try:
            with winreg.OpenKey(root_key, sub) as key:  # type: ignore[arg-type]
                for value_name in names:
                    try:
                        val, _ = winreg.QueryValueEx(key, value_name)
                    except OSError:
                        continue
                    if val:
                        found.append(Path(str(val)))
        except OSError:
            pass

    for root_key, sub in (
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Rockstar Games\Grand Theft Auto IV",
        ),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Rockstar Games\Grand Theft Auto IV"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Rockstar Games\Grand Theft Auto IV Complete Edition",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Rockstar Games\Grand Theft Auto IV Complete Edition",
        ),
    ):
        _read(root_key, sub, ("InstallFolder", "Install Dir", "InstallFolderSteam"))

    for root_key, sub in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam"),
    ):
        _read(root_key, sub, ("SteamPath", "InstallPath"))

    return found


def _linux_macos_steam_homes() -> list[Path]:
    """Common Steam library homes on Linux / macOS / Flatpak (no-op if absent)."""
    home = Path.home()
    homes = [
        home / ".local" / "share" / "Steam",
        home / ".steam" / "steam",
        home / ".steam" / "root",
        home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        home / "Library" / "Application Support" / "Steam",
    ]
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        homes.append(Path(xdg) / "Steam")
    return homes


def _candidate_roots() -> list[Path]:
    """
    Build candidate GTA IV install roots.

    Strategy (Firecrawl / PCGamingWiki common layouts + live discovery):
    1. Registry Rockstar + Steam InstallPath
    2. Every Windows drive: known Steam / SteamLibrary / Rockstar folders
    3. Parse every libraryfolders.vdf found (covers relocated libraries)
    4. Linux / macOS Steam home paths when present
    """
    candidates: list[Path] = []
    steam_roots: list[Path] = []

    # 1) Registry hints first (highest confidence when present).
    for p in _registry_paths():
        # Steam InstallPath is a client root; Rockstar keys are game roots.
        if (p / "steamapps").is_dir() or (p / "steam.exe").is_file():
            steam_roots.append(p)
        else:
            candidates.append(p)
            for name in _GAME_FOLDER_NAMES:
                candidates.append(p / name)

    # 2) Per-drive Steam + Rockstar probes.
    drives = _windows_drives()
    if not drives and os.name == "nt":
        drives = [Path("C:/")]
    for drive in drives:
        steam_roots.extend(_steam_roots_on_drive(drive))
        for rel in _ROCKSTAR_INSTALL_REL:
            candidates.append(drive / rel)

    # 3) Non-Windows Steam homes.
    steam_roots.extend(_linux_macos_steam_homes())

    # 4) Resolve Steam libraries via VDF + default common/ folders.
    seen_steam: set[str] = set()
    for steam in steam_roots:
        try:
            key = str(steam.resolve()).lower()
        except OSError:
            key = str(steam).lower()
        if key in seen_steam:
            continue
        seen_steam.add(key)
        vdfs = [
            steam / "steamapps" / "libraryfolders.vdf",
            steam / "config" / "libraryfolders.vdf",
        ]
        libs = [steam]
        for vdf in vdfs:
            if vdf.is_file():
                libs.extend(_parse_libraryfolders_vdf(vdf))
        for lib in libs:
            candidates.extend(_gta_under_steam_library(lib))

    return candidates


def find_gtaiv_install() -> Path | None:
    """Locate first GTA IV install with common/data or GTAIV.exe."""
    found = list_gtaiv_installs()
    return found[0] if found else None


def list_gtaiv_installs() -> list[Path]:
    """Auto-detect all known install locations (deduped, resolved)."""
    seen: set[str] = set()
    out: list[Path] = []
    for raw in _candidate_roots():
        root = _normalize_install(raw)
        if root is None:
            continue
        key = str(root).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(root)
    return out


def _file_version(exe: Path) -> str:
    """Read Windows FileVersion string from GTAIV.exe (best-effort)."""
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return ""
    if not exe.is_file():
        return ""
    size = ctypes.windll.version.GetFileVersionInfoSizeW(str(exe), None)
    if not size:
        return ""
    buf = ctypes.create_string_buffer(size)
    if not ctypes.windll.version.GetFileVersionInfoW(str(exe), 0, size, buf):
        return ""
    uflen = wintypes.UINT()
    ptr = ctypes.c_void_p()
    if ctypes.windll.version.VerQueryValueW(
        buf, r"\VarFileInfo\Translation", ctypes.byref(ptr), ctypes.byref(uflen)
    ):
        trans = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_uint16))
        lang = f"{trans[0]:04x}{trans[1]:04x}"
        query = rf"\StringFileInfo\{lang}\FileVersion"
        if (
            ctypes.windll.version.VerQueryValueW(
                buf, query, ctypes.byref(ptr), ctypes.byref(uflen)
            )
            and ptr.value
        ):
            return ctypes.wstring_at(ptr.value).strip()

    class VS_FIXEDFILEINFO(ctypes.Structure):
        _fields_ = [
            ("dwSignature", wintypes.DWORD),
            ("dwStrucVersion", wintypes.DWORD),
            ("dwFileVersionMS", wintypes.DWORD),
            ("dwFileVersionLS", wintypes.DWORD),
            ("dwProductVersionMS", wintypes.DWORD),
            ("dwProductVersionLS", wintypes.DWORD),
            ("dwFileFlagsMask", wintypes.DWORD),
            ("dwFileFlags", wintypes.DWORD),
            ("dwFileOS", wintypes.DWORD),
            ("dwFileType", wintypes.DWORD),
            ("dwFileSubtype", wintypes.DWORD),
            ("dwFileDateMS", wintypes.DWORD),
            ("dwFileDateLS", wintypes.DWORD),
        ]

    if ctypes.windll.version.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(uflen)):
        info = ctypes.cast(ptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
        ms, ls = info.dwFileVersionMS, info.dwFileVersionLS
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    return ""


def _asi_count(root: Path) -> int:
    try:
        return sum(1 for p in root.glob("*.asi") if p.is_file())
    except OSError:
        return 0


def _detect_markers(root: Path) -> tuple[str, ...]:
    found: list[str] = []
    seen: set[str] = set()
    for rel, label in _MOD_MARKERS:
        if (root / rel).exists() and label not in seen:
            seen.add(label)
            found.append(label)
    return tuple(found)


def _guess_edition(root: Path, version: str) -> str:
    name = root.name.lower()
    parent = root.parent.name.lower()
    if "complete" in name or "complete" in parent or "eflc" in name:
        return "CE"
    if version.startswith("1.2."):
        return "CE"
    if (root / "TLAD").is_dir() or (root / "TBoGT").is_dir():
        return "EFLC"
    return "IV"


def inspect_install(path: Path | None) -> GameInstall | None:
    """Version + modded state for a GTA IV install root."""
    if path is None:
        return None
    root = _normalize_install(path)
    if root is None:
        return None
    exe = root / "GTAIV.exe"
    version = _file_version(exe) if exe.is_file() else ""
    asi = _asi_count(root)
    markers = _detect_markers(root)
    mods = load_mod_weapon_names(root)
    mod_guns = len(mods)
    modded = asi > 0 or bool(markers) or mod_guns > 0
    return GameInstall(
        path=root,
        version=version or "unknown",
        edition=_guess_edition(root, version),
        modded=modded,
        asi_count=asi,
        mod_weapon_count=mod_guns,
        markers=markers,
    )


@lru_cache(maxsize=8)
def load_mod_weapon_names(install: Path | None = None) -> dict[int, str]:
    """Merge weaponinfo.xml (+ common mod overlay paths) for non-stock IDs."""
    root = install or find_gtaiv_install()
    if root is None:
        return {}
    root = _normalize_install(root) or root
    merged: dict[int, str] = {}
    search_paths = [
        root / "common" / "data" / "weaponinfo.xml",
        root / "update" / "common" / "data" / "weaponinfo.xml",
        root / "modloader",
        root / "plugins",
        root / "IVSDK",
    ]
    for p in search_paths:
        if p.is_file() and p.suffix.lower() == ".xml":
            merged.update(_parse_weaponinfo(p))
        elif p.is_dir():
            try:
                for xml in p.rglob("weaponinfo*.xml"):
                    merged.update(_parse_weaponinfo(xml))
            except OSError:
                pass
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
    weapon_ids: list[int],
    *,
    refresh_install: bool = False,
    install: Path | None = None,
) -> list[DetectedWeapon]:
    if refresh_install:
        load_mod_weapon_names.cache_clear()
    mods = load_mod_weapon_names(install)
    return [classify_weapon(wid, mod_names=mods) for wid in weapon_ids]
