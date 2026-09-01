# M0 — Backup / restore + localisation proof

Evidence: VERIFIED_LOCAL (схема `ru/loca.xml`).  
In-game 2026-09-01: главное меню показало
`MM6X TEST — Параметры`. Restore ещё не подтверждён.

## Выбранный ключ

| | |
|---|---|
| Key | `Gui/Mainmenu/Options` |
| Где видно | Главное меню, кнопка параметров |
| Original | `Параметры` |
| Test | `MM6X TEST — Параметры` |

Почему безопасно: не квест, не NPC, не предмет, не строка загрузки
движка. Меню уже на экране после старта. Достаточно языка «Русский».

## Backup plan (M0-010)

- Копия **байт-в-байт** в репозиторий, не в каталог MMX:
  `backups/mmx/loca-ru/loca.xml` (gitignored).
- Рядом `manifest.json` с SHA-256.
- Повторный backup без `--force` — отказ.
- `--force` не удаляет старое: слот переименовывается в
  `loca-ru.<UTC>/`.
- Restore копирует backup обратно и сверяет SHA-256.

Состояние (`status`):

- `ORIGINAL` — текущий файл = backup
- `TEST_PATCHED` — значение ключа начинается с `MM6X TEST —`
- `UNKNOWN` — файл изменён иначе
- `NO_BACKUP` — копии ещё нет

Ubisoft ставит игру в `Program Files (x86)`. Apply/restore могут
потребовать PowerShell **от имени администратора**.

## Команды

Подставьте свой каталог MMX или задайте `MMX_GAME_PATH` в `.env`.

```powershell
$game = "C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\Might & Magic X Legacy"
```

### 1. Prepare (игра не меняется)

```powershell
python tools\modding\mmx_mod.py --game-path $game prepare-localisation-test
```

### 2. Backup

```powershell
python tools\modding\mmx_mod.py --game-path $game backup
python tools\modding\mmx_mod.py --game-path $game status
```

Ожидание: `state: ORIGINAL` после backup, пока файл не патчили.

### 3. Apply

```powershell
python tools\modding\mmx_mod.py --game-path $game apply-localisation-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status
```

Без `--yes-i-understand` запись в игру не выполняется.  
Ожидание: `state: TEST_PATCHED`.

### 4. Запуск MMX вручную

Запустите Might & Magic X: Legacy через Ubisoft Connect.  
CLI игру не запускает.

### 5. Проверка в игре

1. Язык интерфейса — русский.
2. Главное меню: вместо «Параметры» должно быть
   `MM6X TEST — Параметры`.
3. Остальные пункты меню без префикса MM6X.

### 6. Закрыть игру

Полностью выйдите из MMX (не оставляйте её в фоне).

### 7. Restore

```powershell
python tools\modding\mmx_mod.py --game-path $game restore-localisation-test --yes-i-understand
```

### 8. Status

```powershell
python tools\modding\mmx_mod.py --game-path $game status
```

Ожидание: `state: ORIGINAL`, SHA-256 = backup.

## Откат, если CLI недоступен

Скопировать `backups\mmx\loca-ru\loca.xml` поверх:

`Might and Magic X Legacy_Data\StreamingAssets\Localisation\ru\loca.xml`

затем снова `status`. Не удаляйте каталог backup.

## Что инструмент не трогает

StaticData, Dialog, Maps, DLL, ModdingKit, сохранения.
