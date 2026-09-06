# M2 — Conversion Framework

Цель: из normalized MM6 JSON стабильно получать staged MMX
контент (loca / Dialog / StaticData / maps), без записи в игру
без `--dry-run` / backup.

New Sorpigal как карта — **M3**, не здесь.

## Сделано

- Машинный реестр: `tools/converters/id_registry.json` (M2-001)
- Аллокатор: `tools/converters/allocate_mmx_ids.py` (M2-002)
- Полоса ID `20000-29999` (ADR-009)
- Проверка: `tools/validators/validate_id_registry.py`
- Loca overlay: `tools/converters/generate_mmx_loca.py` (M2-003)
  (`mod/Localisation/en|ru/loca.xml`, 32 ключа MM6X)
- Dialog overlay: `tools/converters/generate_mmx_dialog.py` (M2-004)
  (`mod/Dialog/Mm6JanisDialog.xml`, `Mm6AndoverDialog.xml`)
- StaticData overlay: `tools/converters/generate_mmx_staticdata.py`
  (M2-005) — NPC / QuestSteps / QuestObjectives / Token /
  LoreBook в `mod/StaticData/`
- Validation: `tools/validators/validate_mmx_mod.py` (M2-006)
  — связность registry ↔ loca ↔ dialog ↔ StaticData / `mod/`
- Build manifest: `tools/converters/build_mmx_manifest.py` (M2-007)
  — `mod/build_manifest.json` (9 файлов, SHA-256, stage_rel)
- Stage/restore: `tools/modding/stage_mmx_mod.py` (M2-008/009)
  — merge loca keys + CSV rows by StaticID; dialog copy;
  backup в `backups/mmx/mm6x-overlay/`

**Важно:** overlay — не полные vanilla-файлы. Stage делает
**merge**, не replace (`loca`/`CSV`). Dialog — новые XML.
Запись в игру только с `--stage --yes-i-understand`.

Ключ = Token 20001, кодекс = LoreBook 20000 + Token 20002.
Иконки/портреты/ImagePath — reuse vanilla assets
(**HYPOTHESIS**: достаточно для load).

Не путать с vanilla `Sorpigal` и
`LOCATION_SORPIGAL_THE_GOBLIN_WATCHTOWER` (дом в MMX-городе).

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\validators\validate_id_registry.py
python tools\converters\allocate_mmx_ids.py --self-test
python tools\converters\allocate_mmx_ids.py --dry-run
python tools\converters\allocate_mmx_ids.py --write
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\converters\generate_mmx_dialog.py --write --check-vanilla
python tools\converters\generate_mmx_staticdata.py --write --check-vanilla
python tools\validators\validate_mmx_mod.py
python tools\converters\build_mmx_manifest.py --write
python tools\modding\stage_mmx_mod.py --self-test
python tools\modding\stage_mmx_mod.py --dry-run
python tools\modding\stage_mmx_mod.py --status
# запись в игру (осторожно):
# python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
# python tools\modding\stage_mmx_mod.py --restore --yes-i-understand
```

(`MMX_GAME_PATH` в `.env`; иначе `--game-path` как в `env.example`.)

## Дальше

M2-010 regression fixtures. Игра **не** менялась в этой итерации
(только dry-run plan). In-game проверка stage — вручную после
явного `--stage`.
