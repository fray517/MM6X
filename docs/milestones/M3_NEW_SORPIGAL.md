# M3 — New Sorpigal Design

Цель: спроектировать MMX-карту Нью-Сорпигаля **до** greybox (M4).
Источник топологии — MM6 `OutE3.Odm` / `2DEvents` / `OUTE3.EVT`.
Не масштабировать координаты MM6 напрямую
(`docs/design/MAP_CONVERSION.md`).

## Сделано

### M3-001 Original topology
- Extract: `tools/extract/extract_mm6_topology.py`
- Machine: `references/mm6/new_sorpigal.topology.json`
- Design: `docs/design/NEW_SORPIGAL_TOPOLOGY.md`
- 40 узлов / 4 перехода. ODM XY — HYPOTHESIS.

### M3-002 Quest-critical landmarks
- Machine: `references/mm6/new_sorpigal.landmarks.json`
- Design: `docs/design/NEW_SORPIGAL_LANDMARKS.md`
- F0: ратуша #89 + вход Дозора #171 (+ D01 в M5)
- F1: таверна #92 (Андовер)
- Маршрут квеста #83 зафиксирован

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_evt.py
python tools\extract\extract_mm6_topology.py --write-curated
```

## Дальше

M3-003 NPC list, затем buildings/services, encounters, exits,
grid sketch / cell budget, quest dependency graph, approve.
