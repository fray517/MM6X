# M3 — New Sorpigal Design

Цель: спроектировать MMX-карту Нью-Сорпигаля **до** greybox (M4).
Не масштабировать координаты MM6 напрямую
(`docs/design/MAP_CONVERSION.md`).

## Сделано

| ID | Артефакты |
|---|---|
| M3-001…006 | topology / landmarks / npcs / services / encounters / travel |
| M3-007 | `new_sorpigal.grid_sketch.json`, `NEW_SORPIGAL_GRID_SKETCH.md` |

M3-007: CITY **24×18** `New_Sorpigal`; F0 hall(10,9)→gate(21,9);
не трогать vanilla `Sorpigal.xml`. Layout = HYPOTHESIS.

## Дальше

M3-008 Cell budget, M3-009 quest dependency graph, M3-010 approve.
