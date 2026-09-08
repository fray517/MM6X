# M4 — New Sorpigal Prototype

Цель: playable greybox `New_Sorpigal` по approve M3
(`docs/design/NEW_SORPIGAL_DESIGN_APPROVAL.md`).

Не править vanilla `Sorpigal.xml`.

## M4-001 Greybox/grid map — Done

- Generator: `tools/converters/generate_mmx_map.py`
  (+ `mmx_map.py`)
- Output: `mod/Maps/New_Sorpigal.xml` (**32×30**, CITY/CASTLE;
  SceneName=`Sorpigal` + walk footprint VERIFIED_LOCAL)
- Sketch: `references/mm6/new_sorpigal.grid_sketch.json`
- Walk: `references/mmx/sorpigal.walk.json`
- Stage: kind `map` = **copy** (как Dialog); dry-run only
- Evidence layout anchors: **HYPOTHESIS** (snapped);
  terrain: **VERIFIED_LOCAL**

Содержимое greybox:

| Элемент | Клетка / ID |
|---|---|
| PARTY | (19,19) Trigger 1, face EAST |
| Janis stub | (19,20) NPC_IDS,20000 Trigger 10 (garrison) |
| Andover stub | (16,15) NPC_IDS,20001 Trigger 11 (Inn) |
| Gate | (28,17) ENTRANCE→Goblinwatch **Enabled**; key **20001** |
| Road mob | (22,19) Trigger 60, SpawnStaticID **150** (Spider) |
| Corridor #83 | BFS ≈21 PASSABLE steps |
| PASSABLE | Sorpigal footprint 303/960 |

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
- Gate ENTRANCE **Enabled** + key-lock (M4-008)
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

## M4-005 Localisation — Done

- Inventory: `docs/design/NEW_SORPIGAL_LOCALISATION.md`
- Validator: `tools/validators/validate_mmx_loca.py`
  (`--check-vanilla`, en/ru parity, dialog/map/CSV refs)
- **53** keys; F2 SIGN без UI-слова «stub»
- `validate_mmx_mod` сверяет map Location/SIGN ↔ loca

```powershell
python tools\validators\validate_mmx_loca.py --check-vanilla --list
```

## M4-006 First quest flow — Done

E2E #83 (stub D01):

| Step | Artifact |
|---|---|
| Accept + key | Janis (M4-004) |
| Gate Enabled | `New_Sorpigal` Trigger 20 → `Goblinwatch.xml` |
| Stub 6×6 Cave1 | `mod/Maps/Goblinwatch.xml` |
| Codex | chest ADD_TOKEN **20002** + ADD_LOREBOOK **20000** |
| Return | exit → town party |
| Turn-in | Janis SolveQuest (M4-004) |

Doc: `docs/design/NEW_SORPIGAL_QUEST_FLOW_83.md`  
JSON: `references/mm6/new_sorpigal.quest_flow_83.json`

## M4-007 Goblin encounter — Done

- Cell **(22,19)** east road (`enc.goblin_road`) — Giant Spider **150** (L1)
- Trigger **60**, `SpawnObjectType=MONSTER`
- `SpawnStaticID=**50**` (`MONSTER_GOBLIN`, VERIFIED_LOCAL)
- PeasantM2 optional — не ставили

## M4-008 Goblinwatch entrance — Done

Gate Trigger **20** `(28,17)`:

| Command | Detail | Evidence |
|---|---|---|
| `USE_ENTRANCE` | `PARTY_CHECK` token **20001** | VERIFIED_LOCAL |
| `REMOVE_TOKEN` | Extra **20001**, `ON_SUCCESS` | door pattern VERIFIED; on entrance HYPOTHESIS |
| `GAME_MESSAGE` | `OBJECT_INTERACTION_MM6_GOBLINWATCH_LOCKED` `ON_FAIL` | VERIFIED_LOCAL |
| Exit stub | `Goblinwatch` → town без ключа | — |

Regen:

```powershell
python tools\converters\generate_mmx_map.py --write
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\validators\validate_mmx_mod.py
```

## M4-009 Route playtest — In progress

Offline (Done):

| Check | Result |
|---|---|
| BFS `accept_to_gate` | **11** steps, via PASSABLE |
| BFS `tavern_to_hall` | **3** steps |
| WMP overlay **20000** | `WorldMapPointsStaticData.csv` |
| SceneName reuse | town=`Sorpigal`, dungeon=`Cave1` |
| config `start` | `New_Sorpigal` (bypass tutorial lock) |
| Stage dry-run | actions OK |

Doc: `docs/design/NEW_SORPIGAL_ROUTE_PLAYTEST.md`

In-game: checklist в doc (владелец). Риски size≠scene
(HYPOTHESIS). После pass → BACKLOG `[x]`, затем M4-010.

```powershell
python tools\modding\stage_mmx_mod.py --dry-run
# python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
```

## Дальше

In-game M4-009 → M4-010 Save/load.
