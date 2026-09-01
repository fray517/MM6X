# MM6X Backlog

`[ ] Todo  [>] In progress  [x] Done  [!] Blocked`

## M0 — Prove MMX Modding Pipeline
### Audit
- [x] M0-001 Identify exact MMX installation path
- [x] M0-002 Identify distribution/build clues
- [x] M0-003 Record executable and key DLL hashes
- [x] M0-004 Inventory StreamingAssets
- [x] M0-005 Inventory Managed assemblies
- [x] M0-006 Detect ModdingKit/editor assets
- [x] M0-007 Generate local MMX audit report
### Safety
- [x] M0-010 Define backup plan
- [x] M0-011 Implement read-only manifest/hash audit
- [x] M0-012 Implement dry-run staging
- [x] M0-013 Verify clean restore
- [x] M0-014 Define dedicated test-save policy
### Localisation
- [x] M0-020 Locate active localisation
- [x] M0-021 Select safe test key
- [x] M0-022 Apply staged string change
- [x] M0-023 Verify in game
- [x] M0-024 Restore
- [x] M0-025 Document
### StaticData
- [x] M0-030 Inspect real schemas
- [x] M0-031 Select reversible value
- [x] M0-032 Apply test change
- [x] M0-033 Verify
- [x] M0-034 Restore
- [x] M0-035 Document delimiter/encoding/schema
### Dialog
- [x] M0-040 Inspect Dialog schema
- [x] M0-041 Select test dialogue
- [x] M0-042 Modify/inject one entry
- [x] M0-043 Verify
- [x] M0-044 Restore
- [x] M0-045 Document conditions/actions/IDs
### Maps
- [x] M0-050 Identify map/modding workflow
- [x] M0-051 Open existing/test map
- [x] M0-052 Make reversible map change
- [x] M0-053 Verify
- [x] M0-054 Restore
- [x] M0-055 Document workflow/formats
### MMXLegacy
- [x] M0-060 Research source/license
- [x] M0-061 Document compatibility
- [x] M0-062 Map relevant projects
- [x] M0-063 Decide whether M1 requires it
- [x] M0-064 Record ADR
### Acceptance
- [x] M0-070 Known-clean state
- [x] M0-071 Localisation reproducible
- [x] M0-072 StaticData reproducible
- [x] M0-073 Dialog reproducible
- [x] M0-074 Map modification reproducible
- [x] M0-075 Restore reproducible
- [x] M0-076 Procedure reproducible from docs

## M1 — MM6 Source Model
- [x] M1-001 Define normalized schema
- [x] M1-002 Stable IDs
- [x] M1-003 MM6 installation audit
- [x] M1-004 NPC sources
- [x] M1-005 Quest sources
- [x] M1-006 Item sources
- [x] M1-007 Monster sources
- [x] M1-008 Map/topology sources
- [>] M1-009 New Sorpigal manifest
- [>] M1-010 Goblinwatch manifest

## M2 — Conversion Framework
- [ ] M2-001 ID registry
- [ ] M2-002 MMX target ID allocator
- [ ] M2-003 Localisation generator
- [ ] M2-004 Dialog generator/patcher
- [ ] M2-005 StaticData patch generator
- [ ] M2-006 Validation CLI
- [ ] M2-007 Build manifest
- [ ] M2-008 Install/stage CLI
- [ ] M2-009 Restore CLI
- [ ] M2-010 Regression fixtures

## M3 — New Sorpigal Design
- [ ] M3-001 Original topology
- [ ] M3-002 Quest-critical landmarks
- [ ] M3-003 NPC list
- [ ] M3-004 Buildings/services
- [ ] M3-005 Encounters
- [ ] M3-006 Exits/travel
- [ ] M3-007 Grid conversion sketch
- [ ] M3-008 Cell budget
- [ ] M3-009 Quest dependency graph
- [ ] M3-010 Approve design

## M4 — New Sorpigal Prototype
- [ ] M4-001 Greybox/grid map
- [ ] M4-002 Landmarks
- [ ] M4-003 Andover
- [ ] M4-004 Town Hall quest giver
- [ ] M4-005 Localisation
- [ ] M4-006 First quest flow
- [ ] M4-007 Goblin encounter
- [ ] M4-008 Goblinwatch entrance
- [ ] M4-009 Route playtest
- [ ] M4-010 Save/load

## M5 — Goblinwatch
- [ ] M5-001 Original topology
- [ ] M5-002 MMX grid conversion
- [ ] M5-003 Greybox
- [ ] M5-004 Encounters
- [ ] M5-005 Secrets
- [ ] M5-006 NILBOG puzzle
- [ ] M5-007 Quest item
- [ ] M5-008 Return quest flow
- [ ] M5-009 Playtest
- [ ] M5-010 Vertical slice accepted
