from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.save_vitality import read_vitality, set_vitality
from src.save_weapons import read_loadout, write_loadout
from src.versioning import (
    GameFamily,
    SAVEGAME_VERSION_COMPAT,
    WriteTechnique,
    check_write,
    detect_game_family,
    resolve_write_profile,
    status_chip,
)
from src.weapon_detect import classify_weapon
from tests.unit.fixtures import (
    make_minimal_save,
    make_pre_ce_save,
    write_ce_save,
    write_pre_ce_save,
)


def test_write_profile_v57_inplace(tmp_path: Path):
    save = write_ce_save(tmp_path)
    check = check_write(save)
    assert check.allowed
    assert check.profile is not None
    assert check.profile.technique == WriteTechnique.PLAYERINFO_INPLACE_V57
    assert check.identity.game_family == GameFamily.CE
    chip = status_chip(check.identity, check)
    assert "PlayerInfo in-place" in chip
    assert "OK" in chip
    assert "v57" in chip
    assert "CE" in chip


def test_write_profile_pre_ce_v57_inplace(tmp_path: Path):
    save = write_pre_ce_save(tmp_path)
    check = check_write(save)
    assert check.allowed
    assert check.identity.game_family == GameFamily.PRE_CE
    assert check.profile.technique == WriteTechnique.PLAYERINFO_INPLACE_V57
    assert any("pre-CE" in w for w in check.warnings)
    chip = status_chip(check.identity, check)
    assert "pre-CE" in chip


def test_detect_game_family_from_end_marker():
    assert detect_game_family(make_minimal_save()) == GameFamily.CE
    assert detect_game_family(make_pre_ce_save()) == GameFamily.PRE_CE
    assert 57 in SAVEGAME_VERSION_COMPAT
    assert any("1.2.0.59" in s for s in SAVEGAME_VERSION_COMPAT[57])
    assert any("1.0.8.0" in s for s in SAVEGAME_VERSION_COMPAT[57])


def test_write_profile_rejects_bad_version(tmp_path: Path):
    save = write_ce_save(tmp_path, version=1)
    check = check_write(save)
    assert not check.allowed
    assert check.profile.technique == WriteTechnique.UNSUPPORTED


def test_read_write_loadout_roundtrip(tmp_path: Path):
    save = write_ce_save(tmp_path)
    app_base = tmp_path / "app"
    app_base.mkdir()
    old = read_loadout(save.read_bytes())
    assert old.weapon_ids[2] == 7
    assert old.ammo[2] == 50
    assert old.detected[2].kind == "stock"

    weapons = list(old.weapon_ids)
    ammo = list(old.ammo)
    weapons[2] = 15  # M4
    ammo[2] = 200
    weapons[9] = 0xABCD  # mod / unknown
    ammo[9] = 10

    _o, new, bak, check = write_loadout(
        save, weapons, ammo, backup=True, app_base=app_base
    )
    assert check.allowed
    assert bak is not None
    assert new.weapon_ids[2] == 15
    assert new.ammo[2] == 200
    assert new.detected[9].kind == "mod"
    assert "unknown" in new.detected[9].name.lower() or "0x" in new.detected[9].name


def test_mod_weapon_classification():
    stock = classify_weapon(7)
    assert stock.kind == "stock"
    assert "PISTOL" in stock.name
    mod = classify_weapon(0x9001, mod_names={})
    assert mod.kind == "mod"
    named = classify_weapon(0x9001, mod_names={0x9001: "SuperRifle"})
    assert named.kind == "mod"
    assert named.name == "SuperRifle"


def test_vitality_roundtrip(tmp_path: Path):
    save = write_ce_save(tmp_path, health=180.0, armour=40.0, max_health=200, max_armour=100)
    app_base = tmp_path / "app"
    app_base.mkdir()
    old = read_vitality(save.read_bytes())
    assert abs(old.health - 180.0) < 0.01
    assert abs(old.armour - 40.0) < 0.01
    assert old.max_health == 200
    assert old.max_armour == 100

    _o, new, bak, check = set_vitality(
        save, 200.0, 100.0, 250, 150, backup=True, app_base=app_base
    )
    assert check.allowed
    assert bak is not None
    assert abs(new.health - 200.0) < 0.01
    assert abs(new.armour - 100.0) < 0.01
    assert new.max_health == 250
    assert new.max_armour == 150
    assert abs(read_vitality(save.read_bytes()).health - 200.0) < 0.01
    assert read_vitality(save.read_bytes()).max_health == 250


def test_vitality_refuses_bad_version(tmp_path: Path):
    save = write_ce_save(tmp_path, version=99)
    with pytest.raises(RuntimeError, match="Unsupported"):
        set_vitality(save, 100.0, 50.0, 200, 100, backup=False)


def test_loadout_refuses_bad_version(tmp_path: Path):
    save = write_ce_save(tmp_path, version=99)
    with pytest.raises(RuntimeError, match="Unsupported"):
        write_loadout(save, [0] * 10, [0] * 10, backup=False)


def test_resolve_write_profile_direct():
    data = make_minimal_save()
    from src.versioning import inspect_save

    # Use a fake CE path via write helper pattern
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        save = write_ce_save(Path(td))
        ident = inspect_save(save)
        profile = resolve_write_profile(ident)
        assert profile.technique == WriteTechnique.PLAYERINFO_INPLACE_V57
        assert profile.allowed
        # silence unused
        _ = data
