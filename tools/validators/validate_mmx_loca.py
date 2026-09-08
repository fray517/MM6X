"""Validate MM6X localisation overlay (en/ru parity + refs).

Checks catalog ↔ mod/Localisation, dialog/map/StaticData refs,
optional vanilla key collision. Does not write into the game.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOLS / "converters"))
sys.path.insert(0, str(TOOLS / "modding"))

from mmx_ids import AllocError  # noqa: E402
from mmx_loca import (  # noqa: E402
    LANGS,
    catalog_for_lang,
    load_json,
    merge_loca_keys,
    parse_loca_ids,
)
from mmx_mod import env_game_path, load_env, resolve_data_dir  # noqa: E402
from mmx_ids import find_child, scan_namespace  # noqa: E402

DEFAULT_REGISTRY = TOOLS / "converters" / "id_registry.json"
DEFAULT_CATALOG = TOOLS / "converters" / "loca_catalog.json"
DEFAULT_DIALOG_CATALOG = TOOLS / "converters" / "dialog_catalog.json"
DEFAULT_SD_CATALOG = TOOLS / "converters" / "staticdata_catalog.json"
DEFAULT_MOD = REPO_ROOT / "mod"
ENV_PATH_KEY = "MMX_GAME_PATH"

SIGN_RE = re.compile(r"SIGN_MM6_[A-Z0-9_]+")
LOCA_KEY_RE = re.compile(r'locaKey="([^"]+)"')


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def walk_dialog_loca(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        key = node.get("locaKey")
        if isinstance(key, str) and key:
            out.add(key)
        for value in node.values():
            walk_dialog_loca(value, out)
    elif isinstance(node, list):
        for item in node:
            walk_dialog_loca(item, out)


def map_loca_keys(map_xml: str) -> set[str]:
    found = set(SIGN_RE.findall(map_xml))
    for match in re.finditer(
        r"<LocationLocaName>([^<]+)</LocationLocaName>",
        map_xml,
    ):
        found.add(match.group(1).strip())
    return {key for key in found if key}


def staticdata_loca_keys(catalog: dict[str, Any]) -> set[str]:
    """Collect loca-like strings from known StaticData columns."""
    keys: set[str] = set()
    loca_fields = {
        "NameKey",
        "Name",
        "FlavorDescription",
        "ShortDescription",
        "Description",
        "TitleKey",
        "TextKey",
        "AuthorKey",
        "Location",
    }
    tables = catalog.get("tables") or {}
    for table in tables.values():
        for row in table.get("rows") or []:
            if not isinstance(row, dict):
                continue
            for field in loca_fields:
                value = row.get(field)
                if isinstance(value, str) and value.startswith(
                    (
                        "NPC_NAME_",
                        "TOKEN_",
                        "QUEST_",
                        "LOCATION_",
                        "LOREBOOK_",
                        "DIALOG_",
                        "SIGN_",
                        "WORLDMAP_",
                    )
                ):
                    keys.add(value)
    return keys


def validate_loca(
    *,
    registry: dict[str, Any],
    catalog: dict[str, Any],
    dialog_catalog: dict[str, Any],
    sd_catalog: dict[str, Any],
    mod_dir: Path,
    vanilla_ids: set[str] | None,
) -> list[str]:
    errors: list[str] = []
    try:
        keys = merge_loca_keys(registry, catalog)
    except ValueError as exc:
        return [f"catalog: {exc}"]
    if not keys:
        return ["нет loca-ключей"]

    key_set = set(keys)
    for lang in LANGS:
        try:
            rows = catalog_for_lang(catalog, keys, lang)
        except ValueError as exc:
            _err(errors, f"catalog/{lang}: {exc}")
            continue
        for key, text in rows:
            if not text.strip():
                _err(errors, f"{lang}/{key}: пустая строка")

        path = mod_dir / "Localisation" / lang / "loca.xml"
        if not path.is_file():
            _err(errors, f"нет {path}")
            continue
        try:
            disk = parse_loca_ids(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _err(errors, f"{lang}: {exc}")
            continue
        if disk != keys:
            missing = sorted(key_set - set(disk))
            extra = sorted(set(disk) - key_set)
            if missing:
                _err(
                    errors,
                    f"{lang}: нет на диске {', '.join(missing)}",
                )
            if extra:
                _err(
                    errors,
                    f"{lang}: лишние {', '.join(extra)}",
                )

    en_path = mod_dir / "Localisation" / "en" / "loca.xml"
    ru_path = mod_dir / "Localisation" / "ru" / "loca.xml"
    if en_path.is_file() and ru_path.is_file():
        en_ids = parse_loca_ids(en_path.read_text(encoding="utf-8"))
        ru_ids = parse_loca_ids(ru_path.read_text(encoding="utf-8"))
        if en_ids != ru_ids:
            _err(errors, "en/ru: разный набор ключей")

    dialogs = dialog_catalog.get("dialogs") or {}
    for name, tree in dialogs.items():
        used: set[str] = set()
        walk_dialog_loca(tree, used)
        missing = sorted(used - key_set)
        if missing:
            _err(
                errors,
                f"dialog {name}: нет loca {', '.join(missing)}",
            )

    map_path = mod_dir / "Maps" / "New_Sorpigal.xml"
    if map_path.is_file():
        used_map = map_loca_keys(map_path.read_text(encoding="utf-8"))
        missing = sorted(used_map - key_set)
        if missing:
            _err(
                errors,
                f"map: нет loca {', '.join(missing)}",
            )
    gw_path = mod_dir / "Maps" / "Goblinwatch.xml"
    if gw_path.is_file():
        used_gw = map_loca_keys(gw_path.read_text(encoding="utf-8"))
        missing_gw = sorted(used_gw - key_set)
        if missing_gw:
            _err(
                errors,
                f"Goblinwatch map: нет loca "
                f"{', '.join(missing_gw)}",
            )

    sd_keys = staticdata_loca_keys(sd_catalog)
    missing_sd = sorted(sd_keys - key_set)
    if missing_sd:
        _err(
            errors,
            f"staticdata catalog: нет loca "
            f"{', '.join(missing_sd)}",
        )

    if vanilla_ids is not None:
        clash = sorted(key_set & vanilla_ids)
        if clash:
            _err(
                errors,
                "коллизия с vanilla: " + ", ".join(clash),
            )

    return errors


def run_self_test() -> None:
    catalog = {
        "strings": {
            "A": {"en": "a", "ru": "а"},
            "B": {"en": "b", "ru": "б"},
        }
    }
    registry = {
        "entries": [
            {
                "slots": [
                    {"namespace": "loca", "value": "A"},
                ]
            }
        ]
    }
    keys = merge_loca_keys(registry, catalog)
    assert keys == ["A", "B"]
    assert map_loca_keys(
        "<LocationLocaName>LOCATION_X</LocationLocaName>"
        "SIGN_MM6_FOO"
    ) == {"LOCATION_X", "SIGN_MM6_FOO"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_mmx_loca.py",
        description="MM6X loca en/ru + refs (game not patched).",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
    )
    parser.add_argument(
        "--dialog-catalog",
        type=Path,
        default=DEFAULT_DIALOG_CATALOG,
    )
    parser.add_argument(
        "--staticdata-catalog",
        type=Path,
        default=DEFAULT_SD_CATALOG,
    )
    parser.add_argument(
        "--mod-dir",
        type=Path,
        default=DEFAULT_MOD,
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"MMX для --check-vanilla. Иначе {ENV_PATH_KEY}.",
    )
    parser.add_argument(
        "--check-vanilla",
        action="store_true",
        help="Проверить коллизии ключей с vanilla loca.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Печатать все ключи.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
    if args.self_test:
        try:
            run_self_test()
        except AssertionError as exc:
            print(f"self-test FAIL: {exc}", file=sys.stderr)
            return 1
        print("self-test OK")
        return 0

    for path in (
        args.registry,
        args.catalog,
        args.dialog_catalog,
        args.staticdata_catalog,
    ):
        if not path.is_file():
            print(f"нет файла: {path}", file=sys.stderr)
            return 2

    try:
        registry = load_json(args.registry)
        catalog = load_json(args.catalog)
        dialog_cat = load_json(args.dialog_catalog)
        sd_cat = load_json(args.staticdata_catalog)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"JSON: {exc}", file=sys.stderr)
        return 1

    vanilla: set[str] | None = None
    if args.check_vanilla:
        try:
            game = args.game_path or env_game_path()
            if game is None:
                raise AllocError(
                    f"нужен --game-path или {ENV_PATH_KEY}"
                )
            data = resolve_data_dir(game.expanduser())
            assets = find_child(data, "StreamingAssets")
            if assets is None:
                raise AllocError("нет StreamingAssets")
            found = scan_namespace(assets, "loca")
            vanilla = {str(item) for item in found}
        except AllocError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    errors = validate_loca(
        registry=registry,
        catalog=catalog,
        dialog_catalog=dialog_cat,
        sd_catalog=sd_cat,
        mod_dir=args.mod_dir,
        vanilla_ids=vanilla,
    )
    keys = merge_loca_keys(registry, catalog)
    if args.list:
        for key in keys:
            print(key)
    if errors:
        print(f"FAIL ({len(errors)})", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    print(
        f"OK loca keys={len(keys)} en/ru "
        f"dialog+map+staticdata"
        + (" vanilla_ok" if args.check_vanilla else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
