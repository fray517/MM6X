"""Parse MM6 ITEMS.TXT / Scroll.txt slice (message scrolls).

Scroll bodies stay out of git. This module only structures rows.
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

LEGEND_RE = re.compile(
    r"^\s*([А-ЯЁ])\.\s+(.*\S)\s*$",
    re.MULTILINE,
)
OPEN_CLOSE_RE = re.compile(
    r"Открывает дверь\s+(\d+)"
    r"(?:\s+и\s+закрывает дверь\s+(\d+))?",
    re.IGNORECASE,
)


def parse_tsv(text: str) -> list[list[str]]:
    """Quoted multiline TSV (Scroll.txt messages)."""
    reader = csv.reader(
        io.StringIO(text),
        delimiter="\t",
        quotechar='"',
        doublequote=True,
    )
    return [row for row in reader if row]


def parse_items(text: str) -> dict[int, dict[str, str]]:
    """Index ITEMS.TXT by item number."""
    rows = parse_tsv(text)
    if not rows:
        return {}
    header = rows[1] if len(rows) > 1 else rows[0]
    keyed: dict[int, dict[str, str]] = {}
    for row in rows:
        if not row or not row[0].strip().isdigit():
            continue
        item_id = int(row[0].strip())
        fields: dict[str, str] = {}
        for index, name in enumerate(header):
            key = name.strip() or f"col{index}"
            value = row[index].strip() if index < len(row) else ""
            fields[key] = value
        keyed[item_id] = fields
    return keyed


def parse_scrolls(text: str) -> dict[int, dict[str, str]]:
    """Index Scroll.txt by Item#."""
    rows = parse_tsv(text)
    keyed: dict[int, dict[str, str]] = {}
    for row in rows:
        if not row or not row[0].strip().isdigit():
            continue
        item_id = int(row[0].strip())
        keyed[item_id] = {
            "item_id": str(item_id),
            "message": row[1].strip() if len(row) > 1 else "",
            "dungeon": row[2].strip() if len(row) > 2 else "",
            "notes": row[3].strip() if len(row) > 3 else "",
        }
    return keyed


def parse_legend(message: str) -> list[dict[str, Any]]:
    """Letter lines from the Goblinwatch codex (M44)."""
    entries: list[dict[str, Any]] = []
    for match in LEGEND_RE.finditer(message):
        letter = match.group(1)
        rest = match.group(2)
        kind = "other"
        opens: int | None = None
        closes: int | None = None
        low = rest.casefold()
        if "ловуш" in low:
            kind = "trap"
        elif "обслуживан" in low:
            kind = "maintenance"
        elif "сброс" in low:
            kind = "reset"
        else:
            hit = OPEN_CLOSE_RE.search(rest)
            if hit:
                kind = "door_switch"
                opens = int(hit.group(1))
                if hit.group(2):
                    closes = int(hit.group(2))
        entries.append(
            {
                "letter": letter,
                "kind": kind,
                "opens_logical": opens,
                "closes_logical": closes,
                "text": rest,
            }
        )
    return entries


def logical_door_ids(
    legend: list[dict[str, Any]],
    plates: list[dict[str, Any]],
) -> dict[str, list[int]]:
    """Map scroll door 1-6 onto EVT door_id lists."""
    by_letter = {
        plate["letter"]: plate
        for plate in plates
        if plate.get("letter")
    }
    groups: dict[int, set[int]] = {}
    for entry in legend:
        plate = by_letter.get(entry["letter"])
        if plate is None or plate.get("kind") != "door_switch":
            continue
        opens_n = entry.get("opens_logical")
        closes_n = entry.get("closes_logical")
        if opens_n is not None:
            groups.setdefault(opens_n, set()).update(plate.get("opens") or [])
        if closes_n is not None:
            groups.setdefault(closes_n, set()).update(
                plate.get("closes") or [],
            )
    return {
        str(number): sorted(door_ids)
        for number, door_ids in sorted(groups.items())
    }


def run_self_test() -> None:
    """Synthetic legend; no game files."""
    sample = (
        "А. Ловушка.\n"
        "Б. Открывает дверь 4 и закрывает дверь 5.\n"
        "Г. Открывает дверь 6.\n"
        "М. Обслуживание.\n"
        "П. Сброс.\n"
    )
    legend = parse_legend(sample)
    assert [item["letter"] for item in legend] == list("АБГМП")
    assert legend[0]["kind"] == "trap"
    assert legend[1]["opens_logical"] == 4
    assert legend[1]["closes_logical"] == 5
    assert legend[2]["opens_logical"] == 6
    assert legend[2]["closes_logical"] is None
    assert legend[3]["kind"] == "maintenance"
    assert legend[4]["kind"] == "reset"
    plates = [
        {
            "letter": "Б",
            "kind": "door_switch",
            "opens": [55, 56],
            "closes": [57, 58],
        },
        {
            "letter": "Г",
            "kind": "door_switch",
            "opens": [59, 60],
            "closes": [],
        },
    ]
    groups = logical_door_ids(legend, plates)
    assert groups["4"] == [55, 56]
    assert groups["5"] == [57, 58]
    assert groups["6"] == [59, 60]
