"""Unit tests for vehicles.ide name mapping and livery labels."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.vehicles_catalog import (
    clear_vehicle_cache,
    list_livery_options,
    list_vehicles,
    livery_label,
    load_vehicle_index_map,
    vehicle_name,
)


def _write_ide(path: Path, names: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(f"{n}, {n}, car, vehshare" for n in names)
    path.write_text(f"# test ide\ncars\n{rows}\nend\n", encoding="utf-8")


def test_merge_order_dedupes_episode_names(tmp_path: Path):
    clear_vehicle_cache()
    _write_ide(tmp_path / "common" / "data" / "vehicles.ide", ["admiral", "banshee"])
    _write_ide(tmp_path / "TBoGT" / "common" / "data" / "vehicles.ide", ["banshee", "bullet"])
    mapping = load_vehicle_index_map(str(tmp_path))
    assert mapping == {0: "admiral", 1: "banshee", 2: "bullet"}
    assert vehicle_name(2, tmp_path) == "Bullet"
    assert vehicle_name(99, tmp_path) == "Model 99"
    assert [name for _, name in list_vehicles(tmp_path)] == ["Admiral", "Banshee", "Bullet"]
    clear_vehicle_cache()


def test_nested_gtaiv_folder_is_resolved(tmp_path: Path):
    clear_vehicle_cache()
    _write_ide(tmp_path / "GTAIV" / "common" / "data" / "vehicles.ide", ["turismo"])
    assert vehicle_name(0, tmp_path) == "Turismo"
    clear_vehicle_cache()


def test_fallback_without_install():
    clear_vehicle_cache()
    assert vehicle_name(95) == "Turismo"
    assert vehicle_name(1234) == "Model 1234"


def test_livery_labels_and_options():
    assert livery_label(255) == "None"
    assert livery_label(0xFFFFFFFF) == "None"
    assert livery_label(3) == "Style 3"
    opts = list_livery_options(40)
    assert opts[0] == (255, "None")
    keys = [k for k, _ in opts]
    assert 0 in keys and 15 in keys and 40 in keys
