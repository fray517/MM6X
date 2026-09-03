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
- Johara: `JoharaDialog.xml` (1931 bytes, UTF-8 без BOM, LF).
  `ConversationKey=JoharaDialog`, NPC StaticID=2. VERIFIED_LOCAL.
- Evidence: VERIFIED_LOCAL

## Localisation
- `StreamingAssets/Localisation/<lang>/loca.xml`
- Языки: br, cn, cz, de, en, es, fr, hu, it, jp, kr, pl, ro, ru
- `en/loca.xml`: UTF-8 XML, корень `Localization`
- `ru/loca.xml`: UTF-8 **with BOM**, 8127 `LocaData`, LF.
- Evidence: VERIFIED_LOCAL
- M0 test key: `Gui/Mainmenu/Options` → «Параметры»
  (главное меню). Процедура:
  `docs/milestones/M0_LOCALISATION_TEST.md`.
- In-game, 2026-09-01: русское главное меню показало
  `MM6X TEST — Параметры`. Evidence: VERIFIED_LOCAL.
- Restore loca: `state: ORIGINAL` (`de5a7668…e60d064`).
- StaticData M0 test: `Potions.csv` StaticID=1 `Price` 45 → 9999
  (Johara в Sorpigal). In-game: цена 9999. VERIFIED_LOCAL.
  Restore: `ORIGINAL` (`f919fa74…c88372`).
- Dialog M0 test: `JoharaDialog.xml` `dialog id=1` locaKey
  `DIALOG_TEXT_JOHARA_1` → `DIALOG_TEXT_JOHARA_5`.
  In-game: Johara говорит про знатока магии и Люс. VERIFIED_LOCAL.
  Restore: `ORIGINAL` (`23bbb1a3…720dab`).

## Managed
22 DLL. Evidence: VERIFIED_LOCAL

Помимо ключевых Legacy.*: `CsvSerializer.dll`,
`Legacy.Editor.Runtime.dll`, `Flow.dll`, `DecalSystem.Runtime.dll`,
UnityScript/Boo, Mono/`mscorlib`.

## Maps
- `StreamingAssets/Maps/*.xml`, 92 файла, корень `Grid`.
- Типы: DUNGEON 77, OUTDOOR 10, CITY 5.
- Примеры: `Cave1.xml` (6×6 dungeon), `Sorpigal.xml` (32×30 city),
  `theworld.xml` (~7 MB outdoor).
- `Sorpigal.xml`: UTF-8 BOM, CRLF, 506224 bytes.
  Старт PARTY Trigger 1 = клетка 31,19 WEST. VERIFIED_LOCAL.
- M0 map test: Slot `X=29 Y=19` Terrain
  `PASSABLE NO_PARTY_BARK` → `BLOCKED`.
  In-game: новая игра, второй шаг на запад — стена. VERIFIED_LOCAL.
  Restore: `ORIGINAL` (`f24b25f4…00d4bc`).
  Процедура: `docs/milestones/M0_MAP_TEST.md`.
- Evidence: VERIFIED_LOCAL
- Схема: `docs/technical/MMX_DATA_SCHEMA.md`.

## ModdingKit / editor
Каталог `ModdingKit/` лежит рядом с игрой. Evidence: VERIFIED_LOCAL

- `Assets/MMXL_ModKit/` — EditorAssets, GameAssets, Materials,
  Models, ModSample, Prefabs, Scenes, Scripts, Shaders, Textures
- `Assets/Gizmos/` — gizmos редактора (NPC, monster, door, spawn…)
- `ProjectSettings/` — Unity project, `productName: modkit`
- `MMXL_Mod_Export/MMXL Sample Mod/` — образец экспорта:
  `Asset/`, `Localisation/`, `Map/`, `Staticdata/`,
  `config.txt`, `modinfo.xml`

Вывод для M0: vanilla data доступны. MMXL ModKit **неполон**
на Ubisoft-сборке (нет `Legacy.Editor*.dll`). MMXLegacy **не**
нужен для M1 и не закрывает editor-дыру (ADR-008).
Заметки: `docs/research/MMXLEGACY.md`.

## StaticID ranges (M2)
Скан `StreamingAssets/StaticData`, VERIFIED_LOCAL:

| Table | n | min | max |
|---|---:|---:|---:|
| NpcStaticData | 278 | 1 | 10000 |
| QuestSteps | 120 | 1 | 10002 |
| QuestObjectives | 209 | 1 | 10002 |
| Token | 558 | -1 | 804 |
| LoreBookStaticData | 39 | 1 | 39 |
| DungeonEntryStaticData | 23 | 1 | 23 |
| WorldMapPointsStaticData | 40 | 1 | 40 |
| MonsterStaticData | 202 | 1 | 10006 |

ID ≥10000 — test-строки (HirelingTest, TokenAddedTest, …).
Полоса MM6X: 20000-29999 (ADR-009).
Карта `Sorpigal` уже есть. Loca
`LOCATION_SORPIGAL_THE_GOBLIN_WATCHTOWER` — дом MMX-Сорпигала,
не данж MM6.

## Installed mods
Признаков установленного third-party мода в StreamingAssets нет.
Evidence: VERIFIED_LOCAL (по составу каталогов)

## Observations
- Сборка Ubisoft; Steam/Ubisoft DLL не смешивать.
- Modding surface совпадает с community-ожиданиями:
  StaticData CSV, Dialog XML, Localisation XML, Maps XML.
- Есть официальный ModdingKit, но editor DLL на этой сборке нет.
  Map proof: правка `Maps/*.xml` без Unity. VERIFIED_LOCAL.
- Схема данных (loca/dialog/CSV/maps/ModdingKit):
  `docs/technical/MMX_DATA_SCHEMA.md`. VERIFIED_LOCAL.
- `resources.assets` ~334 MB; в репозиторий не копировать.
- ModdingKit на этой Ubisoft-сборке **неполон**:
  `Legacy.Editor.dll` и `Legacy.Editor.LevelEditor.dll` отсутствуют
  (есть только `.meta` + `Ionic.Zip.dll`). VERIFIED_LOCAL.
