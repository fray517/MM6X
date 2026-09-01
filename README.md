# MM6X — Might & Magic VI on Might & Magic X

## Цель
Total conversion: **сюжет и контент Might & Magic VI на технической базе Might & Magic X: Legacy**.

### Источник истины
- MM6: сюжет, квесты, NPC, Enroth, подземелья, секреты, важные предметы.
- MMX: Unity-runtime, grid movement, бой, UI, inventory/dialog/save framework.

### Главное правило
Географию сохраняем **топологически**, но расстояния адаптируем под клеточное движение MMX.

## Первый milestone
Сначала доказываем modding pipeline:
1. Read-only аудит установленной MMX.
2. Backup/restore.
3. Одна правка Localisation.
4. Одна правка StaticData.
5. Одна правка Dialog.
6. Одна тестовая правка карты.
7. Только после этого — New Sorpigal.

Начни с `START_HERE.md`.
