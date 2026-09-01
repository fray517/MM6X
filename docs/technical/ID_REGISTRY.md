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
MMX numeric ID не выдаём, пока нет правил collision (M2-002).

## Зарезервировано для slice

Evidence: VERIFIED_LOCAL, кроме слова NILBOG/НИЛБОГ (порядок
нажатий плит — HYPOTHESIS).

| Stable ID | MM6 source | MMX target | Status |
|---|---|---|---|
| `mm6.region.new_sorpigal` | MapStats #15 `OutE3.Odm` + `OUTE3.EVT` | не MMX `Sorpigal` | mapped |
| `mm6.dungeon.goblinwatch` | MapStats #16 `D01.Blv` + `D01.EVT` | TBD | mapped |
| `mm6.location.new_sorpigal.town_hall` | `2DEvents.txt` #89; `OUTE3.EVT` e28 | TBD | mapped |
| `mm6.npc.new_sorpigal.janis` | `NPCdata.txt` #291 Жанис | TBD | mapped |
| `mm6.npc.new_sorpigal.andover` | `NPCdata.txt` #1; `GLOBAL.EVT` e1 | TBD | mapped |
| `mm6.quest.new_sorpigal.goblinwatch` | `Quests.txt` #83 / QBit 83 | TBD | mapped |
| `mm6.quest_stage.new_sorpigal.goblinwatch.accept` | `GLOBAL.EVT` e3 | TBD | mapped |
| `mm6.quest_stage.new_sorpigal.goblinwatch.turnin` | `GLOBAL.EVT` e4 | TBD | mapped |
| `mm6.item.goblinwatch.key` | `ITEMS.TXT` #489 | TBD | mapped |
| `mm6.item.goblinwatch.codex` | `ITEMS.TXT` #543 | TBD | mapped |
| `mm6.secret.goblinwatch.nilbog` | `D01.EVT` e19–34 буквы А–П | TBD | mapped |
| `mm6.travel_link.new_sorpigal.goblinwatch` | `OUTE3.EVT` e101 → `D01.blv` | TBD | mapped |

`OutD1.Odm` — «Серебряная бухта», не Нью-Сорпигаль.

Проверка id: `python tools\validators\validate_mm6_model.py`.
