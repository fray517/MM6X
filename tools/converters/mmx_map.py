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
DEFAULT_SORPIGAL_WALK = (
    Path(__file__).resolve().parents[2]
    / "references"
    / "mmx"
    / "sorpigal.walk.json"
)


class MapGenError(ValueError):
    """Invalid sketch or map build input."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


TerrainCell = tuple[str, str]  # terrain, height
TerrainGrid = dict[tuple[int, int], TerrainCell]


def load_terrain_grid(path: Path) -> tuple[int, int, TerrainGrid]:
    """Full terrain+height grid from extracted vanilla map."""
    data = load_json(path)
    width = int(data["width"])
    height = int(data["height"])
    grid: TerrainGrid = {}
    cells = data.get("cells")
    if isinstance(cells, list) and cells:
        for cell in cells:
            x, y = int(cell["x"]), int(cell["y"])
            grid[(x, y)] = (
                str(cell.get("terrain") or "BLOCKED"),
                str(cell.get("height") or "0"),
            )
    else:
        for pair in data.get("passable") or []:
            grid[(int(pair[0]), int(pair[1]))] = ("PASSABLE", "0")
    if not grid:
        raise MapGenError(f"пустой terrain: {path}")
    return width, height, grid


def load_walk_json(path: Path) -> set[tuple[int, int]]:
    """PASSABLE cells from extracted vanilla map footprint."""
    _, _, grid = load_terrain_grid(path)
    return {xy for xy, (terr, _) in grid.items() if terr == "PASSABLE"}


def resolve_terrain_grid(
    sketch: dict[str, Any],
) -> tuple[int, int, TerrainGrid]:
    """Prefer terrain_source walk_json; else zone union @ height 0."""
    src = sketch.get("terrain_source") or {}
    rel = src.get("walk_json")
    size = sketch["size_proposal"]["m4_greybox"]
    width, height = int(size["width"]), int(size["height"])
    if rel:
        root = Path(__file__).resolve().parents[2]
        path = root / str(rel)
        if not path.is_file():
            raise MapGenError(f"нет walk json: {path}")
        tw, th, grid = load_terrain_grid(path)
        if tw != width or th != height:
            raise MapGenError(
                f"walk size {tw}x{th} != sketch {width}x{height}"
            )
        return width, height, grid
    walk = passable_set(sketch)
    grid = {
        (x, y): ("PASSABLE", "0")
        for x, y in walk
    }
    return width, height, grid


def resolve_walk(sketch: dict[str, Any]) -> set[tuple[int, int]]:
    """PASSABLE set for BFS / placement checks."""
    _, _, grid = resolve_terrain_grid(sketch)
    return {xy for xy, (terr, _) in grid.items() if terr == "PASSABLE"}


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
    *,
    force_border_blocked: bool = True,
) -> str:
    if force_border_blocked and is_border(x, y, width, height):
        return "BLOCKED"
    if (x, y) in walk:
        return "PASSABLE"
    return "BLOCKED"


def terrain_from_grid(
    grid: TerrainGrid,
    x: int,
    y: int,
) -> str:
    cell = grid.get((x, y))
    return cell[0] if cell else "BLOCKED"


def height_from_grid(
    grid: TerrainGrid,
    x: int,
    y: int,
) -> str:
    cell = grid.get((x, y))
    return cell[1] if cell else "0"


def transition_types(
    x: int,
    y: int,
    width: int,
    height: int,
    walk: set[tuple[int, int]],
    *,
    force_border_blocked: bool = True,
) -> list[str]:
    here = terrain_at(
        x,
        y,
        width,
        height,
        walk,
        force_border_blocked=force_border_blocked,
    )
    if here != "PASSABLE":
        return ["OPEN", "OPEN", "OPEN", "OPEN"]
    out: list[str] = []
    for dx, dy in _NEIGHBOR_DELTAS:
        nx, ny = x + dx, y + dy
        if nx < 0 or ny < 0 or nx >= width or ny >= height:
            out.append("CLOSED")
            continue
        if (
            terrain_at(
                nx,
                ny,
                width,
                height,
                walk,
                force_border_blocked=force_border_blocked,
            )
            == "PASSABLE"
        ):
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



def _party_check_require_token(token_id: int) -> str:
    """PARTY_CHECK with token in first inventory slot.

    Format VERIFIED_LOCAL (Castle_Portmeyron / Fort_Laegaire):
    ``PARTY_CHECK,NONE,,,,id,-1,-1,-1,-1,-1,-1,-1``.
    """
    return (
        f"PARTY_CHECK,NONE,,,,{token_id},"
        "-1,-1,-1,-1,-1,-1,-1"
    )


def _trigger_entrance_stub(
    tid: int,
    x: int,
    y: int,
    target_map: str,
    direction: str = "EAST",
    *,
    enabled: bool = True,
    target_spawn_id: int | None = None,
    require_token_id: int | None = None,
    locked_loca: str | None = None,
    consume_token: bool = False,
    object_type_command: bool = False,
) -> str:
    """ENTRANCE to linked map (M4-006 stub; M4-008 key gate).

    Key-lock: ``PARTY_CHECK`` on USE_ENTRANCE (VERIFIED_LOCAL).
    Consume: ``REMOVE_TOKEN`` Timing=ON_SUCCESS — door pattern
    VERIFIED_LOCAL; on USE_ENTRANCE = HYPOTHESIS.
    Cave scenes use ``ObjectTypeCommand`` (Cave1 VERIFIED_LOCAL).
    """
    pad = _indent(4)
    tag = (
        "ObjectTypeCommand" if object_type_command else "Command"
    )
    spawn = tid if target_spawn_id is None else target_spawn_id
    en = "true" if enabled else "false"
    if require_token_id is None:
        pre = "NONE"
    else:
        pre = _party_check_require_token(require_token_id)
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
    ]
    # Cave1 order: SET_DATA then USE_ENTRANCE.
    lines.append(
        f'{pad}  <{tag} Type="SET_DATA" '
        f'TargetSpawnID="{tid}" '
        f'Extra="PREFAB,Prefabs/InteractiveObjects/'
        f'ChangeLevel/ChangeLevel_Outdoor" '
        f'Precondition="NONE" Timing="ON_SPAWN" '
        f'RequiredState="NONE" ActivateCount="-1" />'
    )
    lines.append(
        f'{pad}  <{tag} Type="USE_ENTRANCE" '
        f'TargetSpawnID="{spawn}" '
        f'Extra="{target_map}" '
        f'Precondition="{pre}" Timing="ON_EXECUTE" '
        f'RequiredState="NONE" ActivateCount="-1" />'
    )
    if require_token_id is not None and consume_token:
        lines.append(
            f'{pad}  <{tag} Type="REMOVE_TOKEN" '
            f'TargetSpawnID="{tid}" '
            f'Extra="{require_token_id}" '
            f'Precondition="NONE" Timing="ON_SUCCESS" '
            f'RequiredState="NONE" ActivateCount="1" />'
        )
    if locked_loca is not None:
        lines.append(
            f'{pad}  <{tag} Type="GAME_MESSAGE" '
            f'TargetSpawnID="{tid}" '
            f'Extra="{locked_loca},2" '
            f'Precondition="NONE" Timing="ON_FAIL" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        )
    lines.extend(
        [
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
    )
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
        # Token 20001 = Goblinwatch key (MM6 item #489).
        "require_token_id": 20001,
        "locked_loca": "OBJECT_INTERACTION_MM6_GOBLINWATCH_LOCKED",
        "consume_token": True,
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
# Giant Spider 150 for L1 (Goblin 50 ≈525 HP). VERIFIED_LOCAL.
_GOBLIN_SPAWN_STATIC_ID = 150
DEFAULT_CAVE1_WALK = (
    Path(__file__).resolve().parents[2]
    / "references"
    / "mmx"
    / "cave1.walk.json"
)
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
            req = bind.get("require_token_id")
            bucket.append(
                _trigger_entrance_stub(
                    int(bind["entrance_tid"]),
                    x,
                    y,
                    str(bind["target_map"]),
                    enabled=True,
                    target_spawn_id=1,
                    require_token_id=(
                        None if req is None else int(req)
                    ),
                    locked_loca=bind.get("locked_loca"),
                    consume_token=bool(
                        bind.get("consume_token", False)
                    ),
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
    if width != 32 or height != 30:
        raise MapGenError(
            f"expected 32x30 Sorpigal-matched, got "
            f"{width}x{height}"
        )
    name = str(mmx["name"])
    if name != "New_Sorpigal":
        raise MapGenError(f"unexpected map name {name}")
    walk = resolve_walk(sketch)
    _, _, grid = resolve_terrain_grid(sketch)
    for anchor in sketch.get("anchors") or []:
        c = anchor["cell"]
        cell = (int(c["x"]), int(c["y"]))
        if cell not in walk:
            raise MapGenError(
                f"anchor {anchor.get('landmark_id')} "
                f"{cell} not PASSABLE"
            )
    party = sketch["party_start"]["cell"]
    party_xy = (int(party["x"]), int(party["y"]))
    if party_xy not in walk:
        raise MapGenError(f"party {party_xy} not PASSABLE")
    placements = build_placements(sketch)
    wmp = int(mmx["world_map_point_id"])
    loca = str(mmx["loca_location"])
    map_type = str(mmx.get("type") or "CITY")
    style = str(mmx.get("style") or "CASTLE")
    scene = str(mmx.get("scene_name") or "Sorpigal")

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
        f"  <SceneName>{scene}</SceneName>",
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
            terr = terrain_from_grid(grid, x, y)
            hgt = height_from_grid(grid, x, y)
            trans = transition_types(
                x,
                y,
                width,
                height,
                walk,
                force_border_blocked=False,
            )
            lines.append(
                f'      <Slot Height="{hgt}" Terrain="{terr}" '
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
    """COMMAND_CONTAINER: ADD_TOKEN + ADD_LOREBOOK (Cave OTC)."""
    pad = _indent(4)
    tag = "ObjectTypeCommand"
    lines = [
        f'{pad}<Trigger ID="{tid}">',
        f"{pad}  <MonsterGroupID>0</MonsterGroupID>",
        (
            f'{pad}  <{tag} Type="SET_DATA" '
            f'TargetSpawnID="{tid}" '
            f'Extra="PREFAB,Prefabs/InteractiveObjects/'
            f'LootContainer/Chest/LootChest_Gold" '
            f'Precondition="NONE" Timing="ON_SPAWN" '
            f'RequiredState="NONE" ActivateCount="-1" />'
        ),
        (
            f'{pad}  <{tag} Type="ADD_TOKEN" '
            f'TargetSpawnID="{tid}" Extra="{token_id}" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="1" />'
        ),
        (
            f'{pad}  <{tag} Type="ADD_LOREBOOK" '
            f'TargetSpawnID="{tid}" Extra="{lorebook_id}" '
            f'Precondition="NONE" Timing="ON_EXECUTE" '
            f'RequiredState="NONE" ActivateCount="1" />'
        ),
        (
            f'{pad}  <{tag} Type="SET_ENABLED" '
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
    """M4 stub DUNGEON 6x6: Cave1 terrain/heights + OTC exit."""
    width, height, grid = load_terrain_grid(DEFAULT_CAVE1_WALK)
    if width != 6 or height != 6:
        raise MapGenError("cave1.walk.json must be 6x6")
    walk = {
        xy
        for xy, (terr, _) in grid.items()
        if terr == "PASSABLE"
    }
    party_xy = (0, 1)
    exit_xy = (1, 1)
    vault_xy = (4, 4)
    for cell in (party_xy, exit_xy, vault_xy):
        if cell not in walk:
            raise MapGenError(
                f"Goblinwatch cell {cell} not PASSABLE"
            )
    placements: dict[tuple[int, int], list[str]] = {}
    placements[party_xy] = [
        _trigger_party(1, party_xy[0], party_xy[1], "EAST"),
    ]
    placements[exit_xy] = [
        _trigger_entrance_stub(
            8,
            exit_xy[0],
            exit_xy[1],
            "New_Sorpigal.xml",
            direction="WEST",
            enabled=True,
            target_spawn_id=1,
            object_type_command=True,
        ),
        _trigger_sign(
            52,
            exit_xy[0],
            exit_xy[1],
            "SIGN_MM6_GOBLINWATCH_EXIT",
        ),
    ]
    placements[vault_xy] = [
        _trigger_codex_stub(50, vault_xy[0], vault_xy[1]),
        _trigger_sign(
            51,
            vault_xy[0],
            vault_xy[1],
            "SIGN_MM6_GOBLINWATCH_STUB_VAULT",
        ),
    ]

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
        "  <SceneName>Cave1</SceneName>",
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
            terr = terrain_from_grid(grid, x, y)
            hgt = height_from_grid(grid, x, y)
            trans = transition_types(
                x,
                y,
                width,
                height,
                walk,
                force_border_blocked=False,
            )
            lines.append(
                f'      <Slot Height="{hgt}" Terrain="{terr}" '
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


def bfs_path_len(
    walk: set[tuple[int, int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> int | None:
    """Shortest 4-neighbour path on PASSABLE set, or None."""
    if start not in walk or goal not in walk:
        return None
    if start == goal:
        return 0
    q: list[tuple[tuple[int, int], int]] = [(start, 0)]
    seen = {start}
    while q:
        (x, y), dist = q.pop(0)
        for nx, ny in (
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ):
            nxt = (nx, ny)
            if nxt not in walk or nxt in seen:
                continue
            if nxt == goal:
                return dist + 1
            seen.add(nxt)
            q.append((nxt, dist + 1))
    return None


def _anchor_cell(
    sketch: dict[str, Any],
    landmark_id: str,
) -> tuple[int, int]:
    for anchor in sketch.get("anchors") or []:
        if anchor.get("landmark_id") == landmark_id:
            cell = anchor["cell"]
            return int(cell["x"]), int(cell["y"])
    raise MapGenError(f"нет anchor {landmark_id}")


def verify_routes(sketch: dict[str, Any]) -> list[dict[str, Any]]:
    """Offline route playtest: BFS hall→gate (+ sketch routes).

    Evidence: topology HYPOTHESIS; connectivity check local.
    """
    walk = resolve_walk(sketch)
    results: list[dict[str, Any]] = []
    for route in sketch.get("routes") or []:
        rid = str(route.get("id") or "")
        src = str(route.get("from") or "")
        dst = str(route.get("to") or "")
        start = _anchor_cell(sketch, src)
        goal = _anchor_cell(sketch, dst)
        steps = bfs_path_len(walk, start, goal)
        via = route.get("via_cells") or []
        via_ok = all(
            (int(p[0]), int(p[1])) in walk for p in via
        )
        results.append(
            {
                "id": rid,
                "from": src,
                "to": dst,
                "start": start,
                "goal": goal,
                "bfs_steps": steps,
                "via_passable": via_ok,
                "ok": steps is not None and via_ok,
            }
        )
    return results


def summarize(sketch: dict[str, Any], xml_text: str) -> dict[str, Any]:
    size = sketch["size_proposal"]["m4_greybox"]
    walk = resolve_walk(sketch)
    width = int(size["width"])
    height = int(size["height"])
    blocked = width * height - len(
        [
            1
            for x in range(width)
            for y in range(height)
            if terrain_at(
                x,
                y,
                width,
                height,
                walk,
                force_border_blocked=False,
            )
            == "PASSABLE"
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
    assert "<Width>32</Width>" in xml
    assert "<Height>30</Height>" in xml
    assert "<Name>New_Sorpigal</Name>" in xml
    assert "<SceneName>Sorpigal</SceneName>" in xml
    assert 'SpawnObjectType>PARTY' in xml
    assert "NPC_IDS,20000" in xml
    assert "NPC_IDS,20001" in xml
    assert "START_DIALOGUE" in xml
    assert "SpawnObjectType>SIGN" in xml
    assert "SIGN_MM6_NEW_SORPIGAL_TOWN_HALL" in xml
    assert "Goblinwatch.xml" in xml
    assert "PARTY_CHECK" in xml
    assert 'Enabled>true</Enabled>' in xml
    assert "Sorpigal.xml" not in xml.replace(
        "MAP_Sorpigal", "MAP_X"
    )
    assert xml.count("<Slot ") == 32 * 30
    routes = verify_routes(sketch)
    assert routes, "нет routes в sketch"
    assert all(r["ok"] for r in routes), routes
    hall_gate = next(
        r
        for r in routes
        if r["id"] == "route.quest83.accept_to_gate"
    )
    assert hall_gate["bfs_steps"] is not None
    assert hall_gate["bfs_steps"] <= 30
    assert xml.count("<Row>") == 30
    assert xml.count("SpawnObjectType>SIGN") == 7
    assert "SpawnObjectType>MONSTER" in xml
    assert "SpawnStaticID>150</SpawnStaticID>" in xml
    assert 'Trigger ID="60"' in xml
    info = summarize(sketch, xml)
    assert info["corridor_steps"] <= 25
    assert info["passable"] >= 200

    stub = render_goblinwatch_stub_xml()
    assert "<Name>Goblinwatch</Name>" in stub
    assert "<SceneName>Cave1</SceneName>" in stub
    assert "<Width>6</Width>" in stub
    assert "<Height>6</Height>" in stub
    assert stub.count("<Slot ") == 36
    assert "ADD_TOKEN" in stub and "Extra=\"20002\"" in stub
    assert "ADD_LOREBOOK" in stub and "Extra=\"20000\"" in stub
    assert "New_Sorpigal.xml" in stub
    assert "SIGN_MM6_GOBLINWATCH_STUB_VAULT" in stub
    assert "SIGN_MM6_GOBLINWATCH_EXIT" in stub
    assert "ObjectTypeCommand" in stub
    assert 'Height="0.3112983"' in stub
    assert "<X>0</X>" in stub and "<Y>1</Y>" in stub
