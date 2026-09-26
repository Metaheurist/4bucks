"""Stock + episodic GTA IV weapon IDs (GTAMods List of Weapons)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Episode = Literal["base", "tlad", "tbogt", "shared", "meta"]
Category = Literal[
    "melee",
    "handgun",
    "shotgun",
    "smg",
    "assault",
    "sniper",
    "heavy",
    "thrown",
    "special",
    "meta",
]


@dataclass(frozen=True)
class WeaponDef:
    id: int
    name: str
    stock: bool = True
    episode: Episode = "base"
    category: Category = "special"


# IDs 0..57 from https://gtamods.com/wiki/List_of_Weapons_(GTA4)
_RAW: tuple[tuple[int, str, Episode, Category], ...] = (
    (0, "UNARMED", "shared", "melee"),
    (1, "BASEBALLBAT", "base", "melee"),
    (2, "POOLCUE", "base", "melee"),
    (3, "KNIFE", "base", "melee"),
    (4, "GRENADE", "base", "thrown"),
    (5, "MOLOTOV", "base", "thrown"),
    (6, "ROCKET", "base", "heavy"),
    (7, "PISTOL", "base", "handgun"),
    (8, "UNUSED0", "meta", "meta"),
    (9, "DEAGLE", "base", "handgun"),
    (10, "SHOTGUN", "base", "shotgun"),
    (11, "BARETTA", "base", "shotgun"),
    (12, "MICRO_UZI", "base", "smg"),
    (13, "MP5", "base", "smg"),
    (14, "AK47", "base", "assault"),
    (15, "M4", "base", "assault"),
    (16, "SNIPERRIFLE", "base", "sniper"),
    (17, "M40A1", "base", "sniper"),
    (18, "RLAUNCHER", "base", "heavy"),
    (19, "FTHROWER", "base", "heavy"),
    (20, "MINIGUN", "base", "heavy"),
    # TLAD
    (21, "EPISODIC_1 (GRENADE LAUNCHER)", "tlad", "heavy"),
    (22, "EPISODIC_2 (ASSAULT SHOTGUN)", "tlad", "shotgun"),
    (23, "EPISODIC_3 (UNUSED)", "meta", "meta"),
    (24, "EPISODIC_4 (BROKEN POOL CUE)", "tlad", "melee"),
    (25, "EPISODIC_5 (GL GRENADE)", "tlad", "thrown"),
    (26, "EPISODIC_6 (SAWN-OFF)", "tlad", "shotgun"),
    (27, "EPISODIC_7 (AUTO PISTOL)", "tlad", "handgun"),
    (28, "EPISODIC_8 (PIPE BOMB)", "tlad", "thrown"),
    # TBoGT
    (29, "EPISODIC_9 (PISTOL .44)", "tbogt", "handgun"),
    (30, "EPISODIC_10 (AA12 EXPLOSIVE)", "tbogt", "shotgun"),
    (31, "EPISODIC_11 (AA12)", "tbogt", "shotgun"),
    (32, "EPISODIC_12 (P90)", "tbogt", "smg"),
    (33, "EPISODIC_13 (GOLDEN UZI)", "tbogt", "smg"),
    (34, "EPISODIC_14 (M249)", "tbogt", "assault"),
    (35, "EPISODIC_15 (ADV SNIPER)", "tbogt", "sniper"),
    (36, "EPISODIC_16 (STICKY BOMB)", "tbogt", "thrown"),
    (37, "EPISODIC_17 (BUZZARD RL)", "tbogt", "heavy"),
    (38, "EPISODIC_18 (BUZZARD ROCKET)", "tbogt", "heavy"),
    (39, "EPISODIC_19 (BUZZARD MINIGUN)", "tbogt", "heavy"),
    (40, "EPISODIC_20 (APC CANNON)", "tbogt", "heavy"),
    (41, "EPISODIC_21 (PARACHUTE)", "tbogt", "special"),
    (42, "EPISODIC_22 (UNUSED)", "meta", "meta"),
    (43, "EPISODIC_23 (UNUSED)", "meta", "meta"),
    (44, "EPISODIC_24 (UNUSED)", "meta", "meta"),
    (45, "CAMERA", "shared", "special"),
    (46, "OBJECT", "meta", "meta"),
    (47, "WEAPONTYPE_LAST", "meta", "meta"),
    (48, "ARMOUR", "meta", "meta"),
    (49, "RAMMEDBYCAR", "meta", "meta"),
    (50, "RUNOVERBYCAR", "meta", "meta"),
    (51, "EXPLOSION", "meta", "meta"),
    (52, "UZI_DRIVEBY", "meta", "meta"),
    (53, "DROWNING", "meta", "meta"),
    (54, "FALL", "meta", "meta"),
    (55, "UNIDENTIFIED", "meta", "meta"),
    (56, "ANYMELEE", "meta", "meta"),
    (57, "ANYWEAPON", "meta", "meta"),
)

STOCK_WEAPONS: dict[int, WeaponDef] = {
    wid: WeaponDef(id=wid, name=name, stock=True, episode=ep, category=cat)
    for wid, name, ep, cat in _RAW
}

# Giveable weapons for pickers (exclude unused / meta damage types)
UI_WEAPON_IDS: tuple[int, ...] = tuple(
    wid
    for wid, name, ep, cat in _RAW
    if cat != "meta" and "UNUSED" not in name
)


def stock_name(weapon_id: int) -> str | None:
    w = STOCK_WEAPONS.get(weapon_id)
    return w.name if w else None


def is_stock_id(weapon_id: int) -> bool:
    return weapon_id in STOCK_WEAPONS and STOCK_WEAPONS[weapon_id].category != "meta"


def short_name(weapon_id: int) -> str:
    """Compact label for slot cards."""
    w = STOCK_WEAPONS.get(weapon_id)
    if weapon_id == 0:
        return "Empty"
    if w is None:
        return f"0x{weapon_id:X}"
    name = w.name
    if "(" in name and ")" in name:
        return name[name.find("(") + 1 : name.rfind(")")].strip()
    return name.replace("_", " ").title()


def weapons_for(
    episode: str = "iv",
    *,
    category: Category | None = None,
) -> list[WeaponDef]:
    """
    Filter stock weapons for the episode strip.

    episode: iv | tlad | tbogt | all | mods
    (mods returns empty - UI handles custom IDs separately)
    """
    key = (episode or "iv").lower()
    if key in ("mods", "mod"):
        return []
    out: list[WeaponDef] = []
    for wid in UI_WEAPON_IDS:
        w = STOCK_WEAPONS[wid]
        if category is not None and w.category != category:
            continue
        if key in ("all", "*"):
            out.append(w)
            continue
        if key in ("iv", "base"):
            if w.episode in ("base", "shared"):
                out.append(w)
        elif key == "tlad":
            if w.episode in ("tlad", "shared"):
                out.append(w)
        elif key == "tbogt":
            if w.episode in ("tbogt", "shared"):
                out.append(w)
        else:
            if w.episode in ("base", "shared"):
                out.append(w)
    return out


def dropdown_options(episode: str = "all") -> list[tuple[str, int]]:
    """(label, id) pairs for weapon pickers."""
    return [(f"{w.id}: {w.name}", w.id) for w in weapons_for(episode)]


def picker_options(episode: str = "iv") -> list[tuple[str, int]]:
    """Friendly labels for the weapons picker dialog."""
    opts = [(f"{short_name(w.id)}  ·  {w.id}", w.id) for w in weapons_for(episode)]
    if not opts and episode.lower() in ("mods", "mod"):
        return []
    return opts
