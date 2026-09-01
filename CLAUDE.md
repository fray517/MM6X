# CLAUDE.md — MM6X Development Contract

## Контекст
MM6X — total conversion MMX, воссоздающий MM6.

## Текущий milestone
**M0 — Prove the MMX Modding Pipeline.**

Не начинай полноценный New Sorpigal до завершения M0.

## Порядок технических решений
Всегда проверяй от менее инвазивного к более инвазивному:
1. StreamingAssets / config / data
2. StaticData CSV
3. Dialog XML
4. Localisation
5. MMX map/modding tooling
6. MMXLegacy extension
7. custom C# engine patch

Не переписывай систему, которая уже существует в MMX, без подтверждённого ограничения.

## Локальная проверка обязательна
Известные community modding surfaces включают:
- `Might and Magic X Legacy_Data/StreamingAssets`
- `StreamingAssets/StaticData`
- `StreamingAssets/Dialog`
- `StreamingAssets/Localisation`
- `Might and Magic X Legacy_Data/Managed`
- `Legacy.Core.dll`
- `Legacy.Framework.dll`
- `Legacy.Game.dll`

Но реальные имена, схемы и версии сначала проверяются в установленной копии пользователя.

Steam/Ubisoft builds могут различаться. Нельзя считать DLL взаимозаменяемыми.

## Безопасность
Никогда молча не:
- перезаписывай оригинальные файлы без backup;
- патч DLL без точной версии/hash;
- удаляй файлы игры;
- ломай существующие saves;
- распространяй оригинальные assets;
- копируй third-party code без проверки лицензии.

## Source of truth
Narrative/content → MM6.
Runtime/mechanics → MMX.

Конфликт фиксируй в `DECISIONS.md`.

## Map conversion
Не масштабируй MM6 coordinates напрямую.
Используй:
`landmarks → route graph → quest topology → grid plan → MMX map`.

## Conversion pipeline
`MM6 local install → extractor → normalized JSON → validator → MMX converter → staged mod`.

## Workflow Cursor
Для каждой задачи:
1. Прочитай PROJECT_CHARTER.md.
2. Прочитай ARCHITECTURE.md.
3. Прочитай relevant milestone и BACKLOG.md.
4. Исследуй реальные файлы.
5. Перечисли изменяемые файлы.
6. Сделай минимальную обратимую правку.
7. Дай validation/rollback.
8. Обнови BACKLOG.md только по факту.
9. Новые факты занеси в `docs/research/MMX_AUDIT.md`.

## Evidence
Маркируй выводы:
- VERIFIED_LOCAL
- VERIFIED_SOURCE
- HYPOTHESIS

## Python
Python 3.11+, pathlib, argparse, type hints, без machine-specific paths.
Для потенциально destructive операций — `--dry-run`.

## M0 Done
Повторяемо умеем:
- восстановить clean state;
- применить test mod;
- увидеть Localisation change;
- увидеть StaticData change;
- увидеть Dialog change;
- загрузить map change;
- удалить/откатить mod;
- повторить всё по документации.
