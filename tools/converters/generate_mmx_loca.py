"""Generate mod/Localisation overlay from registry + catalog.

Does not write into the game install. Default is --dry-run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mmx_ids import AllocError, find_child, scan_namespace
from mmx_loca import (
    LANGS,
    catalog_for_lang,
    load_json,
    loca_keys,
    parse_loca_ids,
    render_loca,
    run_self_test,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE / "id_registry.json"
DEFAULT_CATALOG = HERE / "loca_catalog.json"
DEFAULT_OUT = REPO_ROOT / "mod" / "Localisation"
ENV_PATH_KEY = "MMX_GAME_PATH"

sys.path.insert(0, str(TOOLS / "modding"))
from mmx_mod import (  # noqa: E402
    env_game_path,
    load_env,
    resolve_data_dir,
)


def vanilla_loca_ids(game_path: Path) -> set[str]:
    data = resolve_data_dir(game_path)
    assets = find_child(data, "StreamingAssets")
    if assets is None:
        raise AllocError("нет StreamingAssets")
    found = scan_namespace(assets, "loca")
    return {str(item) for item in found}


def write_lang(
    out_dir: Path,
    lang: str,
    xml_text: str,
) -> Path:
    folder = out_dir / lang
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "loca.xml"
    path.write_text(xml_text, encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_mmx_loca.py",
        description="MM6X loca overlay (en/ru). Game install is not patched.",
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
        help="loca_catalog.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда писать Localisation/<lang>/loca.xml.",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"MMX для проверки коллизий. Иначе {ENV_PATH_KEY}.",
    )
    parser.add_argument(
        "--check-vanilla",
        action="store_true",
        help="Сверить ключи с vanilla loca (нужен MMX).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файлы не писать.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать overlay в mod/Localisation.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Проверка escape/XML без файлов игры.",
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
        keys = loca_keys(registry)
        if not keys:
            raise ValueError("в registry нет loca-ключей")
        if args.check_vanilla:
            game_path = args.game_path or env_game_path()
            if game_path is None:
                raise AllocError(
                    f"нужен --game-path или {ENV_PATH_KEY}"
                )
            vanilla = vanilla_loca_ids(game_path.expanduser())
            clash = [key for key in keys if key in vanilla]
            if clash:
                raise AllocError(
                    "ключи уже в vanilla: " + ", ".join(clash)
                )
        payloads: dict[str, str] = {}
        for lang in LANGS:
            rows = catalog_for_lang(catalog, keys, lang)
            xml_text = render_loca(rows)
            parsed = parse_loca_ids(xml_text)
            if parsed != keys:
                raise ValueError(f"{lang}: набор ключей не совпал")
            payloads[lang] = xml_text
    except (OSError, ValueError, AllocError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"OK keys={len(keys)} langs={','.join(LANGS)}")
    for key in keys:
        print(f"  {key}")
    if args.dry_run:
        print("dry-run: loca not written")
        return 0
    for lang, xml_text in payloads.items():
        path = write_lang(args.output_dir, lang, xml_text)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
