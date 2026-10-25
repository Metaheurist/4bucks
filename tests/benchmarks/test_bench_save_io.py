"""Micro-benchmarks for save parsing and editing hot paths (pytest-benchmark).

Run locally:  python -m pytest tests/benchmarks --benchmark-only
CI:           .github/workflows/benchmark.yml compares means against the main baseline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.carcols_catalog import parse_col_table
from src.playerinfo import parse_blocks
from src.safehouse_parking import SAFEHOUSES
from src.save_garage import FLAG_VALID, list_safehouse_slots, read_stored_cars
from src.save_money import read_money, set_money
from src.save_vitality import read_vitality
from src.save_weapons import read_loadout
from src.versioning import inspect_save
from tests.unit.fixtures import _pack_stored_car, make_minimal_save, write_ce_save


@pytest.fixture(scope="module")
def garage_save() -> bytes:
    cars = [
        _pack_stored_car(model=90 + i, x=spot.x, y=spot.y, z=spot.z, rot=spot.rot, flags=FLAG_VALID)
        for i, spot in enumerate(s for sh in SAFEHOUSES for s in sh.spots)
    ]
    return make_minimal_save(with_garages=True, garage_cars=cars[:20])


@pytest.fixture(scope="module")
def carcols_text() -> str:
    rows = "\n".join(f"{i % 256},{(i * 7) % 256},{(i * 13) % 256},-,grey\t# {i} colour {i}" for i in range(137))
    return f"col\n{rows}\nend\n"


def test_bench_parse_blocks(benchmark, garage_save):
    blocks = benchmark(parse_blocks, garage_save)
    assert len(blocks) >= 5


def test_bench_read_money(benchmark, garage_save):
    money, _, _, _ = benchmark(read_money, garage_save)
    assert money == 413_388


def test_bench_read_loadout(benchmark, garage_save):
    loadout = benchmark(read_loadout, garage_save)
    assert loadout is not None


def test_bench_read_vitality(benchmark, garage_save):
    vit = benchmark(read_vitality, garage_save)
    assert vit.health == 200.0


def test_bench_read_stored_cars(benchmark, garage_save):
    cars = benchmark(read_stored_cars, garage_save)
    assert len(cars) == 20


def test_bench_list_safehouse_slots(benchmark, garage_save):
    slots = benchmark(list_safehouse_slots, garage_save)
    assert any(s.car is not None for s in slots)


def test_bench_parse_carcols(benchmark, carcols_text):
    table = benchmark(parse_col_table, carcols_text)
    assert len(table) == 137


def test_bench_inspect_save(benchmark, tmp_path):
    path = write_ce_save(tmp_path, with_garages=True)
    identity = benchmark(inspect_save, path)
    assert identity is not None


def test_bench_set_money_roundtrip(benchmark, tmp_path):
    path = write_ce_save(tmp_path, money=1_000)
    _, new, _, _ = benchmark(set_money, path, 2_500_000, backup=False)
    assert new == 2_500_000
