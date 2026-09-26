"""Unit tests for Block 4 StoredCar garage editing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.playerinfo import parse_blocks
from src.safehouse_parking import SAFEHOUSES, nearest_safehouse
from src.save_garage import (
    FLAG_VALID,
    list_safehouse_slots,
    read_stored_cars,
    spawn_at_safehouse,
    update_stored_car,
)
from tests.unit.fixtures import _pack_stored_car, make_minimal_save, write_ce_save


def test_nearest_safehouse_broker():
    hit = nearest_safehouse(904.0, -499.0)
    assert hit is not None
    sh, spot = hit
    assert sh.id == "broker"
    assert spot in (0, 1)


def test_garages_block_index_and_roundtrip(tmp_path: Path):
    car = _pack_stored_car(
        model=95,
        x=904.31,
        y=-500.05,
        z=14.98,
        rot=(1, 99, 1),
        colors=(1, 2, 3, 4),
        flags=FLAG_VALID,
    )
    raw = make_minimal_save(with_garages=True, garage_cars=[car])
    blocks = parse_blocks(raw)
    assert len(blocks) >= 5
    cars = read_stored_cars(raw)
    assert cars[0].valid
    assert cars[0].model == 95
    assert cars[0].colors == (1, 2, 3, 4)
    slots = list_safehouse_slots(raw)
    broker = [s for s in slots if s.safehouse_id == "broker"]
    assert any(s.car and s.car.model == 95 for s in broker)


def test_update_preserves_pose(tmp_path: Path):
    car = _pack_stored_car(
        model=92,
        x=904.31,
        y=-500.05,
        z=14.98,
        rot=(1, 99, 1),
        flags=FLAG_VALID,
    )
    path = write_ce_save(
        tmp_path,
        with_garages=True,
        garage_cars=[car],
    )
    old, new, _, check = update_stored_car(
        path, 0, model=95, colors=(9, 8, 7, 6), backup=False
    )
    assert check.allowed
    assert old.model == 92
    assert new.model == 95
    assert abs(new.x - 904.31) < 0.01
    assert abs(new.y - (-500.05)) < 0.01
    assert new.colors == (9, 8, 7, 6)


def test_clear_slot(tmp_path: Path):
    car = _pack_stored_car(model=92, x=904.31, y=-500.05, z=14.98, flags=FLAG_VALID)
    path = write_ce_save(tmp_path, with_garages=True, garage_cars=[car])
    _, new, _, _ = update_stored_car(path, 0, clear=True, backup=False)
    assert not new.valid
    assert new.model == 0


def test_spawn_into_free_spot(tmp_path: Path):
    path = write_ce_save(tmp_path, with_garages=True, garage_cars=[])
    new, _, check = spawn_at_safehouse(
        path, "broker", model=95, colors=(0, 0, 0, 0), backup=False
    )
    assert check.allowed
    assert new.valid
    assert new.model == 95
    hit = nearest_safehouse(new.x, new.y)
    assert hit is not None and hit[0].id == "broker"


def test_spawn_refuses_when_house_full(tmp_path: Path):
    sh = SAFEHOUSES[0]  # broker
    packed = [
        _pack_stored_car(
            model=90 + i,
            x=spot.x,
            y=spot.y,
            z=spot.z,
            rot=spot.rot,
            flags=FLAG_VALID,
        )
        for i, spot in enumerate(sh.spots)
    ]
    path = write_ce_save(tmp_path, with_garages=True, garage_cars=packed)
    try:
        spawn_at_safehouse(path, "broker", model=95, backup=False)
        assert False, "expected full parking error"
    except RuntimeError as e:
        assert "full" in str(e).lower()
