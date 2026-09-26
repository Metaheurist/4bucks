# Save format (PlayerInfo)

Based on [GTAMods Wiki - Saves (GTA 4)](https://gtamods.com/wiki/Saves_(GTA_4)) and local CE verification.

## Metadata (`0x00`-`0x10F`)

| Offset | Type | Field |
|--------|------|-------|
| 0x00 | uint32 | savegame version (`SAVEGAME_VERSION_NUMBER`; observed **57** for CE 1.2.0.32 / 1.2.0.43+ / 1.2.0.59 and pre-CE GTASnP samples) |
| 0x04 | uint32 | size field |
| 0x0C | char[4] | `SAVE` |
| 0x10 | wchar_t[128] | last mission title |

Data BLOCKs start at **0x110**.

## PlayerInfo (Block 1)

After the five-byte `BLOCK` string:

| Relative | Meaning |
|----------|---------|
| +0x10 | constant **192** (PlayerInfo size) |
| +0x14 | PlayerInfo start |

Offsets below are relative to **PlayerInfo start** (`BLOCK` + `0x14`):

| Offset | Type | Field |
|--------|------|-------|
| +0x08 | uint32 LE | money |
| +0x10 | uint32 LE | display money |
| +0x24 | uint16 LE | max health |
| +0x26 | uint16 LE | max armour |
| +0x50 | float LE | health |
| +0x54 | float LE | armour |
| +0x58 | uint32 | current weapon slot |
| +0x5c | uint32[10] | weapon IDs |
| +0x84 | uint16[10] | weapons ammo |

4Bucks patches these fields in place (money and display money kept equal). Locator: `src/playerinfo.py`.

## Checksum

Per the wiki, the trailing checksum is ignored by the PC game on load. The editor does not rewrite it.

## Unchanged regions

File length, block sizes, Scripts, Stats, Radar, and End block are never modified.
