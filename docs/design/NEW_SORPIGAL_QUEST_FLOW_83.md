# New Sorpigal — quest #83 first flow (M4-006)

Evidence dialog/StaticData: **VERIFIED_LOCAL** (M4-004).
Stub dungeon: **Cave1-matched 6×6** (size+walk VERIFIED_LOCAL);
auto-codex via `ADD_TOKEN` / `ADD_LOREBOOK`.

Machine checklist:
`references/mm6/new_sorpigal.quest_flow_83.json`.

## Player path (M4)

```text
Janis accept → key token 20001
      │
      ▼
East road → gate (28,17) key 20001 → consume
      │
      ▼
Goblinwatch stub 6×6 (Cave1 walk)
  chest (4,4): ADD_TOKEN 20002 + ADD_LOREBOOK 20000
  exit (0,1) → New_Sorpigal party spawn
      │
      ▼
Objective/FollowUp → turn-in step 20001
      │
      ▼
Janis turn-in → SolveQuest + removeTokenID codex
```

## Maps

| File | Role |
|---|---|
| `mod/Maps/New_Sorpigal.xml` | Town; gate Trigger 20 → `Goblinwatch.xml` |
| `mod/Maps/Goblinwatch.xml` | Stub D01; codex grant; return |

Generate:

```powershell
python tools\converters\generate_mmx_map.py --write
python tools\converters\generate_mmx_loca.py --write --check-vanilla
python tools\validators\validate_mmx_mod.py
```

## Stub vs M5

| M4 stub | M5 |
|---|---|
| 6×6 Cave1 footprint | full D01 grid + own scene |
| Click chest → codex | NILBOG plates + chest[1] |
| Key PARTY_CHECK + REMOVE_TOKEN | Compare/Subtract #489 |
| Goblin road optional | full encounters |

## Parallel #81

Andover letter не блокирует #83 (M4-003).
