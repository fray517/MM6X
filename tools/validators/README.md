# Validators
Normalized MM6 JSON: schema_version, stable id, kind, mapping.
Overlay связность: registry ↔ loca ↔ dialog ↔ StaticData.

```powershell
python tools\validators\validate_mm6_model.py
python tools\validators\validate_mm6_model.py path\to\model.json
python tools\validators\validate_id_registry.py
python tools\validators\validate_mmx_mod.py --self-test
python tools\validators\validate_mmx_mod.py
python tools\validators\validate_mmx_loca.py --check-vanilla
python tools\converters\run_m2_regression.py
```
