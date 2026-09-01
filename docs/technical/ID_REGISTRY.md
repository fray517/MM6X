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

| Stable ID | MM6 source | MMX target | Status |
|---|---|---|---|
| `mm6.region.new_sorpigal` | `games.lod` / `Outd1.odm` (HYPOTHESIS) | не MMX `Sorpigal` | research |
| `mm6.dungeon.goblinwatch` | `games.lod` / `d01.blv` (HYPOTHESIS) | TBD | research |
| `mm6.npc.new_sorpigal.andover` | `Icons.lod` NPC tables | TBD | research |
| `mm6.quest.new_sorpigal.goblinwatch` | `OUTD1.EVT` / `D01.EVT` / `Quests.txt` | TBD | research |
| `mm6.secret.goblinwatch.nilbog` | `D01.EVT` (HYPOTHESIS) | TBD | research |
| `mm6.travel_link.new_sorpigal.goblinwatch` | Outd1 ↔ d01 | TBD | research |

Проверка id: `python tools\validators\validate_mm6_model.py`.
