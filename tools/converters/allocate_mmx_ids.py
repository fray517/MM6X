"""Assign unused MMX target IDs into id_registry.json.

Does not write into the game. Default is --dry-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mmx_ids import (
    BAND_CEIL,
    BAND_FLOOR,
    NAMESPACES,
    AllocError,
    find_child,
    next_free,
    run_self_test,
    scan_namespace,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = Path(__file__).resolve().parent / "id_registry.json"
ENV_PATH_KEY = "MMX_GAME_PATH"

sys.path.insert(0, str(TOOLS / "modding"))
from mmx_mod import (  # noqa: E402
    env_game_path,
    load_env,
    resolve_data_dir,
)


def streaming_assets(game_path: Path) -> Path:
    data = resolve_data_dir(game_path)
    assets = find_child(data, "StreamingAssets")
    if assets is None or not assets.is_dir():
        raise AllocError("нет StreamingAssets")
    return assets


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_all(assets: Path) -> dict[str, set[Any]]:
    used: dict[str, set[Any]] = {}
    for namespace in NAMESPACES:
        used[namespace] = scan_namespace(assets, namespace)
    return used


def _fold(values: set[Any]) -> set[str]:
    return {str(item).casefold() for item in values}


def allocate(
    registry: dict[str, Any],
    used: dict[str, set[Any]],
) -> list[str]:
    """Fill unassigned int slots. Check string collisions. Mutates registry."""
    changes: list[str] = []
    band = registry.get("id_band") or {}
    floor = int(band.get("floor", BAND_FLOOR))
    ceil = int(band.get("ceil", BAND_CEIL))
    if floor != BAND_FLOOR or ceil != BAND_CEIL:
        raise AllocError("id_band не совпадает с mmx_ids")
    ours: dict[str, set[Any]] = {name: set() for name in NAMESPACES}
    for entry in registry.get("entries") or []:
        stable = entry.get("stable_id")
        for slot in entry.get("slots") or []:
            namespace = slot.get("namespace")
            value = slot.get("value")
            if namespace not in NAMESPACES:
                raise AllocError(f"{stable}: namespace {namespace}")
            kind = NAMESPACES[namespace]["kind"]
            vanilla = used[namespace]
            if value is None:
                if kind != "int":
                    continue
                if slot.get("status") != "unassigned":
                    continue
                taken = set(vanilla) | ours[namespace]
                assigned = next_free(taken, floor)
                slot["value"] = assigned
                slot["status"] = "reserved"
                ours[namespace].add(assigned)
                changes.append(
                    f"{stable} {namespace}={assigned}"
                )
                continue
            if kind == "int":
                number = int(value)
                if number in vanilla:
                    raise AllocError(
                        f"{stable} {namespace}={number} занят vanilla"
                    )
                if number < floor or number > ceil:
                    raise AllocError(
                        f"{stable} {namespace}={number} вне полосы"
                    )
                if number in ours[namespace]:
                    raise AllocError(
                        f"{stable} {namespace}={number} дубликат"
                    )
                ours[namespace].add(number)
                continue
            text = str(value)
            if text.casefold() in _fold(vanilla):
                raise AllocError(
                    f"{stable} {namespace}={text!r} занят vanilla"
                )
            if text.casefold() in _fold(ours[namespace]):
                raise AllocError(
                    f"{stable} {namespace}={text!r} дубликат"
                )
            ours[namespace].add(text)
    return changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="allocate_mmx_ids.py",
        description="Reserve unused MMX IDs for MM6X slice entities.",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"Каталог MMX. Иначе {ENV_PATH_KEY} из .env.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="id_registry.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать назначения, файл не писать.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать reserved ID в registry.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Синтетический next_free без игры.",
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
    if not args.registry.is_file():
        print(f"Нет registry: {args.registry}", file=sys.stderr)
        return 2
    try:
        assets = streaming_assets(game_path)
        used = scan_all(assets)
        registry = load_registry(args.registry)
        changes = allocate(registry, used)
    except (AllocError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not changes:
        print("OK no new IDs (already reserved)")
    else:
        print(f"OK assign {len(changes)}")
        for line in changes:
            print(f"  {line}")
    if args.dry_run:
        print("dry-run: registry not written")
        return 0
    args.registry.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.registry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
