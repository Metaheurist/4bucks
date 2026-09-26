"""Version-aware CE save identity, write profiles, and eligibility."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Observed SAVEGAME_VERSION_NUMBER (file dword @ 0x00 / version.txt).
# Firecrawl + GTASnP sample survey (2026-09): dword 57 is shared across the
# EXE families below. No other PC dword values were found in public sources
# or downloaded SGTA4xx samples; local CE 1.2.0.59 version.txt is 57.
ALLOWED_SAVEGAME_VERSIONS: frozenset[int] = frozenset({57})

# EXE / launcher families known to emit or accept saves with these dwords.
# Labels follow GTASnP categories; 1.2.0.59 is the local Complete Edition build.
SAVEGAME_VERSION_COMPAT: dict[int, tuple[str, ...]] = {
    57: (
        "1.0.8.0 IV / 1.1.3.0 EFLC and older",
        "1.2.0.32 CE",
        "1.2.0.43 CE and newer",
        "1.2.0.59 CE",
    ),
}

SAVE_MAGIC = b"SAVE"
PLAYERINFO_SIZE = 192
METADATA_LEN = 0x110
END_MARKER = b"END\x00"
# GFWL-era End blocks keep a trailing signature after END (often 0xCD padding).
_PRE_CE_TRAILING_MIN = 8


class ProfileKind(str, Enum):
    CE_PROFILES = "ce_profiles"
    GFWL = "gfwl"
    XLIVELESS = "xliveless"
    UNKNOWN = "unknown"


class GameFamily(str, Enum):
    """
    Structural family from End-block shape (not from the version dword).

    GTASnP splits CE into 1.2.0.32 vs 1.2.0.43+ using deeper format cues;
    Save 4Bucks only needs PRE_CE vs CE for PlayerInfo write safety (Parik:
    PlayerInfo layout is shared; End trim and Radar wchar differ).
    """

    PRE_CE = "pre_ce"
    CE = "ce"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        return {
            GameFamily.PRE_CE: "pre-CE",
            GameFamily.CE: "CE",
            GameFamily.UNKNOWN: "unknown family",
        }[self]

    @property
    def gtasnp_hint(self) -> str:
        return {
            GameFamily.PRE_CE: "1.0.8.0 IV / 1.1.3.0 EFLC and older (typical)",
            GameFamily.CE: "1.2.0.32 / 1.2.0.43+ / 1.2.0.59 CE (typical)",
            GameFamily.UNKNOWN: "unclassified End block",
        }[self]


class WriteTechnique(str, Enum):
    """How PlayerInfo fields are patched for a given save family."""

    # Name keeps "V57" because that is the only allowlisted dword; the same
    # in-place offsets apply to every GameFamily that carries dword 57.
    PLAYERINFO_INPLACE_V57 = "playerinfo_inplace_v57"
    UNSUPPORTED = "unsupported"

    @property
    def label(self) -> str:
        return {
            WriteTechnique.PLAYERINFO_INPLACE_V57: "PlayerInfo in-place",
            WriteTechnique.UNSUPPORTED: "unsupported",
        }[self]


@dataclass(frozen=True)
class SaveWriteProfile:
    """Named write technique resolved from save identity + path checks."""

    technique: WriteTechnique
    allowed: bool
    reason: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class WriteCheck:
    identity: "SaveIdentity"
    allowed: bool
    reason: str
    warnings: tuple[str, ...] = ()
    profile: SaveWriteProfile | None = None


@dataclass(frozen=True)
class SaveIdentity:
    path: Path
    file_version: int
    size_field: int
    magic: bytes
    mission_title: str
    profile_kind: ProfileKind
    game_family: GameFamily
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

    @property
    def compat_exes(self) -> tuple[str, ...]:
        return SAVEGAME_VERSION_COMPAT.get(self.file_version, ())


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


def detect_game_family(blob: bytes) -> GameFamily:
    """
    Classify save family from the End marker trail.

    Pre-CE / GFWL builds typically append a signature after ``END\\0``
    (often including ``CD CD CD CD`` padding). Complete Edition trims that
    trail so ``END\\0`` sits at (or within a few bytes of) EOF.
    """
    idx = blob.rfind(END_MARKER)
    if idx < 0:
        return GameFamily.UNKNOWN
    trailing = len(blob) - (idx + len(END_MARKER))
    if trailing >= _PRE_CE_TRAILING_MIN:
        return GameFamily.PRE_CE
    if trailing <= 4:
        return GameFamily.CE
    return GameFamily.UNKNOWN


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
    game_family = detect_game_family(blob)

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
        game_family=game_family,
        playerinfo_const=playerinfo_const,
        block_count=len(blocks),
        money=money,
        display_money=display,
    )


def resolve_write_profile(
    identity: SaveIdentity, *, allow_non_ce_path: bool = False
) -> SaveWriteProfile:
    """
    Select the write technique for this save.

    Dword 57 spans pre-CE and CE EXE families (GTASnP survey). Parik: PlayerInfo
    layout matches across CE vs older IV; only End-block trim and Radar Blip
    sprite char→wchar differ. Money / weapons / vitality use in-place PlayerInfo
    patches for every allowlisted dword. Unsupported dwords and GFWL paths are
    refused rather than inventing Radar/End rewrites.
    """
    warnings: list[str] = []

    if not identity.magic_ok:
        return SaveWriteProfile(
            WriteTechnique.UNSUPPORTED,
            False,
            f"Missing SAVE magic (got {identity.magic!r})",
        )
    if not identity.version_ok:
        return SaveWriteProfile(
            WriteTechnique.UNSUPPORTED,
            False,
            f"Unsupported savegame version {identity.file_version} "
            f"(allowed: {sorted(ALLOWED_SAVEGAME_VERSIONS)})",
        )
    if identity.block_count < 2:
        return SaveWriteProfile(
            WriteTechnique.UNSUPPORTED,
            False,
            f"Expected PlayerInfo block, got {identity.block_count} blocks",
        )
    if not identity.playerinfo_ok:
        return SaveWriteProfile(
            WriteTechnique.UNSUPPORTED,
            False,
            f"Unexpected PlayerInfo size marker {identity.playerinfo_const} "
            f"(expected {PLAYERINFO_SIZE})",
        )

    if identity.profile_kind == ProfileKind.GFWL:
        return SaveWriteProfile(
            WriteTechnique.UNSUPPORTED,
            False,
            "GFWL/LocalAppData save path - not supported (Complete Edition Profiles only)",
        )
    if identity.profile_kind != ProfileKind.CE_PROFILES:
        msg = f"Non-CE profile path ({identity.profile_kind.value})"
        if allow_non_ce_path:
            warnings.append(msg + " - writing anyway")
        else:
            return SaveWriteProfile(
                WriteTechnique.UNSUPPORTED,
                False,
                msg + ". Confirm to force, or move to CE Profiles.",
            )

    if identity.game_family == GameFamily.PRE_CE:
        warnings.append(
            "pre-CE End signature - PlayerInfo layout OK (Parik); "
            "file still loads only on matching / downgraded EXEs"
        )
    elif identity.game_family == GameFamily.UNKNOWN:
        warnings.append("End block family unclassified - PlayerInfo gate passed")

    name = identity.path.name
    if not re.fullmatch(r"SGTA4\d{2}", name):
        warnings.append(f"Unusual save name {name!r} (expected SGTA4xx)")

    return SaveWriteProfile(
        WriteTechnique.PLAYERINFO_INPLACE_V57,
        True,
        "OK",
        tuple(warnings),
    )


def check_write(
    path: Path, data: bytes | None = None, *, allow_non_ce_path: bool = False
) -> WriteCheck:
    """Return whether PlayerInfo edits are allowed for this save."""
    identity = inspect_save(path, data)
    profile = resolve_write_profile(identity, allow_non_ce_path=allow_non_ce_path)
    return WriteCheck(
        identity,
        profile.allowed,
        profile.reason,
        profile.warnings,
        profile,
    )


def status_chip(identity: SaveIdentity, check: WriteCheck | None = None) -> str:
    kind = {
        ProfileKind.CE_PROFILES: "Profiles",
        ProfileKind.GFWL: "GFWL",
        ProfileKind.XLIVELESS: "XLiveLess",
        ProfileKind.UNKNOWN: "Unknown path",
    }[identity.profile_kind]
    if check is None:
        profile = resolve_write_profile(identity, allow_non_ce_path=True)
        ok = profile.allowed
        technique = profile.technique.label
    else:
        ok = check.allowed
        technique = (
            check.profile.technique.label
            if check.profile is not None
            else resolve_write_profile(identity).technique.label
        )
    state = "OK" if ok else "write blocked"
    return (
        f"v{identity.file_version} · {identity.game_family.label} · "
        f"{kind} · {technique} · {state}"
    )
