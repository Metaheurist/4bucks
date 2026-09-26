from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.weapon_detect import (
    GameInstall,
    _gta_under_steam_library,
    _normalize_install,
    _parse_libraryfolders_vdf,
    _steam_roots_on_drive,
    inspect_install,
    list_gtaiv_installs,
)


def test_normalize_install_nested_gtaiv(tmp_path: Path):
    root = tmp_path / "Grand Theft Auto IV"
    nested = root / "GTAIV"
    nested.mkdir(parents=True)
    (nested / "GTAIV.exe").write_bytes(b"MZ")
    (nested / "common" / "data").mkdir(parents=True)
    assert _normalize_install(root) == nested.resolve()
    assert _normalize_install(nested) == nested.resolve()


def test_inspect_install_marks_asi_modded(tmp_path: Path):
    root = tmp_path / "GTAIV"
    root.mkdir()
    (root / "GTAIV.exe").write_bytes(b"MZ")
    (root / "common" / "data").mkdir(parents=True)
    (root / "demo.asi").write_text("x", encoding="utf-8")
    (root / "GTAIV.EFLC.FusionFix.ini").write_text("x", encoding="utf-8")
    info = inspect_install(root)
    assert isinstance(info, GameInstall)
    assert info.modded is True
    assert info.asi_count == 1
    assert "FusionFix" in info.markers
    assert "Modded" in info.status_line


def test_inspect_install_vanilla(tmp_path: Path):
    root = tmp_path / "GTAIV"
    root.mkdir()
    (root / "GTAIV.exe").write_bytes(b"MZ")
    (root / "common" / "data").mkdir(parents=True)
    info = inspect_install(root)
    assert info is not None
    assert info.modded is False
    assert "Vanilla" in info.status_line


def test_list_gtaiv_installs_returns_paths():
    # Smoke: function runs; may be empty on machines without IV.
    found = list_gtaiv_installs()
    assert isinstance(found, list)
    for p in found:
        assert p.is_dir()
        assert (p / "GTAIV.exe").is_file() or (p / "common" / "data").is_dir()


def test_parse_libraryfolders_vdf(tmp_path: Path):
    steam = tmp_path / "Steam"
    steamapps = steam / "steamapps"
    steamapps.mkdir(parents=True)
    other = tmp_path / "SteamLibrary"
    other.mkdir()
    vdf = steamapps / "libraryfolders.vdf"
    vdf.write_text(
        f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"path"\t\t"{steam.as_posix()}"\n\t}}\n'
        f'\t"1"\n\t{{\n\t\t"path"\t\t"{other.as_posix()}"\n\t}}\n}}\n',
        encoding="utf-8",
    )
    libs = _parse_libraryfolders_vdf(vdf)
    resolved = {str(p.resolve()) for p in libs}
    assert str(steam.resolve()) in resolved
    assert str(other.resolve()) in resolved


def test_steam_roots_on_drive_finds_steamlibrary(tmp_path: Path):
    lib = tmp_path / "SteamLibrary"
    (lib / "steamapps").mkdir(parents=True)
    found = _steam_roots_on_drive(tmp_path)
    assert lib in found
    games = _gta_under_steam_library(lib)
    assert any(p.name == "Grand Theft Auto IV" for p in games)
