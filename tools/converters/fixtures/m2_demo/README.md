# M2 demo fixture

Offline regression slice (не production Goblinwatch).

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\run_m2_regression.py
# после намеренного изменения каталогов:
# python tools\converters\run_m2_regression.py --update-expected
```

Содержит: registry + catalogs → `expected/` golden overlay,
`vanilla_stub/` для merge/restore без реальной игры.
