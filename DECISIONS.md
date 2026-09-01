# Architecture Decision Records

## ADR-001 — MMX runtime foundation
Accepted. Unreal Engine из проекта исключён.

## ADR-002 — MM6 content source of truth
Accepted.

## ADR-003 — MMX grid/combat model
Accepted. Не восстанавливаем MM6 free movement/real-time combat.

## ADR-004 — Topology over exact distance
Accepted.

## ADR-005 — Least-invasive modification
Accepted: data → map tooling → MMXLegacy → custom C# patch.

## ADR-006 — Normalized intermediate MM6 model
Accepted.

## ADR-007 — No proprietary assets in repository
Accepted.

## ADR-008 — MMXLegacy hard dependency
Rejected as hard dependency.

M1 (MM6 source model) MMXLegacy не требует.

Контент на Ubisoft-сборке грузится из StreamingAssets без замены
Managed: loca, CSV, Dialog XML, Maps XML доказаны in-game (M0).

MMXLegacy (https://github.com/Albeoris/MMXLegacy, MIT, last push
2017-12-23) — rewritten engine, ставится копированием DLL в
`Managed`. Не закрывает дыру ModdingKit (`Legacy.Editor*.dll`).
Steam/Ubisoft DLL невзаимозаменяемы. Исходники движка в MM6X не
вендорить.

К слою C возвращаемся только при verified blocker vanilla data.
До тех пор: data/XML overlay, как ADR-005.

Исследование: `docs/research/MMXLEGACY.md`.
