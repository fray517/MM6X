# New Sorpigal — original topology (M3-001)

Evidence: **VERIFIED_LOCAL** (GOG MM6, `Icons.lod` / `OUTE3.EVT`).
Machine copy: `references/mm6/new_sorpigal.topology.json`.
Full report (gitignore): `reports/topology_oute3.json`.

MapStats #15 `Нью-Сорпигаль` → `OutE3.Odm`, 2D map code **E3**.
Не путать с MMX `Sorpigal` и с `OutD1` (Серебряная бухта).

## Принцип

Только **узлы и рёбра**. Точные MM6-координаты в MMX не
переносим. Относительный compass-layout ниже — **HYPOTHESIS**,
пока не разобран `OutE3.Odm` (spawn/locations).

## Узлы (2DEvents, Map=E3)

| role | count | ids / names |
|---|---:|---|
| quest_hub | 1 | #89 Ратуша (Жанис) |
| social | 1 | #92 Одинокий рыцарь (Дирк; 2D Андовера) |
| travel_hub | 2 | #48 конюшни → Айронфист; #57 лодки → Mist |
| dungeon_entrance | 3 | #171 Дозор; #172 Заброшенный храм; #188 Кузница Гарика |
| service | 11 | оружие/броня/магия/лавка, храм, тренировка, банк, 4 гильдии |
| residence | 22 | House P/M/R* (без Not Used) |

Значимые service (имена VERIFIED_LOCAL):

- #1 Магазин ножей (Кейн)
- #15 Простая защита (Гарри)
- #29 Всевидящее око (Вильма)
- #42 Все для дороги (Рино)
- #69 Храм Нью-Сорпигаль (Джошуа)
- #79 Полигон (Натан, max lvl 15)
- #113 Сберегательный дом (Шмиди)
- #137 Начальная гильдия Стихий (Джероми)
- #139 Начальная гильдия Эго (Телиана)
- #141 Острие клинка (Далимар)
- #147 Притон морских разбойников (Отшельник)

## Рёбра map_transition (`OUTE3.EVT`)

| event | house | → map | stable / title |
|---:|---:|---|---|
| 101 | 171 | `D01.blv` | `mm6.dungeon.goblinwatch` / Дозор |
| 102 | 172 | `D02.blv` | Заброшенный храм |
| 103 | 188 | `D18.Blv` | Кузница Гарика |
| 104 | — | `OutB3.Odm` | Драконсэнд (outdoor exit) |

Spawn XYZ на целевой карте есть в EVT (см. topology JSON);
для MMX grid они — ориентир, не метры.

Доп. travel (не MoveToMap, а schedule в 2DEvents):

- Stables #48 → Castle Ironfist / `OutD3.Odm` (M,W,F)
- Boats #57 → Mist / `OutE2.Odm` (Tu,Th,Sa)

## Encounter layer (MapStats #15)

- Mon1: Goblin / Гоблин
- Mon2: PeasantM2 / Ученик мага

Зоны спавна на outdoor — HYPOTHESIS до ODM/DDM decode.

## Граф (логический)

```text
[OutB3 Драконсэнд] ←e104── (outdoor)
                         │
        ┌──── travel ────┼──── travel ────┐
        │                │                │
   stables#48        TOWN CORE         boats#57
   → OutD3           (shops/guilds     → OutE2
                      temple#69
                      train#79
                      bank#113
                      tavern#92
                      town hall#89)
                         │
              ┌──────────┼──────────┐
              │          │          │
           D01#171    D02#172    D18#188
           Goblinwatch Abandoned  Garik
```

Town core внутри outdoor E3 полностью связан пешком
(один outdoor map) — отдельные «улицы» появятся на MMX grid
в M3-007, опираясь на quest routes (M3-002/009), не на
сырые координаты.

## Вне scope M3-001

- Список NPC и привязки (M3-003)
- Полный каталог услуг/цен (M3-004)
- Encounter placement (M3-005)
- Cell budget / grid sketch (M3-007/008)
- Decode `OutE3.Odm` location XY (можно подключить позже
  как уточнение layout; не блокер design approve)

## Refresh

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_evt.py
python tools\extract\extract_mm6_topology.py --write-curated
```
