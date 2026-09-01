# MMX Data Schema

Status: RUN 2026-09-01  
Evidence по умолчанию: **VERIFIED_LOCAL** (Ubisoft-установка, read-only).  
Полные тексты/ассеты в репозиторий не копировались.

Связанный аудит: `docs/research/MMX_AUDIT.md`.  
Машинный дамп (gitignored): `reports/schema_probe.json`.

```text
MMX content
 ├── Localisation  loca.xml          key → text
 ├── NPC           NpcStaticData.csv
 ├── Dialog        Dialog/*.xml
 ├── Quest         QuestSteps.csv + QuestObjectives.csv
 ├── Monster       MonsterStaticData.csv
 ├── Map           Maps/*.xml  (+ ModdingKit export)
 └── Token         Token.csv (флаги квестов/диалогов)
```

Кодировки:

| Формат | Encoding | Замечания |
|---|---|---|
| `loca.xml` | UTF-8 | XML declaration |
| `Dialog/*.xml` | UTF-8 | 1/268 файлов содержит cp1252 `…` (`TutorialDialog.xml`) |
| `StaticData/*.csv` | UTF-8 (часто BOM) | разделитель `,`; строки `#…` — комментарии |
| `Maps/*.xml` | UTF-8 | корень `Grid`; BOM встречается |

CSV: `TRUE`/`FALSE` в верхнем регистре. Пустая колонка без имени в NPC — дизайнерский комментарий, не ID.

---

## Связи ID

```text
NpcStaticData.StaticID
 ├── ConversationKey  →  Dialog/{ConversationKey}.xml
 ├── NameKey          →  loca.xml LocaData@id
 └── PortraitKey      →  портрет (ресурс, не loca)

QuestSteps.StaticID
 ├── GivenByNPCID     →  NpcStaticData.StaticID  (0 = нет NPC)
 ├── Objectives       →  QuestObjectives.StaticID  (пары id,flag)
 ├── FollowUpStep     →  QuestSteps.StaticID       (0 = конец)
 ├── Name / Flavor / Short  →  loca.xml
 └── TokenID / SteadyLoot   →  награды

QuestObjectives.StaticID
 ├── NpcID                 →  NpcStaticData
 ├── KillMonsterStaticID   →  MonsterStaticData
 ├── TokenID               →  Token.csv
 └── Location              →  loca-ключ локации

Map Grid
 ├── WorldMapPointID       →  WorldMapPointsStaticData
 ├── Slot/Trigger@ID       →  spawner id (диалоги/команды ссылаются сюда)
 ├── SpawnObjectType=NPC_CONTAINER + SpawnStaticID → NPC
 ├── SpawnObjectType=MONSTER + SpawnStaticID       → Monster
 ├── Trigger/Objective@ID  →  QuestObjectives
 └── Command START_DIALOGUE Extra → имя карты `.xml` или пусто

Dialog
 ├── text@locaKey     →  loca.xml
 ├── condition questID / tokenID / npcID / objectiveID / map
 └── function dialogID / questID / tokenID / targetSpawnerID
```

Vanilla `config.txt`: `start = "Sorpigal"`.  
Имя карты = `Maps/{Name}.xml` = `Grid/Name` = `Grid/SceneName`.

---

## Localisation

Файл: `StreamingAssets/Localisation/<lang>/loca.xml`  
Языки: br, cn, cz, de, en, es, fr, hu, it, jp, kr, pl, ro, ru.

```text
Localization
 └── LocaData@id = KEY
       └── text node = localized string
```

- en: 8107 ключей, все уникальны.
- ru: 8127 ключей (+20 относительно en).
- Дочерних элементов у `LocaData` нет, только атрибут `id` и текст.

Топ префиксов ключей (en): `DIALOG`, `SUFFIX`, `MONSTER`, `QUEST`, `OPTIONS`, `NPC`, `SKILL`, `LOCATION`, `SPELL`, `VIDEO`, `RELIC`, `RIDDLE`, `LOREBOOK`, `CHARACTER`, `TOKEN`, `PREFIX`, `ACTION`, `GUI`, `TRAP`, `HIRELING`.

Имена:

- NPC: `NPC_NAME_*`
- квест: `QUEST_STEP_*_NAME` / `_FLAVOR` / `_SHORT`, `QUEST_OBJECTIVE_*`
- диалог: `DIALOG_TEXT_*`, `DIALOG_OPTION_*`
- монстр: `MONSTER_*`

Подмена одной `LocaData` по `id` — безопасный M0 localisation proof. HYPOTHESIS: игра читает язык из настроек и берёт `Localisation/<lang>/loca.xml`.

---

## NPC

Файл: `StaticData/NpcStaticData.csv` — 278 строк.

```text
NPC
 ├── StaticID              int, уникальный
 ├── NameKey               loca NPC_NAME_*
 ├── HirelingProfession    пусто у большинства; иначе HIRELING_*
 ├── (unnamed col)         ярлык, не ключ данных
 ├── PortraitKey           PIC_unique_* / PIC_generic_*
 ├── ConversationKey       имя Dialog-файла без .xml
 ├── TravelStationID       в vanilla всегда 0
 ├── NpcEffects            эффекты наёмника (см. ниже)
 ├── HirePrice / HireShare
 ├── CanBeFired            TRUE/FALSE
 ├── AllowItemSell         TRUE/FALSE
 └── MinimapSymbol         NORMAL | HOUSE | SHRINE | INN | SMITH
```

`ConversationKey` совпадает с файлом: `LordHaartDialog` → `Dialog/LordHaartDialog.xml`.

Наёмник (~29 из 278): `HirelingProfession` + `NpcEffects` вида  
`HIRE_BONUSXP,PERMANENT,0.1,0` (можно несколько эффектов подряд).  
Периодичность: `PERMANENT`, `ONCE_A_TURN`, `ONCE_A_DAY`, `ON_DEMAND`.

Пустая 4-я колонка — человеческий ярлык (`Trainer: Sword - Grand Master`), не ключ данных.

---

## Quest

Две таблицы. Квест = **step** (запись журнала) + список **objectives**.

### QuestSteps.csv — 120 строк

```text
QuestStep
 ├── StaticID
 ├── Type
 │     QUEST_TYPE_MAIN | SIDE | ONGOING | GRANDMASTER | PROMOTION
 ├── Name / FlavorDescription / ShortDescription   loca-ключи
 ├── GivenByNPCID          NPC, 0 если не NPC
 ├── Objectives            "id,flag,id,flag,…"  (flag в vanilla = 1)
 ├── FollowUpStep          следующий step, 0 = нет
 ├── RepeatTime            в vanilla всегда 0
 ├── RewardXP
 ├── TokenID               выдаваемый токен (иногда список)
 └── loot
       ├── SteadyLoot      CLASS,id,min,max,chance[,…]
       ├── GoldChance / GoldAmount   "min,max"
       └── Item*           в vanilla пустые/нулевые
```

Цепочки: `FollowUpStep` ведёт на другой `StaticID` (например 1 → 110).

### QuestObjectives.csv — 209 строк

```text
Objective
 ├── StaticID
 ├── Description           loca QUEST_OBJECTIVE_*
 ├── IsMainObjective       TRUE/FALSE
 ├── IsReturn              TRUE = «вернуться к NPC»
 ├── NpcID                 связанный NPC (0 = нет)
 ├── TokenID               0 или токен-условие/награда
 ├── KillMonsterClass      в vanilla всегда NONE
 ├── KillMonsterType       NONE | именованная волна/тип
 ├── KillMonsterStaticID   0 или MonsterStaticData.StaticID
 ├── DaysToPass            0 | 1 | 7 | 28
 ├── StepsOnTerrain        почти не используется (1 строка)
 └── Location              loca локации, часто пусто
```

Как закрывается objective — не в CSV, а в диалогах (`SolveQuestFunction`) и на карте (`Trigger/Objective`). HYPOTHESIS: токен + kill + return-to-NPC покрывают большую часть.

Первый vanilla-квест: step 1 `QUEST_STEP_LOOKING_FOR_JOB_1_*`, `GivenByNPCID=14` (Dunstan), objective `1`.

---

## Dialog

Каталог: `StreamingAssets/Dialog/*.xml` — 268 файлов.  
Корень каждого: `NpcConversationStaticData`.

```text
NpcConversationStaticData @rootDialogID
 ├── offer @id                  магазин/услуга (необязательно)
 └── dialog @id
       ├── @fakeNpcID           подмена портрета (0 = нет)
       ├── @hideBackButton / @hideNpcsAndCloseButton / @hideNpcAndPortrait
       ├── @randomText
       ├── text @locaKey        реплика (всегда ключ, не inline)
       │     └── @voiceID       опционально VO-клип
       └── entry                вариант ответа игрока
             ├── text @locaKey
             ├── condition*     xsi:type + failState
             └── function*      xsi:type + параметры
```

`rootDialogID` почти всегда `1`. Переходы: `GoToFunction@dialogID`. Выход: `QuitFunction`.  
`dialogID=-1` встречается как «закрыть/назад».

Все 2885 узлов `text` ссылаются на loca через `locaKey`. Inline-текста нет.

`failState`: `HIDDEN` (783) >> `DISABLED` (24).

### Conditions (все 268 файлов)

| xsi:type | Зачем |
|---|---|
| `QuestActiveCondition` / `QuestInactiveCondition` / `QuestFinishedCondition` / `QuestNotFinishedCondition` / `QuestNotActiveCondition` / `QuestNotInactiveCondition` | состояние квеста (`questID`) |
| `ObjectiveSolvedCondition` / `ObjectiveNotSolvedCondition` | `objectiveID` |
| `TokenAcquiredCondition` / `TokenNotAcquiredCondition` | `tokenID` |
| `HirelingHiredCondition` / `HirelingNotHiredCondition` / `HirelingPeriodicityCondition` / `HirelingFreeSlotCondition` | `npcID` |
| `CheckOnMapCondition` / `CheckNotOnMapCondition` | `map` |
| `PartyHasClassCondition` / `PartyNotHasClassCondition` | `class` |
| `PartyHasRaceCondition` / `PartyNotHasRaceCondition` / `PartyHasRaceGenderCondition` | `race`, `gender` |
| `DayTimeEqualsCondition` / `DayTimeNotEqualsCondition` | `dayTime` |
| `BrokenItemsCondition` / `UnidentifiedItemsCondition` | `repairType` |
| `PrivilegeUnlockedCondition` / `RewardUnlockedCondition` | `privilegeID` / `rewardID` |
| `MuleInventoryEmptyCondition` / `MuleInventoryNotEmptyCondition` | вьючное животное |

### Functions (все 268 файлов)

| xsi:type | Главные атрибуты |
|---|---|
| `GoToFunction` | `dialogID` |
| `QuitFunction` | — |
| `QuestFunction` | `questID` (выдать/активировать) |
| `SolveQuestFunction` / `ForceSolveQuestFunction` | `questID` |
| `GiveTokenFunction` | `tokenID` |
| `ActivateLevelTriggerFunction` | `targetSpawnerID` |
| `HirelingFunction` | `npcID`, `conditionTarget` (HIRE / FIRE) |
| `TriggerAggroFunction` | `monsterID` |
| `ItemTradingFunction` | магазин |
| `RepairFunction` / `IdentifyFunction` | услуги |
| `TravelFunction` | `mapName` |
| `ChangeNpcContainerFunction` | `containerID`, `npcID` |
| `ObeliskFunction` | обелиски |
| `ExecuteTriggerFunction` | триггер карты |
| `StartDLCFunction` / `CutsceneStateFunction` / `AutoSaveFunction` | служебные |
| `RemoveSetFunction` / `DecreaseAttributeFunction` | редкие |
| `KillMonsterFunction` / `GameOverFunction` | единичные |

Опечатки vanilla (не ломать при патче): `RandomText` vs `randomText`, `ideBackButton`, `backToDialodId`, `targetSpawnerId` vs `targetSpawnerID`.

Минимальный файл: один `dialog` + один `text@locaKey` (например `ImperialSentinelBridgeDialog.xml`).

---

## Monster

Файл: `StaticData/MonsterStaticData.csv` — 202 строки, широкая боевая таблица.

```text
Monster
 ├── StaticID
 ├── Name                   внутреннее имя (не loca)
 ├── NameKey                loca MONSTER_*
 ├── Prefab                 Prefabs/Creatures/…
 ├── MenuPath               категория бестиария Undead/Ghost
 ├── Size                   SMALL | MEDIUM | BIG
 ├── Grade                  CORE | ELITE | CHAMPION | BOSS
 ├── Class                  UNDEAD | HUMANOID | BEAST | HUMAN | ELEMENTAL | NONE
 ├── Type                   GHOST, SKELETON, …
 ├── Gender / AIBehaviour
 ├── AccessibleTerrains     PASSABLE,WATER,ROUGH,FOREST,…
 ├── aggro                  AggroRange*, SightAggroRange*, AlwaysTriggerAggro
 ├── combat                 melee / ranged / spells / resists / HP / XP
 ├── Abilities              UNDEAD,1,VINDICTIVE,1,…
 └── loot                   SteadyLoot, ItemDropChance, Gold*, Prefix/Suffix, TokenID
```

`TokenID=0` у обычных; ненулевой — квестовый дроп-флаг.  
`BestiaryEntry` / `BestiaryThresholds` — журнал бестиария.  
На карте монстр ставится `SpawnObjectType=MONSTER` + `SpawnStaticID`.

---

## Map

92 XML в `StreamingAssets/Maps/`. Корень — **`Grid`**, не `<Map>`.

Типы карт: `DUNGEON` (77), `OUTDOOR` (10), `CITY` (5).  
Стили (тайлсет): `CASTLE`, `CAVES`, `RUINS`, `TEMPLE`, `PALACE`.

Разобраны: `Cave1.xml` (данж 6×6) и `Sorpigal.xml` (город 32×30).  
`theworld.xml` — огромная outdoor-сетка (~7 MB), та же схема.

```text
Grid
 ├── Name / SceneName              совпадают с именем файла
 ├── MinimapName                   MinimapMaps/MAP_*
 ├── LocationLocaName              loca LOCATION_*
 ├── Type / Style
 ├── WorldMapPointID
 ├── Width / Height                клетки
 ├── OffsetX/Y/Z, MinLevel/MaxLevel
 ├── MusicAudioIDDay/Night, IsWithFightMusic
 └── GridSlots
       └── Row × Height
             └── Slot × Width
                   ├── @Height @Terrain @TerrainSound @MapArea
                   ├── Position/X,Y
                   ├── Transition × 4     стороны клетки
                   │     @Type OPEN|CLOSED  @IsDynamic
                   └── Trigger*           объекты на клетке
                         ├── @ID          spawner id
                         ├── SpawnObjectType        элемент, не атрибут
                         ├── SpawnStaticID / SpawnDirection / SpawnTime
                         ├── MonsterGroupID / ChallengeID / Enabled / InitialState
                         ├── Position, OffsetPosition, ObjectRotation
                         ├── Objective@ID          квестовая цель
                         ├── Command*              действия
                         └── ObjectTypeCommand*    то же для типа объекта
```

`Terrain` (проверено): `BLOCKED`, `PASSABLE`, редко `PASSABLE NO_PARTY_BARK`.  
Ровно 4 `Transition` на слот → стороны света. HYPOTHESIS: порядок N,E,S,W.

NPC на карте: `SET_DATA Extra="NPC_IDS,<StaticID>"`, не `SpawnStaticID`
(у контейнеров часто `10`). Johara = `NPC_IDS,2` (Trigger 24, клетка 6,22).

Старт новой игры в Sorpigal: PARTY Trigger ID=1, `Enabled=true`,
клетка 31,19, `SpawnDirection=WEST`. VERIFIED_LOCAL.

`Sorpigal.xml`: UTF-8 **with BOM**, CRLF, 506224 bytes. VERIFIED_LOCAL.

### SpawnObjectType

| Тип | Cave1 | Sorpigal |
|---|---:|---:|
| `PARTY` | 1 | 5 |
| `ENTRANCE` | 1 | 3 |
| `MONSTER` | 1 | — |
| `CONTAINER` | 2 | 8 |
| `NPC_CONTAINER` | — | 26 |
| `SENSOR` | — | 29 |
| `DOOR` / `TELEPORTER` / `BARREL` | — | есть |
| `PLACEHOLDER` / `COMMAND_CONTAINER` / `SIGN` / `RECHARGING_OBJECT` | — | есть |

NPC на карте = `NPC_CONTAINER` + `SET_DATA Extra="NPC_IDS,<id>"`.  
`SpawnStaticID` у городских контейнеров часто `10`, это не NPC id.  
Партия = `PARTY`. Переходы между картами = `ENTRANCE` + `USE_ENTRANCE`.

### Command Type (Sorpigal)

`SET_DATA`, `SET_ENABLED`, `START_DIALOGUE`, `START_DEFINED_DIALOG`, `ROTATE_PARTY`, `OPEN_CONTAINER`, `BARREL_INTERACTION`, `TOGGLE_DOOR`, `USE_ENTRANCE`, `TRIGGER_HINT`, `TELEPORT`, `SPAWN_MONSTER`, `RECHARGER_INTERACTION`, `VIEW_SIGN`, `ADD_LOREBOOK`, `MOVE_OBJECT`.

`START_DIALOGUE@TargetSpawnID` указывает на `Trigger@ID` NPC.  
`Extra` иногда имя другой карты (`Spider_Lair_1.xml`), иногда пусто.  
`START_DEFINED_DIALOG@Extra` — числовые пары (`14,17`), `Precondition` вида `PARTY_CHECK,…`.

Атрибуты команды: `Type`, `TargetSpawnID`, `Extra`, `Precondition`, `Timing`, `RequiredState`, `ActivateCount`.

Город Sorpigal уже есть в MMX (`LOCATION_SORPIGAL-BY-THE-SEA`, `WorldMapPointID=3`). Это MMX-Сорпигал, не MM6 New Sorpigal. Не переписывать без M0 map proof.

---

## Token

`StaticData/Token.csv` — флаги прогресса, которые диалоги и квесты проверяют/выдают.

Колонки: `StaticID`, `Icon`, `Name`, `Usage`, `Description`, `Menupath`, `TokenVisible`, `SetID`, `Replacement`, `RemoveSilent`.  
`StaticID=-1` = `TOKEN_NONE`. Имена — loca-ключи `TOKEN_*`.

---

## ModdingKit

Путь: `{MMX}/ModdingKit/`. Unity 4 проект (`productName: modkit`).

```text
ModdingKit/
 ├── Assets/
 │    ├── Gizmos/                 иконки объектов в сцене
 │    └── MMXL_ModKit/
 │         ├── EditorAssets/      grid shaders, path_collection.csv, settings.txt
 │         ├── GameAssets/Staticdata/   56 CSV для редактора
 │         ├── Materials / Models / Textures / Shaders / Prefabs
 │         ├── Prefabs/           Castle, Cave, Lighting, ShantiriRuins
 │         ├── Scenes/Dungeon/    Spider_Lair.unity + lightmaps + terrain
 │         ├── Scripts/           Decal System (.cs) + Editor/*.dll.meta
 │         └── ModSample/         ModInfo.asset (описывает экспорт)
 ├── ProjectSettings/
 └── MMXL_Mod_Export/MMXL Sample Mod/    готовый пакет
```

Счётчики: 126 prefab, 1 сцена `.unity`, 17 `.cs` (только Decal System), 3 заявленных DLL.

### Неполный editor на этой сборке

В `Scripts/Editor/`:

| Файл | Статус |
|---|---|
| `Ionic.Zip.dll` | есть |
| `Legacy.Editor.dll` | **нет**, только `.meta` |
| `Legacy.Editor.LevelEditor.dll` | **нет**, только `.meta` |

`ModInfo.asset` ссылается на скрипт из `Legacy.Editor.LevelEditor.dll` (guid `53992036…`). Без этих DLL Unity-редактор карт, скорее всего, не откроет инспектор мода.  
**HYPOTHESIS:** Steam/другой depot могут содержать `Legacy.Editor*.dll`.
MMXLegacy их не даёт (rewritten `Legacy.Core/Game`, не editor).
На Ubisoft-копии карты правим XML, не Unity. VERIFIED_LOCAL (M0-074).

В игровом `Managed/` есть `Legacy.Editor.Runtime.dll` — это runtime, не editor.

`EditorAssets/settings.txt` (фрагмент путей):

```text
clientExport = "../client/assets/StreamingAssets/Maps"
maps = "_LevelScenes/"
dungeons = "Dungeons"
cities = "Cities"
outdoor = "Outdoor"
```

Пути — от внутренней раскладки Limbic, не от этой установки.

`path_collection.csv`: имя объекта (`CUTSCENE/Iven`) → путь prefab. Первая часть имени = `EObjectType`.

### Образец экспорта `MMXL Sample Mod`

```text
modinfo.xml
config.txt
Asset/Spider_Lair.pak          ~171 MB, 3D/asset bundle
Asset/Spider_Lair_Minimap.png
Asset/assets.db
Map/Spider_Lair.xml            та же Grid-схема, что vanilla Maps/
Localisation/<lang>/loca.xml   полные копии всех языков
Staticdata/*.csv               почти полный набор таблиц
```

`modinfo.xml`:

```xml
<Mod>
  <Name>…</Name>
  <Creators>…</Creators>
  <Description>…</Description>
  <Version>1.0</Version>
  <DefaultLanguage>English</DefaultLanguage>
</Mod>
```

В sample **нет** `Dialog/`. `ModInfo.asset` поле `m_dialogPath` пустое.  
Диалоги, похоже, живут отдельно в `StreamingAssets/Dialog` и не входят в стандартный export карты.

`config.txt` мода — те же секции, что у vanilla (`[map]`, `[grid]`, `[gametime]`, `[gameplay]`, `[conditions]`, `[skills]`, `[party]`, `[combat]`…). Sample стартует в `Spider_Lair`, party `7,10,5,3`, `maxLevel=25`. Vanilla: `start=Sorpigal`, `maxLevel=50`.

Как игра **подхватывает** папку мода (отдельный Mods-каталог vs overlay StreamingAssets) на этой сборке ещё не проверялось. HYPOTHESIS до M0 install/stage.

---

## Выводы для MM6X

1. Контентный пайплайн без C# patch: CSV + Dialog XML + loca.xml + Maps XML.
2. Новые NPC/квесты = новые строки StaticData + файл диалога + ключи loca + (для мира) Trigger на карте.
3. Карта — клеточная `Grid`; расстояния MM6 сюда не масштабируются.
4. Токены — основной «флаг сюжета» между диалогом, квестом и картой.
5. Официальный kit на Ubisoft-установке **неполон** (нет editor DLL).
   Карты: правка `Maps/*.xml`. VERIFIED_LOCAL.
6. В MMX уже есть город `Sorpigal` — не путать с New Sorpigal MM6.
7. MMXLegacy не hard dependency (ADR-008).

M0 закрыт: `docs/milestones/M0_ACCEPTANCE.md`. Дальше — M1.
