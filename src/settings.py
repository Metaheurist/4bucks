"""Persist Save 4Bucks UI settings next to the app."""

from __future__ import annotations

import json
from pathlib import Path

from .backup import app_dir

SETTINGS_NAME = "save4bucks_settings.json"

DEFAULTS = {
    "autobackup": True,
    "also_autosave": True,
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
        if isinstance(loaded, dict):
            for k in DEFAULTS:
                if k in loaded:
                    data[k] = bool(loaded[k])
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return data


def save_settings(settings: dict, base: Path | None = None) -> None:
    path = settings_path(base)
    out = {k: bool(settings.get(k, DEFAULTS[k])) for k in DEFAULTS}
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
