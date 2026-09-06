# Modding tools

M0 proofs: `mmx_mod.py` (loca / Potions / Johara / Sorpigal map).

M2 overlay stage/restore:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\modding\stage_mmx_mod.py --self-test
python tools\modding\stage_mmx_mod.py --dry-run
python tools\modding\stage_mmx_mod.py --status
# python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
# python tools\modding\stage_mmx_mod.py --restore --yes-i-understand
```

Merge (не replace): loca keys, CSV rows by StaticID.
Dialog: copy новых XML. Backup: `backups/mmx/mm6x-overlay/`.
