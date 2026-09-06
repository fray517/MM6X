"""Classify New Sorpigal 2D buildings / services for design."""

from __future__ import annotations

from typing import Any

from mm6_topology import classify_row

# MMX-facing service categories (design, not engine enums).
CATEGORY = {
    "Weapon Shop": "shop_weapon",
    "Armor Shop": "shop_armor",
    "Magic Shop": "shop_magic",
    "General Store": "shop_general",
    "Stables": "travel_stables",
    "Boats": "travel_boats",
    "Temple": "temple",
    "Training": "training",
    "Town Hall": "town_hall",
    "Tavern": "tavern",
    "Bank": "bank",
    "Element Guild": "guild_element",
    "Self Guild": "guild_self",
    "Merc Guild": "guild_merc",
    "Thieves Guild": "guild_thieves",
    "Dungeon Ent": "dungeon_entrance",
}


def fidelity_for_building(house_id: int, role: str) -> str:
    """Align with M3-002 landmarks; shops default F3."""
    if house_id in {89, 171}:
        return "F0"
    if house_id == 92:
        return "F1"
    if house_id in {48, 57, 69, 79, 172, 188}:
        return "F2"
    if role == "residence":
        return "F3"
    return "F3"


def building_from_2d_row(row: dict[str, str]) -> dict[str, Any] | None:
    role = classify_row(row)
    if role == "unused":
        return None
    raw_id = row.get("#") or row.get("#_1")
    if not raw_id or not raw_id.isdigit():
        return None
    hid = int(raw_id)
    btype = row.get("Type", "").strip()
    item: dict[str, Any] = {
        "house_id": hid,
        "type": btype,
        "role": role,
        "category": CATEGORY.get(btype, "other"),
        "name": row.get("Name", "").strip(),
        "proprietor": row.get("Proprieter Name", "").strip(),
        "title": row.get("Title", "").strip(),
        "open_hour": row.get("Open", "").strip(),
        "closed_hour": row.get("Closed", "").strip(),
        "stock_a": row.get("A", "").strip(),
        "stock_b": row.get("B", "").strip(),
        "stock_c": row.get("C", "").strip(),
        "val": row.get("Val", "").strip(),
        "notes": (row.get("Notes:") or row.get("Notes") or "").strip(),
        "fidelity": fidelity_for_building(hid, role),
        "evidence": "VERIFIED_LOCAL",
    }
    return item


def buildings_from_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item = building_from_2d_row(row)
        if item is None:
            continue
        out.append(item)
    out.sort(key=lambda x: (x["fidelity"], x["house_id"]))
    return out


def summarize_buildings(
    buildings: list[dict[str, Any]],
) -> dict[str, Any]:
    by_f: dict[str, int] = {}
    by_cat: dict[str, int] = {}
    for item in buildings:
        if item["role"] == "residence":
            continue
        by_f[item["fidelity"]] = by_f.get(item["fidelity"], 0) + 1
        by_cat[item["category"]] = by_cat.get(item["category"], 0) + 1
    residences = sum(1 for b in buildings if b["role"] == "residence")
    return {
        "building_count": len(buildings),
        "non_residence": len(buildings) - residences,
        "residence_count": residences,
        "by_fidelity_non_residence": by_f,
        "by_category_non_residence": by_cat,
    }
