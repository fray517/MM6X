"""Read D01 letter plates and simulate a press sequence.

Read-only towards the game. Report stays gitignored.
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
from mm6_evt import EvtError, parse_evt, parse_str
from mm6_lod import LodError, Mm6Lod
from mm6_plates import (
    group_insns,
    plates_from_evt,
    run_self_test,
    simulate_sequence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS = REPO_ROOT / "reports"
DEFAULT_STEM = "D01"
DEFAULT_SEQUENCE = "НИЛБОГ"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_plates.py",
        description=(
            "Read-only D01 letter-plate maze from Icons.lod EVT."
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
        help="Куда писать plates_d01.json.",
    )
    parser.add_argument(
        "--stem",
        default=DEFAULT_STEM,
        help="Имя карты без расширения (дефолт D01).",
    )
    parser.add_argument(
        "--encoding",
        default="cp1251",
        help="Кодировка .STR (эта сборка: cp1251).",
    )
    parser.add_argument(
        "--sequence",
        default=DEFAULT_SEQUENCE,
        help="Буквы по порядку, без пробелов.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файлы не писать.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Синтетический one-shot Compare без игры.",
    )
    return parser


def print_plates(plates: list[dict[str, Any]]) -> None:
    for plate in plates:
        letter = plate["letter"]
        kind = plate["kind"]
        extra = ""
        if kind == "door_switch":
            extra = (
                f" open={plate['opens']} close={plate['closes']}"
                f" var={plate['latch_var']}"
            )
        elif kind == "teleport":
            dest = plate.get("teleport") or {}
            extra = (
                f" x={dest.get('x')} y={dest.get('y')}"
                f" z={dest.get('z')} map={dest.get('map')!r}"
            )
        print(
            f"  e{plate['event_id']} {letter} {kind}{extra}"
        )


def print_sim(sim: dict[str, Any]) -> None:
    print(f"sequence {sim['sequence']}")
    for step in sim["steps"]:
        if step.get("error"):
            print(
                f"  {step['index']} {step['letter']}: {step['error']}"
            )
            continue
        if not step["did_work"]:
            print(
                f"  {step['index']} {step['letter']}: skip (already used)"
            )
            continue
        changes = step["door_changes"]
        if not changes:
            print(
                f"  {step['index']} {step['letter']}: {step['kind']}"
            )
            continue
        bits = [
            f"d{item['door_id']}:{item['from']}->{item['to']}"
            for item in changes
        ]
        print(
            f"  {step['index']} {step['letter']}: " + ", ".join(bits)
        )
    print(f"open_doors {sim['open_doors']}")


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
        evt_name = find_named(lod, args.stem, "evt")
        if evt_name is None:
            print(f"MISS {args.stem}.EVT", file=sys.stderr)
            return 1
        evt_blob, evt_how, evt_name = read_entry(lod, evt_name)
        insns = parse_evt(evt_blob)
        str_name = find_named(lod, args.stem, "str")
        texts: list[str] = []
        if str_name is not None:
            str_blob, _, str_name = read_entry(lod, str_name)
            texts = parse_str(str_blob, args.encoding)
    except (LodError, EvtError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    plates = plates_from_evt(insns, texts)
    grouped = group_insns(insns)
    sim = simulate_sequence(plates, grouped, args.sequence)
    print(
        f"OK {evt_name} how={evt_how} plates={len(plates)}"
    )
    print_plates(plates)
    print_sim(sim)
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": "Icons.lod",
        "stem": args.stem,
        "evidence": "VERIFIED_LOCAL",
        "plates": plates,
        "simulation": sim,
        "note": (
            "Door maze, not InputString. Sequence is not checked. "
            "Full EVT bytecode stays gitignored."
        ),
    }
    if not args.dry_run:
        args.reports_dir.mkdir(parents=True, exist_ok=True)
        path = args.reports_dir / "plates_d01.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"index {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
