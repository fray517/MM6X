# START HERE

## Первый шаг
Нужна установленная Might & Magic X: Legacy. Сначала Cursor ничего в ней не меняет.

## Первый промпт для Cursor
```text
Read:
- PROJECT_CHARTER.md
- CLAUDE.md
- ARCHITECTURE.md
- BACKLOG.md
- docs/milestones/M0_MODDING_PIPELINE.md

We are starting MM6X: Might & Magic VI content on the Might & Magic X: Legacy technical foundation.

Implement ONLY M0-001 through M0-007 and M0-011: a read-only installation audit.

Requirements:
1. Do not modify any MMX files.
2. Create a Python 3.11+ CLI under tools/audit/.
3. Accept --game-path.
4. Never hardcode my username, Steam path or drive.
5. Detect/report:
   - executable candidates
   - `Might and Magic X Legacy_Data`
   - StreamingAssets structure
   - StaticData files
   - Dialog files
   - Localisation folders/files
   - Managed DLLs
   - Legacy.Core.dll / Legacy.Framework.dll / Legacy.Game.dll
   - likely ModdingKit files if present
6. SHA-256 important executables/DLLs, not every asset.
7. Produce JSON and Markdown reports.
8. Add --help.
9. Use standard library unless insufficient.
10. Before coding list exact files.
11. After coding give exact Windows command to run.
12. Update BACKLOG.md only for completed work.

Do not start MM6 extraction, New Sorpigal, dialogue editing, DLL patching or map creation.
```

Ожидаемый запуск:
`python tools\audit\audit_mmx.py --game-path "D:\Games\Might & Magic X - Legacy"`

Первый успех: получены `reports/mmx_audit.json` и `reports/MMX_AUDIT.md` без изменения игры.
