# MM6 source files (this GOG install)

Evidence: VERIFIED_LOCAL (имена записей lod + декодированные
allowlisted `.txt`; полные таблицы в git не копировать).
Сборка: GOG + MM6patch, см. `MM6_AUDIT.md`.

Raw extract (gitignore): `references/mm6/raw/`.
Команда: `python tools\extract\extract_mm6_text.py`.

## NPC (M1-004)

`Icons.lod`:

- `NPCdata.txt` — слоты/привязки NPC
- `npcnames.txt`, `npctext.txt`, `npctopic.txt`, `NPCNews.txt`
- `npcprof.txt`, `npcbtb.txt`
- `2DEvents.txt` — 2D-локации (дома/магазины)

Портреты: `NPC001`… в том же lod (графика, не копировать).

Slice (не дамп таблицы):

- NPC #1 `Андовер Портбелло`, pic 81, колонка 2D Location = 92.
- 2DEvents #92 на карте E3 — таверна «Одинокий рыцарь»,
  трактирщик Дирк (не дом Андовера).
- 2DEvents #89 — Ратуша Нью-Сорпигаля, клерк Жанис.

## Quest / dialogue scripts (M1-005)

- `Quests.txt`, `GLOBAL.TXT`, `GLOBAL.EVT`
- По карте: `OUTE3.EVT`, `D01.EVT`, … (83 `.EVT`)
- `Awards.txt`, `Autonote.txt`

Slice:

- Quest #81 — письмо Сулмана Андоверу в Нью-Сорпигале.
- Quest #83 — код двери Дозора гоблинов; **Set by Town Hall**,
  возврат в ратушу. Не квест Андовера.
- Quest #126 — канделябр для Андовера.

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
- `MapStats.txt` в `Icons.lod` (имена карт)

Полный индекс id/имя/файл (gitignore):
`reports/mapstats_index.json`.

Slice VERIFIED_LOCAL:

| Stable id | MapStats | Файл | EVT |
|---|---:|---|---|
| `mm6.region.new_sorpigal` | 15 Нью-Сорпигаль | `OutE3.Odm` | `OUTE3.EVT` |
| `mm6.dungeon.goblinwatch` | 16 Дозор гоблинов | `D01.Blv` | `D01.EVT` |

`OutD1.Odm` = «Серебряная бухта». Не путать с Нью-Сорпигалем.

Вход в данж на outdoor E3: `2DEvents.txt` #171
«Дозор гоблинов» (Dungeon Ent).

## Decode lod (для extract)

Каталог MM6: header 256 байт, root entry сразу после него.
`file.abs_offset = root.dataOffset + entry.dataOffset`.
Текстовые `.txt` в `Icons.lod`: `LodImageHeader_MM6` (48 байт),
`flags & 0x100`, payload zlib (`78 9c`).
VERIFIED_SOURCE: OpenEnroth `LodReader` / `LodFormats`.
