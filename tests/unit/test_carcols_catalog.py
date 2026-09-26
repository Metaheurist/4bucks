"""Unit tests for carcols.dat paint swatch parsing."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.carcols_catalog import (
    clear_carcols_cache,
    list_paint_colors,
    load_color_table,
    paint_label,
    parse_col_table,
)


FIXTURE = ROOT / "tests" / "fixtures" / "carcols_min.dat"


def test_parse_col_table_indices_and_labels():
    text = FIXTURE.read_text(encoding="utf-8")
    table = parse_col_table(text)
    assert set(table) == {0, 1, 27, 133}
    assert table[0].label == "Black"
    assert table[1].r == 37 and table[1].label == "Black Poly"
    assert table[27].label == "Very Red"
    assert table[133].label == "Very White"


def test_load_color_table_from_install_layout(tmp_path: Path):
    clear_carcols_cache()
    data = tmp_path / "common" / "data"
    data.mkdir(parents=True)
    (data / "carcols.dat").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    # Episodic overlay adds a higher index
    tbogt = tmp_path / "TBoGT" / "common" / "data"
    tbogt.mkdir(parents=True)
    (tbogt / "carcols.dat").write_text(
        "col\n245,180,0,-,yellow\t\t\t# 134 SuperD yellow\nend\n",
        encoding="utf-8",
    )
    table = load_color_table(str(tmp_path))
    assert 0 in table and 27 in table and 134 in table
    assert table[134].label == "SuperD yellow"
    assert paint_label(27, tmp_path) == "27 · Very Red"
    labels = dict(list_paint_colors(tmp_path))
    assert labels[134] == "134 · SuperD yellow"
    clear_carcols_cache()


def test_fallback_without_install():
    clear_carcols_cache()
    table = load_color_table("")
    assert 0 in table
    assert paint_label(99, None).startswith("99 ·")
