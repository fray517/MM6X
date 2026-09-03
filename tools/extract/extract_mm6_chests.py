"""Read chest item lists from an MM6 indoor .dlv (games.lod).

Chests are 20 packed MapChest records (GrayFace MM6 Item 0x1C).
Does not write into the game. Full .dlv stays gitignored.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mm6_lod import LodError, Mm6Lod, decode_maybe_compressed

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_REPORTS = REPO_ROOT / "reports"
GAMES_LOD = "games.lod"

ITEM_SIZE = 0x1C
CHEST_SLOTS = 140
CHEST_HEADER = 4
CHEST_SIZE = CHEST_HEADER + CHEST_SLOTS * ITEM_SIZE + CHEST_SLOTS * 2
CHEST_COUNT = 20
DEFAULT_STEMS = ("D01",)


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
    found = find_child(folder, GAMES_LOD)
    if found is not None and found.is_file():
        return found
    return find_child(game_path, GAMES_LOD)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_named(lod: Mm6Lod, stem: str, suffix: str) -> str | None:
    want = f"{stem}.{suffix}".casefold()
    for name in lod.names():
        if name.casefold() == want:
            return name
    return None


def parse_chest(blob: bytes, offset: int) -> dict[str, Any]:
    picture, flags = struct.unpack_from("<HH", blob, offset)
    items: list[dict[str, int]] = []
    base = offset + CHEST_HEADER
    for slot in range(CHEST_SLOTS):
        number = struct.unpack_from("<i", blob, base + slot * ITEM_SIZE)[0]
        if number == 0:
            continue
        items.append({"slot": slot, "item_id": number})
    return {
        "picture": picture,
        "flags": flags,
        "items": items,
    }


def plausible_item(number: int) -> bool:
    if number == 0:
        return True
    if -7 <= number <= -1:
        return True
    if 1 <= number <= 800:
        return True
    return False


def chest_block_ok(blob: bytes, base: int) -> bool:
    span = CHEST_SIZE * CHEST_COUNT
    if base < 0 or base + span > len(blob):
        return False
    filled = 0
    loot_levels = 0
    for index in range(CHEST_COUNT):
        offset = base + index * CHEST_SIZE
        picture = struct.unpack_from("<H", blob, offset)[0]
        if picture > 7:
            return False
        chest = parse_chest(blob, offset)
        if chest["items"]:
            filled += 1
        for item in chest["items"]:
            number = item["item_id"]
            if not plausible_item(number):
                return False
            if -7 <= number <= -1:
                loot_levels += 1
    return filled >= 2 and loot_levels >= 3


def find_chest_block(blob: bytes) -> int | None:
    """Locate 20 packed MapChest records via item Number hits."""
    seen: set[int] = set()
    start = 0
    while True:
        if start + 4 > len(blob):
            break
        number = struct.unpack_from("<i", blob, start)[0]
        if 1 <= number <= 800:
            for slot in range(CHEST_SLOTS):
                chest = start - CHEST_HEADER - slot * ITEM_SIZE
                if chest < 0:
                    break
                for index in range(CHEST_COUNT):
                    base = chest - index * CHEST_SIZE
                    if base in seen:
                        continue
                    seen.add(base)
                    if chest_block_ok(blob, base):
                        return base
        start += 1
    return None


def summarize_map(
    stem: str,
    dlv_name: str,
    blob: bytes,
    how: str,
) -> dict[str, Any]:
    base = find_chest_block(blob)
    if base is None:
        return {
            "stem": stem,
            "dlv": dlv_name,
            "how": how,
            "error": "chest block not found",
        }
    chests = []
    for index in range(CHEST_COUNT):
        row = parse_chest(blob, base + index * CHEST_SIZE)
        row["index"] = index
        chests.append(row)
    return {
        "stem": stem,
        "dlv": dlv_name,
        "how": how,
        "decoded_bytes": len(blob),
        "chest_offset": base,
        "chests": chests,
        "evidence": "VERIFIED_LOCAL",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_chests.py",
        description="Read-only chest item lists from MM6 indoor .dlv.",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"Каталог MM6. Иначе {ENV_PATH_KEY} из .env.",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS,
        help="Куда писать chests_slice.json.",
    )
    parser.add_argument(
        "--stem",
        action="append",
        dest="stems",
        default=None,
        help="Имя карты без расширения. Можно повторять.",
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
        print("games.lod не найден.", file=sys.stderr)
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
        dlv_name = find_named(lod, stem, "dlv")
        if dlv_name is None:
            print(f"MISS {stem}.dlv", file=sys.stderr)
            failed += 1
            continue
        try:
            raw = lod.read_blob(dlv_name)
            blob, how = decode_maybe_compressed(raw)
        except LodError as exc:
            print(f"FAIL {stem}.dlv: {exc}", file=sys.stderr)
            failed += 1
            continue
        summary = summarize_map(stem, dlv_name, blob, how)
        maps.append(summary)
        if summary.get("error"):
            print(f"FAIL {dlv_name}: {summary['error']}", file=sys.stderr)
            failed += 1
            continue
        filled = [
            chest
            for chest in summary["chests"]
            if chest["items"]
        ]
        print(
            f"OK {dlv_name} how={how} chests={len(filled)} "
            f"offset={summary['chest_offset']}"
        )
        for chest in filled:
            ids = [item["item_id"] for item in chest["items"]]
            print(f"  chest[{chest['index']}] items={ids}")
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": "games.lod",
        "evidence": "VERIFIED_LOCAL",
        "maps": maps,
        "note": "Derived chest index. Full .dlv stays gitignored.",
    }
    if not args.dry_run:
        args.reports_dir.mkdir(parents=True, exist_ok=True)
        path = args.reports_dir / "chests_slice.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"index {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
