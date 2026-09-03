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

- Quest #81 — письмо Сулмана Андоверу (`GLOBAL.EVT` e1, NPC #1,
  item 505, QBit 81→82).
- Quest #83 — Дозор гоблинов: **Жанис** NPC #291, ратуша.
  Accept `GLOBAL.EVT` e3: QBit 83, item **489** ключ.
  Turn-in `GLOBAL.EVT` e4: item **543** кодекс, Award 53,
  Exp 2000, Gold 2000, снять QBit 83.
  Кодекс лежит в `d01.dlv` **chest[1]** (`D01.EVT` e41
  `OpenChest 1`), плюс два случайных LB1 (`-1`).
  Текст: `Scroll.txt` item 543 / ITEMS `Mod1=M44`.
  `npctopic.txt` #3/#4: «Дозор гоблинов» (GLOBAL e3/e4).
- Quest #126 — канделябр для Андовера (`GLOBAL.EVT` e296).

EVT slice (не копировать bytecode в git):

- `OUTE3.EVT` e28 house 89 ратуша; e101 house 171 → `D01.blv`.
- `D01.EVT` e51 выход → `OutE3.Odm`.
- `D01.EVT` e19–34: плиты букв А–П (не `InputString`).
  Это maze дверей, не пароль: каждая плита (кроме А/М/П)
  одноразовая (`Compare var>=1` → Exit), открывает одни
  двери (action 1) и закрывает другие (action 0).
  П (e34) сбрасывает vars 105–117, текстуры `T1swDd` и
  все maze-двери в 0. А (e19) — `CastSpell` (ловушка).
  М (e31) — телепорт по той же карте (`map=0`).
  Последовательность в EVT **не проверяется**.
  Симулятор: `python tools\extract\extract_mm6_plates.py`.
  НИЛБОГ оставляет открытыми все 14 maze-дверей;
  ГОБЛИН — только 40/51/52. VERIFIED_LOCAL (симуляция).
  Уникальный «верный порядок» для прохождения комнат
  без BLV — HYPOTHESIS. e66 `OnMapReload` чинит текстуры;
  var 107 дважды, 108 пропущен (баг оригинала).
- Декодер: `python tools\extract\extract_mm6_evt.py`.
  MM6 Compare/Set: `u8 var + u32 value` (не MM7 u16).
  Compare прыгает на target_step если `var >= value`.

## Items (M1-006)

- `ITEMS.TXT`, `STDITEMS.TXT`, `SPCITEMS.TXT`
- `RNDITEMS.TXT`, `USEITEMS.TXT`, `Scroll.txt`
- Дубль `SPCITEMS.TXT` также в `games.lod`

Slice VERIFIED_LOCAL:

- #489 ключ: `Misc`, не свиток. Жанис даёт на accept.
- #505 письмо Сулмана: `Mscroll` `M6` (текст в `Scroll.txt`).
- #543 кодекс: `Mscroll` `M44`, dungeon `D1`.
  Легенда плит А–П (ловушка / двери 1–6 / обслуживание /
  сброс). Слово НИЛБОГ в свитке **нет**.
  Полный текст только в `reports/scrolls_slice.json` (gitignore).
- Логические двери свитка ↔ EVT (симулятор плит):

| № | door_id |
|---:|---|
| 1 | 40, 51, 52 |
| 2 | 36, 47, 48 |
| 3 | 38, 44 |
| 4 | 55, 56 |
| 5 | 57, 58 |
| 6 | 59, 60 |

- #500 (`M1`, D1): короткая запись `III = 16 & IV = 4`
  (другая комбинация кнопок; не кодекс).
- Квест #83: «Найдите код к двери…»; Award #53:
  «Разгадана загадка Дозора гоблинов».
- CLI: `python tools\extract\extract_mm6_scrolls.py`.

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
Карты в `games.lod` (`.blv`/`.dlv`/`.odm`): после записи lod —
`u32 compressed + u32 decompressed + zlib` (`how=size_pair`).
VERIFIED_SOURCE: OpenEnroth `LodReader` / `LodFormats`.
VERIFIED_LOCAL: D01 blv/dlv.
