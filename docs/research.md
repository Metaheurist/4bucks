# Research notes

Sources used for version-aware PlayerInfo editing.

Local research dumps (not in this repository):

`D:\SteamLibrary\steamapps\common\Grand Theft Auto IV\_mod_work\.firecrawl\`

| File | Content |
|------|---------|
| `agent-save-version.json` | Version matrix and edit rules |
| `gtamods-saves.md` | Wiki scrape |
| `gtasnp-gtaiv.md` | GTASnP version help |
| `forum-save-format.md` | GTAForums CE format thread (Parik) |

Public URLs:

- https://gtamods.com/wiki/Saves_(GTA_4)
- https://gtamods.com/wiki/List_of_Weapons_(GTA4)
- https://gtasnp.com/help/games/gtaiv
- https://gtasnp.com/upload/updates/read/42
- https://gtaforums.com/topic/952609-gta4-save-file-format/

## SAVEGAME_VERSION_NUMBER survey (2026-09)

| Source | Result |
|--------|--------|
| Local CE `GTAIV/common/data/version.txt` (EXE 1.2.0.59) | `[SAVEGAME_VERSION_NUMBER] 57` |
| GTASnP downloads labeled `1.2.0.43 CE and newer` (n≈39) | dword @ 0x00 = **57** |
| GTASnP download labeled `1.2.0.32 CE` | dword = **57** |
| GTASnP downloads labeled `1.0.8.0 IV / 1.1.3.0 EFLC and older` | dword = **57** |
| Public web / wiki / agent search for other dwords | No published dword↔patch table; no other integers confirmed |

Family split uses End-block shape (GFWL trail vs trimmed CE `END`), matching Parik / GTASnP practice rather than the dword alone. See [versioning.md](versioning.md).

## Write adaptation

Parik: CE vs older - PlayerInfo unchanged; End-block signature trimmed; Radar Blip sprite field `char`→`wchar_t`. Save 4Bucks uses `PLAYERINFO_INPLACE_V57` for allowlisted dword **57** across detected CE and pre-CE families (money, weapons, vitality) and refuses unsupported dwords.

GTASnP: cross-version load asymmetry (1.0.8 / 1.2.0.32 / 1.2.0.43+). Edits do not downgrade or convert save format.

Weapon IDs: [List of Weapons (GTA4)](https://gtamods.com/wiki/List_of_Weapons_(GTA4)). Unknown slot IDs are treated as mod/custom.
