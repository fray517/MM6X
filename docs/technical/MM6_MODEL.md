# Normalized MM6 model

Промежуточная JSON-модель между файлами MM6 и контентом MMX.
Не содержит proprietary binaries. Evidence в полях `evidence`.

Файл-контейнер (один регион или весь мир):

```text
Mm6Model
 ├── schema_version        сейчас 1
 └── entities[]            сущности со stable id
```

## Сущность

```text
Entity
 ├── id                    mm6.<kind>.<slug>
 ├── kind                  см. список ниже
 ├── title                 человекочитаемое имя (наше)
 ├── mm6_source
 │     ├── container       lod / файл, если известен
 │     ├── entry           имя записи в lod
 │     ├── id              числовой/внутренний id MM6
 │     └── evidence        VERIFIED_LOCAL | HYPOTHESIS
 ├── mmx_target
 │     ├── id              numeric/string MMX, пока часто null
 │     └── status          unassigned | reserved | bound
 ├── fidelity              F0 | F1 | F2 | F3
 ├── related[]             другие stable id
 └── notes
```

`kind`: `region`, `location`, `map_node`, `route`, `npc`,
`dialogue`, `quest`, `quest_stage`, `item`, `monster`,
`encounter`, `dungeon`, `secret`, `trainer`, `shop`,
`travel_link`.

Квест описываем **независимо от MMX**, затем stages → ближайшие
MMX conditions/functions (ARCHITECTURE).

Карта: landmarks → routes → quest topology → grid. Координаты
MM6 в MMX не масштабируем.

## Файлы

- Схема проверки: `tools/validators/mm6_model_schema.md`
  (правила в `validate_mm6_model.py`).
- Пример: `tools/validators/fixtures/mm6_model_example.json`.
- Манифесты slice: `references/mm6/*.manifest.json`.
- ID: `docs/technical/ID_REGISTRY.md`
  (MMX слоты: `tools/converters/id_registry.json`).

Из lod в git не копируем. Экстрактор пишет в
`references/mm6/raw/` (gitignore):
`python tools\extract\extract_mm6_text.py`.
EVT/STR: `python tools\extract\extract_mm6_evt.py`.
Плиты D01: `python tools\extract\extract_mm6_plates.py`.
Свитки: `python tools\extract\extract_mm6_scrolls.py`.
