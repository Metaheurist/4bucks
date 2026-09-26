# Savegame versioning

App SemVer is separate - see [`src/__init__.py`](../src/__init__.py) and [CHANGELOG.md](CHANGELOG.md).

## Allowlist (file dword @ 0x00)

| Savegame version dword | Status | Observed EXE families |
|------------------------|--------|------------------------|
| **57** | Supported (PlayerInfo in-place) | `1.0.8.0 IV / 1.1.3.0 EFLC and older`, `1.2.0.32 CE`, `1.2.0.43 CE and newer`, `1.2.0.59 CE` |
| Other | Write refused | - |

Code: `src/versioning.py` → `ALLOWED_SAVEGAME_VERSIONS`, `SAVEGAME_VERSION_COMPAT`, `GameFamily`, `WriteTechnique`, `SaveWriteProfile`.

### Why only 57?

Public docs ([GTAMods](https://gtamods.com/wiki/Saves_(GTA_4))) say the dword comes from `common/data/version.txt` `[SAVEGAME_VERSION_NUMBER]`, but they do not publish a dword↔patch table. Survey (Firecrawl + GTASnP downloads + local CE install):

- Local CE `1.2.0.59` `version.txt` → **57**
- GTASnP samples labeled `1.2.0.43 CE and newer`, `1.2.0.32 CE`, and `1.0.8.0 IV / 1.1.3.0 EFLC and older` all carried dword **57**
- No other dword values appeared in sampled `SGTA4xx` files

GTASnP still splits EXE families by End/Radar structure, not by this dword. Save 4Bucks therefore allowlists **57** and classifies family separately.

## Game family (End block)

| Family | Detection | Typical GTASnP label |
|--------|-----------|----------------------|
| `ce` | `END\\0` at/near EOF (trimmed signature) | 1.2.0.32 / 1.2.0.43+ / 1.2.0.59 |
| `pre_ce` | ≥8 bytes after `END\\0` (GFWL-style trail, often `CD CD CD CD`) | 1.0.8.0 / 1.1.3.0 and older |
| `unknown` | No `END` marker or odd trail | - |

PlayerInfo edits are allowed for both `ce` and `pre_ce` when dword is 57 and the PlayerInfo marker is 192. `pre_ce` writes add a warning (load still requires a matching / downgraded EXE).

## Write techniques

| Technique | When | Behaviour |
|-----------|------|-----------|
| `PLAYERINFO_INPLACE_V57` | Allowlisted dword (57), PlayerInfo marker 192, eligible path | Patch money, weapons, and vitality in PlayerInfo only |
| `UNSUPPORTED` | Anything else | Refuse with reason |

Parik ([GTAForums CE save format](https://gtaforums.com/topic/952609-gta4-save-file-format/)): CE PlayerInfo matches older IV; End-block signature trim and Radar Blip sprite `char`→`wchar_t` differ. End and Radar are not rewritten.

UI chip example: `v57 · CE · Profiles · PlayerInfo in-place · OK`.

## Path kinds

| Kind | Path pattern | Write |
|------|--------------|-------|
| `ce_profiles` | `...\\GTA IV\\Profiles\\<8 hex>\\` | Allowed |
| `gfwl` | `LocalAppData\\...\\savegames\\user_*` | Refused |
| `xliveless` / unknown | Documents savegames / other | Confirm to force |

## Preflight checks

1. `SAVE` magic @ 0x0C
2. Version in allowlist
3. At least 2 BLOCKs; PlayerInfo marker **192**
4. Prefer CE Profiles path
5. Classify End-block family (informational + warnings)

## Cross-version load

From [GTASnP](https://gtasnp.com/help/games/gtaiv) and [update #42](https://gtasnp.com/upload/updates/read/42):

| EXE family | Can load | Cannot load without downgrade |
|------------|----------|-------------------------------|
| 1.0.8.0 / 1.1.3.0 and older | Older same-era saves | 1.2.0.32+ CE saves |
| 1.2.0.32 CE | Older saves | 1.2.0.43+ saves |
| 1.2.0.43+ / 1.2.0.59 CE | All previous | - |

PlayerInfo edits do not convert or downgrade save format. Writing money/weapons/vitality on a `pre_ce` or early-CE file does not make it load on an incompatible EXE.
