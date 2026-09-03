# Architecture — MM6X

## Общая схема
```text
MM6 source material
        ↓
MM6 audit / extraction
        ↓
NORMALIZED MODEL (JSON)
        ↓
validators + converters
        ↓
MMX MOD CONTENT
  ├─ StaticData
  ├─ Dialog
  ├─ Localisation
  └─ Maps
        ↓
MMX Runtime
        ↓ (только если нужно)
MMXLegacy
        ↓ (last resort)
custom C# patches
```

## Репозиторий
- `tools/audit/` — read-only аудит MMX/MM6.
- `tools/extract/` — read-only extract MM6 `.txt` / `.EVT` /
  сундуки `.dlv` / плиты D01 / свитки.
- `tools/converters/` — normalized MM6 → MMX.
- `tools/validators/` — проверки schema/IDs/references.
- `mod/` — только наш authored/generated payload.
- `references/` — notes, manifests, hashes; не proprietary assets.
- `patches/` — только наши patch metadata/scripts.

## Modification layers
### A. StreamingAssets
Первый выбор: StaticData, Dialog, Localisation, config/resources.

### B. Map/modding tooling
Для New Sorpigal, Goblinwatch и следующих карт. Workflow подтверждается локально.

### C. MMXLegacy
Используем только при доказанной необходимости.

### D. Custom C# patch
Только для verified blockers. Каждый patch документирует target build, assembly, backup, compatibility, test.

## Normalized MM6 model
Основные сущности:
`Region, Location, MapNode, Route, NPC, Dialogue, Quest, QuestStage, Item, Monster, Encounter, Dungeon, Secret, Trainer, Shop, TravelLink`.

## Stable IDs
Примеры:
- `mm6.region.new_sorpigal`
- `mm6.npc.new_sorpigal.andover`
- `mm6.quest.new_sorpigal.goblinwatch`
- `mm6.dungeon.goblinwatch`

Храним mapping:
`MM6X stable ID ↔ MM6 source ID ↔ MMX target ID`.

## Map conversion
`MM6 region → landmarks → routes → quest-critical topology → grid plan → MMX map`.

## Quest conversion
Сначала описываем MM6 quest независимо от MMX, затем отображаем stages на ближайшие MMX conditions/actions.

## Future build command
Цель:
`python tools/build_mod.py --game-path "..."`

Этапы: validate → allocate/check IDs → generate data/dialog/localisation → stage maps → manifest.

Сейчас: `python tools\converters\allocate_mmx_ids.py --dry-run`  
Loca overlay: `python tools\converters\generate_mmx_loca.py --dry-run`.

## Safety
Install tooling в будущем поддерживает `--dry-run`, backup и restore.
