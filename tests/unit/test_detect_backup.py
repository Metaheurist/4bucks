from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backup import create_dual_backup, is_backup_name
from src.detect import list_slots, slot_label
from tests.unit.fixtures import write_ce_save


def test_slot_labels():
    assert slot_label("SGTA400") == "Slot 1"
    assert slot_label("SGTA412") == "Autosave (IV)"
    assert slot_label("SGTA413") == "Autosave (TLAD)"


def test_list_slots_skips_backups(tmp_path: Path):
    save = write_ce_save(tmp_path, name="SGTA400", money=1)
    create_dual_backup(save, 1, base=tmp_path / "app")
    (save.parent / "SGTA400.bak_before_money_1").write_bytes(save.read_bytes())
    slots = list_slots(save.parent)
    names = [s.slot_name for s in slots]
    assert names == ["SGTA400"]


def test_is_backup_name():
    assert is_backup_name("SGTA412.backup")
    assert is_backup_name("SGTA412.bak_before_money_100")
    assert not is_backup_name("SGTA412")
