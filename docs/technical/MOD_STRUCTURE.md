# Proposed Mod Staging

Vanilla sample export (`ModdingKit/MMXL_Mod_Export/MMXL Sample Mod`)
выглядит так. Evidence: VERIFIED_LOCAL.

```text
mod/
├── modinfo.xml
├── config.txt
├── Asset/                 # .pak + minimap, не хранить в git
├── Map/
├── Localisation/<lang>/loca.xml
└── Staticdata/            # CSV overlay
```

Диалоги в sample export **нет**. Их, скорее всего, стейджим отдельно:

```text
mod/StreamingAssets/
├── StaticData/
├── Dialog/
└── Localisation/ru/
```

Как игра монтирует мод-папку — ещё не подтверждено (M0 stage/install).
Схема полей: `docs/technical/MMX_DATA_SCHEMA.md`.
