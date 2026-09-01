# MM6 source files (this GOG install)

Evidence: VERIFIED_LOCAL (имена записей lod, тела не извлечены).
Сборка: GOG + MM6patch, см. `MM6_AUDIT.md`.

## NPC (M1-004)

`Icons.lod`:

- `NPCdata.txt` — слоты/привязки NPC
- `npcnames.txt`, `npctext.txt`, `npctopic.txt`, `NPCNews.txt`
- `npcprof.txt`, `npcbtb.txt`
- `2DEvents.txt` — 2D-локации (дома/магазины)

Портреты: `NPC001`… в том же lod (графика, не копировать).

## Quest / dialogue scripts (M1-005)

- `Quests.txt`, `GLOBAL.TXT`, `GLOBAL.EVT`
- По карте: `OUTD1.EVT`, `D01.EVT`, … (83 `.EVT`)
- `Awards.txt`, `Autonote.txt`

## Items (M1-006)

- `ITEMS.TXT`, `STDITEMS.TXT`, `SPCITEMS.TXT`
- `RNDITEMS.TXT`, `USEITEMS.TXT`, `Scroll.txt`
- Дубль `SPCITEMS.TXT` также в `games.lod`

## Monsters (M1-007)

- `MONSTERS.TXT`
- Спрайты: `SPRITES.LOD` (не таблица)

## Map / topology (M1-008)

`games.lod`:

- Outdoor: `Outa1.odm`…`Oute3.odm` (и `.ddm`)
- Indoor: `d01.blv`…`d20.blv`, `t1.blv`…`t8.blv`, `hive.blv`,
  `oracle.blv`, `pyramid.blv`, `sewer.blv`, `sci-fi.blv`, CD/z*
- `MapStats.txt` в `Icons.lod` (имена карт; тело пока не декодировали)

Slice HYPOTHESIS (файл есть, привязка имени — нет MapStats decode):

| Stable id | Кандидат |
|---|---|
| `mm6.region.new_sorpigal` | `Outd1.odm` + `OUTD1.EVT` |
| `mm6.dungeon.goblinwatch` | `d01.blv` + `D01.EVT` |

Следующий шаг extract: только нужные `.txt`/`.EVT` в
`references/mm6/raw/` (gitignore), затем JSON модели.
