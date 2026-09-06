# Mod staging
Только MM6X-authored/generated files. Не хранить copied proprietary
assets и не копировать vanilla loca целиком.

Сейчас:

- `mod/Localisation/en|ru/loca.xml` — 31 ключ MM6X
- `mod/Dialog/Mm6JanisDialog.xml` — квест Дозора (accept/turn-in)
- `mod/Dialog/Mm6AndoverDialog.xml` — заглушка письма Сулмана

```powershell
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\converters\generate_mmx_dialog.py --write --check-vanilla
```

В игру не ставится, пока нет M2-008 stage CLI.
