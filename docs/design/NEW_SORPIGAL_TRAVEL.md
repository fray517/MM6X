# New Sorpigal — exits / travel (M3-006)

Evidence: **VERIFIED_LOCAL** (`OUTE3.EVT`, `D01.EVT`,
`2DEvents` stables/boats, topology). Machine:
`references/mm6/new_sorpigal.travel.json`.
Refresh: `python tools\extract\extract_mm6_travel.py --write-curated`
(нужны topology + `reports/evt_slice.json`).

Spawn XYZ — координаты MM6 на **целевой** карте, не клетки MMX.

## F0 — квест #83 (обязательно для M4/M5)

| Link | From → To | Notes |
|---|---|---|
| `exit.oute3.e101` | OutE3 #171 → `D01.blv` | ключ **489**; QBit 300 |
| `exit.d01.e51` | D01 → `OutE3.Odm` | возврат в город |

Stable: `mm6.travel_link.new_sorpigal.goblinwatch`.

## F2 — оболочка (stub OK в M4)

### Dungeon entrances
| Event | House | → |
|---:|---:|---|
| 102 | 172 | `D02.blv` Заброшенный храм |
| 103 | 188 | `D18.Blv` Кузница Гарика |

### Outdoor edge
| Event | → |
|---:|---|
| 104 | `OutB3.Odm` Драконсэнд (house_id нет) |

### Scheduled hubs (2DEvents)
| Hub | Days | Cost | Dest |
|---|---|---:|---|
| Stables #48 | M,W,F | 2 | `OutD3.Odm` Айронфист |
| Boats #57 | Tu,Th,Sa | 3 | `OutE2.Odm` Остров Тумана |

Полный world-travel engine — не M4; достаточно service shell.

## Граф

```text
OutB3 ◄──e104── OutE3 ──e101(+key)──► D01 ──e51──► OutE3
                 │  \──e102──► D02
                 │   \─e103──► D18
                 ├── stables#48 ──(M/W/F)──► OutD3
                 └── boats#57 ──(Tu/Th/Sa)──► OutE2
```

## MMX design

- F0: два перехода Town ↔ Goblinwatch (отдельные maps).
- F2: маркеры входов / edge / travel UI без реальных дальних карт.
- Не переносить MM6 spawn XYZ в grid 1:1.

## Не делать здесь

- Grid cell placement (M3-007)
- Cell budget (M3-008)
- Quest dependency graph formalization (M3-009)
