"""Dual-location Autobackup for 4Bucks."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class BackupResult:
    beside: Path
    app_copy: Path


def app_dir() -> Path:
    """Directory of Save4Bucks.exe or repo root when run from source."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def backups_dir(base: Path | None = None) -> Path:
    d = (base or app_dir()) / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def beside_backup_path(save: Path) -> Path:
    return save.with_name(save.name + ".backup")


def app_backup_path(save: Path, old_money: int, base: Path | None = None) -> Path:
    profile = save.parent.name
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{profile}_{save.name}_{stamp}_m{old_money}.backup"
    return backups_dir(base) / name


def create_dual_backup(save: Path, old_money: int, *, base: Path | None = None) -> BackupResult:
    """
    Copy save to:
      1) {SGTA4xx}.backup beside the save (overwrite)
      2) app_dir/backups/{profile}_{slot}_{stamp}_m{old}.backup
    Fail closed: raise if either copy fails.
    """
    save = Path(save)
    if not save.is_file():
        raise FileNotFoundError(f"Save not found: {save}")

    beside = beside_backup_path(save)
    app_copy = app_backup_path(save, old_money, base=base)

    try:
        shutil.copy2(save, beside)
    except OSError as e:
        raise RuntimeError(f"Beside-save backup failed ({beside}): {e}") from e

    try:
        app_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(save, app_copy)
    except OSError as e:
        raise RuntimeError(f"App-folder backup failed ({app_copy}): {e}") from e

    if not beside.is_file() or beside.stat().st_size != save.stat().st_size:
        raise RuntimeError(f"Beside-save backup incomplete: {beside}")
    if not app_copy.is_file() or app_copy.stat().st_size != save.stat().st_size:
        raise RuntimeError(f"App-folder backup incomplete: {app_copy}")

    return BackupResult(beside=beside, app_copy=app_copy)


def is_backup_name(name: str) -> bool:
    lower = name.lower()
    return (
        lower.endswith(".backup")
        or ".bak_before_money_" in lower
        or ".backup." in lower
    )
