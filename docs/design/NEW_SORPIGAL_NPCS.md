# New Sorpigal — NPC list (M3-003)

Evidence: **VERIFIED_LOCAL** (`NPCdata.txt` + `npcprof.txt` +
topology E3 houses). Machine:
`references/mm6/new_sorpigal.npcs.json`.
Refresh: `python tools\extract\extract_mm6_npcs.py --write-curated`.

## Два слоя

1. **Dialogue NPCs** — строки `NPCdata`, колонка `2D Location`
   ∈ домов E3. **27** шт.
2. **Service agents** — имена из `2DEvents` Proprietor
   (UI магазина/храма/…). **15** шт. Обычно **нет** в NPCdata
   (исключение: Жанис #291 = и клерк, и proprietor ратуши).
   Дирк (трактирщик) — только 2D; Андовер/Мария — NPCs в #92.

Портреты `NPC###` в lod не копировать в git.

## Fidelity (M4)

| F | NPC | House | Зачем |
|---|---|---|---|
| **F0** | #291 Жанис (Клерк) | #89 Ратуша | квест #83 |
| **F1** | #1 Андовер Портбелло | #92 Таверна | письмо #81 / M4-003 |
| **F2** | #2 Мария | #92 | сосед по таверне |
| **F2** | #3 Франк Фейрчальд | #89 | другие квесты ратуши |
| **F3** | остальные 23 | дома 465–487 | учителя / учителя |

`m4_required` в JSON: **291, 1**.

## F0 / F1 подробно

### Жанис #291
- Profession 72 «Клерк», pic из NPCdata
- Event A=**3** (accept #83), C=399
- Stable: `mm6.npc.new_sorpigal.janis` → MMX NPC 20000

### Андовер #1
- Profession 74 «Последователь Баа»
- 2D Location **92** (таверна, не отдельный дом)
- Event A=**1** (письмо), B=**296** (канделябр #126)
- Stable: `mm6.npc.new_sorpigal.andover` → MMX NPC 20001

## Service agents (F3 для M4, нужны позже)

Кейн, Гарри, Вильма, Рино, Арон, Брайан, Джошуа, Натан,
Дирк, Шмиди, Джероми, Телиана, Далимар, Отшельник (+ Жанис).
В MMX: либо hireling/shop UI без диалог-NPC, либо отдельные
stub NPC — решение в M3-004.

## F3 дома (сводка)

Много «Учитель» (prof 13) в House P/M/R — skill trainers.
Плюс адвокат, горшечник, мистик, знахарь, учёный и т.д.
Полный список — в `new_sorpigal.npcs.json`.

## Не делать здесь

- Полные тексты/topics (уже в M1 slice для #83)
- Shop price tables (M3-004)
- Spawn placement на grid (M3-007 / M4)
