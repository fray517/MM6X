# M3 — New Sorpigal Design

Цель: спроектировать MMX-карту Нью-Сорпигаля **до** greybox (M4).
Источник топологии — MM6 `OutE3.Odm` / `2DEvents` / `OUTE3.EVT`.
Не масштабировать координаты MM6 напрямую
(`docs/design/MAP_CONVERSION.md`).

## M3-001 Original topology — Done

- Extract: `tools/extract/extract_mm6_topology.py`
- Machine: `references/mm6/new_sorpigal.topology.json`
- Design: `docs/design/NEW_SORPIGAL_TOPOLOGY.md`
- Evidence: **VERIFIED_LOCAL** (GOG Icons.lod + evt_slice)

Сводка E3: 40 узлов (18 значимых + 22 дома), 4 map-transition.
ODM XY — ещё не декодированы (HYPOTHESIS layout).

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_evt.py
python tools\extract\extract_mm6_topology.py --self-test
python tools\extract\extract_mm6_topology.py --write-curated
```

## Дальше

M3-002 quest-critical landmarks (ратуша / таверна / вход D01 /
маршруты квеста #83), затем NPC / services / exits /
grid sketch.
