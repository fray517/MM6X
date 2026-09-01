"""Parse MM6 .EVT / .STR (OpenEnroth EvtProgram layout).

Instruction: length byte, then eventId u16, step u8, opcode u8,
then opcode payload. STR is concatenated NUL-terminated strings.

VERIFIED_SOURCE: OpenEnroth EvtProgram::load / initLevelStrings.
"""

from __future__ import annotations

import struct
from typing import Any

VAR_QBITS = 0x10
VAR_INVENTORY_HANDS = 0x11
VAR_AWARD = 0x0C
VAR_AUTONOTES = 0xDF

OPCODES: dict[int, str] = {
    0: "Invalid",
    1: "Exit",
    2: "SpeakInHouse",
    3: "PlaySound",
    4: "MouseOver",
    5: "LocationName",
    6: "MoveToMap",
    7: "OpenChest",
    8: "ShowFace",
    9: "ReceiveDamage",
    10: "SetSnow",
    11: "SetTexture",
    12: "ShowMovie",
    13: "SetSprite",
    14: "Compare",
    15: "ChangeDoorState",
    16: "Add",
    17: "Subtract",
    18: "Set",
    19: "SummonMonsters",
    21: "CastSpell",
    22: "SpeakNPC",
    23: "SetFacesBit",
    24: "ToggleActorFlag",
    25: "RandomGoTo",
    26: "InputString",
    29: "StatusText",
    30: "ShowMessage",
    31: "OnTimer",
    32: "ToggleIndoorLight",
    33: "PressAnyKey",
    34: "SummonItem",
    35: "ForPartyMember",
    36: "Jmp",
    37: "OnMapReload",
    38: "OnLongTimer",
    39: "SetNPCTopic",
    40: "MoveNPC",
    41: "GiveItem",
    42: "ChangeEvent",
    43: "CheckSkill",
}


class EvtError(ValueError):
    """Malformed EVT/STR payload."""


def parse_str(payload: bytes, encoding: str) -> list[str]:
    """NUL-separated map strings (OpenEnroth initLevelStrings)."""
    texts: list[str] = []
    offset = 0
    size = len(payload)
    while offset < size:
        end = payload.find(b"\x00", offset)
        if end < 0:
            chunk = payload[offset:]
            offset = size
        else:
            chunk = payload[offset:end]
            offset = end + 1
        texts.append(chunk.decode(encoding, errors="replace"))
    return texts


def _u8(data: bytes, index: int) -> int | None:
    if index >= len(data):
        return None
    return data[index]


def _u16(data: bytes, index: int) -> int | None:
    if index + 2 > len(data):
        return None
    return struct.unpack_from("<H", data, index)[0]


def _u32(data: bytes, index: int) -> int | None:
    if index + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, index)[0]


def _decode_var_op(opcode: int, data: bytes) -> dict[str, Any]:
    """MM6: u8 var + u32 value (+ u8 jump for Compare).

    MM7 OpenEnroth uses u16 var. This GOG MM6 EVT is the shorter
    layout (Compare 6 bytes, Set/Add/Sub 5). VERIFIED_LOCAL.
    """
    info: dict[str, Any] = {}
    is_cmp = opcode == 14
    mm6_len = 6 if is_cmp else 5
    if len(data) == mm6_len:
        info["var"] = data[0]
        info["value"] = struct.unpack_from("<I", data, 1)[0]
        info["layout"] = "mm6"
        if is_cmp:
            info["target_step"] = data[5]
        return info
    info["var"] = _u16(data, 0)
    info["value"] = _u32(data, 2)
    info["layout"] = "mm7"
    if is_cmp:
        info["target_step"] = _u8(data, 6)
    return info


def decode_payload(opcode: int, data: bytes) -> dict[str, Any]:
    """Decode known fields; unknown opcodes stay as hex."""
    info: dict[str, Any] = {}
    if opcode == 4:
        info["text_id"] = _u8(data, 0)
    elif opcode in (2,):
        info["house_id"] = _u32(data, 0)
    elif opcode in (7,):
        info["chest_id"] = _u8(data, 0)
    elif opcode == 15:
        info["door_id"] = _u8(data, 0)
        info["door_action"] = _u8(data, 1)
    elif opcode in (14, 16, 17, 18):
        info.update(_decode_var_op(opcode, data))
    elif opcode in (26, 29, 30):
        info["text_id"] = _u32(data, 0)
    elif opcode == 22:
        info["npc_id"] = _u32(data, 0)
    elif opcode == 35:
        info["who"] = _u8(data, 0)
    elif opcode == 36:
        info["target_step"] = _u8(data, 0)
    elif opcode == 39 and len(data) >= 9:
        info["npc_id"] = _u32(data, 0)
        info["topic_index"] = _u8(data, 4)
        info["topic_event"] = _u32(data, 5)
    elif opcode == 41:
        info["treasure_level"] = _u8(data, 0)
        info["treasure_type"] = _u8(data, 1)
        info["item_id"] = _u32(data, 2)
    elif opcode == 42:
        info["event_id"] = _u32(data, 0)
    elif opcode == 6 and len(data) >= 26:
        info["x"] = struct.unpack_from("<i", data, 0)[0]
        info["y"] = struct.unpack_from("<i", data, 4)[0]
        info["z"] = struct.unpack_from("<i", data, 8)[0]
        rest = data[26:]
        info["map"] = rest.split(b"\x00", 1)[0].decode(
            "ascii",
            errors="replace",
        )
    return info


def parse_evt(payload: bytes) -> list[dict[str, Any]]:
    """Split a map .EVT into instructions."""
    insns: list[dict[str, Any]] = []
    pos = 0
    size = len(payload)
    while pos < size:
        length = payload[pos]
        total = length + 1
        if total < 5:
            raise EvtError(f"EVT record too small at {pos}")
        if pos + total > size:
            raise EvtError(f"EVT truncated at {pos}")
        event_id, step, opcode = struct.unpack_from(
            "<HBB",
            payload,
            pos + 1,
        )
        data = payload[pos + 5 : pos + total]
        name = OPCODES.get(opcode, f"op{opcode}")
        item: dict[str, Any] = {
            "event_id": event_id,
            "step": step,
            "opcode": opcode,
            "opname": name,
        }
        decoded = decode_payload(opcode, data)
        if decoded:
            item.update(decoded)
        insns.append(item)
        pos += total
    return insns


def qbit_refs(insns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in insns:
        if item.get("var") != VAR_QBITS:
            continue
        rows.append(
            {
                "event_id": item["event_id"],
                "step": item["step"],
                "opname": item["opname"],
                "qbit": item.get("value"),
            }
        )
    return rows
