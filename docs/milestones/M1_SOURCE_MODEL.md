# M1 — MM6 Source Model

Цель: нормализованная JSON-модель MM6 и inventory источников.
New Sorpigal как карта MMX — с M3, не здесь.

## Сделано

- Схема: `docs/technical/MM6_MODEL.md`
- ID: `docs/technical/ID_REGISTRY.md`
- Аудит GOG-установки: `docs/research/MM6_AUDIT.md` (M1-003)
- Карта файлов: `docs/research/MM6_SOURCES.md` (M1-004…008)
- Манифесты slice: `references/mm6/*.manifest.json`
  (OutE3 / D01 — VERIFIED_LOCAL)
- Extract `.txt`: `tools/extract/extract_mm6_text.py`
- Extract `.EVT`/`.STR`: `tools/extract/extract_mm6_evt.py`
  (OUTE3, D01, GLOBAL; индекс `reports/evt_slice.json`)

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\validators\validate_mm6_model.py
python tools\audit\audit_mm6.py
python tools\extract\extract_mm6_text.py --dry-run
python tools\extract\extract_mm6_evt.py --dry-run
```

(`MM6_GAME_PATH` в `.env`; агент Cursor `.env` не видит — тогда
`--game-path` как в `env.example`.)

Консоль Windows cp1251 ломает русские имена — UTF-8 через
`$env:PYTHONIOENCODING` или писать в файл.

## Дальше

Где в D01 появляется кодекс #543 (сундук BLV, не EVT).  
Порядок плит НИЛБОГ — пока HYPOTHESIS.
Normalized JSON сверх fixture — M2.
