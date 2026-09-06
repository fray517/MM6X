"""Build New Sorpigal NPC list from NPCdata + topology houses."""

from __future__ import annotations

from typing import Any


def parse_npcprof(text: str) -> dict[int, str]:
    """Map profession id → name from npcprof.txt."""
    out: dict[int, str] = {}
    for line in text.splitlines()[1:]:
        parts = line.split("\t")
        if not parts or not parts[0].isdigit():
            continue
        out[int(parts[0])] = parts[1].strip() if len(parts) > 1 else ""
    return out


def parse_npcdata(text: str) -> list[dict[str, str]]:
    """Parse NPCdata.txt rows (TSV after 2 header lines)."""
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        parts = line.split("\t")
        if len(parts) < 7 or not parts[0].strip().isdigit():
            continue
        rows.append(
            {
                "id": parts[0].strip(),
                "name": parts[1].strip(),
                "pic": parts[2].strip(),
                "state": parts[3].strip() if len(parts) > 3 else "",
                "fame": parts[4].strip() if len(parts) > 4 else "",
                "rep": parts[5].strip() if len(parts) > 5 else "",
                "house_id": parts[6].strip(),
                "profession_id": (
                    parts[7].strip() if len(parts) > 7 else ""
                ),
                "join": parts[8].strip() if len(parts) > 8 else "",
                "news": parts[9].strip() if len(parts) > 9 else "",
                "event_a": parts[10].strip() if len(parts) > 10 else "",
                "event_b": parts[11].strip() if len(parts) > 11 else "",
                "event_c": parts[12].strip() if len(parts) > 12 else "",
                "notes": parts[13].strip() if len(parts) > 13 else "",
            }
        )
    return rows


def _int_or_zero(raw: str) -> int:
    return int(raw) if raw.isdigit() else 0


def filter_npcs_on_houses(
    rows: list[dict[str, str]],
    house_ids: set[int],
    professions: dict[int, str],
    house_names: dict[int, str],
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for row in rows:
        if not row["house_id"].isdigit():
            continue
        hid = int(row["house_id"])
        if hid not in house_ids:
            continue
        pid = _int_or_zero(row["profession_id"])
        found.append(
            {
                "mm6_npc_id": int(row["id"]),
                "name": row["name"].rstrip(),
                "pic": _int_or_zero(row["pic"]),
                "house_id": hid,
                "house_name": house_names.get(hid, ""),
                "profession_id": pid,
                "profession": professions.get(pid, ""),
                "event_a": _int_or_zero(row["event_a"]),
                "event_b": _int_or_zero(row["event_b"]),
                "event_c": _int_or_zero(row["event_c"]),
                "notes": row["notes"],
                "evidence": "VERIFIED_LOCAL",
            }
        )
    found.sort(key=lambda item: (item["house_id"], item["mm6_npc_id"]))
    return found


def classify_npc(npc: dict[str, Any]) -> str:
    """Fidelity for New Sorpigal M4 slice."""
    nid = npc["mm6_npc_id"]
    if nid == 291:
        return "F0"
    if nid == 1:
        return "F1"
    if nid in {2, 3}:
        return "F2"
    return "F3"


def stable_id_for(npc: dict[str, Any]) -> str | None:
    mapping = {
        291: "mm6.npc.new_sorpigal.janis",
        1: "mm6.npc.new_sorpigal.andover",
    }
    return mapping.get(npc["mm6_npc_id"])
