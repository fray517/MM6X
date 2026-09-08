# New Sorpigal — cell budget (M3-008)

Evidence sizes: **VERIFIED_LOCAL** (все 5 vanilla CITY =
32×30 или 32×32, 960–1024 клеток). Layout zones:
**HYPOTHESIS** (`grid_sketch`). Machine:
`references/mm6/new_sorpigal.cell_budget.json`.

## Утверждённый размер M4

| Map | W×H | Cells | Type |
|---|---|---:|---|
| **`New_Sorpigal`** | **24×18** | **432** | CITY / CASTLE |
| Goblinwatch (stub M4) | 8×8 | 64 | DUNGEON (отдельный XML) |
| Goblinwatch (M5 target) | 12×12 | 144 | DUNGEON |

432 ≈ **45%** площади vanilla Sorpigal (960) — намеренно:
только F0/F1 + F2 stubs. Движок допускает нестандартные
размеры (Cave1 6×6 и др.). HYPOTHESIS: CITY≠32 не ломает load.

**Не** править `Sorpigal.xml`.

## Зоны (inclusive bbox; пересекаются)

| Zone | BBox | Cells |
|---|---|---:|
| waterfront | 0,0–9,5 | 60 |
| town_core | 6,5–15,12 | 80 |
| road_east | 15,6–23,12 | 63 |
| inland_north | 8,12–16,17 | 54 |

Сумма ≠ 432: зоны overlap + «пустой» фон = BLOCKED/terrain.

## Terrain budget

| Metric | Target |
|---|---|
| PASSABLE | **55–70%** → ~238–302 клеток |
| Border BLOCKED | ≥1 клетка по краю |
| Коридор #83 | min width 1, preferred **2** |
| Шаги hall→gate | 4–10 (sketch ≈6) |

## Content caps (M4)

| Content | Min | Max |
|---|---:|---:|
| F0 landmarks (hall, gate) | 2 | 2 |
| F1 tavern | 1 | 1 |
| F2 stub landmarks | 0 | 6 |
| NPC containers (Janis+Andover) | 2 | 6 |
| Monster spawns | 1 | 3 |
| Map transitions (real) | 1 (D01) | 1+stubs |
| Party start | 1 | 1 |

## Expansion path

1. M4: 24×18 (432) — greybox accept  
2. Если тесно для F3 shops → 28×20 (560)  
3. Опционально «как CITY width» → 32×24 (768) — не блокер M4

## Acceptance (для M4-001)

- XML `Width=24` `Height=18` грузится  
- Пешком hall→gate ≤10 PASSABLE шагов  
- Жанис + таверна + gate на местах  
- ≥1 Goblin на east road  
- Vanilla `Sorpigal.xml` не изменён  

Детальный quest graph — M3-009; approve design — M3-010.
