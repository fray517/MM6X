# New Sorpigal — grid conversion sketch (M3-007)

Evidence layout: **HYPOTHESIS** (ODM XY не декодированы).
MMX size refs: **VERIFIED_LOCAL** (`Sorpigal` 32×30 CITY,
`SeaHaven` 32×32, `Cave1` 6×6).
Machine: `references/mm6/new_sorpigal.grid_sketch.json`.

Не путать с vanilla MMX `Sorpigal.xml` (Sorpigal-by-the-Sea).
Новая карта: **`New_Sorpigal`** (`id_registry` map slot).

## Принцип

`landmarks → routes → quest topology → grid plan → MMX map`
(`MAP_CONVERSION.md`). Метры MM6 не масштабируем.

## Предлагаемый размер (M4 greybox)

| Map | Type | Size | Milestone |
|---|---|---|---|
| `New_Sorpigal` | CITY / CASTLE | **24×18** | M4 |
| `Goblinwatch` | DUNGEON | ~12×12 (hint) | M5 (stub OK в M4) |

Точный cell budget — **M3-008** (`NEW_SORPIGAL_CELL_BUDGET.md`):
24×18 = **432** cells. 24×18 < vanilla город,
хватает на F0/F1 + F2 stubs.

## Оси sketch

- **X+** = восток (к Дозору)
- **Y+** = север / inland  
Согласовать с `Slot Position` при авторинге XML.

## Зоны (bbox в клетках 24×18)

```text
y17 .................. stables ..................
y15 ........ [inland_north] .....................
y12 ---------------------------------------------
y9   hall──road──────────────► GATE(#171)
y8   tavern
y5   ------------ [town_core] -------------------
y2   boats / waterfront
y0   ============================================
     x0        x10              x21           x23
```

| Zone | bbox (x0,y0)–(x1,y1) | Содержимое |
|---|---|---|
| waterfront | 0,0–9,5 | лодки #57 |
| town_core | 6,5–15,12 | ратуша #89, таверна #92, сервисы |
| road_east | 15,6–23,12 | вход Дозора #171, goblin enc |
| inland_north | 8,12–16,17 | конюшни #48 |

## Якоря (proposed cells)

| Landmark | Cell | F |
|---|---|---|
| Town hall #89 | (10,9) | F0 |
| Tavern #92 | (8,8) | F1 |
| Goblinwatch gate #171 | (21,9) | F0 |
| Boats #57 | (3,2) | F2 |
| Stables #48 | (12,15) | F2 |
| Temple/Train stubs | inland / core edge | F2 |
| D02 / D18 shells | (18,14) / (20,5) | F2 |

Party start: **(10,7)** у ратуши.

## Маршруты

1. **#83 accept→gate:** (10,9)→(21,9) ≈ **6** шагов по коридору Y=9.
2. **Таверна→ратуша:** ≈ **2** шага.
3. Goblin pack на клетке **(17,9)** (M3-005). PeasantM2 опционально (14,11).

## Связь карт

```text
New_Sorpigal (CITY)
    trigger @ (21,9) ──key──► Goblinwatch (DUNGEON, M5)
         ▲                         │
         └──────── exit e51 ───────┘
```

World exits (OutB3 / stables / boats) — маркеры F2, без
полноценных дальних карт в M4.

## Что не входит в M3-007

- ~~Полный `New_Sorpigal.xml`~~ → **M4-001 Done**
  (`mod/Maps/New_Sorpigal.xml`)
- Финальный cell budget (M3-008) — Done
- Quest dependency graph formal (M3-009) — Done
- Approve (M3-010) — Done
