# MMXLegacy — research (M0-060…062)

Источник: https://github.com/Albeoris/MMXLegacy  
Evidence: VERIFIED_SOURCE (публичный GitHub, 2026-09-01).  
В репозиторий MM6X **не клонировать и не вендорить**.

## Лицензия

- SPDX: MIT. Copyright (c) 2017 Albeoris.
- Файл: `LICENSE` в корне репозитория.
- MIT покрывает работу Albeoris. Содержимое — rewritten
  `Legacy.Core` / `Legacy.Game` / …, то есть производное от
  proprietary MMX. Распространять эти исходники вместе с MM6X
  нельзя (ADR-007 + риск IP), даже при MIT-шапке.

## Что это

Не Harmony-плагин и не недостающий Unity-editor. Это **переписанный
движок**: готовые сборки копируются поверх
`Might and Magic X Legacy_Data/Managed`.

Последний push: `2017-12-23`, commit
`22aac69f36f0852872927c86ea7b22af98604899`. Репозиторий не
архивирован, но фактически заморожен.

README: Visual Studio 2017; в `References/` кладутся DLL из
локальной установки игры (proprietary, в git Albeoris их нет).

## Проекты в `Legacy.sln`

| Проект | Зачем |
|---|---|
| `Legacy.Core` | игровая логика (карта, бой, данные) |
| `Legacy.Game` | Unity-обвязка |
| `Legacy.Framework` | общий каркас |
| `CsvSerializer` | CSV, как в vanilla Managed |
| `Assembly-CSharp` / `-firstpass` | Unity generated |
| `Legacy.Injection` | внедрение |
| `Legacy.Debugger` | attach к процессу |
| `Legacy.MSBuild` | сборка |
| `Mods/MerchantSkill` | пример: overlay `Might and Magic X Legacy_Data/` |

Wiki (2017): bugfix боя/Windsword; features через `config.txt`;
extensions — «новые файлы с уникальными id, для этого нужен
движок». HYPOTHESIS: overlay новых файлов — фича MMXLegacy, не
vanilla. Vanilla M0 доказал **патч существующих** файлов.

MMXLegacy **не содержит** `Legacy.Editor.dll` /
`Legacy.Editor.LevelEditor.dll`. Дыру ModdingKit не закрывает.

## Совместимость с нашей установкой

Локально: Ubisoft Connect, не Steam. Хеши
`docs/research/MMX_AUDIT.md`. Unity candidate `4.2.2f1`
(HYPOTHESIS).

Community (форумы): Steam и Ubisoft `Legacy.Core.dll` **различаются**.
Подтверждает контракт: DLL сборок не смешивать.

Ставить бинарники MMXLegacy 2017 на Ubisoft-сборку 2026 **нельзя**
без отдельного proof (хеш цели, backup, in-game). Это слой C/D
архитектуры, не M1.

Онлайн-сервер из README, скорее всего, уже мёртв (Ubisoft decommission).
На решение M1 не влияет.

## Нужен ли для M1

M1 — модель исходников MM6 (схема, ID, аудит установки MM6).
К Managed MMX не обращается.

Контентный пайплайн M2+ на этой сборке доказан без C#: loca, CSV,
Dialog XML, Maps XML. New Sorpigal как XML-grid — тот же слой, что
M0-074.

MMXLegacy оставляем запасным вариантом, если появится **verified
blocker** vanilla data (новый тип condition/function, загрузчик
мод-папки, баг движка). До такого блока — не ставить.
