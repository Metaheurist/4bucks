# Versioning

## Allowlist

| Savegame version dword @ 0x00 | Status |
|-------------------------------|--------|
| **57** | Supported (CE `1.2.0.59` / matching `version.txt`) |
| Other | **Write refused** |

Code: `src/versioning.py` → `ALLOWED_SAVEGAME_VERSIONS`.

## Path kinds

| Kind | Path pattern | Write |
|------|--------------|-------|
| `ce_profiles` | `...\GTA IV\Profiles\<8 hex>\` | Allowed |
| `gfwl` | `LocalAppData\...\savegames\user_*` | Refused |
| `xliveless` / unknown | Documents savegames / other | Confirm to force |

## Preflight checks

1. `SAVE` magic @ 0x0C  
2. Version ∈ allowlist  
3. ≥ 2 BLOCKs; PlayerInfo marker **192**  
4. Prefer CE Profiles path  

UI chip example: `CE save v57 · Profiles · OK to edit`.

## Cross-version game load (context)

From [GTASnP](https://gtasnp.com/help/games/gtaiv): newer CE can usually load older saves; older EXE often cannot load newer saves without downgrade. Money edits do not convert save format.
