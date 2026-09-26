"""Persist 4Bucks UI settings next to the app."""

from __future__ import annotations

import json
from pathlib import Path

from .backup import app_dir

SETTINGS_NAME = "save4bucks_settings.json"

DEFAULTS: dict = {
    "autobackup": True,
    "also_autosave": True,
    "last_profile": "",
    "last_slot": "",
    "last_install": "",
}


def settings_path(base: Path | None = None) -> Path:
    return (base or app_dir()) / SETTINGS_NAME


def load_settings(base: Path | None = None) -> dict:
    path = settings_path(base)
    data = dict(DEFAULTS)
    if not path.is_file():
        return data
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            return data
        data["autobackup"] = bool(loaded.get("autobackup", DEFAULTS["autobackup"]))
        data["also_autosave"] = bool(loaded.get("also_autosave", DEFAULTS["also_autosave"]))
        lp = loaded.get("last_profile", "")
        ls = loaded.get("last_slot", "")
        li = loaded.get("last_install", "")
        data["last_profile"] = str(lp) if lp is not None else ""
        data["last_slot"] = str(ls) if ls is not None else ""
        data["last_install"] = str(li) if li is not None else ""
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return data


def save_settings(settings: dict, base: Path | None = None) -> None:
    path = settings_path(base)
    out = {
        "autobackup": bool(settings.get("autobackup", DEFAULTS["autobackup"])),
        "also_autosave": bool(settings.get("also_autosave", DEFAULTS["also_autosave"])),
        "last_profile": str(settings.get("last_profile") or ""),
        "last_slot": str(settings.get("last_slot") or ""),
        "last_install": str(settings.get("last_install") or ""),
    }
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
