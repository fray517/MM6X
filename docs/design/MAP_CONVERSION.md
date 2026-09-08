# MM6 → MMX Map Conversion
1. Landmark inventory.
2. Route graph.
3. Quest dependency overlay.
4. Cell budget.
5. Encounter placement.
6. Secrets/puzzles.
7. Fidelity review F0–F3.

Не конвертировать координаты MM6 напрямую: topology важнее metric accuracy.

## New Sorpigal (M3-001 / M3-002)

Топология: `docs/design/NEW_SORPIGAL_TOPOLOGY.md`,
`references/mm6/new_sorpigal.topology.json`.

Quest landmarks: `docs/design/NEW_SORPIGAL_LANDMARKS.md`,
`references/mm6/new_sorpigal.landmarks.json`.

NPC list: `docs/design/NEW_SORPIGAL_NPCS.md`,
`references/mm6/new_sorpigal.npcs.json`.

Services: `docs/design/NEW_SORPIGAL_SERVICES.md`,
`references/mm6/new_sorpigal.services.json`.

Encounters: `docs/design/NEW_SORPIGAL_ENCOUNTERS.md`,
`references/mm6/new_sorpigal.encounters.json`.

Travel: `docs/design/NEW_SORPIGAL_TRAVEL.md`,
`references/mm6/new_sorpigal.travel.json`.

Grid sketch: `docs/design/NEW_SORPIGAL_GRID_SKETCH.md`,
`references/mm6/new_sorpigal.grid_sketch.json`
(24×18 CITY; layout HYPOTHESIS).

Cell budget: `docs/design/NEW_SORPIGAL_CELL_BUDGET.md`,
`references/mm6/new_sorpigal.cell_budget.json` (432 cells).

Quest graph: `docs/design/NEW_SORPIGAL_QUEST_GRAPH.md`,
`references/mm6/new_sorpigal.quest_graph.json`.

Design approval: `docs/design/NEW_SORPIGAL_DESIGN_APPROVAL.md`.

Greybox map (M4-001): `mod/Maps/New_Sorpigal.xml`,
`docs/milestones/M4_NEW_SORPIGAL.md`.
Generate: `python tools\converters\generate_mmx_map.py --write`.

Landmarks MMX (M4-002):
`references/mm6/new_sorpigal.landmarks_mmx.json`
(SIGN + START_DIALOGUE; F2 shells).

Refresh extracts:
```powershell
python tools\extract\extract_mm6_topology.py --write-curated
python tools\extract\extract_mm6_npcs.py --write-curated
python tools\extract\extract_mm6_services.py --write-curated
python tools\extract\extract_mm6_encounters.py --write-curated
python tools\extract\extract_mm6_travel.py --write-curated
```

