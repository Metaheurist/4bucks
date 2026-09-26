from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.settings import DEFAULTS, load_settings, save_settings


def test_defaults_include_last_save_keys():
    assert "last_profile" in DEFAULTS
    assert "last_slot" in DEFAULTS
    assert "last_install" in DEFAULTS
    assert DEFAULTS["last_profile"] == ""
    assert DEFAULTS["last_slot"] == ""
    assert DEFAULTS["last_install"] == ""


def test_settings_roundtrip_last_save(tmp_path: Path):
    save_settings(
        {
            "autobackup": False,
            "also_autosave": True,
            "last_profile": str(tmp_path / "Profiles" / "Rockstar"),
            "last_slot": "SGTA412",
            "last_install": str(tmp_path / "GTAIV"),
        },
        base=tmp_path,
    )
    loaded = load_settings(base=tmp_path)
    assert loaded["autobackup"] is False
    assert loaded["also_autosave"] is True
    assert loaded["last_profile"].endswith("Rockstar")
    assert loaded["last_slot"] == "SGTA412"
    assert loaded["last_install"].endswith("GTAIV")


def test_load_settings_missing_file_returns_defaults(tmp_path: Path):
    loaded = load_settings(base=tmp_path)
    assert loaded == DEFAULTS
