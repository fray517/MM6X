"""Extract allowlisted MM6 .EVT/.STR and a slice index.

Read-only towards the game. Raw bodies stay in
references/mm6/raw/ (gitignore). Git gets only curated facts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mm6_evt import EvtError, parse_evt, parse_str, qbit_refs
from mm6_lod import LodError, Mm6Lod, decode_maybe_compressed

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_OUT = REPO_ROOT / "references" / "mm6" / "raw"
DEFAULT_REPORTS = REPO_ROOT / "reports"
LOD_NAME = "icons.lod"

# Slice maps. GLOBAL for town-hall / QBit scripts.
DEFAULT_STEMS = ("OUTE3", "D01", "GLOBAL")

INTEREST = re.compile(
    r"nilbog|goblin|гоблин|комбин|combin|vault|дверь|"
    r"ратуш|town.?hall|andover|андов|sulman|сулман|"
    r"candel|канделябр|письм|letter|код",
    re.IGNORECASE,
)


def load_env(start: Path | None = None) -> None:
    """Load KEY=VALUE from .env without overriding the process env."""
    here = (start or REPO_ROOT).resolve()
    env_file: Path | None = None
    for folder in (here, *here.parents):
        candidate = folder / ".env"
        if candidate.is_file():
            env_file = candidate
            break
    if env_file is None:
        return
    try:
        text = env_file.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in "\"'"
        ):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def env_game_path() -> Path | None:
    raw = os.environ.get(ENV_PATH_KEY, "").strip().strip('"')
    if not raw:
        return None
    return Path(raw)


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


def find_lod(game_path: Path) -> Path | None:
    data = find_child(game_path, "Data")
    folder = data if data is not None and data.is_dir() else game_path
    found = find_child(folder, LOD_NAME)
    if found is not None and found.is_file():
        return found
    return find_child(game_path, LOD_NAME)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_entry(lod: Mm6Lod, name: str) -> tuple[bytes, str, str]:
    entry = lod.get(name)
    if entry is None:
        raise LodError(f"no entry {name!r}")
    blob = lod.read_blob(entry.name)
    payload, how = decode_maybe_compressed(blob)
    return payload, how, entry.name


def find_named(lod: Mm6Lod, stem: str, suffix: str) -> str | None:
    want = f"{stem}.{suffix}".casefold()
    for name in lod.names():
        if name.casefold() == want:
            return name
    return None


def str_index(texts: list[str], text_id: int | None) -> str | None:
    if text_id is None:
        return None
    if 0 <= text_id < len(texts):
        return texts[text_id]
    return None


def summarize(
    stem: str,
    evt_name: str,
    str_name: str | None,
    insns: list[dict[str, Any]],
    texts: list[str],
) -> dict[str, Any]:
    event_ids = sorted({item["event_id"] for item in insns})
    interesting = []
    for index, text in enumerate(texts):
        if text and INTEREST.search(text):
            interesting.append({"index": index, "text": text})
    inputs = []
    messages = []
    for item in insns:
        if item["opname"] not in (
            "InputString",
            "StatusText",
            "ShowMessage",
            "MouseOver",
        ):
            continue
        tid = item.get("text_id")
        resolved = str_index(texts, tid)
        row = {
            "event_id": item["event_id"],
            "step": item["step"],
            "opname": item["opname"],
            "text_id": tid,
            "text": resolved,
        }
        if item["opname"] == "InputString":
            inputs.append(row)
        if resolved and INTEREST.search(resolved):
            messages.append(row)
        elif item["opname"] == "InputString":
            messages.append(row)
    houses = [
        {
            "event_id": item["event_id"],
            "house_id": item.get("house_id"),
        }
        for item in insns
        if item["opname"] == "SpeakInHouse"
    ]
    moves = [
        {
            "event_id": item["event_id"],
            "map": item.get("map"),
            "x": item.get("x"),
            "y": item.get("y"),
            "z": item.get("z"),
        }
        for item in insns
        if item["opname"] == "MoveToMap"
    ]
    doors = [
        {
            "event_id": item["event_id"],
            "door_id": item.get("door_id"),
            "action": item.get("door_action"),
        }
        for item in insns
        if item["opname"] == "ChangeDoorState"
    ]
    inventory = [
        {
            "event_id": item["event_id"],
            "opname": item["opname"],
            "item_id": item.get("value"),
        }
        for item in insns
        if item.get("var") == 17
    ]
    topics = [
        {
            "event_id": item["event_id"],
            "npc_id": item.get("npc_id"),
            "topic_index": item.get("topic_index"),
            "topic_event": item.get("topic_event"),
        }
        for item in insns
        if item["opname"] == "SetNPCTopic"
    ]
    letters = []
    for item in insns:
        if item["opname"] != "MouseOver":
            continue
        text = str_index(texts, item.get("text_id"))
        if text and len(text) == 1:
            letters.append(
                {
                    "event_id": item["event_id"],
                    "letter": text,
                }
            )
    return {
        "stem": stem,
        "evt": evt_name,
        "str": str_name,
        "insn_count": len(insns),
        "event_count": len(event_ids),
        "string_count": len(texts),
        "qbits": qbit_refs(insns),
        "input_string": inputs,
        "strings_of_interest": interesting,
        "text_ops_of_interest": messages,
        "speak_in_house": houses,
        "move_to_map": moves,
        "doors": doors,
        "inventory": inventory,
        "npc_topics": topics,
        "letter_plates": letters,
    }


def write_raw(
    out_dir: Path,
    name: str,
    payload: bytes,
    how: str,
    *,
    is_text: bool,
    encoding: str,
    text: str | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = Path(name).name
    if is_text and text is not None:
        (out_dir / f"{safe}.utf8.txt").write_text(
            text,
            encoding="utf-8",
        )
    else:
        (out_dir / safe).write_bytes(payload)
    meta = {
        "lod": "Icons.lod",
        "entry": name,
        "how": how,
        "decoded_bytes": len(payload),
        "created_utc": utc_now(),
        "evidence": "VERIFIED_LOCAL",
    }
    (out_dir / f"{safe}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def numbered_str(texts: list[str]) -> str:
    lines = [f"{index}\t{text}" for index, text in enumerate(texts)]
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_evt.py",
        description="Read-only extract of slice .EVT/.STR from Icons.lod.",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"Каталог MM6. Иначе {ENV_PATH_KEY} из .env.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда писать raw (gitignore).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS,
        help="Куда писать evt_slice.json.",
    )
    parser.add_argument(
        "--stem",
        action="append",
        dest="stems",
        default=None,
        help="Имя карты без расширения. Можно повторять.",
    )
    parser.add_argument(
        "--encoding",
        default="cp1251",
        help="Кодировка .STR (эта сборка: cp1251).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файлы не писать.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
    game_path = args.game_path or env_game_path()
    if game_path is None:
        print(
            f"Укажите --game-path или {ENV_PATH_KEY} в .env.",
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
    except LodError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    stems = args.stems or list(DEFAULT_STEMS)
    maps: list[dict[str, Any]] = []
    failed = 0
    for stem in stems:
        evt_name = find_named(lod, stem, "evt")
        if evt_name is None:
            print(f"MISS {stem}.EVT", file=sys.stderr)
            failed += 1
            continue
        try:
            evt_blob, evt_how, evt_name = read_entry(lod, evt_name)
            insns = parse_evt(evt_blob)
        except (LodError, EvtError) as exc:
            print(f"FAIL {stem}.EVT: {exc}", file=sys.stderr)
            failed += 1
            continue
        str_name = find_named(lod, stem, "str")
        texts: list[str] = []
        str_blob = b""
        str_how = "missing"
        if str_name is not None:
            try:
                str_blob, str_how, str_name = read_entry(lod, str_name)
                texts = parse_str(str_blob, args.encoding)
            except LodError as exc:
                print(f"FAIL {stem}.STR: {exc}", file=sys.stderr)
                failed += 1
        summary = summarize(stem, evt_name, str_name, insns, texts)
        maps.append(summary)
        print(
            f"OK {evt_name} insns={summary['insn_count']} "
            f"events={summary['event_count']} "
            f"str={len(texts)} how={evt_how}"
        )
        if args.dry_run:
            continue
        write_raw(
            args.output_dir,
            evt_name,
            evt_blob,
            evt_how,
            is_text=False,
            encoding=args.encoding,
        )
        if str_name is not None:
            write_raw(
                args.output_dir,
                str_name,
                str_blob,
                str_how,
                is_text=True,
                encoding=args.encoding,
                text=numbered_str(texts),
            )
            print(f"  wrote STR {str_name} strings={len(texts)}")
        print(f"  wrote EVT {evt_name}")
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": "Icons.lod",
        "evidence": "VERIFIED_LOCAL",
        "maps": maps,
        "note": (
            "Derived slice index. Full EVT bytecode stays gitignored."
        ),
    }
    if not args.dry_run:
        args.reports_dir.mkdir(parents=True, exist_ok=True)
        path = args.reports_dir / "evt_slice.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"index {path}")
    else:
        # Still print compact facts for the console.
        for item in maps:
            print(
                f"  {item['stem']}: qbits={len(item['qbits'])} "
                f"input={len(item['input_string'])} "
                f"letters={len(item['letter_plates'])} "
                f"interest={len(item['strings_of_interest'])}"
            )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
