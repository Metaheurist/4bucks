# Save format (money)

Based on [GTAMods Wiki - Saves (GTA 4)](https://gtamods.com/wiki/Saves_(GTA_4)) and local CE verification.

## Metadata (`0x00`-`0x10F`)

| Offset | Type | Field |
|--------|------|-------|
| 0x00 | uint32 | savegame version (`SAVEGAME_VERSION_NUMBER`, CE 1.2.0.59 → **57**) |
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
| +0x14+0x08 | **money** uint32 LE |
| +0x14+0x10 | **display money** uint32 LE |

Save 4Bucks writes **only** those two fields and keeps them equal.

## Checksum

Wiki: trailing checksum is **ignored** by the PC game for load. We do not rewrite it.

## What we never change

File length, block sizes, Scripts, Stats, Radar, End block.
