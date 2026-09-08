"""Build MMX Grid XML for New_Sorpigal greybox (M4-001).

Layout from references/mm6/new_sorpigal.grid_sketch.json.
Does not touch the game install. Evidence layout: HYPOTHESIS.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Transition order matches Cave1/Sorpigal samples (HYPOTHESIS: N,E,S,W).
_NEIGHBOR_DELTAS = (
    (0, 1),   # N
    (1, 0),   # E
    (0, -1),  # S
    (-1, 0),  # W
)

DEFAULT_SKETCH = (
    Path(__file__).resolve().parents[2]
    / "references"
    / "mm6"
    / "new_sorpigal.grid_sketch.json"
)


class MapGenError(ValueError):
    """Invalid sketch or map build input."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bbox_cells(bbox: dict[str, Any]) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for x in range(int(bbox["x0"]), int(bbox["x1"]) + 1):
        for y in range(int(bbox["y0"]), int(bbox["y1"]) + 1):
            cells.add((x, y))
    return cells


def passable_set(sketch: dict[str, Any]) -> set[tuple[int, int]]:
    """Union of sketch zones + routes + F0/F1 anchors + party."""
    cells: set[tuple[int, int]] = set()
    for zone in sketch.get("zones") or []:
        cells |= _bbox_cells(zone["bbox"])
    for route in sketch.get("routes") or []:
        for pair in route.get("via_cells") or []:
            cells.add((int(pair[0]), int(pair[1])))
    start = sketch.get("party_start") or {}
    cell = start.get("cell") or {}
    if "x" in cell and "y" in cell:
        cells.add((int(cell["x"]), int(cell["y"])))
    for anchor in sketch.get("anchors") or []:
        c = anchor["cell"]
        cells.add((int(c["x"]), int(c["y"])))
    return cells


def is_border(x: int, y: int, width: int, height: int) -> bool:
    return x == 0 or y == 0 or x == width - 1 or y == height - 1


def terrain_at(
    x: int,
    y: int,
    width: int,
    height: int,
    walk: set[tuple[int, int]],
) -> str:
    if is_border(x, y, width, height):
        return "BLOCKED"
    if (x, y) in walk:
        return "PASSABLE"
    return "BLOCKED"


def transition_types(
    x: int,
    y: int,
    width: int,
    height: int,
    walk: set[tuple[int, int]],
) -> list[str]:
    here = terrain_at(x, y, width, height, walk)
    if here != "PASSABLE":
        return ["OPEN", "OPEN", "OPEN", "OPEN"]
    out: list[str] = []
    for dx, dy in _NEIGHBOR_DELTAS:
        nx, ny = x + dx, y + dy
        if nx < 0 or ny < 0 or nx >= width or ny >= height:
            out.append("CLOSED")
            continue
        if terrain_at(nx, ny, width, height, walk) == "PASSABLE":
            out.append("OPEN")
        else:
            out.append("CLOSED")
    return out


def _indent(level: int) -> str:
    return "  " * level


def _trigger_party(tid: int, x: int, y: int, direction: str) -> str:
    pad = _indent(4)
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        f"{pad}  <SpawnObjectType>PARTY</SpawnObjectType>",
        f"{pad}  <SpawnDirection>{direction}</SpawnDirection>",
        f"{pad}  <SpawnStaticID>0</SpawnStaticID>",
        f"{pad}  <SpawnTime>EVERYTIME</SpawnTime>",
        f"{pad}  <Enabled>true</Enabled>",
        f"{pad}  <OpenableByMonsters>false</OpenableByMonsters>",
        f"{pad}  <ChallengeID>0</ChallengeID>",
        f"{pad}  <InitialState>NONE</InitialState>",
        f"{pad}  <Position>",
        f"{pad}    <X>{x}</X>",
        f"{pad}    <Y>{y}</Y>",
        f"{pad}  </Position>",
        f"{pad}  <OffsetPosition>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </OffsetPosition>",
        f"{pad}  <ObjectRotation>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </ObjectRotation>",
        f"{pad}</Trigger>",
    ]
    return "\n".join(lines)


def _trigger_npc(
    tid: int,
    x: int,
    y: int,
    npc_static_id: int,
    direction: str = "SOUTH",
) -> str:
    """NPC_CONTAINER + START_DIALOGUE (ConversationKey via StaticData)."""
    pad = _indent(4)
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        (
            f'{pad}  <Command Type="SET_DATA" '
            f'TargetSpawnID="{tid}" '
            f'Extra="NPC_IDS,{npc_static_id}" '
            f'Precondition="NONE" Timing="ON_SPAWN" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        (
            f'{pad}  <Command Type="START_DIALOGUE" '
            f'TargetSpawnID="{tid}" Extra="" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        (
            f'{pad}  <Command Type="SET_DATA" '
            f'TargetSpawnID="{tid}" '
            f'Extra="PREFAB,Prefabs/InteractiveObjects/NPC/'
            f'Generic_Guard" '
            f'Precondition="NONE" Timing="ON_SPAWN" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        f"{pad}  <SpawnObjectType>NPC_CONTAINER</SpawnObjectType>",
        f"{pad}  <SpawnDirection>{direction}</SpawnDirection>",
        f"{pad}  <SpawnStaticID>10</SpawnStaticID>",
        f"{pad}  <SpawnTime>EVERYTIME</SpawnTime>",
        f"{pad}  <Enabled>true</Enabled>",
        f"{pad}  <OpenableByMonsters>false</OpenableByMonsters>",
        f"{pad}  <ChallengeID>0</ChallengeID>",
        f"{pad}  <InitialState>NONE</InitialState>",
        f"{pad}  <Position>",
        f"{pad}    <X>{x}</X>",
        f"{pad}    <Y>{y}</Y>",
        f"{pad}  </Position>",
        f"{pad}  <OffsetPosition>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </OffsetPosition>",
        f"{pad}  <ObjectRotation>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </ObjectRotation>",
        f"{pad}</Trigger>",
    ]
    return "\n".join(lines)


def _trigger_sign(
    tid: int,
    x: int,
    y: int,
    loca_key: str,
    direction: str = "SOUTH",
) -> str:
    """SIGN with VIEW_SIGN → loca (vanilla pattern VERIFIED_LOCAL)."""
    pad = _indent(4)
    pre = f"PLAIN,NONE,{loca_key}"
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        (
            f'{pad}  <ObjectTypeCommand Type="SET_DATA" '
            f'TargetSpawnID="{tid}" '
            f'Extra="PREFAB,Prefabs/InteractiveObjects/'
            f'Signs/Sign_V5" '
            f'Precondition="NONE" Timing="ON_SPAWN" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        (
            f'{pad}  <ObjectTypeCommand Type="VIEW_SIGN" '
            f'TargetSpawnID="{tid}" Extra="" '
            f'Precondition="{pre}" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        f"{pad}  <SpawnObjectType>SIGN</SpawnObjectType>",
        f"{pad}  <SpawnDirection>{direction}</SpawnDirection>",
        f"{pad}  <SpawnStaticID>1</SpawnStaticID>",
        f"{pad}  <SpawnTime>EVERYTIME</SpawnTime>",
        f"{pad}  <Enabled>true</Enabled>",
        f"{pad}  <OpenableByMonsters>false</OpenableByMonsters>",
        f"{pad}  <ChallengeID>0</ChallengeID>",
        f"{pad}  <InitialState>NONE</InitialState>",
        f"{pad}  <Position>",
        f"{pad}    <X>{x}</X>",
        f"{pad}    <Y>{y}</Y>",
        f"{pad}  </Position>",
        f"{pad}  <OffsetPosition>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </OffsetPosition>",
        f"{pad}  <ObjectRotation>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </ObjectRotation>",
        f"{pad}</Trigger>",
    ]
    return "\n".join(lines)



def _trigger_entrance_stub(
    tid: int,
    x: int,
    y: int,
    target_map: str,
    direction: str = "EAST",
    *,
    enabled: bool = True,
    target_spawn_id: int | None = None,
) -> str:
    """ENTRANCE to linked map (M4-006 stub Goblinwatch)."""
    pad = _indent(4)
    spawn = tid if target_spawn_id is None else target_spawn_id
    en = "true" if enabled else "false"
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        (
            f'{pad}  <Command Type="USE_ENTRANCE" '
            f'TargetSpawnID="{spawn}" '
            f'Extra="{target_map}" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        (
            f'{pad}  <Command Type="SET_DATA" '
            f'TargetSpawnID="{tid}" '
            f'Extra="PREFAB,Prefabs/InteractiveObjects/'
            f'ChangeLevel/ChangeLevel_Outdoor" '
            f'Precondition="NONE" Timing="ON_SPAWN" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        f"{pad}  <SpawnObjectType>ENTRANCE</SpawnObjectType>",
        f"{pad}  <SpawnDirection>{direction}</SpawnDirection>",
        f"{pad}  <SpawnStaticID>3</SpawnStaticID>",
        f"{pad}  <SpawnTime>EVERYTIME</SpawnTime>",
        f"{pad}  <Enabled>{en}</Enabled>",
        f"{pad}  <OpenableByMonsters>false</OpenableByMonsters>",
        f"{pad}  <ChallengeID>0</ChallengeID>",
        f"{pad}  <InitialState>NONE</InitialState>",
        f"{pad}  <Position>",
        f"{pad}    <X>{x}</X>",
        f"{pad}    <Y>{y}</Y>",
        f"{pad}  </Position>",
        f"{pad}  <OffsetPosition>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </OffsetPosition>",
        f"{pad}  <ObjectRotation>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </ObjectRotation>",
        f"{pad}</Trigger>",
    ]
    return "\n".join(lines)


def _trigger_monster(
    tid: int,
    x: int,
    y: int,
    spawn_static_id: int,
    direction: str = "WEST",
) -> str:
    """Standing MONSTER spawn (Cave1 pattern). VERIFIED_LOCAL."""
    pad = _indent(4)
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        f"{pad}  <SpawnObjectType>MONSTER</SpawnObjectType>",
        f"{pad}  <SpawnDirection>{direction}</SpawnDirection>",
        f"{pad}  <SpawnStaticID>{spawn_static_id}</SpawnStaticID>",
        f"{pad}  <SpawnTime>EVERYTIME</SpawnTime>",
        f"{pad}  <Enabled>true</Enabled>",
        f"{pad}  <OpenableByMonsters>false</OpenableByMonsters>",
        f"{pad}  <ChallengeID>0</ChallengeID>",
        f"{pad}  <InitialState>NONE</InitialState>",
        f"{pad}  <Position>",
        f"{pad}    <X>{x}</X>",
        f"{pad}    <Y>{y}</Y>",
        f"{pad}  </Position>",
        f"{pad}  <OffsetPosition>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </OffsetPosition>",
        f"{pad}  <ObjectRotation>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </ObjectRotation>",
        f"{pad}</Trigger>",
    ]
    return "\n".join(lines)


def _triggers_for_cell(
    x: int,
    y: int,
    placements: dict[tuple[int, int], list[str]],
) -> str:
    chunks = placements.get((x, y))
    if not chunks:
        return ""
    return "\n" + "\n".join(chunks)


# landmark_id → (npc_trigger, sign_trigger, sign_loca, npc_id|None)
_LANDMARK_BINDINGS: dict[str, dict[str, Any]] = {
    "lm.town_hall": {
        "npc_tid": 10,
        "npc_static_id": 20000,
        "sign_tid": 30,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_TOWN_HALL",
        "fidelity": "F0",
    },
    "lm.tavern_lonely_knight": {
        "npc_tid": 11,
        "npc_static_id": 20001,
        "sign_tid": 31,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_TAVERN",
        "fidelity": "F1",
    },
    "lm.goblinwatch_entrance": {
        "entrance_tid": 20,
        "sign_tid": 32,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_GOBLINWATCH_GATE",
        "fidelity": "F0",
        "target_map": "Goblinwatch.xml",
    },
    "lm.stables": {
        "sign_tid": 40,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_STABLES",
        "fidelity": "F2",
    },
    "lm.boats": {
        "sign_tid": 41,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_BOATS",
        "fidelity": "F2",
    },
    "lm.abandoned_temple_entrance": {
        "sign_tid": 42,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_ABANDONED_TEMPLE",
        "fidelity": "F2",
    },
    "lm.garik_forge_entrance": {
        "sign_tid": 43,
        "sign_loca": "SIGN_MM6_NEW_SORPIGAL_GARIK_FORGE",
        "fidelity": "F2",
    },
}


# MMX MonsterStaticData StaticID — VERIFIED_LOCAL Ubisoft install.
_GOBLIN_SPAWN_STATIC_ID = 50  # MONSTER_GOBLIN
_ENCOUNTER_TRIGGER_IDS = {
    "enc.goblin_road": 60,
}


def build_placements(
    sketch: dict[str, Any],
) -> dict[tuple[int, int], list[str]]:
    """Map cell → XML trigger fragments (M4-001/002/007)."""
    place: dict[tuple[int, int], list[str]] = {}
    start = sketch["party_start"]["cell"]
    sx, sy = int(start["x"]), int(start["y"])
    place.setdefault((sx, sy), []).append(
        _trigger_party(1, sx, sy, "EAST")
    )

    by_lm = {
        a["landmark_id"]: a for a in (sketch.get("anchors") or [])
    }
    for lm_id, bind in _LANDMARK_BINDINGS.items():
        if lm_id not in by_lm:
            raise MapGenError(f"нет anchor {lm_id} в sketch")
        cell = by_lm[lm_id]["cell"]
        x, y = int(cell["x"]), int(cell["y"])
        bucket = place.setdefault((x, y), [])
        if "npc_tid" in bind:
            bucket.append(
                _trigger_npc(
                    int(bind["npc_tid"]),
                    x,
                    y,
                    int(bind["npc_static_id"]),
                )
            )
        if "entrance_tid" in bind:
            bucket.append(
                _trigger_entrance_stub(
                    int(bind["entrance_tid"]),
                    x,
                    y,
                    str(bind["target_map"]),
                    enabled=True,
                    target_spawn_id=1,
                )
            )
        bucket.append(
            _trigger_sign(
                int(bind["sign_tid"]),
                x,
                y,
                str(bind["sign_loca"]),
            )
        )

    for enc in sketch.get("encounters_on_grid") or []:
        eid = str(enc.get("id") or "")
        if eid not in _ENCOUNTER_TRIGGER_IDS:
            continue
        cell = enc["cell"]
        x, y = int(cell["x"]), int(cell["y"])
        tid = _ENCOUNTER_TRIGGER_IDS[eid]
        place.setdefault((x, y), []).append(
            _trigger_monster(
                tid,
                x,
                y,
                _GOBLIN_SPAWN_STATIC_ID,
                direction="WEST",
            )
        )
    return place


def render_grid_xml(sketch: dict[str, Any]) -> str:
    mmx = sketch["mmx_map"]
    size = sketch["size_proposal"]["m4_greybox"]
    width = int(size["width"])
    height = int(size["height"])
    if width != 24 or height != 18:
        raise MapGenError(
            f"expected 24x18 greybox, got {width}x{height}"
        )
    name = str(mmx["name"])
    if name != "New_Sorpigal":
        raise MapGenError(f"unexpected map name {name}")
    walk = passable_set(sketch)
    placements = build_placements(sketch)
    wmp = int(mmx["world_map_point_id"])
    loca = str(mmx["loca_location"])
    map_type = str(mmx.get("type") or "CITY")
    style = str(mmx.get("style") or "CASTLE")

    lines: list[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        (
            "<Grid "
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        ),
        f"  <name>{name}_gridData</name>",
        "  <hideFlags>None</hideFlags>",
        f"  <Name>{name}</Name>",
        f"  <SceneName>{name}</SceneName>",
        # Reuse vanilla minimap path until custom art exists.
        "  <MinimapName>MinimapMaps/MAP_Sorpigal</MinimapName>",
        f"  <LocationLocaName>{loca}</LocationLocaName>",
        f"  <Type>{map_type}</Type>",
        f"  <Style>{style}</Style>",
        f"  <WorldMapPointID>{wmp}</WorldMapPointID>",
        "  <MusicAudioIDDay>AtmosphereVillageDay</MusicAudioIDDay>",
        (
            "  <MusicAudioIDNight>"
            "AtmosphereVillageNight"
            "</MusicAudioIDNight>"
        ),
        "  <IsWithFightMusic>true</IsWithFightMusic>",
        f"  <Width>{width}</Width>",
        f"  <Height>{height}</Height>",
        "  <OffsetX>0</OffsetX>",
        "  <OffsetY>0</OffsetY>",
        "  <OffsetZ>0</OffsetZ>",
        "  <MinLevel>1</MinLevel>",
        "  <MaxLevel>1</MaxLevel>",
        "  <GridSlots>",
    ]

    for y in range(height):
        lines.append("    <Row>")
        for x in range(width):
            terr = terrain_at(x, y, width, height, walk)
            trans = transition_types(x, y, width, height, walk)
            lines.append(
                f'      <Slot Height="0" Terrain="{terr}" '
                f'TerrainSound="NONE" MapArea="NONE">'
            )
            lines.append("        <Position>")
            lines.append(f"          <X>{x}</X>")
            lines.append(f"          <Y>{y}</Y>")
            lines.append("        </Position>")
            for ttype in trans:
                lines.append(
                    f'        <Transition Type="{ttype}" '
                    f'IsDynamic="false" />'
                )
            extra = _triggers_for_cell(x, y, placements)
            if extra:
                lines.append(extra)
            lines.append("      </Slot>")
        lines.append("    </Row>")

    lines.append("  </GridSlots>")
    lines.append("</Grid>")
    lines.append("")
    return "\n".join(lines)


def _trigger_codex_stub(
    tid: int,
    x: int,
    y: int,
    *,
    token_id: int = 20002,
    lorebook_id: int = 20000,
) -> str:
    """COMMAND_CONTAINER: ADD_TOKEN codex + ADD_LOREBOOK (M4 stub)."""
    pad = _indent(4)
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        (
            f'{pad}  <Command Type="SET_DATA" '
            f'TargetSpawnID="{tid}" '
            f'Extra="PREFAB,Prefabs/InteractiveObjects/'
            f'LootContainer/Chest/LootChest_Gold" '
            f'Precondition="NONE" Timing="ON_SPAWN" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        (
            f'{pad}  <Command Type="ADD_TOKEN" '
            f'TargetSpawnID="{tid}" Extra="{token_id}" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="1" />'
        ),
        (
            f'{pad}  <Command Type="ADD_LOREBOOK" '
            f'TargetSpawnID="{tid}" Extra="{lorebook_id}" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="1" />'
        ),
        (
            f'{pad}  <Command Type="SET_ENABLED" '
            f'TargetSpawnID="{tid}" Extra="False" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="1" />'
        ),
        (
            f"{pad}  <SpawnObjectType>"
            f"COMMAND_CONTAINER</SpawnObjectType>"
        ),
        f"{pad}  <SpawnDirection>CENTER</SpawnDirection>",
        f"{pad}  <SpawnStaticID>19</SpawnStaticID>",
        f"{pad}  <SpawnTime>EVERYTIME</SpawnTime>",
        f"{pad}  <Enabled>true</Enabled>",
        f"{pad}  <OpenableByMonsters>false</OpenableByMonsters>",
        f"{pad}  <ChallengeID>0</ChallengeID>",
        f"{pad}  <InitialState>NONE</InitialState>",
        f"{pad}  <Position>",
        f"{pad}    <X>{x}</X>",
        f"{pad}    <Y>{y}</Y>",
        f"{pad}  </Position>",
        f"{pad}  <OffsetPosition>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </OffsetPosition>",
        f"{pad}  <ObjectRotation>",
        f"{pad}    <X>0</X>",
        f"{pad}    <Y>0</Y>",
        f"{pad}    <Z>0</Z>",
        f"{pad}  </ObjectRotation>",
        f"{pad}</Trigger>",
    ]
    return "\n".join(lines)


def render_goblinwatch_stub_xml() -> str:
    """M4 stub DUNGEON 8x8: party, codex chest, exit to town."""
    width, height = 8, 8
    walk = {
        (x, y)
        for x in range(1, width - 1)
        for y in range(1, height - 1)
    }
    placements: dict[tuple[int, int], list[str]] = {}
    placements[(1, 1)] = [_trigger_party(1, 1, 1, "EAST")]
    placements[(4, 4)] = [_trigger_codex_stub(50, 4, 4)]
    placements[(1, 1)].append(
        _trigger_entrance_stub(
            8,
            1,
            1,
            "New_Sorpigal.xml",
            direction="WEST",
            enabled=True,
            target_spawn_id=1,
        )
    )
    placements[(4, 4)].append(
        _trigger_sign(
            51,
            4,
            4,
            "SIGN_MM6_GOBLINWATCH_STUB_VAULT",
        )
    )

    lines: list[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        (
            "<Grid "
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        ),
        "  <name>Goblinwatch_gridData</name>",
        "  <hideFlags>None</hideFlags>",
        "  <Name>Goblinwatch</Name>",
        "  <SceneName>Goblinwatch</SceneName>",
        "  <MinimapName>MinimapMaps/MAP_Cave_1</MinimapName>",
        "  <LocationLocaName>LOCATION_MM6_GOBLINWATCH</LocationLocaName>",
        "  <Type>DUNGEON</Type>",
        "  <Style>CAVES</Style>",
        "  <WorldMapPointID>0</WorldMapPointID>",
        "  <MusicAudioIDDay>DungeonCave</MusicAudioIDDay>",
        "  <MusicAudioIDNight>DungeonCave</MusicAudioIDNight>",
        "  <IsWithFightMusic>true</IsWithFightMusic>",
        f"  <Width>{width}</Width>",
        f"  <Height>{height}</Height>",
        "  <OffsetX>0</OffsetX>",
        "  <OffsetY>0</OffsetY>",
        "  <OffsetZ>0</OffsetZ>",
        "  <MinLevel>1</MinLevel>",
        "  <MaxLevel>1</MaxLevel>",
        "  <GridSlots>",
    ]
    for y in range(height):
        lines.append("    <Row>")
        for x in range(width):
            terr = terrain_at(x, y, width, height, walk)
            trans = transition_types(x, y, width, height, walk)
            lines.append(
                f'      <Slot Height="0" Terrain="{terr}" '
                f'TerrainSound="NONE" MapArea="NONE">'
            )
            lines.append("        <Position>")
            lines.append(f"          <X>{x}</X>")
            lines.append(f"          <Y>{y}</Y>")
            lines.append("        </Position>")
            for ttype in trans:
                lines.append(
                    f'        <Transition Type="{ttype}" '
                    f'IsDynamic="false" />'
                )
            extra = _triggers_for_cell(x, y, placements)
            if extra:
                lines.append(extra)
            lines.append("      </Slot>")
        lines.append("    </Row>")
    lines.append("  </GridSlots>")
    lines.append("</Grid>")
    lines.append("")
    return "\n".join(lines)


def corridor_steps(sketch: dict[str, Any]) -> int:
    """PASSABLE Manhattan along route.quest83 (approx)."""
    for route in sketch.get("routes") or []:
        if route.get("id") == "route.quest83.accept_to_gate":
            return int(route.get("approx_steps") or 0)
    raise MapGenError("нет route.quest83.accept_to_gate")


def summarize(sketch: dict[str, Any], xml_text: str) -> dict[str, Any]:
    size = sketch["size_proposal"]["m4_greybox"]
    walk = passable_set(sketch)
    width = int(size["width"])
    height = int(size["height"])
    blocked = width * height - len(
        [
            1
            for x in range(width)
            for y in range(height)
            if terrain_at(x, y, width, height, walk) == "PASSABLE"
        ]
    )
    passable = width * height - blocked
    return {
        "name": sketch["mmx_map"]["name"],
        "width": width,
        "height": height,
        "cells": width * height,
        "passable": passable,
        "blocked": blocked,
        "corridor_steps": corridor_steps(sketch),
        "xml_bytes": len(xml_text.encode("utf-8")),
        "party": sketch["party_start"]["cell"],
        "triggers": [
            "PARTY:1",
            "Janis:10",
            "Andover:11",
            "Gate:20",
            "Goblin:60",
            "signs:30-32,40-43",
        ],
        "sign_keys": sorted(
            {
                str(b["sign_loca"])
                for b in _LANDMARK_BINDINGS.values()
            }
        ),
    }


def run_self_test() -> None:
    sketch = load_json(DEFAULT_SKETCH)
    xml = render_grid_xml(sketch)
    assert "<Width>24</Width>" in xml
    assert "<Height>18</Height>" in xml
    assert "<Name>New_Sorpigal</Name>" in xml
    assert 'SpawnObjectType>PARTY' in xml
    assert "NPC_IDS,20000" in xml
    assert "NPC_IDS,20001" in xml
    assert "START_DIALOGUE" in xml
    assert "SpawnObjectType>SIGN" in xml
    assert "SIGN_MM6_NEW_SORPIGAL_TOWN_HALL" in xml
    assert "Goblinwatch.xml" in xml
    assert 'Enabled>true</Enabled>' in xml
    assert "Sorpigal.xml" not in xml.replace(
        "MAP_Sorpigal", "MAP_X"
    )
    # Count slots
    assert xml.count("<Slot ") == 24 * 18
    assert xml.count("<Row>") == 18
    assert xml.count("SpawnObjectType>SIGN") == 7
    assert "SpawnObjectType>MONSTER" in xml
    assert "SpawnStaticID>50</SpawnStaticID>" in xml
    assert 'Trigger ID="60"' in xml
    info = summarize(sketch, xml)
    assert info["corridor_steps"] <= 10
    assert info["passable"] >= 50

    stub = render_goblinwatch_stub_xml()
    assert "<Name>Goblinwatch</Name>" in stub
    assert "<Width>8</Width>" in stub
    assert "<Height>8</Height>" in stub
    assert stub.count("<Slot ") == 64
    assert "ADD_TOKEN" in stub and "Extra=\"20002\"" in stub
    assert "ADD_LOREBOOK" in stub and "Extra=\"20000\"" in stub
    assert "New_Sorpigal.xml" in stub
    assert "SIGN_MM6_GOBLINWATCH_STUB_VAULT" in stub
