# Mod staging
Только MM6X-authored/generated files. Не хранить copied proprietary
assets и не копировать vanilla loca/CSV целиком.

Сейчас:

- `mod/Localisation/en|ru/loca.xml` — 54 ключа MM6X (M4-005/006)
- `mod/Dialog/Mm6JanisDialog.xml` — #83 accept/key/progress/turn-in
  (FollowUp 20001 + removeTokenID; M4-004)
- `mod/Dialog/Mm6AndoverDialog.xml` — письмо Сулмана #81 (M4-003)
- `mod/Maps/New_Sorpigal.xml` — greybox + gate → Goblinwatch
- `mod/Maps/Goblinwatch.xml` — stub 8×8 + codex chest (M4-006)
- `mod/StaticData/*.csv` — NPC 20000/20001; quests 20000–20002;
  tokens 20000–20004; lorebook 20000
- `mod/build_manifest.json` — SHA-256 inventory для stage

```powershell
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\converters\generate_mmx_dialog.py --write --check-vanilla
python tools\converters\generate_mmx_staticdata.py --write --check-vanilla
python tools\converters\generate_mmx_map.py --write
python tools\validators\validate_mmx_mod.py
python tools\converters\build_mmx_manifest.py --write
```

В игру не ставится без явного stage:

```powershell
python tools\modding\stage_mmx_mod.py --dry-run
# python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
# python tools\modding\stage_mmx_mod.py --restore --yes-i-understand
```

Stage **merge** loca/CSV; **copy** Dialog + Maps.
Backup: `backups/mmx/mm6x-overlay/`.

