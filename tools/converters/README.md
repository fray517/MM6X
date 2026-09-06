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

## Dialog overlay (M2-004)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\generate_mmx_dialog.py --self-test
python tools\converters\generate_mmx_dialog.py --dry-run --check-vanilla
python tools\converters\generate_mmx_dialog.py --write --check-vanilla
```

Каталог: `tools/converters/dialog_catalog.json`.
Выход: `mod/Dialog/Mm6JanisDialog.xml`, `Mm6AndoverDialog.xml`.
Quest/token ID берутся из `id_registry.json`. Игру CLI не патчит.

## StaticData overlay (M2-005)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\generate_mmx_staticdata.py --self-test
python tools\converters\generate_mmx_staticdata.py --dry-run --check-vanilla
python tools\converters\generate_mmx_staticdata.py --write --check-vanilla
```

Каталог: `tools/converters/staticdata_catalog.json`.
Выход: `mod/StaticData/` — только строки MM6X
(Npc / QuestSteps / QuestObjectives / Token / LoreBook).
Header сверяется с vanilla. Игру CLI не патчит.

## Build manifest (M2-007)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\build_mmx_manifest.py --self-test
python tools\converters\build_mmx_manifest.py --dry-run
python tools\converters\build_mmx_manifest.py --write
python tools\converters\build_mmx_manifest.py --check
```

Выход: `mod/build_manifest.json` — path / kind / size / sha256 /
`stage_rel` (относительно Data). Игру CLI не патчит.

## Stage / restore (M2-008 / M2-009)

```powershell
python tools\modding\stage_mmx_mod.py --self-test
python tools\modding\stage_mmx_mod.py --dry-run
python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
python tools\modding\stage_mmx_mod.py --restore --yes-i-understand
```

См. `tools/modding/README.md`. ADR-010: merge, не replace.

## Regression fixtures (M2-010)

```powershell
python tools\converters\run_m2_regression.py
python tools\converters\run_m2_regression.py --update-expected
```

Fixture: `tools/converters/fixtures/m2_demo/` (offline, без игры).



