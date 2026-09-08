# New Sorpigal — quest dependency graph (M3-009)

Evidence: **VERIFIED_LOCAL** (`GLOBAL.EVT`, `OUTE3.EVT`, `D01`,
landmarks). Machine:
`references/mm6/new_sorpigal.quest_graph.json`.

## Квесты slice

| ID | Title | Priority | M4 | M5 |
|---:|---|---|---|---|
| **83** | Дозор гоблинов | primary | да | да (интерьер) |
| **81** | Письмо Сулмана | secondary | да (Андовер) | — |
| **126** | Канделябр Андовера | deferred | нет | нет |

#81 и #83 **параллельны**: общая карта города, разных NPC,
нет общих QBit/item на критическом пути.

## Критический путь #83

```text
Жанис ──accept e3──► QBit83 + Key489
                         │
                         ▼
              Gate #171 (consume key, QBit300)
                         │
                         ▼
              D01 ──chest[1]──► Codex543
               │                    │
               └──e51→OutE3─────────┘
                         │
                         ▼
              Жанис turn-in e4 ──► Award53 + XP/Gold
                                   (clear QBit83)
```

Узлы/рёбра — в JSON (`nodes`, `edges`, `critical_path_83`).

M4-004 MMX: accept step **20000** + key token **20001**;
turn-in FollowUp **20001** + codex **20002** (`removeTokenID`).

## M4 vs M5

| Must M4 | Stub OK M4 | Must M5 |
|---|---|---|
| accept + key | full D01 geometry | D01 grid |
| gate transition | NILBOG plates | plates + chest |
| turn-in if codex held | auto-grant codex after enter | exit e51 |

## #81 (кратко)

Андовер @ таверна #92 → letter **505**, QBit **81→82**
(`GLOBAL.EVT` e1). Не блокирует #83.
M4-003: MMX step/obj **20002**, quest token **20003**,
letter token **20004**; delivery вне slice.

## Зависимости для grid (связь с M3-007/008)

1. Hall + gate на одной CITY map, короткий PASSABLE path.  
2. D01 — отдельная DUNGEON map.  
3. Tavern в town_core (F1), не на path #83.  

Approve design — **M3-010**.
