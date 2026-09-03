# ID Registry

Project-owned stable IDs не зависят от MMX numeric IDs.

## Грамматика (M1-002)

```text
mm6.<kind>.<slug>[.<slug>...]
```

- `kind` — одно из: `region`, `location`, `map_node`, `route`,
  `npc`, `dialogue`, `quest`, `quest_stage`, `item`, `monster`,
  `encounter`, `dungeon`, `secret`, `trainer`, `shop`,
  `travel_link`.
- `slug` — `[a-z0-9_]+`, сегменты через точку.
- Иерархия места: `mm6.npc.new_sorpigal.andover`.
- Глобальные данжи без города: `mm6.dungeon.goblinwatch`.

Mapping: **stable ↔ MM6 source ↔ MMX target**.  
Источник назначений: `tools/converters/id_registry.json`.

## Полоса MMX ID (M2-002, ADR-009)

Vanilla уже занимает sparse ID около **10000** (test NPC/quests).
VERIFIED_LOCAL: `NpcStaticData` max 10000, `QuestSteps` max 10002,
`Token` max 804, `WorldMapPoints` max 40.

MM6X numeric ID: **20000–29999** на таблицу, не пересекаясь
с used vanilla. Строки (`New_Sorpigal`, `Mm6JanisDialog`,
`LOCATION_MM6_*`) тоже проверяются на коллизию.

Статус слота: `unassigned` → `reserved` (аллокатор) → `bound`
(когда строка реально лежит в staged mod).

```powershell
python tools\validators\validate_id_registry.py
python tools\converters\allocate_mmx_ids.py --dry-run
```

## Зарезервировано для slice

Evidence: VERIFIED_LOCAL (скан Ubisoft MMX + MM6 slice).
Ключ→Token и кодекс→LoreBook — HYPOTHESIS.
Плиты NILBOG — maze дверей, не слот StaticID.

| Stable ID | MM6 source | MMX target | Status |
|---|---|---|---|
| `mm6.region.new_sorpigal` | MapStats #15 `OutE3.Odm` | map `New_Sorpigal`, WMP 20000 | reserved |
| `mm6.dungeon.goblinwatch` | MapStats #16 `D01.Blv` | map `Goblinwatch`, DE 20000 | reserved |
| `mm6.location.new_sorpigal.town_hall` | `2DEvents.txt` #89 | loca `LOCATION_MM6_*TOWN_HALL` | reserved |
| `mm6.npc.new_sorpigal.janis` | `NPCdata.txt` #291 | NPC 20000, `Mm6JanisDialog` | reserved |
| `mm6.npc.new_sorpigal.andover` | `NPCdata.txt` #1 | NPC 20001, `Mm6AndoverDialog` | reserved |
| `mm6.quest.new_sorpigal.goblinwatch` | QBit 83 | Token 20000 | reserved |
| `mm6.quest_stage...accept` | `GLOBAL.EVT` e3 | step/obj 20000 | reserved |
| `mm6.quest_stage...turnin` | `GLOBAL.EVT` e4 | step/obj 20001 | reserved |
| `mm6.item.goblinwatch.key` | `ITEMS.TXT` #489 | Token 20001 | reserved |
| `mm6.item.goblinwatch.codex` | #543 / `Scroll.txt` M44 | LoreBook 20000 | reserved |
| `mm6.secret.goblinwatch.nilbog` | `D01.EVT` e19–34 | карта (слотов нет) | — |
| `mm6.travel_link...goblinwatch` | `OUTE3.EVT` e101 | карта (слотов нет) | — |

`OutD1.Odm` — «Серебряная бухта», не Нью-Сорпигаль.
Vanilla `Sorpigal` не переиспользуем.

Проверка модели: `python tools\validators\validate_mm6_model.py`.
