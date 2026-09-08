# New Sorpigal — encounters (M3-005)

Evidence: **VERIFIED_LOCAL** (`MapStats.txt` #15/#16,
`MONSTERS.TXT` tiers). Machine:
`references/mm6/new_sorpigal.encounters.json`.
Refresh: `python tools\extract\extract_mm6_encounters.py --write-curated`.

Точные координаты спавна на `OutE3.Odm` **не** декодированы —
placement на MMX grid = **HYPOTHESIS** (маршрут ратуша → вход #171).

## Outdoor — MapStats #15 `OutE3.Odm`

| Field | Value |
|---|---|
| Encounter chance | **10%** |
| Refill days | 168 |
| Trap / Tres | 1 / 6 |
| Lock | 0 |

| Slot | Pic stem | Name | % | Dif | Count | Tiers (MONSTERS) |
|---:|---|---|---:|---:|---|---|
| M1 | Goblin | Гоблин | 50 | 1 | 3–5 | #76–78 A/B/C |
| M2 | PeasantM2 | Ученик мага | 50 | 1 | 3–5 | #136–138 A/B/C |
| M3 | — | — | 0 | — | — | — |

Tier names (не спрайты в git): Гоблин / шаман / король;
Ученик мага / Начинающий маг / Маг.

## Quest dungeon — MapStats #16 `D01.Blv` (M5)

Enc% 10; M1 Rat 40%, M2 Goblin 30%, M3 Bloodsucker 30%;
Dif 2/2/1; refill 672. Для greybox M4 **не** обязателен.

## Design для M4 (F1) — M4-007 Done

1. Outdoor **Goblin** pack: cell (17,9), Trigger 60,
   MMX `SpawnStaticID=50` (`MONSTER_GOBLIN`). **VERIFIED_LOCAL**.
2. Опционально **PeasantM2** — не в M4-007.
3. Bind: map Trigger / `SpawnObjectType=MONSTER`.
4. Полный D01 encounter set — **M5**.

Не копировать `MONSTERS.TXT` целиком и не класть sprite LOD.

## Не делать здесь

- ODM/DDM spawn XY decode
- MMX MonsterStaticData IDs (allocator позже)
- Exits/travel schedules (M3-006)
