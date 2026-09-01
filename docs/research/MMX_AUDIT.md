# MMX Local Installation Audit
Status: RUN 2026-09-01

Полный машинный дамп (gitignored): `reports/mmx_audit.json`,
`reports/MMX_AUDIT.md`. Ниже — curated facts для репозитория.
Аудит был read-only: файлы игры не изменялись.

## Game path
- Install: Ubisoft Game Launcher, `...\games\Might & Magic X Legacy`
- Unity data dir: `Might and Magic X Legacy_Data`
- Main exe: `Might and Magic X Legacy.exe` (10518512 bytes)
- Evidence: VERIFIED_LOCAL

Путь задаётся через `--game-path` / `MMX_GAME_PATH`, в код не вшит.

## Build / distribution
- Дистрибуция: Ubisoft/Uplay (`uplay_r1_loader.dll`). Steam-маркеров нет.
- Evidence: VERIFIED_LOCAL
- Unity layout: Unity 4 (`mainData`, `level0`…`level9`).
  Нет `globalgamemanagers` / `boot.config`.
- Evidence: VERIFIED_LOCAL
- Unity version candidate из `mainData`: `4.2.2f1`
- Evidence: HYPOTHESIS (строка из бинарника, не FileVersion)

## Executable and key DLL hashes
SHA-256, VERIFIED_LOCAL:

| File | Size | SHA-256 |
|---|---:|---|
| `Might and Magic X Legacy.exe` | 10518512 | `b9b2797b888c28639afcda3fa9586fe3ace8a33b1046148fce67d30c903febf4` |
| `Managed/Legacy.Core.dll` | 924656 | `0ed6fd3b07dab1567e6f162e91e560c136973c5aa4a740e98835c3086a101a82` |
| `Managed/Legacy.Framework.dll` | 913392 | `c8be8857318e3915a57bc3860b02c71ae808cacb64237340f825314eae06654c` |
| `Managed/Legacy.Game.dll` | 694608 | `b58f317e7bd86acc43044d7c23fbec6c32a0ca47d033dcbcce429c791e7cabd9` |
| `Managed/UnityEngine.dll` | 513008 | `20483309acb0d7cf758dec80ce6189f9a3a3390734c4a4b9452e591b281794ec` |
| `Managed/Assembly-CSharp.dll` | 100848 | `7335320cc433f700b3bfd1396a9595425950a7266f21114b19de434d6142832f` |
| `uplay_r1_loader.dll` | 418616 | `c2ce063afd30d6ef41d9020d00899d873e15f196ee7248ab0be22338174d77c3` |

В корне также: `GDFTool.exe`, `LegacyFirewallAdd.exe`,
`LegacyFirewallDel.exe`, `LegacyGDFInstall.exe`.

## StreamingAssets
Путь: `Might and Magic X Legacy_Data/StreamingAssets` (718 files).
Evidence: VERIFIED_LOCAL

| Entry | Notes |
|---|---|
| `StaticData/` | 57 `*.csv` |
| `Dialog/` | 268 `*.xml` |
| `Localisation/` | 14 language dirs, each `loca.xml` |
| `Maps/` | 92 `*.xml` |
| `res/` | 276 files |
| `Videos/` | 7 files |
| `config.txt` | present |
| `CreditsData.xml` | present |
| `optionSettings.txt` | present |
| `optionSettings32.txt` | present |

Сторонних мод-каталогов в StreamingAssets не видно.

## StaticData
- Формат: CSV. Evidence: VERIFIED_LOCAL
- Пример `NpcStaticData.csv`: заголовок с `#` комментариями,
  поля через запятую (`StaticID,NameKey,...`).
- Evidence: VERIFIED_LOCAL (один файл; схему остальных ещё не сверяли)
- Есть `CsvSerializer.dll` в Managed.

Ключевые таблицы для контента: `NpcStaticData.csv`,
`QuestSteps.csv`, `QuestObjectives.csv`, `MonsterStaticData.csv`,
`DungeonEntryStaticData.csv`, `WorldMapPointsStaticData.csv`.

## Dialog
- `StreamingAssets/Dialog/*.xml`, 268 файлов.
- Имена вида `*Dialog.xml` (NPC). Есть `TestConversation.xml`.
- Evidence: VERIFIED_LOCAL

## Localisation
- `StreamingAssets/Localisation/<lang>/loca.xml`
- Языки: br, cn, cz, de, en, es, fr, hu, it, jp, kr, pl, ro, ru
- `en/loca.xml`: UTF-8 XML, корень `Localization`
- Evidence: VERIFIED_LOCAL
- Русский `ru/loca.xml` есть — удобно для M0 localisation proof.

## Managed
22 DLL. Evidence: VERIFIED_LOCAL

Помимо ключевых Legacy.*: `CsvSerializer.dll`,
`Legacy.Editor.Runtime.dll`, `Flow.dll`, `DecalSystem.Runtime.dll`,
UnityScript/Boo, Mono/`mscorlib`.

## Maps
- `StreamingAssets/Maps/*.xml`, 92 файла.
- Примеры: `Castle_Portmeyron_1.xml`, `Cave1.xml`,
  `Tower_of_Enigma_3.xml`, `worldOfTEST.xml`
- Evidence: VERIFIED_LOCAL
- Схема XML карт ещё не разбиралась (M0-050).

## ModdingKit / editor
Каталог `ModdingKit/` лежит рядом с игрой. Evidence: VERIFIED_LOCAL

- `Assets/MMXL_ModKit/` — EditorAssets, GameAssets, Materials,
  Models, ModSample, Prefabs, Scenes, Scripts, Shaders, Textures
- `Assets/Gizmos/` — gizmos редактора (NPC, monster, door, spawn…)
- `ProjectSettings/` — Unity project, `productName: modkit`
- `MMXL_Mod_Export/MMXL Sample Mod/` — образец экспорта:
  `Asset/`, `Localisation/`, `Map/`, `Staticdata/`,
  `config.txt`, `modinfo.xml`

Вывод для M0: vanilla data + комплектный MMXL ModKit доступны
локально. Нужен ли MMXLegacy — ещё не решено (ADR-008).

## Installed mods
Признаков установленного third-party мода в StreamingAssets нет.
Evidence: VERIFIED_LOCAL (по составу каталогов)

## Observations
- Сборка Ubisoft; Steam/Ubisoft DLL не смешивать.
- Modding surface совпадает с community-ожиданиями:
  StaticData CSV, Dialog XML, Localisation XML, Maps XML.
- Есть официальный ModdingKit — карты, скорее всего, через него,
  а не через правку `resources.assets`. HYPOTHESIS до M0-050.
- `resources.assets` ~334 MB; в репозиторий не копировать.
