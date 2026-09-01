# Audit tools

Read-only аудит установок MMX и MM6. Файлы игр не изменяются.

```powershell
python tools\audit\audit_mmx.py --help
python tools\audit\audit_mmx.py --game-path "D:\Games\Might & Magic X - Legacy"
python tools\audit\audit_mm6.py --help
python tools\audit\audit_mm6.py --game-path "D:\Games\Might and Magic 6"
```

Если в `.env` задан `MMX_GAME_PATH` / `MM6_GAME_PATH`, `--game-path`
можно не указывать. Шаблон: `env.example`.

Отчёты (gitignore):

- `reports\mmx_audit.json`, `reports\MMX_AUDIT.md`
- `reports\mm6_audit.json`, `reports\MM6_AUDIT.md`

SHA-256 только для exe (и ключевых DLL MMX), не для всех ассетов.
