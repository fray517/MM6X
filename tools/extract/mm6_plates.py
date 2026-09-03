"""Goblinwatch letter plates (D01.EVT e19-34).

Not a typed password. Each letter is a one-shot door switch,
a trap, a teleport, or a full reset. Sequence is not checked.
"""

from __future__ import annotations

from typing import Any

PLATE_EVENT_IDS = range(19, 35)
RESET_VARS = range(105, 118)
DOOR_CLOSED = 0
DOOR_OPEN = 1


def click_insns(insns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Skip MouseOver; it shares step 0 with the click stream."""
    return [item for item in insns if item.get("opname") != "MouseOver"]


def _find_step(
    insns: list[dict[str, Any]],
    step: int,
) -> int | None:
    for index, item in enumerate(insns):
        if item.get("step") == step:
            return index
    return None


def execute_event(
    insns: list[dict[str, Any]],
    variables: dict[int, int],
    doors: dict[int, int],
) -> dict[str, Any]:
    """Run one event's click stream. Mutates variables and doors."""
    click = click_insns(insns)
    door_changes: list[dict[str, int]] = []
    did_work = False
    pos = 0
    guard = 0
    while pos < len(click) and guard < 256:
        guard += 1
        item = click[pos]
        name = item.get("opname")
        if name == "Exit":
            break
        if name == "Compare":
            current = variables.get(item["var"], 0)
            if current >= item["value"]:
                nxt = _find_step(click, item["target_step"])
                if nxt is None:
                    break
                pos = nxt
                continue
            pos += 1
            continue
        if name == "Jmp":
            nxt = _find_step(click, item["target_step"])
            if nxt is None:
                break
            pos = nxt
            continue
        if name == "Set":
            variables[item["var"]] = item["value"]
            did_work = True
        elif name == "ChangeDoorState":
            door_id = item["door_id"]
            action = item["door_action"]
            if action in (DOOR_CLOSED, DOOR_OPEN):
                previous = doors.get(door_id, DOOR_CLOSED)
                doors[door_id] = action
                if previous != action:
                    door_changes.append(
                        {
                            "door_id": door_id,
                            "from": previous,
                            "to": action,
                        }
                    )
            did_work = True
        elif name in ("SetTexture", "CastSpell", "MoveToMap"):
            did_work = True
        pos += 1
    return {
        "did_work": did_work,
        "door_changes": door_changes,
    }


def _letter_of(
    insns: list[dict[str, Any]],
    texts: list[str],
) -> str | None:
    for item in insns:
        if item.get("opname") != "MouseOver":
            continue
        text_id = item.get("text_id")
        if not isinstance(text_id, int):
            continue
        if 0 <= text_id < len(texts):
            text = texts[text_id]
            if text:
                return text
    return None


def _is_reset(click: list[dict[str, Any]]) -> bool:
    for item in click:
        if item.get("opname") != "Set":
            continue
        if item.get("value") != 0:
            continue
        if item.get("var") in RESET_VARS:
            return True
    return False


def _classify(click: list[dict[str, Any]]) -> str:
    names = [item.get("opname") for item in click]
    if "MoveToMap" in names:
        return "teleport"
    if _is_reset(click):
        return "reset"
    if "ChangeDoorState" in names:
        return "door_switch"
    if "CastSpell" in names:
        return "trap"
    return "other"


def describe_plate(
    event_id: int,
    insns: list[dict[str, Any]],
    texts: list[str],
) -> dict[str, Any]:
    """One letter event: latch, doors, textures."""
    click = click_insns(insns)
    kind = _classify(click)
    latch_var: int | None = None
    opens: list[int] = []
    closes: list[int] = []
    textures: list[dict[str, Any]] = []
    for item in click:
        name = item.get("opname")
        if name == "Compare" and latch_var is None:
            latch_var = item.get("var")
        elif name == "ChangeDoorState":
            door_id = item.get("door_id")
            action = item.get("door_action")
            if action == DOOR_OPEN and door_id not in opens:
                opens.append(door_id)
            elif action == DOOR_CLOSED and door_id not in closes:
                closes.append(door_id)
        elif name == "SetTexture":
            textures.append(
                {
                    "face_id": item.get("face_id"),
                    "texture": item.get("texture"),
                }
            )
    move = next(
        (item for item in click if item.get("opname") == "MoveToMap"),
        None,
    )
    plate: dict[str, Any] = {
        "event_id": event_id,
        "letter": _letter_of(insns, texts),
        "kind": kind,
        "latch_var": latch_var,
        "opens": opens,
        "closes": closes,
        "textures": textures,
    }
    if move is not None:
        plate["teleport"] = {
            "x": move.get("x"),
            "y": move.get("y"),
            "z": move.get("z"),
            "map": move.get("map"),
        }
    return plate


def plates_from_evt(
    insns: list[dict[str, Any]],
    texts: list[str],
) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in insns:
        event_id = item["event_id"]
        if event_id not in PLATE_EVENT_IDS:
            continue
        grouped.setdefault(event_id, []).append(item)
    plates = []
    for event_id in PLATE_EVENT_IDS:
        if event_id not in grouped:
            continue
        plates.append(describe_plate(event_id, grouped[event_id], texts))
    return plates


def simulate_sequence(
    plates: list[dict[str, Any]],
    insns_by_event: dict[int, list[dict[str, Any]]],
    letters: str,
) -> dict[str, Any]:
    """Apply letter presses. Doors start closed (same as П reset)."""
    by_letter = {
        plate["letter"]: plate
        for plate in plates
        if plate.get("letter")
    }
    variables: dict[int, int] = {var: 0 for var in RESET_VARS}
    doors: dict[int, int] = {}
    steps: list[dict[str, Any]] = []
    for index, letter in enumerate(letters, start=1):
        plate = by_letter.get(letter)
        if plate is None:
            steps.append(
                {
                    "index": index,
                    "letter": letter,
                    "error": "unknown letter",
                }
            )
            continue
        event_id = plate["event_id"]
        result = execute_event(
            insns_by_event[event_id],
            variables,
            doors,
        )
        steps.append(
            {
                "index": index,
                "letter": letter,
                "event_id": event_id,
                "kind": plate["kind"],
                "did_work": result["did_work"],
                "door_changes": result["door_changes"],
            }
        )
    open_doors = sorted(
        door_id
        for door_id, state in doors.items()
        if state == DOOR_OPEN
    )
    return {
        "sequence": letters,
        "steps": steps,
        "vars": {str(key): value for key, value in sorted(variables.items())},
        "open_doors": open_doors,
        "evidence": "VERIFIED_LOCAL",
        "note": (
            "Initial doors = closed (action 0), matching e34 reset. "
            ".dlv door bits not parsed."
        ),
    }


def group_insns(
    insns: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in insns:
        grouped.setdefault(item["event_id"], []).append(item)
    return grouped


def run_self_test() -> None:
    """Synthetic one-shot Compare; no game files."""
    insns = [
        {
            "event_id": 20,
            "step": 0,
            "opname": "MouseOver",
            "text_id": 0,
        },
        {
            "event_id": 20,
            "step": 0,
            "opname": "Compare",
            "var": 105,
            "value": 1,
            "target_step": 3,
        },
        {
            "event_id": 20,
            "step": 1,
            "opname": "Set",
            "var": 105,
            "value": 1,
        },
        {
            "event_id": 20,
            "step": 2,
            "opname": "ChangeDoorState",
            "door_id": 55,
            "door_action": 1,
        },
        {
            "event_id": 20,
            "step": 3,
            "opname": "Exit",
        },
    ]
    variables: dict[int, int] = {105: 0}
    doors: dict[int, int] = {}
    first = execute_event(insns, variables, doors)
    assert first["did_work"] is True
    assert doors[55] == DOOR_OPEN
    assert variables[105] == 1
    second = execute_event(insns, variables, doors)
    assert second["did_work"] is False
    assert second["door_changes"] == []
    assert doors[55] == DOOR_OPEN
