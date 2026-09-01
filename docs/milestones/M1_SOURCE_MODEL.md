# M1 — MM6 Source Model

Цель: нормализованная JSON-модель MM6 и inventory источников.
New Sorpigal как карта MMX — с M3, не здесь.

## Сделано

- Схема: `docs/technical/MM6_MODEL.md`
- ID: `docs/technical/ID_REGISTRY.md`
- Аудит GOG-установки: `docs/research/MM6_AUDIT.md` (M1-003)
- Карта файлов: `docs/research/MM6_SOURCES.md` (M1-004…008)
- Манифесты slice: `references/mm6/*.manifest.json`

## Команды

```powershell
python tools\validators\validate_mm6_model.py
python tools\audit\audit_mm6.py
```

(`MM6_GAME_PATH` в `.env`; агент Cursor `.env` не видит — тогда
`--game-path` как в `env.example`.)

## Дальше

Декодировать `MapStats.txt` (подтвердить Outd1 / d01).  
Точечный extract таблиц NPC/quest в `references/mm6/raw/` (gitignore).
