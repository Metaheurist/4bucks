# Known issues

- **OneDrive / Controlled Folder Access** - CE saves live under Documents; sync or locks can prevent edits from sticking. Confirm the Profiles path the game uses.
- **Autosave episode mix-up** - `SGTA412` = IV, `413` = TLAD, `414` = TBoGT. Loading the wrong episode autosave can error.
- **GTASnP slot naming** - some pages call `SGTA400` autosave; for CE trust GTAMods (slot-1 + 412/413/414 autosaves).
- **Checksum fixers for SA/III** - not applicable to IV CE PlayerInfo edits.
- **Zolika IVSaveEditor** - peer tool; listed support skews to 1.0.x - do not assume CE validation.
- **Live memory trainers** - unrelated; Save 4Bucks is save-file only.
- **Editing while the game runs** - changes may be overwritten on exit.
- **Repo / reinstall** - `backups\` next to the app can be lost if that folder is deleted; keep an extra copy if needed.
- **Flet x86** - desktop client is primarily x64; x86 packs may fail depending on the Flet desktop build.

See [research.md](research.md) for format and version sources.
