"""CLI: generate mod/Maps/New_Sorpigal.xml greybox.

Does not write into the game install. Default is --dry-run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mmx_map import (
    DEFAULT_SKETCH,
    MapGenError,
    load_json,
    render_grid_xml,
    run_self_test,
    summarize,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "mod" / "Maps" / "New_Sorpigal.xml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_mmx_map.py",
        description=(
            "New_Sorpigal greybox Grid XML from grid_sketch. "
            "Game install is not patched."
        ),
    )
    parser.add_argument(
        "--sketch",
        type=Path,
        default=DEFAULT_SKETCH,
        help="new_sorpigal.grid_sketch.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда писать Maps/*.xml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файл не писать.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать XML в mod/Maps/.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Проверки генератора без записи.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        try:
            run_self_test()
        except (OSError, MapGenError, AssertionError) as exc:
            print(f"self-test FAIL: {exc}", file=sys.stderr)
            return 1
        print("self-test OK")
        return 0

    if args.write and args.dry_run:
        print(
            "Укажите либо --write, либо --dry-run.",
            file=sys.stderr,
        )
        return 2
    if not args.write:
        args.dry_run = True

    if not args.sketch.is_file():
        print(f"нет sketch: {args.sketch}", file=sys.stderr)
        return 2

    try:
        sketch = load_json(args.sketch)
        xml = render_grid_xml(sketch)
        info = summarize(sketch, xml)
    except (OSError, MapGenError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(
        f"OK {info['name']} {info['width']}x{info['height']} "
        f"passable={info['passable']} blocked={info['blocked']} "
        f"corridor≈{info['corridor_steps']} "
        f"bytes={info['xml_bytes']}"
    )
    print(f"  party=({info['party']['x']},{info['party']['y']})")
    print(f"  triggers={', '.join(info['triggers'])}")

    if args.dry_run:
        print("dry-run: map not written")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 without BOM (Cave1 style). VERIFIED_LOCAL Cave1.
    args.output.write_text(xml, encoding="utf-8", newline="\n")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
