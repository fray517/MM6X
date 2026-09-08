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

Диалоги / live Goblin / enable gate — M4-003+.

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

## M4-002 Landmarks — Done

- NPC: `START_DIALOGUE` на Жанис (10) / Андовер (11)
- SIGN ×7 (F0/F1 + F2 shells) + loca `SIGN_MM6_*`
- Binding: `references/mm6/new_sorpigal.landmarks_mmx.json`
- Prefab: Generic_Guard / Sign_V5 (**HYPOTHESIS** reuse)
- Gate ENTRANCE остаётся **Enabled=false** (M4-008)
- Quest content: M4-003 Andover, M4-004 Janis

```powershell
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\converters\generate_mmx_map.py --write
python tools\validators\validate_mmx_mod.py
```

## M4-003 Andover — Done

Квест **#81** «Письмо Сулмана» (parallel к #83):

| | |
|---|---|
| Quest step / obj | **20002** |
| Quest flag token | **20003** |
| Letter token | **20004** (MM6 item 505) |
| Dialog | offer → accept → `GiveToken` letter |
| Delivery | outside New Sorpigal slice (FollowUp=0) |

Текст письма MM6 `Scroll.txt` **не** копируем — только authored loca.
Registry: `mm6.quest.new_sorpigal.sulman_letter` + stage + item.

## M4-004 Town Hall quest giver — Done

Жанис / квест **#83** (паттерн **VERIFIED_LOCAL** `UlaganDialog`):

| Этап | Поведение |
|---|---|
| Accept | `QuestFunction` 20000 → `GiveToken` ключ **20001** |
| In progress | опция при active **20000** |
| Turn-in | active FollowUp **20001** + codex **20002** |
| Solve | `SolveQuest` 20001 + `removeTokenID` 20002 |
| Reward | XP/Gold на step 20001 (уже в StaticData) |

Генератор: `removeTokenID` в `mmx_dialog.py`.

## Дальше

M4-005 Localisation (сверка ключей / smoke en+ru).
