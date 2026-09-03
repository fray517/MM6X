"""Read slice message-scrolls from ITEMS.TXT + Scroll.txt.

Read-only towards the game. Full letter bodies stay gitignored.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from extract_mm6_evt import (
    env_game_path,
    find_lod,
    find_named,
    load_env,
    read_entry,
)
from extract_mm6_text import extract_one
from mm6_evt import EvtError, parse_evt, parse_str
from mm6_lod import LodError, Mm6Lod
from mm6_plates import plates_from_evt
from mm6_scrolls import (
    logical_door_ids,
    parse_items,
    parse_legend,
    parse_scrolls,
    run_self_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS = REPO_ROOT / "reports"
DEFAULT_IDS = (489, 500, 505, 543)
QUEST_ID = 83
AWARD_ID = 53


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_text(text: str, wanted: int) -> str | None:
    for line in text.splitlines():
        cols = line.split("\t")
        if cols and cols[0].strip().isdigit():
            if int(cols[0].strip()) == wanted:
                return cols[1].strip() if len(cols) > 1 else ""
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_scrolls.py",
        description=(
            "Read-only slice of MM6 message scrolls (codex / letters)."
        ),
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help="Каталог MM6. Иначе MM6_GAME_PATH из .env.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS,
        help="Куда писать scrolls_slice.json.",
    )
    parser.add_argument(
        "--item",
        action="append",
        dest="items",
        type=int,
        default=None,
        help="Item#. Можно повторять. Иначе slice.",
    )
    parser.add_argument(
        "--encoding",
        default="cp1251",
        help="Кодировка таблиц (эта сборка: cp1251).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файлы не писать.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Синтетический разбор легенды без игры.",
    )
    return parser


def summarize_item(
    item_id: int,
    items: dict[int, dict[str, str]],
    scrolls: dict[int, dict[str, str]],
) -> dict[str, Any]:
    row = items.get(item_id)
    if row is None:
        return {"item_id": item_id, "error": "not in ITEMS.TXT"}
    name = row.get("Name") or row.get("name") or ""
    equip = row.get("Equip Stat") or ""
    mod1 = row.get("Mod1") or ""
    unidentified = row.get("Not identified name") or ""
    notes = row.get("Notes") or ""
    scroll = scrolls.get(item_id)
    payload: dict[str, Any] = {
        "item_id": item_id,
        "name": name,
        "equip": equip,
        "mod1": mod1,
        "unidentified": unidentified,
        "item_notes": notes,
        "evidence": "VERIFIED_LOCAL",
    }
    if scroll is None:
        return payload
    message = scroll["message"]
    payload["dungeon"] = scroll["dungeon"]
    payload["scroll_notes"] = scroll["notes"]
    payload["message"] = message
    if item_id == 543:
        legend = parse_legend(message)
        payload["legend"] = legend
    return payload


def print_item(item: dict[str, Any]) -> None:
    if item.get("error"):
        print(f"  {item['item_id']}: {item['error']}")
        return
    extra = item.get("mod1") or ""
    dungeon = item.get("dungeon") or ""
    print(
        f"  {item['item_id']} {item['name']}"
        f" {item['equip']} {extra} dungeon={dungeon!r}"
    )
    message = item.get("message") or ""
    if message and "legend" not in item and len(message) <= 80:
        print(f"    {message}")
    legend = item.get("legend")
    if not legend:
        return
    for entry in legend:
        opens = entry.get("opens_logical")
        closes = entry.get("closes_logical")
        if entry["kind"] == "door_switch":
            bit = f"open {opens}"
            if closes is not None:
                bit += f" close {closes}"
        else:
            bit = entry["kind"]
        print(f"    {entry['letter']}: {bit}")


def load_plates(lod: Mm6Lod, encoding: str) -> list[dict[str, Any]]:
    evt_name = find_named(lod, "D01", "evt")
    str_name = find_named(lod, "D01", "str")
    if evt_name is None or str_name is None:
        return []
    evt_blob, _, _ = read_entry(lod, evt_name)
    str_blob, _, _ = read_entry(lod, str_name)
    insns = parse_evt(evt_blob)
    texts = parse_str(str_blob, encoding)
    return plates_from_evt(insns, texts)


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        print("self-test OK")
        return 0
    game_path = args.game_path or env_game_path()
    if game_path is None:
        print(
            "Укажите --game-path или MM6_GAME_PATH в .env.",
            file=sys.stderr,
        )
        return 2
    game_path = game_path.expanduser()
    if not game_path.is_dir():
        print(f"Каталог не найден: {game_path}", file=sys.stderr)
        return 2
    lod_path = find_lod(game_path)
    if lod_path is None:
        print("Icons.lod не найден.", file=sys.stderr)
        return 2
    try:
        lod = Mm6Lod(lod_path)
        items_blob = extract_one(lod, "ITEMS.TXT", args.encoding)
        scroll_blob = extract_one(lod, "Scroll.txt", args.encoding)
        quests_blob = extract_one(lod, "Quests.txt", args.encoding)
        awards_blob = extract_one(lod, "Awards.txt", args.encoding)
    except LodError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    for blob, label in (
        (items_blob, "ITEMS.TXT"),
        (scroll_blob, "Scroll.txt"),
        (quests_blob, "Quests.txt"),
        (awards_blob, "Awards.txt"),
    ):
        if not blob.get("ok"):
            print(f"MISS {label}", file=sys.stderr)
            return 1
    items = parse_items(items_blob["text"])
    scrolls = parse_scrolls(scroll_blob["text"])
    wanted = args.items or list(DEFAULT_IDS)
    slice_items = [
        summarize_item(item_id, items, scrolls)
        for item_id in wanted
    ]
    print(
        f"OK ITEMS how={items_blob['how']} "
        f"Scroll how={scroll_blob['how']}"
    )
    for item in slice_items:
        print_item(item)
    groups: dict[str, list[int]] = {}
    try:
        plates = load_plates(lod, args.encoding)
    except (LodError, EvtError):
        plates = []
    legend = next(
        (item.get("legend") for item in slice_items if item.get("legend")),
        None,
    )
    if legend and plates:
        groups = logical_door_ids(legend, plates)
        print("logical_doors", groups)
    related = {
        "quest_83": _row_text(quests_blob["text"], QUEST_ID),
        "award_53": _row_text(awards_blob["text"], AWARD_ID),
    }
    print(f"quest_83 {related['quest_83']}")
    print(f"award_53 {related['award_53']}")
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": "Icons.lod",
        "evidence": "VERIFIED_LOCAL",
        "items": slice_items,
        "logical_doors": groups,
        "related": related,
        "note": (
            "Slice only. Full ITEMS/Scroll tables stay gitignored."
        ),
    }
    if not args.dry_run:
        args.reports_dir.mkdir(parents=True, exist_ok=True)
        path = args.reports_dir / "scrolls_slice.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"index {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
