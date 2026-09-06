"""Parse MapStats encounter fields for outdoor/dungeon maps."""

from __future__ import annotations

from typing import Any


MAPSTATS_FIELDS = (
    "id",
    "name",
    "file_name",
    "reset_num",
    "first_visit_day",
    "refill_days",
    "lock",
    "trap",
    "tres",
    "enc_chance_pct",
    "m1_pct",
    "m2_pct",
    "m3_pct",
    "mon1_pic",
    "mon1_name",
    "mon1_dif",
    "mon1_count",
    "mon2_pic",
    "mon2_name",
    "mon2_dif",
    "mon2_count",
    "mon3_pic",
    "mon3_name",
    "mon3_dif",
    "mon3_count",
    "track",
    "designer",
)


def parse_mapstats_rows(text: str) -> list[dict[str, str]]:
    """Parse MapStats.txt data rows (header is line index 2)."""
    lines = text.splitlines()
    if len(lines) < 4:
        return []
    rows: list[dict[str, str]] = []
    for line in lines[3:]:
        parts = line.split("\t")
        if not parts or not parts[0].strip().isdigit():
            continue
        while len(parts) < len(MAPSTATS_FIELDS):
            parts.append("")
        row = {
            MAPSTATS_FIELDS[i]: parts[i].strip()
            for i in range(len(MAPSTATS_FIELDS))
        }
        rows.append(row)
    return rows


def row_by_id(
    rows: list[dict[str, str]],
    map_id: int,
) -> dict[str, str] | None:
    want = str(map_id)
    for row in rows:
        if row["id"] == want:
            return row
    return None


def _slot(
    row: dict[str, str],
    index: int,
) -> dict[str, Any] | None:
    pic = row[f"mon{index}_pic"]
    name = row[f"mon{index}_name"]
    if not pic or pic == "0":
        return None
    pct_key = f"m{index}_pct"
    return {
        "slot": index,
        "pic_stem": pic,
        "name": name,
        "chance_pct": int(row[pct_key]) if row[pct_key].isdigit() else 0,
        "dif": int(row[f"mon{index}_dif"])
        if row[f"mon{index}_dif"].isdigit()
        else 0,
        "count_range": row[f"mon{index}_count"].strip(),
    }


def encounter_profile(row: dict[str, str]) -> dict[str, Any]:
    slots = []
    for index in (1, 2, 3):
        slot = _slot(row, index)
        if slot:
            slots.append(slot)
    return {
        "mapstats_id": int(row["id"]),
        "name": row["name"],
        "file_name": row["file_name"],
        "refill_days": int(row["refill_days"])
        if row["refill_days"].isdigit()
        else 0,
        "lock": int(row["lock"]) if row["lock"].isdigit() else 0,
        "trap": int(row["trap"]) if row["trap"].isdigit() else 0,
        "tres": int(row["tres"]) if row["tres"].isdigit() else 0,
        "enc_chance_pct": int(row["enc_chance_pct"])
        if row["enc_chance_pct"].isdigit()
        else 0,
        "monsters": slots,
        "evidence": "VERIFIED_LOCAL",
    }


def parse_monster_tiers(
    text: str,
    pic_stem: str,
) -> list[dict[str, Any]]:
    """MONSTERS.TXT rows whose Picture starts with pic_stem (A/B/C)."""
    want = pic_stem.casefold()
    out: list[dict[str, Any]] = []
    for line in text.splitlines()[2:]:
        parts = line.split("\t")
        if len(parts) < 8 or not parts[0].strip().isdigit():
            continue
        picture = parts[1].strip()
        if not picture.casefold().startswith(want):
            continue
        # Goblin vs GoblinWatch — require exact stem + letter suffix
        rest = picture[len(pic_stem) :]
        if rest and rest[0] not in "ABC":
            continue
        if not rest:
            continue
        out.append(
            {
                "mm6_monster_id": int(parts[0]),
                "picture": picture,
                "name": parts[2].strip(),
                "level": parts[3].strip(),
                "hp": parts[4].strip(),
                "ac": parts[5].strip(),
                "exp": parts[6].strip(),
                "evidence": "VERIFIED_LOCAL",
            }
        )
    return out
