# Converters
Normalized MM6 JSON → MMX staged data. Игру не трогает.

## ID registry (M2-001 / M2-002)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\validators\validate_id_registry.py
python tools\converters\allocate_mmx_ids.py --self-test
python tools\converters\allocate_mmx_ids.py --dry-run
python tools\converters\allocate_mmx_ids.py --write
```

Реестр: `tools/converters/id_registry.json`.
Полоса: 20000-29999. Скан vanilla обязателен перед `--write`.

## Localisation overlay (M2-003)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\generate_mmx_loca.py --self-test
python tools\converters\generate_mmx_loca.py --dry-run --check-vanilla
python tools\converters\generate_mmx_loca.py --write --check-vanilla
```

Каталог строк: `tools/converters/loca_catalog.json`.
Выход: `mod/Localisation/<lang>/loca.xml` (en, ru).
Vanilla loca не копируется. Игру CLI не патчит.
