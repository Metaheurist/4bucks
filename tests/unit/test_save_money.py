from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.save_money import add_money, parse_blocks, read_money, set_money
from src.versioning import check_write, inspect_save
from tests.unit.fixtures import make_minimal_save, write_ce_save


def test_parse_and_read_money():
    data = make_minimal_save(money=500_000)
    blocks = parse_blocks(data)
    assert len(blocks) >= 2
    m, d, _, _ = read_money(data)
    assert m == 500_000
    assert d == 500_000


def test_set_money_with_dual_backup(tmp_path: Path):
    save = write_ce_save(tmp_path, money=1000)
    app_base = tmp_path / "app"
    app_base.mkdir()
    old, new, bak, check = set_money(save, 250_000, backup=True, app_base=app_base)
    assert old == 1000
    assert new == 250_000
    assert check.allowed
    assert bak is not None
    assert bak.beside == save.with_name(save.name + ".backup")
    assert bak.beside.is_file()
    assert bak.app_copy.is_file()
    assert bak.app_copy.parent == app_base / "backups"
    assert read_money(save.read_bytes())[0] == 250_000
    assert read_money(bak.beside.read_bytes())[0] == 1000


def test_add_money(tmp_path: Path):
    save = write_ce_save(tmp_path, money=100)
    app_base = tmp_path / "app"
    app_base.mkdir()
    old, new, _, _ = add_money(save, 50, backup=True, app_base=app_base)
    assert old == 100
    assert new == 150


def test_version_gate_rejects_bad_version(tmp_path: Path):
    save = write_ce_save(tmp_path, version=1)
    check = check_write(save)
    assert not check.allowed
    assert "Unsupported savegame version" in check.reason
    with pytest.raises(RuntimeError, match="Unsupported"):
        set_money(save, 1, backup=False)


def test_version_gate_rejects_bad_magic(tmp_path: Path):
    save = write_ce_save(tmp_path, magic=b"XXXX")
    check = check_write(save)
    assert not check.allowed


def test_version_gate_rejects_bad_playerinfo(tmp_path: Path):
    save = write_ce_save(tmp_path, playerinfo_const=99)
    check = check_write(save)
    assert not check.allowed
    with pytest.raises(RuntimeError):
        set_money(save, 1, backup=False)


def test_inspect_identity(tmp_path: Path):
    save = write_ce_save(tmp_path, money=42)
    ident = inspect_save(save)
    assert ident.file_version == 57
    assert ident.money == 42
    assert ident.profile_kind.value == "ce_profiles"


def test_backup_fail_closed_aborts_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    save = write_ce_save(tmp_path, money=10)
    app_base = tmp_path / "app"
    app_base.mkdir()

    def boom(*_a, **_k):
        raise RuntimeError("App-folder backup failed (forced)")

    monkeypatch.setattr("src.save_money.create_dual_backup", boom)
    with pytest.raises(RuntimeError, match="backup failed"):
        set_money(save, 99, backup=True, app_base=app_base)
    assert read_money(save.read_bytes())[0] == 10
