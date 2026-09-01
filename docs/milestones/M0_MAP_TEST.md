# M0 — Map proof

Только `StreamingAssets/Maps/Sorpigal.xml`.  
Loca / StaticData / Dialog уже доказаны; этот шаг проверяет Grid XML.

In-game 2026-09-01: новая игра, второй шаг на запад — стена.
Restore: `ORIGINAL`.

Правка через XML, не через Unity: на этой сборке нет
`Legacy.Editor.dll`.

## Выбранное значение

| | |
|---|---|
| Файл | `Sorpigal.xml` |
| Клетка | `X=29 Y=19` (Height `-6.87566376`, уникален) |
| Поле | `Slot@Terrain` |
| Original | `PASSABLE NO_PARTY_BARK` |
| Test | `BLOCKED` |
| Где видно | Новая игра, спавн 31,19 лицом на запад; второй шаг вперёд |

Почему безопасно: не квест, не NPC, не вход на другую карту.
Клетка пустая (нет Trigger). Спавн 31,19 и первая клетка 30,19
остаются проходимыми — можно шагнуть назад. Старый сейв в городе
эту стену не покажет.

Патч — одна уникальная строка `Slot`, XML не переформатируется.

## Команды

```powershell
$game = "C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\Might & Magic X Legacy"
```

### 1. Prepare

```powershell
python tools\modding\mmx_mod.py --game-path $game prepare-map-test
```

### 2. Backup

```powershell
python tools\modding\mmx_mod.py --game-path $game backup-map
python tools\modding\mmx_mod.py --game-path $game status-map
```

### 3. Apply

```powershell
python tools\modding\mmx_mod.py --game-path $game apply-map-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status-map
```

Ожидание: `state: TEST_PATCHED`, terrain `BLOCKED`.

### 4. Игра вручную

**Новая игра** (сейв из середины города не подойдёт).  
Слот `MM6X-M0` см. `M0_TEST_SAVE.md`.

Спавн: коридор на запад. Первый шаг свободен, **второй**
должен упереться в стену.

### 5. Закрыть игру

### 6. Restore

```powershell
python tools\modding\mmx_mod.py --game-path $game restore-map-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status-map
```

Ожидание: `state: ORIGINAL`.

Program Files может потребовать PowerShell от администратора.
