"""Build New Sorpigal exits/travel graph from topology + EVT."""

from __future__ import annotations

import re
from typing import Any

# "Castle Ironfist D3,M,W,F,2" / "Mist E2,Tu,Th,Sa,3"
TRAVEL_RE = re.compile(
    r"^(?P<label>.+?)\s+(?P<code>[A-Za-z]\d+)\s*,\s*(?P<rest>.+)$"
)


def parse_hub_schedule(schedule_a: str) -> dict[str, Any]:
    """Parse 2DEvents stables/boats A field."""
    raw = (schedule_a or "").strip()
    empty = {
        "raw": "",
        "label": "",
        "map_code": "",
        "days": [],
        "cost": None,
    }
    if not raw:
        return empty
    match = TRAVEL_RE.match(raw)
    if not match:
        return {
            "raw": raw,
            "label": raw,
            "map_code": "",
            "days": [],
            "cost": None,
        }
    rest = match.group("rest")
    parts = [p.strip() for p in rest.split(",") if p.strip()]
    cost: int | None = None
    days: list[str] = []
    if parts and parts[-1].isdigit():
        cost = int(parts[-1])
        days = parts[:-1]
    else:
        days = parts
    return {
        "raw": raw,
        "label": match.group("label").strip(),
        "map_code": match.group("code").upper(),
        "days": days,
        "cost": cost,
    }


def fidelity_exit(house_id: int | None, to_map: str) -> str:
    key = to_map.casefold()
    if house_id == 171 or key.startswith("d01"):
        return "F0"
    if key.startswith("outb3"):
        return "F2"
    if house_id in {172, 188}:
        return "F2"
    return "F3"


def fidelity_hub(_kind: str) -> str:
    return "F2"


def build_exits(
    topology_edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exits: list[dict[str, Any]] = []
    for edge in topology_edges:
        if edge.get("kind") != "map_transition":
            continue
        hid = edge.get("house_id")
        to_map = str(edge.get("to_map") or "")
        item: dict[str, Any] = {
            "id": f"exit.oute3.e{edge.get('event_id')}",
            "kind": "map_transition",
            "direction": "outbound",
            "from_region": edge.get("from"),
            "event_id": edge.get("event_id"),
            "house_id": hid,
            "to_map": to_map,
            "to_stable_id": edge.get("to_stable_id"),
            "to_title": edge.get("to_title"),
            "spawn_on_dest": edge.get("spawn"),
            "fidelity": fidelity_exit(
                hid if isinstance(hid, int) else None,
                to_map,
            ),
            "evidence": edge.get("evidence", "VERIFIED_LOCAL"),
        }
        if hid == 171:
            item["requires_item"] = 489
            item["stable_link"] = (
                "mm6.travel_link.new_sorpigal.goblinwatch"
            )
        exits.append(item)
    return exits


def build_return_links(
    d01_moves: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for move in d01_moves:
        dest = str(move.get("map") or "")
        if not dest or dest == "0":
            continue
        if "oute3" not in dest.casefold():
            continue
        links.append(
            {
                "id": f"exit.d01.e{move.get('event_id')}",
                "kind": "map_transition",
                "direction": "inbound_to_oute3",
                "from_map": "D01.Blv",
                "from_stable_id": "mm6.dungeon.goblinwatch",
                "event_id": move.get("event_id"),
                "to_map": dest,
                "to_region": "mm6.region.new_sorpigal",
                "spawn_on_dest": {
                    "x": move.get("x"),
                    "y": move.get("y"),
                    "z": move.get("z"),
                },
                "fidelity": "F0",
                "evidence": "VERIFIED_LOCAL",
                "note": "Quest #83 return to New Sorpigal outdoor.",
            }
        )
    return links


def build_scheduled_travel(
    travel_notes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    hubs: list[dict[str, Any]] = []
    dest_map = {
        48: {
            "file": "OutD3.Odm",
            "title": "Замок Айронфист",
            "mapstats_id": 12,
        },
        57: {
            "file": "OutE2.Odm",
            "title": "Остров Тумана",
            "mapstats_id": 14,
        },
    }
    for note in travel_notes:
        hid = note.get("hub_house_id")
        kind = str(note.get("kind") or "")
        parsed = parse_hub_schedule(str(note.get("schedule_a") or ""))
        meta = dest_map.get(hid if isinstance(hid, int) else -1, {})
        hubs.append(
            {
                "id": f"travel.{kind}.{hid}",
                "kind": kind,
                "house_id": hid,
                "schedule": parsed,
                "dest_file": meta.get("file"),
                "dest_title": meta.get("title"),
                "dest_mapstats_id": meta.get("mapstats_id"),
                "fidelity": fidelity_hub(kind),
                "evidence": "VERIFIED_LOCAL",
                "mmx_note": (
                    "Stub service in M4; full world travel later."
                ),
            }
        )
    return hubs
