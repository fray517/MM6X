"""MMX target ID namespaces and collision-safe allocation.

Vanilla tables already use sparse IDs around 10000 (test rows).
MM6X numeric IDs live in 20000-29999. VERIFIED_LOCAL scan:
NpcStaticData max 10000, QuestSteps max 10002, Token max 804.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any

BAND_FLOOR = 20000
BAND_CEIL = 29999

# How we look up used values in the installed game.
NAMESPACES: dict[str, dict[str, str]] = {
    "npc": {
        "kind": "int",
        "table": "NpcStaticData.csv",
        "column": "StaticID",
    },
    "quest_step": {
        "kind": "int",
        "table": "QuestSteps.csv",
        "column": "StaticID",
    },
    "quest_objective": {
        "kind": "int",
        "table": "QuestObjectives.csv",
        "column": "StaticID",
    },
    "token": {
        "kind": "int",
        "table": "Token.csv",
        "column": "StaticID",
    },
    "lorebook": {
        "kind": "int",
        "table": "LoreBookStaticData.csv",
        "column": "StaticID",
    },
    "dungeon_entry": {
        "kind": "int",
        "table": "DungeonEntryStaticData.csv",
        "column": "StaticID",
    },
    "world_map_point": {
        "kind": "int",
        "table": "WorldMapPointsStaticData.csv",
        "column": "StaticID",
    },
    "dungeon_entry_key": {
        "kind": "str",
        "table": "DungeonEntryStaticData.csv",
        "column": "DungeonEntryID",
    },
    "map": {"kind": "str", "folder": "Maps"},
    "dialog": {"kind": "str", "folder": "Dialog"},
    "loca": {"kind": "str", "loca": "en"},
}


class AllocError(ValueError):
    """Cannot assign an MMX target without a collision."""


def next_free(used: set[int], floor: int = BAND_FLOOR) -> int:
    """First unused int in [floor, BAND_CEIL]."""
    candidate = floor
    while candidate <= BAND_CEIL:
        if candidate not in used:
            return candidate
        candidate += 1
    raise AllocError(f"полоса {floor}-{BAND_CEIL} исчерпана")


def parse_csv_rows(text: str) -> tuple[list[str], list[list[str]]]:
    """Skip # comments; keep the header row."""
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        kept.append(line)
    if not kept:
        return [], []
    reader = csv.reader(io.StringIO("\n".join(kept)))
    rows = list(reader)
    return rows[0], rows[1:]


def column_values(
    text: str,
    column: str,
    *,
    as_int: bool,
) -> set[Any]:
    header, body = parse_csv_rows(text)
    if column not in header:
        raise AllocError(f"нет колонки {column}")
    index = header.index(column)
    found: set[Any] = set()
    for row in body:
        if index >= len(row):
            continue
        raw = row[index].strip()
        if not raw:
            continue
        if as_int:
            if raw.lstrip("-").isdigit():
                found.add(int(raw))
        else:
            found.add(raw)
    return found


def loca_ids(text: str) -> set[str]:
    return set(re.findall(r'id="([^"]+)"', text))


def folder_stems(directory: Path, suffix: str) -> set[str]:
    if not directory.is_dir():
        return set()
    return {
        path.stem
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == suffix
    }


def find_child(directory: Path, name: str) -> Path | None:
    if not directory.is_dir():
        return None
    wanted = name.casefold()
    try:
        for child in directory.iterdir():
            if child.name.casefold() == wanted:
                return child
    except OSError:
        return None
    return None


def scan_namespace(assets: Path, namespace: str) -> set[Any]:
    """Used values in StreamingAssets for one namespace."""
    spec = NAMESPACES.get(namespace)
    if spec is None:
        raise AllocError(f"неизвестный namespace {namespace}")
    kind = spec["kind"]
    if "table" in spec:
        static = find_child(assets, "StaticData")
        if static is None:
            raise AllocError("нет StaticData")
        path = find_child(static, spec["table"])
        if path is None or not path.is_file():
            raise AllocError(f"нет таблицы {spec['table']}")
        text = path.read_text(encoding="utf-8-sig")
        return column_values(
            text,
            spec["column"],
            as_int=(kind == "int"),
        )
    if spec.get("folder"):
        folder = find_child(assets, spec["folder"])
        if folder is None:
            return set()
        suffix = ".xml"
        return folder_stems(folder, suffix)
    if spec.get("loca"):
        loca_root = find_child(assets, "Localisation")
        lang = find_child(loca_root, spec["loca"]) if loca_root else None
        loca_file = find_child(lang, "loca.xml") if lang else None
        if loca_file is None or not loca_file.is_file():
            raise AllocError("нет Localisation/en/loca.xml")
        return loca_ids(loca_file.read_text(encoding="utf-8"))
    raise AllocError(f"не умею сканировать {namespace}")


def run_self_test() -> None:
    assert next_free({10000, 20000}) == 20001
    assert next_free(set()) == BAND_FLOOR
    header, body = parse_csv_rows(
        "# cmt\nStaticID,Name\n1,A\n10000,Test\n"
    )
    assert header == ["StaticID", "Name"]
    assert body[1][0] == "10000"
