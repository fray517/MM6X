# M0 — текущий контекст

Дата: 2026-09-01. Сборка: Ubisoft Connect, не Steam.

Игра: `C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\games\Might & Magic X Legacy`

## M0 закрыт

| Proof | Что меняли | In-game | Restore |
|---|---|---|---|
| Localisation | `ru/loca.xml` ключ `Gui/Mainmenu/Options` | `MM6X TEST — Параметры` | `ORIGINAL` `de5a7668…e60d064` |
| StaticData | `Potions.csv` StaticID=1 Price 45→9999 | Johara, цена 9999 | `ORIGINAL` `f919fa74…c88372` |
| Dialog | `JoharaDialog.xml` id=1 locaKey JOHARA_1→5 | знаток магии / Люс | `ORIGINAL` `23bbb1a3…720dab` |
| Map | `Sorpigal.xml` Slot 29,19 Terrain → BLOCKED | вторая клетка — стена | `ORIGINAL` `f24b25f4…00d4bc` |

Acceptance: `M0_ACCEPTANCE.md`. ADR-008: MMXLegacy **не** hard dependency.

## Сейчас

**M1 — MM6 Source Model** (схема, stable IDs, аудит установки MM6).

New Sorpigal — с M3. DLL не патчить.

## Инварианты

- Не патчить DLL, не трогать ModdingKit, не класть proprietary assets в git.
- Backup в `backups/mmx/` (gitignore), не в каталог игры.
- Apply/restore только с `--yes-i-understand`.
- `--game-path` до subcommand, флаг записи — после.
