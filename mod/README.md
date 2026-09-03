# Mod staging
Только MM6X-authored/generated files. Не хранить copied proprietary
assets и не копировать vanilla loca целиком.

Сейчас: `mod/Localisation/en/loca.xml`, `mod/Localisation/ru/loca.xml`
(15 ключей `LOCATION_MM6_*` / `NPC_NAME_MM6_*` / квест / кодекс).

```powershell
python tools\converters\generate_mmx_loca.py --write --check-vanilla
```
