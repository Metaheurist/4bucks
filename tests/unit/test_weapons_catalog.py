from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.weapons_catalog import (
    STOCK_WEAPONS,
    picker_options,
    short_name,
    weapons_for,
)


def test_weapons_for_iv_excludes_episodes():
    ids = {w.id for w in weapons_for("iv")}
    assert 7 in ids  # PISTOL
    assert 0 in ids  # UNARMED shared
    assert 45 in ids  # CAMERA shared
    assert 21 not in ids  # TLAD grenade launcher
    assert 29 not in ids  # TBoGT pistol .44


def test_weapons_for_tlad_and_tbogt():
    tlad = {w.id for w in weapons_for("tlad")}
    tbogt = {w.id for w in weapons_for("tbogt")}
    assert 21 in tlad and 26 in tlad
    assert 7 not in tlad  # base-only excluded
    assert 0 in tlad  # shared
    assert 29 in tbogt and 41 in tbogt
    assert 7 not in tbogt
    assert 0 in tbogt


def test_weapons_for_all_and_mods():
    all_ids = {w.id for w in weapons_for("all")}
    assert 7 in all_ids and 21 in all_ids and 29 in all_ids
    assert weapons_for("mods") == []
    assert picker_options("mods") == []


def test_weapons_for_category_filter():
    handguns = weapons_for("iv", category="handgun")
    assert {w.id for w in handguns} == {7, 9}


def test_short_name_and_stock_tags():
    assert short_name(0) == "Empty"
    assert short_name(7) == "Pistol"
    assert "GRENADE" in short_name(21).upper()
    assert STOCK_WEAPONS[21].episode == "tlad"
    assert STOCK_WEAPONS[29].episode == "tbogt"
    assert STOCK_WEAPONS[7].category == "handgun"
