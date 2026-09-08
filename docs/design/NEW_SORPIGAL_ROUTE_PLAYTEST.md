# New Sorpigal — route playtest (M4-009)

Offline topology: **локальная проверка BFS**.  
In-game load/quest: **нужен прогон владельца** (ниже).

## Offline (авто)

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python tools\converters\generate_mmx_map.py --self-test
python tools\converters\generate_mmx_map.py --write
python tools\converters\generate_mmx_staticdata.py --write --check-vanilla
python tools\converters\build_mmx_manifest.py --write
python tools\validators\validate_mmx_mod.py
python tools\modding\stage_mmx_mod.py --dry-run
```

Ожидание routes:

| Route | From → To | BFS |
|---|---|---|
| `route.quest83.accept_to_gate` | Town Hall → Gate | ≤20 |
| `route.tavern_to_hall` | Tavern → Town Hall | connected |

## Stage (игра)

Vanilla выход из Sorpigal → world map требует token **2**
(`TOKEN_BLESSING_CLAIRVOYANCE`) — первые миссии. Для M4
playtest: `mod/config.txt` ставит `start = "New_Sorpigal"`.

```powershell
# Если overlay уже staged — сначала restore, потом stage снова
python tools\modding\stage_mmx_mod.py --restore --yes-i-understand
python tools\converters\build_mmx_manifest.py --write
python tools\modding\stage_mmx_mod.py --dry-run
python tools\modding\stage_mmx_mod.py --stage --yes-i-understand
```

Нужна **новая игра** (старый сейв всё ещё в vanilla Sorpigal).

Rollback: `stage_mmx_mod.py --restore --yes-i-understand`.  
Сейв: слот `MM6X-M4` (см. `docs/milestones/M0_TEST_SAVE.md`).

## In-game checklist

| # | Шаг | Pass? |
|---|---|---|
| 1 | **Новая игра** → спавн в `New_Sorpigal` (config start) | |
| 2 | SIGN Town Hall / Tavern / Gate видны | |
| 3 | Janis: accept #83 → ключ token **20001** | |
| 4 | Gate без ключа → locked message | |
| 5 | Hall→gate walk (east road) + Goblin (17,9) | |
| 6 | Gate с ключом → `Goblinwatch` stub; ключ снят | |
| 7 | Chest → codex **20002** + lorebook | |
| 8 | Exit → town; Janis turn-in | |
| 9 | Andover #81 letter (parallel, не блокирует) | |

## Известные риски (HYPOTHESIS)

| Риск | Mitigation |
|---|---|
| `SceneName=Sorpigal` **32×30** + walk JSON | fixed (playtest) |
| `Goblinwatch` **6×6** + Cave1 walk | fixed (playtest feedback) |
| WMP **20000** entry | overlay `WorldMapPointsStaticData.csv` |
| Tutorial lock leave Sorpigal | token 2 / `theworld` — bypass: config `start` |

Evidence SceneName reuse (другие Name): **VERIFIED_LOCAL** (Cave3→Cave1).  
Size match при reuse: **VERIFIED_LOCAL** — у нас size mismatch, риск открыт.

## Результат

- Offline routes: заполняется автотестами.
- In-game: отметить таблицу выше; после pass → BACKLOG M4-009 `[x]`.
