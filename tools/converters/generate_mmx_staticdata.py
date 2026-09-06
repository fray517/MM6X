"""Generate mod/StaticData CSV overlay from catalog + registry.

Does not write into the game install. Default is --dry-run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mmx_ids import AllocError, find_child
from mmx_staticdata import (
    TABLES,
    StaticDataError,
    build_tables,
    load_json,
    parse_csv_data,
    run_self_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE / "id_registry.json"
DEFAULT_CATALOG = HERE / "staticdata_catalog.json"
DEFAULT_OUT = REPO_ROOT / "mod" / "StaticData"
ENV_PATH_KEY = "MMX_GAME_PATH"

sys.path.insert(0, str(TOOLS / "modding"))
from mmx_mod import (  # noqa: E402
    env_game_path,
    load_env,
    resolve_data_dir,
)


def vanilla_headers(game_path: Path) -> dict[str, list[str]]:
    data = resolve_data_dir(game_path)
    assets = find_child(data, "StreamingAssets")
    static = find_child(assets, "StaticData") if assets else None
    if static is None:
        raise AllocError("нет StaticData")
    found: dict[str, list[str]] = {}
    for name in TABLES:
        path = find_child(static, name)
        if path is None or not path.is_file():
            raise AllocError(f"нет vanilla {name}")
        header, _ = parse_csv_data(
            path.read_text(encoding="utf-8-sig")
        )
        found[name] = header
    return found


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_mmx_staticdata.py",
        description=(
            "MM6X StaticData CSV overlay. Game install is not patched."
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="id_registry.json",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="staticdata_catalog.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда писать StaticData/*.csv",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"MMX для сверки header. Иначе {ENV_PATH_KEY}.",
    )
    parser.add_argument(
        "--check-vanilla",
        action="store_true",
        help="Сверить header с vanilla CSV.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файлы не писать.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать overlay в mod/StaticData.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Синтетический CSV без файлов игры.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        print("self-test OK")
        return 0
    if args.write and args.dry_run:
        print("Укажите либо --write, либо --dry-run.", file=sys.stderr)
        return 2
    if not args.write:
        args.dry_run = True
    if not args.registry.is_file() or not args.catalog.is_file():
        print("Нет registry или catalog.", file=sys.stderr)
        return 2
    try:
        registry = load_json(args.registry)
        catalog = load_json(args.catalog)
        payloads = build_tables(registry, catalog)
        if args.check_vanilla:
            game_path = args.game_path or env_game_path()
            if game_path is None:
                raise AllocError(
                    f"нужен --game-path или {ENV_PATH_KEY}"
                )
            headers = vanilla_headers(game_path.expanduser())
            for name, text in payloads.items():
                ours, _ = parse_csv_data(text)
                if ours != headers[name]:
                    raise StaticDataError(
                        f"{name}: header не совпал с vanilla"
                    )
        for name, text in payloads.items():
            header, rows = parse_csv_data(text)
            print(f"OK {name} cols={len(header)} rows={len(rows)}")
            for row in rows:
                print(f"  id={row[0]}")
    except (OSError, StaticDataError, AllocError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.dry_run:
        print("dry-run: StaticData not written")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, text in payloads.items():
        path = args.output_dir / name
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
