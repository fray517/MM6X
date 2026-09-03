# MM6 extract

Read-only извлечение allowlisted `.txt` из `Icons.lod`.
Игра не изменяется. Тела таблиц в git не класть
(`references/mm6/raw/` в `.gitignore`).

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_text.py --help
python tools\extract\extract_mm6_text.py --dry-run
python tools\extract\extract_mm6_text.py --game-path "C:\Program Files\GOG Galaxy\Games\Might and Magic 6"
```

Если в `.env` задан `MM6_GAME_PATH`, `--game-path` можно не указывать.

По умолчанию: `MapStats.txt`, `NPCdata.txt`, `npcnames.txt`,
`Quests.txt`, `2DEvents.txt`, `ITEMS.TXT`, `MONSTERS.TXT`.
Свитки: `--name Scroll.txt` (gitignore raw). Slice кодекса:
`python tools\extract\extract_mm6_scrolls.py`.

Эта русская GOG-сборка: `--encoding cp1251` (дефолт). Выход — UTF-8.

`MapStats.txt` дополнительно даёт `reports/mapstats_index.json`
(gitignore): только id / имя / файл карты.

## EVT / STR

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_evt.py --dry-run
python tools\extract\extract_mm6_evt.py
```

По умолчанию стемы: `OUTE3`, `D01`, `GLOBAL`.
Индекс (gitignore): `reports/evt_slice.json`.
Bytecode `.EVT` в git не класть.

MM6 instruction: length byte, eventId u16, step u8, opcode u8.
Compare/Set: `u8 var + u32 value` (эта сборка). VERIFIED_LOCAL.
STR: NUL-separated strings. VERIFIED_SOURCE: OpenEnroth
`EvtProgram::load` / `initLevelStrings`.

## Chests (indoor .dlv)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_chests.py --dry-run
python tools\extract\extract_mm6_chests.py
```

По умолчанию: `D01`. Индекс: `reports/chests_slice.json`.
`games.lod` карты: `u32 comp + u32 decomp + zlib` (`size_pair`).
MM6 MapChest: picture/flags + 140×Item(0x1C) + 140×i16.
VERIFIED_LOCAL: D01 chest[1] = item 543.

Offset в lod: `root.dataOffset + entry.dataOffset`
(OpenEnroth `LodEntry_MM6`). Не брать абсолютный offset из каталога.

## Letter plates (D01)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_plates.py --self-test
python tools\extract\extract_mm6_plates.py --dry-run
python tools\extract\extract_mm6_plates.py --sequence НИЛБОГ
```

Не `InputString`: одноразовые двери (vars 105-117), П сбрасывает.
Слово в EVT не проверяется. Индекс: `reports/plates_d01.json`.

## Message scrolls

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\extract\extract_mm6_scrolls.py --self-test
python tools\extract\extract_mm6_scrolls.py --dry-run
```

По умолчанию: 489 (ключ), 500 (D01 M1), 505 (письмо Сулмана),
543 (кодекс, `Mod1=M44`). Индекс: `reports/scrolls_slice.json`.
Полные письма в git не класть.
