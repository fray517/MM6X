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

Refresh topology:
`python tools\extract\extract_mm6_topology.py --write-curated`.

