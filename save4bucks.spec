# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec - EXE name/arch from SAVE4BUCKS_ARCH (x64|x86)."""
import os
from pathlib import Path

root = Path(SPECPATH)
assets = root / "assets"
arch = os.environ.get("SAVE4BUCKS_ARCH", "x64").strip().lower()
if arch not in ("x64", "x86"):
    raise SystemExit(f"SAVE4BUCKS_ARCH must be x64 or x86, got {arch!r}")
exe_name = f"Save4Bucks-{arch}"

a = Analysis(
    [str(root / "save4bucks.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(assets / "icon.ico"), "assets"),
        (str(assets / "icon.png"), "assets"),
    ],
    hiddenimports=[
        "src",
        "src.app",
        "src.detect",
        "src.save_money",
        "src.versioning",
        "src.backup",
        "src.settings",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets / "icon.ico"),
)
