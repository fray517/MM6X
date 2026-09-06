# Mod staging
Только MM6X-authored/generated files. Не хранить copied proprietary
assets и не копировать vanilla loca/CSV целиком.

Сейчас:

- `mod/Localisation/en|ru/loca.xml` — 32 ключа MM6X
- `mod/Dialog/Mm6JanisDialog.xml` — квест Дозора (accept/turn-in)
- `mod/Dialog/Mm6AndoverDialog.xml` — заглушка письма Сулмана
- `mod/StaticData/*.csv` — NPC 20000/20001, quest 20000/20001,
  tokens 20000–20002, lorebook 20000
- `mod/build_manifest.json` — SHA-256 inventory для stage

```powershell
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\converters\generate_mmx_dialog.py --write --check-vanilla
python tools\converters\generate_mmx_staticdata.py --write --check-vanilla
python tools\validators\validate_mmx_mod.py
python tools\converters\build_mmx_manifest.py --write
```

В игру не ставится без явного stage:

```powershell
python tools\modding\stage_mmx_mod.py --dry-run
# python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
# python tools\modding\stage_mmx_mod.py --restore --yes-i-understand
```

Stage **merge** loca/CSV в StreamingAssets (не replace целиком).
Backup: `backups/mmx/mm6x-overlay/`.

