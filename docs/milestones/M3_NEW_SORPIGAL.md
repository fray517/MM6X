# M3 — New Sorpigal Design

Цель: спроектировать MMX-карту Нью-Сорпигаля **до** greybox (M4).
Источник — MM6 `OutE3` / `2DEvents` / `NPCdata` / MapStats / EVT.
Не масштабировать координаты MM6 напрямую
(`docs/design/MAP_CONVERSION.md`).

## Сделано

| ID | Артефакты |
|---|---|
| M3-001 | topology |
| M3-002 | landmarks |
| M3-003 | npcs |
| M3-004 | services |
| M3-005 | encounters |
| M3-006 | `new_sorpigal.travel.json`, `NEW_SORPIGAL_TRAVEL.md` |

M3-006: F0 Town↔D01; F2 D02/D18/OutB3 + stables/boats.

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_evt.py
python tools\extract\extract_mm6_topology.py --write-curated
python tools\extract\extract_mm6_travel.py --write-curated
```

## Дальше

M3-007 Grid conversion sketch, M3-008 cell budget,
M3-009 quest dependency graph, M3-010 approve.
