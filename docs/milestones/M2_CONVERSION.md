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
  (`mod/Localisation/en|ru/loca.xml`, 31 ключ MM6X)
- Dialog overlay: `tools/converters/generate_mmx_dialog.py` (M2-004)
  (`mod/Dialog/Mm6JanisDialog.xml`, `Mm6AndoverDialog.xml`)

Numeric ID reserved, не bound: в StreamingAssets ещё не писали.
Ключ = Token 20001, кодекс = LoreBook 20000 + Token 20002
(**HYPOTHESIS** до M2-005 / StaticData).

Не путать с vanilla `Sorpigal` и
`LOCATION_SORPIGAL_THE_GOBLIN_WATCHTOWER` (дом в MMX-городе).

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\validators\validate_id_registry.py
python tools\converters\allocate_mmx_ids.py --self-test
python tools\converters\allocate_mmx_ids.py --dry-run
python tools\converters\allocate_mmx_ids.py --write
python tools\converters\generate_mmx_loca.py --self-test
python tools\converters\generate_mmx_loca.py --dry-run --check-vanilla
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\converters\generate_mmx_dialog.py --self-test
python tools\converters\generate_mmx_dialog.py --dry-run --check-vanilla
python tools\converters\generate_mmx_dialog.py --write --check-vanilla
```

(`MMX_GAME_PATH` в `.env`; иначе `--game-path` как в `env.example`.)

## Дальше

M2-005 StaticData patch (NPC / QuestSteps / Token / LoreBook),
затем build manifest, stage/restore. Overlay **не** в игре до
M2-008. Игра пока не меняется.
