# Audit tools

Read-only аудит установки Might & Magic X: Legacy.
Файлы игры не изменяются.

```powershell
python tools\audit\audit_mmx.py --help
python tools\audit\audit_mmx.py --game-path "D:\Games\Might & Magic X - Legacy"
```

Если в `.env` задан `MMX_GAME_PATH`, `--game-path` можно не указывать.
Шаблон: `env.example`.

Отчёты:

- `reports\mmx_audit.json`
- `reports\MMX_AUDIT.md`

SHA-256 считается только для exe и ключевых DLL, не для всех ассетов.
