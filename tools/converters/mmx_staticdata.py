"""Build MMX StaticData CSV overlay rows from registry + catalog.

Only MM6X rows. Does not copy vanilla tables.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from mmx_ids import AllocError, registry_slot

TABLES = (
    "NpcStaticData.csv",
    "QuestSteps.csv",
    "QuestObjectives.csv",
    "Token.csv",
    "LoreBookStaticData.csv",
    "WorldMapPointsStaticData.csv",
)


class StaticDataError(ValueError):
    """Invalid StaticData catalog or registry slot."""


def load_json(path: Any) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_cell(
    registry: dict[str, Any],
    raw: Any,
) -> str:
    if isinstance(raw, dict) and "ref" in raw:
        slot = raw.get("slot")
        if not slot:
            raise StaticDataError("нет slot у ref")
        try:
            value = registry_slot(registry, raw["ref"], slot)
        except AllocError as exc:
            raise StaticDataError(str(exc)) from exc
        if value is None:
            raise StaticDataError(
                f"слот {raw['ref']} {slot} не назначен"
            )
        return str(value)
    if raw is None:
        return ""
    if isinstance(raw, bool):
        return "TRUE" if raw else "FALSE"
    return str(raw)


def render_row(
    registry: dict[str, Any],
    header: list[str],
    fields: dict[str, Any],
) -> list[str]:
    unknown = set(fields) - set(header)
    if unknown:
        raise StaticDataError(
            f"лишние поля: {sorted(unknown)}"
        )
    return [
        resolve_cell(registry, fields.get(col, ""))
        for col in header
    ]


def render_csv(
    header: list[str],
    rows: list[list[str]],
    *,
    comment_lines: list[str] | None = None,
) -> str:
    """UTF-8 CSV with # comments, matching vanilla layout."""
    buf = io.StringIO(newline="")
    if comment_lines:
        for line in comment_lines:
            buf.write(line.rstrip("\n") + "\n")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        if len(row) != len(header):
            raise StaticDataError(
                f"длина строки {len(row)} != {len(header)}"
            )
        writer.writerow(row)
    return buf.getvalue()


def build_tables(
    registry: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, str]:
    tables = catalog.get("tables")
    if not isinstance(tables, dict):
        raise StaticDataError("catalog.tables должен быть объектом")
    out: dict[str, str] = {}
    for name in TABLES:
        if name not in tables:
            raise StaticDataError(f"нет таблицы {name}")
        spec = tables[name]
        header = spec.get("header")
        rows_spec = spec.get("rows")
        if not isinstance(header, list) or not header:
            raise StaticDataError(f"{name}: плохой header")
        if not isinstance(rows_spec, list):
            raise StaticDataError(f"{name}: rows не список")
        rows = [
            render_row(registry, header, fields)
            for fields in rows_spec
        ]
        comments = spec.get("comments") or []
        if not isinstance(comments, list):
            raise StaticDataError(f"{name}: comments не список")
        out[name] = render_csv(
            [str(col) for col in header],
            rows,
            comment_lines=[str(item) for item in comments],
        )
    return out


def parse_csv_data(text: str) -> tuple[list[str], list[list[str]]]:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        kept.append(line)
    if not kept:
        return [], []
    rows = list(csv.reader(io.StringIO("\n".join(kept))))
    return rows[0], rows[1:]


def run_self_test() -> None:
    registry = {
        "entries": [
            {
                "stable_id": "mm6.npc.new_sorpigal.janis",
                "slots": [
                    {"namespace": "npc", "value": 20000},
                    {
                        "namespace": "dialog",
                        "value": "Mm6JanisDialog",
                    },
                    {
                        "namespace": "loca",
                        "value": "NPC_NAME_MM6_JANIS",
                    },
                ],
            }
        ]
    }
    catalog = {
        "tables": {
            "NpcStaticData.csv": {
                "comments": ["# NPC"],
                "header": [
                    "StaticID",
                    "NameKey",
                    "HirelingProfession",
                    "",
                    "PortraitKey",
                    "ConversationKey",
                    "TravelStationID",
                    "NpcEffects",
                    "HirePrice",
                    "HireShare",
                    "CanBeFired",
                    "AllowItemSell",
                    "MinimapSymbol",
                ],
                "rows": [
                    {
                        "StaticID": {
                            "ref": "mm6.npc.new_sorpigal.janis",
                            "slot": "npc",
                        },
                        "NameKey": {
                            "ref": "mm6.npc.new_sorpigal.janis",
                            "slot": "loca",
                        },
                        "HirelingProfession": "",
                        "": "MM6 Janis",
                        "PortraitKey": "PIC_generic_NOBLEWOMAN",
                        "ConversationKey": {
                            "ref": "mm6.npc.new_sorpigal.janis",
                            "slot": "dialog",
                        },
                        "TravelStationID": 0,
                        "NpcEffects": "",
                        "HirePrice": 0,
                        "HireShare": 0,
                        "CanBeFired": True,
                        "AllowItemSell": True,
                        "MinimapSymbol": "HOUSE",
                    }
                ],
            },
            "QuestSteps.csv": {
                "comments": ["#QuestSteps"],
                "header": ["StaticID", "Name"],
                "rows": [],
            },
            "QuestObjectives.csv": {
                "comments": ["#QuestObjectives"],
                "header": ["StaticID"],
                "rows": [],
            },
            "Token.csv": {
                "comments": ["#QuestToken"],
                "header": ["StaticID"],
                "rows": [],
            },
            "LoreBookStaticData.csv": {
                "comments": ["# Lore Books"],
                "header": ["StaticID"],
                "rows": [],
            },
            "WorldMapPointsStaticData.csv": {
                "comments": ["# World Map"],
                "header": ["StaticID"],
                "rows": [],
            },
        }
    }
    # Only Npc has rows; others empty headers still ok.
    tables = build_tables(registry, catalog)
    header, rows = parse_csv_data(tables["NpcStaticData.csv"])
    assert header[0] == "StaticID"
    assert rows[0][0] == "20000"
    assert rows[0][5] == "Mm6JanisDialog"
    assert "TRUE" in rows[0]
