# MM6 Local Installation Audit

Status: RUN 2026-09-01. Evidence: VERIFIED_LOCAL.

Полный дамп (gitignore): `reports/mm6_audit.json`, `reports/MM6_AUDIT.md`.
Аудит read-only. Тела lod в git не копировать.

## Game path
- GOG Galaxy: `...\GOG Galaxy\Games\Might and Magic 6`
- Data: `data\` (lowercase)
- Product id: `goggame-1207661253`
- Путь: `MM6_GAME_PATH` в `.env` (шаблон `env.example`)

## Executable
| File | Size | SHA-256 |
|---|---:|---|
| `MM6.exe` | 851968 | `fe3adb9ed62cb300f979ef337a9c093a0115d656ebf9ed758408532699ebf4d7` |

## Distribution / overlay
- kind: **gog**. VERIFIED_LOCAL
- `MM6patch.dll` (GrayFace-style patch: `mm6.ini` имеет `PatchLods=1`,
  `DataFiles=1`, `UseMM6textDll=1`)
- Текст: `mm6text.dll`, не `EnglishT.lod`
- Есть `M&M6RUS_voice.exe` (голос, не разбираем)
- Music: пусто; Sounds: mp3; Anims: `Anims1.vid` / `Anims2.vid`

## LOD на диске

| Файл | Записей (каталог) | Роль |
|---|---:|---|
| `Icons.lod` | 2704 | UI, таблицы `.txt`, скрипты `.EVT` |
| `games.lod` | 135 | карты `.blv`/`.odm` + `.dlv`/`.ddm` |
| `BITMAPS.LOD` | 1959 | текстуры |
| `SPRITES.LOD` | 4315 | спрайты |

Классических `events.lod`, `englishd.lod`, `englisht.lod` **нет**.
На этой сборке события — `Icons.lod/*.EVT`. VERIFIED_LOCAL

Unpacked `.blv`/`.odm` рядом с Data нет.

Индекс имён: `python tools\audit\audit_mm6.py` (без извлечения тел).
Текстовые таблицы: `python tools\extract\extract_mm6_text.py`
(Bodies в `references/mm6/raw/`, gitignore).

Источники таблиц/карт: `docs/research/MM6_SOURCES.md`.

Slice MapStats (VERIFIED_LOCAL): #15 Нью-Сорпигаль `OutE3.Odm`;
#16 Дозор гоблинов `D01.Blv`. `OutD1` — Серебряная бухта.
