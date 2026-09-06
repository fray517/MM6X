# M3 — New Sorpigal Design

Цель: спроектировать MMX-карту Нью-Сорпигаля **до** greybox (M4).
Источник — MM6 `OutE3` / `2DEvents` / `NPCdata` / EVT.
Не масштабировать координаты MM6 напрямую
(`docs/design/MAP_CONVERSION.md`).

## Сделано

| ID | Артефакты |
|---|---|
| M3-001 | `new_sorpigal.topology.json`, `NEW_SORPIGAL_TOPOLOGY.md` |
| M3-002 | `new_sorpigal.landmarks.json`, `NEW_SORPIGAL_LANDMARKS.md` |
| M3-003 | `new_sorpigal.npcs.json`, `NEW_SORPIGAL_NPCS.md` |
| M3-004 | `new_sorpigal.services.json`, `NEW_SORPIGAL_SERVICES.md` |

M3-004: 18 сервисов + 22 дома; M4 houses **89 / 171 / 92**.

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_topology.py --write-curated
python tools\extract\extract_mm6_npcs.py --write-curated
python tools\extract\extract_mm6_services.py --self-test
python tools\extract\extract_mm6_services.py --write-curated
```

## Дальше

M3-005 Encounters, M3-006 Exits/travel, затем grid sketch /
cell budget / quest graph / approve.
