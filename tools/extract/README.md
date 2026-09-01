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

Эта русская GOG-сборка: `--encoding cp1251` (дефолт). Выход — UTF-8.

`MapStats.txt` дополнительно даёт `reports/mapstats_index.json`
(gitignore): только id / имя / файл карты.

Offset в lod: `root.dataOffset + entry.dataOffset`
(OpenEnroth `LodEntry_MM6`). Не брать абсолютный offset из каталога.
