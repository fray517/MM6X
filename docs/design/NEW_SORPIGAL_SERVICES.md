# New Sorpigal — buildings / services (M3-004)

Evidence: **VERIFIED_LOCAL** (`2DEvents.txt`, Map=E3).
Machine: `references/mm6/new_sorpigal.services.json`.
Refresh: `python tools\extract\extract_mm6_services.py --write-curated`.

Связь: топология (M3-001), landmarks (M3-002), NPC (M3-003).
Цены/ассортимент MM6 в git не копируем — только метки A/B/C
и часы работы.

## Сводка

- **40** зданий на E3: **18** сервисов/хабов + **22** дома
- Fidelity non-residence: F0×2, F1×1, F2×6, F3×9

## Fidelity для M4

| F | Houses | Здания |
|---|---|---|
| **F0** | #89, #171 | Ратуша; вход Дозора |
| **F1** | #92 | Таверна «Одинокий рыцарь» |
| **F2** | #48, #57, #69, #79, #172, #188 | Конюшни, лодки, храм, полигон, др. входы |
| **F3** | #1, #15, #29, #42, #113, #137, #139, #141, #147 + дома | Магазины, банк, гильдии, residences |

`m4_required_houses`: **89, 171, 92**.  
`m4_stub_ok_houses`: F2 (оболочка без полного MMX shop bind).

## Каталог сервисов (не дома)

| # | category | Name | Hours | Stock A (кратко) |
|---:|---|---|---|---|
| 89 | town_hall | Ратуша | 10–14 | — (квест NPC) |
| 171 | dungeon_entrance | Дозор гоблинов | — | ключ 489 (EVT) |
| 92 | tavern | Одинокий рыцарь | 5–2 | — |
| 48 | travel_stables | Экипажи… | 5–18 | → Ironfist D3 M/W/F |
| 57 | travel_boats | Одиссей | 5–18 | → Mist E2 Tu/Th/Sa |
| 69 | temple | Храм Нью-Сорпигаль | 5–1 | No Errad |
| 79 | training | Полигон | 6–18 | Max level = 15 |
| 172 | dungeon_entrance | Заброшенный храм | — | → D02 |
| 188 | dungeon_entrance | Кузница Гарика | — | → D18 |
| 1 | shop_weapon | Магазин ножей | 6–18 | L1 Weap / L2 Dagger |
| 15 | shop_armor | Простая защита | 6–18 | L1/L2 leather… |
| 29 | shop_magic | Всевидящее око | 8–16 | L1/L2 Misc |
| 42 | shop_general | Все для дороги | 5–22 | items/bottles/herbs |
| 113 | bank | Сберегательный дом | 9–17 | — |
| 137 | guild_element | Гильдия Стихий | 6–18 | F/A/W/E spells 1–4 |
| 139 | guild_self | Гильдия Эго | 6–18 | S/M/B spells 1–4 |
| 141 | guild_merc | Острие клинка | 9–21 | Sword/Axe/… |
| 147 | guild_thieves | Притон… | 18–6 | Dagger/Merchant/… |

## MMX mapping (design)

- **Landmarks + dialog**: town_hall, tavern, dungeon_entrance F0
- **Service shell**: temple, training, shops, bank, guilds —
  позже привязка к MMX StaticData shop/skill tables
  (не блокер greybox M4)
- **Travel**: stables/boats — stub или link к M3-006
- **Residences**: кластер домов; trainers живут внутри (см. NPC F3)

## Не делать здесь

- Encounter spawn (M3-005)
- Полная travel schedule engine (M3-006)
- Cell placement (M3-007)
- Копия ITEMS/shop inventories в репозиторий
