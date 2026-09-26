"""Discover GTA IV CE save profiles and check if the game is running."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .backup import is_backup_name
from .save_money import read_money_file


@dataclass
class SaveSlot:
    path: Path
    slot_name: str
    label: str
    money: int | None
    display: int | None
    modified: datetime
    error: str | None = None


def documents_roots() -> list[Path]:
    roots: list[Path] = []
    home = Path.home()
    candidates = [
        home / "OneDrive" / "Documents",
        Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Documents",
        home / "Documents",
        Path(os.environ.get("USERPROFILE", "")) / "Documents",
    ]
    # Official My Documents (may already be OneDrive-redirected)
    try:
        import ctypes.wintypes

        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        # CSIDL_PERSONAL = 5
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0:
            candidates.insert(0, Path(buf.value))
    except Exception:
        pass

    seen: set[str] = set()
    for c in candidates:
        try:
            resolved = str(c.resolve())
        except OSError:
            continue
        if resolved in seen or not c.is_dir():
            continue
        seen.add(resolved)
        roots.append(c)
    return roots


def find_profile_dirs() -> list[Path]:
    profiles: list[Path] = []
    for root in documents_roots():
        base = root / "Rockstar Games" / "GTA IV" / "Profiles"
        if not base.is_dir():
            continue
        for p in sorted(base.iterdir()):
            if p.is_dir() and any(p.glob("SGTA4*")):
                profiles.append(p)
    return profiles


def slot_label(name: str) -> str:
    if not name.startswith("SGTA4") or len(name) < 7:
        return name
    try:
        n = int(name[5:])
    except ValueError:
        return name
    if n == 12:
        return "Autosave (IV)"
    if n == 13:
        return "Autosave (TLAD)"
    if n == 14:
        return "Autosave (TBoGT)"
    if 0 <= n <= 11:
        return f"Slot {n + 1}"
    return name


def list_slots(profile: Path) -> list[SaveSlot]:
    slots: list[SaveSlot] = []
    for path in sorted(profile.glob("SGTA4*")):
        if not path.is_file():
            continue
        # skip backups (*.backup, legacy *.bak_before_money_*)
        if is_backup_name(path.name):
            continue
        # only real slot files SGTA4##
        if len(path.name) != 7 or not path.name.startswith("SGTA4"):
            continue
        money = display = None
        err = None
        try:
            money, display = read_money_file(path)
        except Exception as e:
            err = str(e)
        slots.append(
            SaveSlot(
                path=path,
                slot_name=path.name,
                label=slot_label(path.name),
                money=money,
                display=display,
                modified=datetime.fromtimestamp(path.stat().st_mtime),
                error=err,
            )
        )
    return slots


def is_gtaiv_running() -> bool:
    try:
        import subprocess

        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq GTAIV.exe", "/FO", "CSV", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return "GTAIV.exe" in out
    except Exception:
        return False
