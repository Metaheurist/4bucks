"""Stock + episodic GTA IV weapon IDs (GTAMods List of Weapons)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeaponDef:
    id: int
    name: str
    stock: bool = True


# IDs 0..57 from https://gtamods.com/wiki/List_of_Weapons_(GTA4)
_STOCK: tuple[tuple[int, str], ...] = (
    (0, "UNARMED"),
    (1, "BASEBALLBAT"),
    (2, "POOLCUE"),
    (3, "KNIFE"),
    (4, "GRENADE"),
    (5, "MOLOTOV"),
    (6, "ROCKET"),
    (7, "PISTOL"),
    (8, "UNUSED0"),
    (9, "DEAGLE"),
    (10, "SHOTGUN"),
    (11, "BARETTA"),
    (12, "MICRO_UZI"),
    (13, "MP5"),
    (14, "AK47"),
    (15, "M4"),
    (16, "SNIPERRIFLE"),
    (17, "M40A1"),
    (18, "RLAUNCHER"),
    (19, "FTHROWER"),
    (20, "MINIGUN"),
    (21, "EPISODIC_1 (GRENADE LAUNCHER)"),
    (22, "EPISODIC_2 (ASSAULT SHOTGUN)"),
    (23, "EPISODIC_3 (UNUSED)"),
    (24, "EPISODIC_4 (BROKEN POOL CUE)"),
    (25, "EPISODIC_5 (GL GRENADE)"),
    (26, "EPISODIC_6 (SAWN-OFF)"),
    (27, "EPISODIC_7 (AUTO PISTOL)"),
    (28, "EPISODIC_8 (PIPE BOMB)"),
    (29, "EPISODIC_9 (PISTOL .44)"),
    (30, "EPISODIC_10 (AA12 EXPLOSIVE)"),
    (31, "EPISODIC_11 (AA12)"),
    (32, "EPISODIC_12 (P90)"),
    (33, "EPISODIC_13 (GOLDEN UZI)"),
    (34, "EPISODIC_14 (M249)"),
    (35, "EPISODIC_15 (ADV SNIPER)"),
    (36, "EPISODIC_16 (STICKY BOMB)"),
    (37, "EPISODIC_17 (BUZZARD RL)"),
    (38, "EPISODIC_18 (BUZZARD ROCKET)"),
    (39, "EPISODIC_19 (BUZZARD MINIGUN)"),
    (40, "EPISODIC_20 (APC CANNON)"),
    (41, "EPISODIC_21 (PARACHUTE)"),
    (42, "EPISODIC_22 (UNUSED)"),
    (43, "EPISODIC_23 (UNUSED)"),
    (44, "EPISODIC_24 (UNUSED)"),
    (45, "CAMERA"),
    (46, "OBJECT"),
    (47, "WEAPONTYPE_LAST"),
    (48, "ARMOUR"),
    (49, "RAMMEDBYCAR"),
    (50, "RUNOVERBYCAR"),
    (51, "EXPLOSION"),
    (52, "UZI_DRIVEBY"),
    (53, "DROWNING"),
    (54, "FALL"),
    (55, "UNIDENTIFIED"),
    (56, "ANYMELEE"),
    (57, "ANYWEAPON"),
)

STOCK_WEAPONS: dict[int, WeaponDef] = {
    wid: WeaponDef(id=wid, name=name, stock=True) for wid, name in _STOCK
}

# Practical giveable weapons for the UI dropdown (exclude meta damage types)
UI_WEAPON_IDS: tuple[int, ...] = tuple(
    i
    for i in range(0, 46)
    if i not in (8, 23, 42, 43, 44)  # unused / unused episodic
)


def stock_name(weapon_id: int) -> str | None:
    w = STOCK_WEAPONS.get(weapon_id)
    return w.name if w else None


def is_stock_id(weapon_id: int) -> bool:
    return weapon_id in STOCK_WEAPONS


def dropdown_options() -> list[tuple[str, int]]:
    """(label, id) pairs for weapon pickers."""
    opts: list[tuple[str, int]] = []
    for wid in UI_WEAPON_IDS:
        name = STOCK_WEAPONS[wid].name
        opts.append((f"{wid}: {name}", wid))
    return opts
