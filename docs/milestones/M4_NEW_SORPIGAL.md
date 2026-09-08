# M4 — New Sorpigal Prototype

Цель: playable greybox `New_Sorpigal` по approve M3
(`docs/design/NEW_SORPIGAL_DESIGN_APPROVAL.md`).

Не править vanilla `Sorpigal.xml`.

## M4-001 Greybox/grid map — Done

- Generator: `tools/converters/generate_mmx_map.py`
  (+ `mmx_map.py`)
- Output: `mod/Maps/New_Sorpigal.xml` (24×18, CITY/CASTLE)
- Sketch: `references/mm6/new_sorpigal.grid_sketch.json`
- Stage: kind `map` = **copy** (как Dialog); dry-run only
- Evidence layout: **HYPOTHESIS**; schema slots: **VERIFIED_LOCAL**

Содержимое greybox:

| Элемент | Клетка / ID |
|---|---|
| PARTY | (10,7) Trigger 1, face EAST |
| Janis stub | (10,9) NPC_IDS,20000 Trigger 10 |
| Andover stub | (8,8) NPC_IDS,20001 Trigger 11 |
| Gate stub | (21,9) ENTRANCE→Goblinwatch **Enabled=false** |
| Corridor #83 | Y≈9, ~6 PASSABLE steps |
| PASSABLE | zone union ≈208/432 (~48%) |

Диалоги / START_DIALOGUE / live Goblin / enable gate —
следующие задачи M4-002+.

### Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\generate_mmx_map.py --self-test
python tools\converters\generate_mmx_map.py --write
python tools\converters\build_mmx_manifest.py --write
python tools\validators\validate_mmx_mod.py
python tools\modding\stage_mmx_mod.py --dry-run
# в игру не ставим без явного --stage --yes-i-understand
```

### Rollback

Удалить `mod/Maps/New_Sorpigal.xml` и пересобрать manifest.
Если когда-то staging: `stage_mmx_mod.py --restore`.

## Дальше

M4-002 Landmarks (полноценные объекты / prefab / dialog hooks).
