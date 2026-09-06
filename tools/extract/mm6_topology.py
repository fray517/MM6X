"""Parse MM6 2DEvents / EVT into a topology slice (read-only)."""

from __future__ import annotations

import csv
import io
from typing import Any


SERVICE_TYPES = {
    "Weapon Shop",
    "Armor Shop",
    "Magic Shop",
    "General Store",
    "Stables",
    "Boats",
    "Temple",
    "Training",
    "Town Hall",
    "Tavern",
    "Bank",
    "Element Guild",
    "Self Guild",
    "Merc Guild",
    "Thieves Guild",
    "Dungeon Ent",
}


def parse_2devents_tsv(text: str) -> list[dict[str, str]]:
    """Parse Icons.lod 2DEvents.txt (TSV, header on line 2)."""
    lines = text.splitlines()
    if len(lines) < 3:
        return []
    # Duplicate "#" headers → rename second.
    raw_header = lines[1].split("\t")
    header: list[str] = []
    seen: dict[str, int] = {}
    for col in raw_header:
        name = col.strip() or "empty"
        count = seen.get(name, 0)
        seen[name] = count + 1
        if count:
            name = f"{name}_{count}"
        header.append(name)
    rows: list[dict[str, str]] = []
    reader = csv.reader(io.StringIO("\n".join(lines[2:])), delimiter="\t")
    for parts in reader:
        if not parts or not any(p.strip() for p in parts):
            continue
        while len(parts) < len(header):
            parts.append("")
        row = {
            header[i]: parts[i].strip()
            for i in range(len(header))
        }
        rows.append(row)
    return rows


def filter_map(
    rows: list[dict[str, str]],
    map_code: str,
) -> list[dict[str, str]]:
    want = map_code.casefold()
    return [
        row
        for row in rows
        if row.get("Map", "").casefold() == want
    ]


def classify_row(row: dict[str, str]) -> str:
    kind = row.get("Type", "").strip()
    if kind in SERVICE_TYPES:
        if kind == "Dungeon Ent":
            return "dungeon_entrance"
        if kind == "Town Hall":
            return "quest_hub"
        if kind in {"Stables", "Boats"}:
            return "travel_hub"
        if kind == "Tavern":
            return "social"
        return "service"
    if kind.startswith("House") or kind.startswith("Hosue"):
        return "residence"
    if kind in {"", "Not Used"}:
        return "unused"
    return "other"


def nodes_from_2devents(
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for row in rows:
        house_id = row.get("#") or row.get("#_1")
        try:
            hid = int(house_id)
        except (TypeError, ValueError):
            continue
        role = classify_row(row)
        if role == "unused":
            continue
        node: dict[str, Any] = {
            "house_id": hid,
            "type": row.get("Type", ""),
            "role": role,
            "name": row.get("Name", ""),
            "proprietor": row.get("Proprieter Name", ""),
            "title": row.get("Title", ""),
            "schedule_a": row.get("A", ""),
            "evidence": "VERIFIED_LOCAL",
        }
        nodes.append(node)
    return nodes


def edges_from_evt_slice(
    oute3: dict[str, Any],
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for item in oute3.get("move_to_map") or []:
        edges.append(
            {
                "kind": "map_transition",
                "from": "mm6.region.new_sorpigal",
                "event_id": item.get("event_id"),
                "house_id": None,
                "to_map": item.get("map"),
                "spawn": {
                    "x": item.get("x"),
                    "y": item.get("y"),
                    "z": item.get("z"),
                },
                "evidence": "VERIFIED_LOCAL",
            }
        )
    house_by_event = {
        item.get("event_id"): item.get("house_id")
        for item in oute3.get("speak_in_house") or []
    }
    for edge in edges:
        eid = edge.get("event_id")
        if eid in house_by_event:
            edge["house_id"] = house_by_event[eid]
    return edges


def summarize_topology(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    by_role: dict[str, int] = {}
    for node in nodes:
        role = node["role"]
        by_role[role] = by_role.get(role, 0) + 1
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "by_role": by_role,
    }
