# M0 — текущий контекст

Дата: 2026-09-01. Сборка: Ubisoft Connect, не Steam.

Игра: `C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\Might & Magic X Legacy`

## Закрыто

| Proof | Что меняли | In-game | Restore |
|---|---|---|---|
| Localisation | `ru/loca.xml` ключ `Gui/Mainmenu/Options` | `MM6X TEST — Параметры` | `ORIGINAL` `de5a7668…e60d064` |
| StaticData | `Potions.csv` StaticID=1 Price 45→9999 | Johara, цена 9999 | `ORIGINAL` `f919fa74…c88372` |
| Dialog | `JoharaDialog.xml` id=1 locaKey JOHARA_1→5 | знаток магии / Люс | `ORIGINAL` `23bbb1a3…720dab` |

Процедуры: `M0_LOCALISATION_TEST.md`, `M0_STATICDATA_TEST.md`,
`M0_DIALOG_TEST.md`.  
CLI: `tools/modding/mmx_mod.py`. Сейвы: `M0_TEST_SAVE.md`.

## Сейчас

**Map proof (M0-051…055).** XML `Grid` в `StreamingAssets/Maps`, не Unity editor (ModdingKit неполон).

Ещё не начат. New Sorpigal не начинать до закрытия M0.

## Инварианты

- Не патчить DLL, не трогать ModdingKit, не класть proprietary assets в git.
- Backup в `backups/mmx/` (gitignore), не в каталог игры.
- Apply/restore только с `--yes-i-understand`.
- `--game-path` до subcommand, флаг записи — после.
