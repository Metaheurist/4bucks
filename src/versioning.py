"""Version-aware CE save identity and write eligibility."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# CE 1.2.0.59 (and matching builds) write this SAVEGAME_VERSION_NUMBER
ALLOWED_SAVEGAME_VERSIONS: frozenset[int] = frozenset({57})

SAVE_MAGIC = b"SAVE"
PLAYERINFO_SIZE = 192
METADATA_LEN = 0x110


class ProfileKind(str, Enum):
    CE_PROFILES = "ce_profiles"
    GFWL = "gfwl"
    XLIVELESS = "xliveless"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SaveIdentity:
    path: Path
    file_version: int
    size_field: int
    magic: bytes
    mission_title: str
    profile_kind: ProfileKind
    playerinfo_const: int | None
    block_count: int
    money: int | None
    display_money: int | None

    @property
    def version_ok(self) -> bool:
        return self.file_version in ALLOWED_SAVEGAME_VERSIONS

    @property
    def magic_ok(self) -> bool:
        return self.magic == SAVE_MAGIC

    @property
    def playerinfo_ok(self) -> bool:
        return self.playerinfo_const == PLAYERINFO_SIZE


@dataclass(frozen=True)
class WriteCheck:
    identity: SaveIdentity
    allowed: bool
    reason: str
    warnings: tuple[str, ...] = ()


def classify_profile_path(path: Path) -> ProfileKind:
    parts = [p.lower() for p in path.resolve().parts]
    joined = "\\".join(parts)
    if "profiles" in parts and "gta iv" in joined:
        return ProfileKind.CE_PROFILES
    if "savegames" in parts and "user_" in path.parent.name.lower():
        return ProfileKind.GFWL
    if "savegames" in parts and (
        "gta iv" in joined or "tlad" in joined or "tbogt" in joined
    ):
        return ProfileKind.XLIVELESS
    return ProfileKind.UNKNOWN


def _decode_mission_title(data: bytes) -> str:
    raw = data[0x10:0x110]
    try:
        return raw.decode("utf-16-le", errors="ignore").split("\x00", 1)[0].strip()
    except Exception:
        return ""


def inspect_save(path: Path, data: bytes | None = None) -> SaveIdentity:
    """Parse metadata + PlayerInfo marker without writing."""
    from .save_money import parse_blocks, read_money

    path = Path(path)
    blob = data if data is not None else path.read_bytes()
    if len(blob) < METADATA_LEN + 18:
        raise RuntimeError(f"Save too short ({len(blob)} bytes)")

    file_version = struct.unpack_from("<I", blob, 0)[0]
    size_field = struct.unpack_from("<I", blob, 4)[0]
    magic = bytes(blob[0x0C:0x10])
    blocks = parse_blocks(blob)

    playerinfo_const: int | None = None
    money = display = None
    if len(blocks) >= 2:
        _, bo, bs = blocks[1]
        block = blob[bo : bo + bs]
        if len(block) >= 5 + 0x14:
            playerinfo_const = struct.unpack_from("<I", block, 5 + 0x10)[0]
        try:
            money, display, _, _ = read_money(blob)
        except Exception:
            pass

    return SaveIdentity(
        path=path,
        file_version=file_version,
        size_field=size_field,
        magic=magic,
        mission_title=_decode_mission_title(blob),
        profile_kind=classify_profile_path(path),
        playerinfo_const=playerinfo_const,
        block_count=len(blocks),
        money=money,
        display_money=display,
    )


def check_write(path: Path, data: bytes | None = None, *, allow_non_ce_path: bool = False) -> WriteCheck:
    """Return whether money edits are allowed for this save."""
    identity = inspect_save(path, data)
    warnings: list[str] = []

    if not identity.magic_ok:
        return WriteCheck(
            identity,
            False,
            f"Missing SAVE magic (got {identity.magic!r})",
        )
    if not identity.version_ok:
        return WriteCheck(
            identity,
            False,
            f"Unsupported savegame version {identity.file_version} "
            f"(allowed: {sorted(ALLOWED_SAVEGAME_VERSIONS)})",
        )
    if identity.block_count < 2:
        return WriteCheck(identity, False, f"Expected PlayerInfo block, got {identity.block_count} blocks")
    if not identity.playerinfo_ok:
        return WriteCheck(
            identity,
            False,
            f"Unexpected PlayerInfo size marker {identity.playerinfo_const} (expected {PLAYERINFO_SIZE})",
        )

    if identity.profile_kind == ProfileKind.GFWL:
        return WriteCheck(
            identity,
            False,
            "GFWL/LocalAppData save path — not supported (Complete Edition Profiles only)",
        )
    if identity.profile_kind != ProfileKind.CE_PROFILES:
        msg = f"Non-CE profile path ({identity.profile_kind.value})"
        if allow_non_ce_path:
            warnings.append(msg + " — writing anyway")
        else:
            return WriteCheck(identity, False, msg + ". Confirm to force, or move to CE Profiles.")

    name = path.name
    if not re.fullmatch(r"SGTA4\d{2}", name):
        warnings.append(f"Unusual save name {name!r} (expected SGTA4xx)")

    return WriteCheck(identity, True, "OK", tuple(warnings))


def status_chip(identity: SaveIdentity, check: WriteCheck | None = None) -> str:
    kind = {
        ProfileKind.CE_PROFILES: "Profiles",
        ProfileKind.GFWL: "GFWL",
        ProfileKind.XLIVELESS: "XLiveLess",
        ProfileKind.UNKNOWN: "Unknown path",
    }[identity.profile_kind]
    if check is None:
        ok = identity.version_ok and identity.magic_ok and identity.playerinfo_ok
    else:
        ok = check.allowed
    state = "OK to edit" if ok else "write blocked"
    return f"CE save v{identity.file_version} · {kind} · {state}"
