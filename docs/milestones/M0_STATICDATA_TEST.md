# M0 — StaticData proof

Только `StreamingAssets/StaticData/Potions.csv`.  
Локализация уже доказана; этот шаг проверяет CSV.

In-game 2026-09-01: Johara, цена 9999. Restore: `ORIGINAL`.

## Выбранное значение

| | |
|---|---|
| Файл | `Potions.csv` |
| Строка | `StaticID=1` `POTION_HEALTH_MINOR` |
| Поле | `Price` |
| Original | `45` |
| Test | `9999` |
| Где видно | Sorpigal → Johara, minor health potion |

Почему безопасно: не квест, не ID, не бой. Johara продаёт
`POTION,1` (`ItemOffers` id 20). Старт vanilla — Sorpigal.

Патч — одна уникальная подстрока, CSV не переформатируется.

## Команды

```powershell
$game = "C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\Might & Magic X Legacy"
```

### 1. Prepare

```powershell
python tools\modding\mmx_mod.py --game-path $game prepare-staticdata-test
```

### 2. Backup

```powershell
python tools\modding\mmx_mod.py --game-path $game backup-staticdata
python tools\modding\mmx_mod.py --game-path $game status-staticdata
```

### 3. Apply

```powershell
python tools\modding\mmx_mod.py --game-path $game apply-staticdata-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status-staticdata
```

Ожидание: `state: TEST_PATCHED`, цена `9999`.

### 4. Игра вручную

Новая игра или слот `MM6X-M0` (см. `M0_TEST_SAVE.md`).  
Sorpigal → торговец Johara → зелье здоровья 1-го ранга.

Ожидание: цена **9999** вместо **45**.

### 5. Закрыть игру

### 6. Restore

```powershell
python tools\modding\mmx_mod.py --game-path $game restore-staticdata-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status-staticdata
```

Ожидание: `state: ORIGINAL`.

Program Files может потребовать PowerShell от администратора.
