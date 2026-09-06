"""CLI: build or verify mod/build_manifest.json.

Does not write into the game install. Default is --dry-run.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from mmx_manifest import (
    ManifestError,
    build_manifest,
    run_self_test,
    verify_manifest,
    write_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOD = REPO_ROOT / "mod"
DEFAULT_OUT = DEFAULT_MOD / "build_manifest.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_mmx_manifest.py",
        description=(
            "MM6X build_manifest.json (hashes). Game is not patched."
        ),
    )
    parser.add_argument(
        "--mod-dir",
        type=Path,
        default=DEFAULT_MOD,
        help="Корень staged mod/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Куда писать JSON. По умолчанию mod/build_manifest.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файл не писать.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать build_manifest.json.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Сверить существующий manifest с диском.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Юнит-проверки во временной папке.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        with tempfile.TemporaryDirectory() as tmp:
            run_self_test(Path(tmp))
        print("self-test OK")
        return 0

    modes = sum(bool(x) for x in (args.dry_run, args.write, args.check))
    if modes == 0:
        args.dry_run = True
    if modes > 1:
        print(
            "Укажите только один режим: --dry-run / --write / --check",
            file=sys.stderr,
        )
        return 2

    out = args.output or (args.mod_dir / "build_manifest.json")

    if args.check:
        if not out.is_file():
            print(f"нет manifest: {out}", file=sys.stderr)
            return 2
        try:
            payload = json.loads(out.read_text(encoding="utf-8"))
            errors = verify_manifest(args.mod_dir, payload)
        except (OSError, json.JSONDecodeError, ManifestError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        if errors:
            print(f"FAIL ({len(errors)})", file=sys.stderr)
            for item in errors:
                print(f"  {item}", file=sys.stderr)
            return 1
        count = len(payload.get("files") or [])
        print(f"OK check {out} files={count}")
        return 0

    try:
        payload = build_manifest(args.mod_dir)
    except ManifestError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    counts = payload.get("counts") or {}
    summary = ", ".join(
        f"{key}={counts[key]}" for key in sorted(counts)
    )
    print(f"OK files={len(payload['files'])} ({summary})")
    for item in payload["files"]:
        print(f"  {item['path']}  {item['sha256'][:12]}…")

    if args.dry_run:
        print("dry-run: build_manifest.json not written")
        return 0

    write_manifest(out, payload)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
