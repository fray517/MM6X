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

## Команды

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\validators\validate_mm6_model.py
python tools\audit\audit_mm6.py
python tools\extract\extract_mm6_text.py --dry-run
python tools\extract\extract_mm6_text.py
```

(`MM6_GAME_PATH` в `.env`; агент Cursor `.env` не видит — тогда
`--game-path` как в `env.example`.)

Консоль Windows cp1251 ломает русские имена — UTF-8 через
`$env:PYTHONIOENCODING` или писать в файл.

## Дальше

Разбор `OUTE3.EVT` / `D01.EVT` (NILBOG, stages).  
Normalized JSON slice сверх fixture — по мере M2.
