# M0 — Acceptance

Дата закрытия proof-слоёв: 2026-09-01. Сборка Ubisoft Connect.

Все четыре процедуры прогнаны по своим докам, с in-game verify
и restore. Повторный in-game цикл для M0-076 не требуется:
команды и ожидания зафиксированы.

| Слой | Документ | In-game | Restore SHA-256 (prefix) |
|---|---|---|---|
| Localisation | `M0_LOCALISATION_TEST.md` | `MM6X TEST — Параметры` | `de5a7668…e60d064` |
| StaticData | `M0_STATICDATA_TEST.md` | Johara, цена 9999 | `f919fa74…c88372` |
| Dialog | `M0_DIALOG_TEST.md` | знаток магии / Люс | `23bbb1a3…720dab` |
| Map | `M0_MAP_TEST.md` | вторая клетка — стена | `f24b25f4…00d4bc` |

Clean state: `status` / `status-staticdata` / `status-dialog` /
`status-map` → `ORIGINAL` (проверено после map restore).

CLI: `tools/modding/mmx_mod.py`.  
`--game-path` до subcommand, `--yes-i-understand` после.  
Backup в `backups/mmx/` (gitignore).

Карты: правка `Maps/*.xml`, не Unity editor (kit неполон).

MMXLegacy не нужен для повторения M0 и для старта M1.
См. ADR-008, `docs/research/MMXLEGACY.md`.
