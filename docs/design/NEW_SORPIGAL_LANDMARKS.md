# New Sorpigal — quest-critical landmarks (M3-002)

Evidence: **VERIFIED_LOCAL** (2DEvents E3, `OUTE3.EVT`,
`GLOBAL.EVT`, `D01` chests). Machine:
`references/mm6/new_sorpigal.landmarks.json`.
Topology base: `docs/design/NEW_SORPIGAL_TOPOLOGY.md`.

Цель: какие узлы **обязаны** попасть на MMX grid до greybox,
а какие можно отложить.

## Fidelity для M4

| F | Смысл | Landmarks |
|---|---|---|
| **F0** | Без них квест #83 не узнаваем | Ратуша #89, вход Дозора #171 (+ интерьер D01 в M5) |
| **F1** | Смежный slice / якорь города | Таверна #92 (Андовер / письмо #81) |
| **F2** | Сохранить как оболочку | Входы #172/#188, конюшни #48, лодки #57 |
| **F3** | Атмосфера после playable route | Магазины / гильдии / храм / банк / дома |

## F0 — квест #83 «Дозор гоблинов»

### 1. Ратуша `#89` → `lm.town_hall`
- NPC **Жанис** #291 (`mm6.npc.new_sorpigal.janis`)
- Accept `GLOBAL.EVT` e3: QBit **83**, item **489** (ключ)
- Turn-in e4: item **543** (кодекс), Award 53, Exp/Gold 2000
- Outdoor: `OUTE3.EVT` SpeakInHouse e28

### 2. Вход Дозора `#171` → `lm.goblinwatch_entrance`
- `OUTE3.EVT` e101 → `D01.blv`
- Нужен ключ **489** (Compare + Subtract)
- Без ключа: StatusText «Дверь заперта.»
- Первый вход: Set QBit **300**
- `mm6.travel_link.new_sorpigal.goblinwatch`

### 3. Интерьер D01 → `lm.goblinwatch_interior` (M5)
- Codex в `d01.dlv` **chest[1]** = item 543
- Плиты NILBOG: `D01.EVT` e19–34
- Выход e51 → `OutE3.Odm`
- Для M4 допустим stub «entered / got codex»; полный данж — M5

## Маршрут #83 (логический)

```text
Ратуша #89 ──accept(+ключ)──► Вход #171 ──ключ──► D01
                                                    │
                                              chest[1] кодекс
                                              плиты (M5)
                                                    │
Ратуша #89 ◄──turnin(кодекс)── OutE3 ◄──e51─────────┘
```

**MMX implication:** ратуша и вход Дозора — на коротком
пешеходном маршруте одной outdoor/town map. Интерьер —
отдельная map (как MM6).

## F1 — таверна `#92` (не #83)

- «Одинокий рыцарь», трактирщик Дирк
- 2D Location Андовера (#1) = **92**
- Письмо Сулмана: `GLOBAL.EVT` e1, item 505, QBit 81→82
- Нужна на карте для M4-003; **не** на критическом пути #83

## F2 / F3 (кратко)

- #172 / #188 — другие Dungeon Ent на E3 (оболочка)
- #48 / #57 — travel hubs (stub OK)
- Остальные service/residence — после playable F0+F1

## Не делать в M3-002

- NPC roster (M3-003)
- Полный каталог услуг (M3-004)
- Grid cell placement (M3-007)
- Decode ODM XY
