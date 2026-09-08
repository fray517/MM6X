# New Sorpigal — design approval (M3-010)

Статус: **APPROVED** (2026-09-08).
Владелец подтвердил freeze как есть (без альтернатив).
Игра / `Sorpigal.xml` не трогаем. Следующий шаг — **M4-001**.

Index артефактов: `references/mm6/new_sorpigal.manifest.json`.
Метод: `docs/design/MAP_CONVERSION.md`
(`landmarks → routes → quest topology → grid → MMX`).

---

## 1. Зачем этот документ

Это **ворота в M4**, не summary M3.
Владелец должен явно принять (или отклонить) freeze ниже.
Без подписи **M4-001 не стартует**.

| Решение | Если «да» | Если «нет» |
|---|---|---|
| Scope freeze §2 | → M4 greybox | правка артефактов M3, повтор review |
| Layout HYPOTHESIS §3 | клетки sketch = target | другой размер/оси/якоря |
| Quest slice §4 | #83+#81 в M4 | сузить/расширить slice |

---

## 2. Scope freeze (M4)

### Must (playable в M4)

| # | Требование | Источник |
|---|---|---|
| 1 | Новая карта **`New_Sorpigal`** (CITY/CASTLE), не правка vanilla `Sorpigal.xml` | M3-007 |
| 2 | Размер **24×18** (432 cells), WMP point **20000** | M3-007/008 |
| 3 | F0: ратуша **#89** + вход Дозора **#171** на одной map, walkable path | M3-002 |
| 4 | F1: таверна **#92** | M3-002/004 |
| 5 | NPC **Жанис #291** (accept/turn-in #83) | M3-003 |
| 6 | NPC **Андовер #1** (письмо #81) | M3-003 |
| 7 | Квест **#83**: accept → key **489** → gate → turn-in (кодекс **543**) | M3-009 |
| 8 | ≥1 Goblin spawn на east road | M3-005 |
| 9 | Stage через M2 overlay (merge loca/CSV), не replace vanilla | ADR-010 |

### Stub OK в M4 (полный контент позже)

| Stub | Когда fully |
|---|---|
| D01 geometry / NILBOG plates / chest layout | **M5** |
| auto-grant кодекса после входа в stub D01 | замена на chest в M5 |
| D02 / D18 / OutB3 shells | post-M4 |
| PeasantM2 encounter | optional |
| Магазины / храм / банк / гильдии (F3) | later |
| Travel hubs (stables #48, boats #57) | F2 shell only |

### Out of M4 (явный non-goal)

- Правка vanilla MMX Sorpigal / Sorpigal-by-the-Sea  
- ODM-accurate layout (XY MM6 ещё не декодированы)  
- Квест **#126** (канделябр)  
- Полные shop economies / цены MM6  
- World travel engine (расписание конюшен/лодок)  
- Копирование proprietary MM6 assets в git  

---

## 3. Layout (HYPOTHESIS) — принять как greybox target?

Evidence layout: **HYPOTHESIS**.  
MMX size refs: **VERIFIED_LOCAL**.  
ODM XY: **не** декодированы → метры MM6 **не** масштабируем.

| Якорь | Cell | F |
|---|---|---|
| Party start | (10,7) | — |
| Town hall #89 | (10,9) | F0 |
| Tavern #92 | (8,8) | F1 |
| Goblinwatch gate #171 | (21,9) | F0 |
| Goblin pack | (17,9) | F0 enc |
| Corridor #83 | Y=9, ~6 steps | F0 |

Оси sketch: **X+** = восток (к Дозору), **Y+** = север.

| Метрика | Target (M3-008) |
|---|---|
| PASSABLE | 55–70% (~238–302) |
| Border BLOCKED | ≥1 клетка |
| Коридор #83 | width 1–2 |
| Шаги hall→gate | 4–10 |

**Решение владельца (2026-09-08):** 24×18 и якоря sketch приняты;
альтернативы нет.

---

## 4. Quest slice

| ID | Title | M4 | M5 | Notes |
|---:|---|---|---|---|
| **83** | Дозор гоблинов | **must** | interior | primary; QBit 83; key 489; codex 543 |
| **81** | Письмо Сулмана | **must** (Андовер) | — | parallel; не блокирует #83 |
| **126** | Канделябр | **out** | — | deferred |

#81 и #83: разные NPC, нет cross-deps на critical path
(**VERIFIED_LOCAL** EVT).

**Решение владельца (2026-09-08):** #81 остаётся **must** в M4
(параллельно #83).

---

## 5. Artifact readiness (M3-001…009)

| ID | Doc | JSON | Evidence | Ready |
|---|---|---|---|---|
| 001 | `NEW_SORPIGAL_TOPOLOGY.md` | `topology.json` | VERIFIED_LOCAL | [x] |
| 002 | `NEW_SORPIGAL_LANDMARKS.md` | `landmarks.json` | VERIFIED_LOCAL | [x] |
| 003 | `NEW_SORPIGAL_NPCS.md` | `npcs.json` | VERIFIED_LOCAL | [x] |
| 004 | `NEW_SORPIGAL_SERVICES.md` | `services.json` | VERIFIED_LOCAL | [x] |
| 005 | `NEW_SORPIGAL_ENCOUNTERS.md` | `encounters.json` | VERIFIED_LOCAL + layout HYP | [x] |
| 006 | `NEW_SORPIGAL_TRAVEL.md` | `travel.json` | VERIFIED_LOCAL | [x] |
| 007 | `NEW_SORPIGAL_GRID_SKETCH.md` | `grid_sketch.json` | layout HYP | [x] |
| 008 | `NEW_SORPIGAL_CELL_BUDGET.md` | `cell_budget.json` | sizes VERIFIED | [x] |
| 009 | `NEW_SORPIGAL_QUEST_GRAPH.md` | `quest_graph.json` | VERIFIED_LOCAL | [x] |

Пути: `docs/design/…`, `references/mm6/new_sorpigal.*.json`.

---

## 6. Design decisions (принять пакетом)

1. **Separate map** `New_Sorpigal` ≠ patch vanilla Sorpigal.  
2. **Size** 24×18 / 432 cells; expand only если smoke-load / playtest требуют.  
3. **Topology > meters**: layout HYPOTHESIS допустим до decode ODM.  
4. **#83 primary**; **#81** parallel secondary (см. вопрос §4).  
5. **D01** = отдельная DUNGEON map; full content = **M5**.  
6. **IDs** полоса 20000–29999; WMP `20000`; loca `LOCATION_MM6_NEW_SORPIGAL`.  
7. **Pipeline** M2 stage/merge (ADR-009/010).  

---

## 7. Risks

### Блокеры approve (если не приняты явно)

| Risk | Почему блокер | Как снять |
|---|---|---|
| Несогласие с 24×18 | меняет M3-007/008 и M4-001 | выбрать размер, обновить sketch |
| Несогласие с east=gate | меняет якоря | новый sketch |
| #81 must vs optional | scope M4-003/005 | решить в §4 |

### Не блокеры (mitigate в M4)

| Risk | Class | Mitigation |
|---|---|---|
| CITY ≠32×32 engine quirk | HYPOTHESIS | smoke-load M4-001 |
| Loca fragment merge | HYPOTHESIS | M2 stage CLI |
| Portrait/icon reuse | HYPOTHESIS | vanilla PIC/ICO |
| #81 stable_id provisional | known | allocate при dialog |

---

## 8. Связь с BACKLOG M4

После approve стартует:

| M4 ID | Зависит от freeze |
|---|---|
| M4-001 Greybox/grid | §2 size + §3 anchors |
| M4-002 Landmarks | F0/F1 houses |
| M4-003 Andover | §4 #81 must |
| M4-004 Town Hall / Janis | #83 |
| M4-005 Localisation | loca keys §6 |
| M4-006 First quest flow | #83 graph |
| M4-007 Goblin | east road |
| M4-008 Goblinwatch entrance | gate + stub D01 |
| M4-009 Route playtest | hall→gate |
| M4-010 Save/load | smoke |

---

## 9. Approval (подпись владельца)

- [x] Scope freeze §2 принят  
- [x] Layout HYPOTHESIS §3 принят как M4 target  
- [x] Quest slice §4 принят (`#81` = **must**)  
- [x] Decisions §6 приняты пакетом  
- [x] Можно стартовать **M4-001**

**Альтернативы / условия владельца:**

```text
нет — freeze как в документе
```

**Дата / статус:** 2026-09-08 — **APPROVED**

Milestone M3 = **Done**. Следующий — M4.
