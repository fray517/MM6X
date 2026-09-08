# New Sorpigal — localisation inventory (M4-005)

Evidence: generated overlay `mod/Localisation/en|ru/loca.xml`.
Catalog: `tools/converters/loca_catalog.json`.
Validator: `tools/validators/validate_mmx_loca.py`.

## Smoke (offline)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\validators\validate_mmx_loca.py --check-vanilla --list
python tools\validators\validate_mmx_mod.py
```

Ожидание: **55** ключей, en == ru, нет коллизий с vanilla,
dialog/map/StaticData refs закрыты.

## Группы ключей

| Prefix | Count (approx) | Назначение |
|---|---:|---|
| `LOCATION_*` / `WORLDMAP_*` | 4 | карта / WMP / ратуша / Дозор |
| `NPC_NAME_*` | 2 | Жанис, Андовер |
| `TOKEN_*` / `QUEST_*` | ~14 | #83 + #81 |
| `LOREBOOK_*` | 3 | кодекс (легенда плит) |
| `DIALOG_*` | ~20 | Mm6Janis + Mm6Andover |
| `SIGN_*` / `OBJECT_INTERACTION_*` | 8 | landmarks + gate locked |

Точный список: `validate_mmx_loca.py --list`.

## Правила

- Только MM6X-authored строки (не dump vanilla / Scroll.txt).
- en и ru обязательны для каждого ключа.
- Stage = **merge** keys (ADR-010), не replace loca.xml.
- F2 signs: «sealed» / имя места — без слова «stub» в UI.

## In-game (позже)

После stage: язык en и ru, ратуша/таверна SIGN + dialog.
Полный playtest — M4-009 (`docs/design/NEW_SORPIGAL_ROUTE_PLAYTEST.md`).
