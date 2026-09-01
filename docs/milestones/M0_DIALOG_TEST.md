# M0 — Dialog proof

Только `StreamingAssets/Dialog/JoharaDialog.xml`.  
Loca и StaticData уже доказаны; этот шаг проверяет XML диалога.

In-game 2026-09-01: Johara, реплика про знатока магии и Люс.
Restore: `ORIGINAL`.

## Выбранный диалог

| | |
|---|---|
| Файл | `JoharaDialog.xml` |
| NPC | StaticID=2, `ConversationKey=JoharaDialog` |
| Узел | `dialog id=1` greeting `text@locaKey` |
| Original | `DIALOG_TEXT_JOHARA_1` |
| Test | `DIALOG_TEXT_JOHARA_5` |
| Где видно | Sorpigal → поговорить с Johara, первая реплика |

Почему безопасно: не квест, не function/condition, не новые id.  
Ключ `DIALOG_TEXT_JOHARA_5` уже есть в том же файле (dialog 4, тренировка).  
Loca не меняем: игра подставит существующую строку.

Ожидание в игре: вместо приветствия — фраза, что партия теперь
«знаток Усиления магии». Варианты Trade / Identify / Gossip без изменений.

Патч — одна уникальная подстрока вокруг `dialog id=1`, XML не
переформатируется.

## Команды

```powershell
$game = "C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\Might & Magic X Legacy"
```

### 1. Prepare

```powershell
python tools\modding\mmx_mod.py --game-path $game prepare-dialog-test
```

### 2. Backup

```powershell
python tools\modding\mmx_mod.py --game-path $game backup-dialog
python tools\modding\mmx_mod.py --game-path $game status-dialog
```

### 3. Apply

```powershell
python tools\modding\mmx_mod.py --game-path $game apply-dialog-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status-dialog
```

Ожидание: `state: TEST_PATCHED`, locaKey `DIALOG_TEXT_JOHARA_5`.

### 4. Игра вручную

Новая игра или слот `MM6X-M0` (см. `M0_TEST_SAVE.md`).  
Sorpigal → Johara → открыть диалог.

Ожидание: первая реплика про «знаток Усиления магии», не приветствие.

### 5. Закрыть игру

### 6. Restore

```powershell
python tools\modding\mmx_mod.py --game-path $game restore-dialog-test --yes-i-understand
python tools\modding\mmx_mod.py --game-path $game status-dialog
```

Ожидание: `state: ORIGINAL`.

Program Files может потребовать PowerShell от администратора.
