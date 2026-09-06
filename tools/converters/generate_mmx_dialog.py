"""Generate mod/Dialog/*.xml from dialog_catalog + id_registry.

Does not write into the game install. Default is --dry-run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mmx_dialog import (
    DialogError,
    dialog_names,
    load_json,
    parse_dialog_root,
    render_npc_dialog,
    run_self_test,
)
from mmx_ids import AllocError, find_child, scan_namespace

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
DEFAULT_REGISTRY = HERE / "id_registry.json"
DEFAULT_CATALOG = HERE / "dialog_catalog.json"
DEFAULT_OUT = REPO_ROOT / "mod" / "Dialog"
ENV_PATH_KEY = "MMX_GAME_PATH"

sys.path.insert(0, str(TOOLS / "modding"))
from mmx_mod import (  # noqa: E402
    env_game_path,
    load_env,
    resolve_data_dir,
)


def dialog_stems(game_path: Path) -> set[str]:
    data = resolve_data_dir(game_path)
    assets = find_child(data, "StreamingAssets")
    dialog = find_child(assets, "Dialog") if assets else None
    if dialog is None:
        return set()
    return scan_namespace(assets, "dialog")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_mmx_dialog.py",
        description="MM6X Dialog XML overlay. Game install is not patched.",
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
        help="dialog_catalog.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда писать Dialog/*.xml",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"MMX для проверки имён файлов. Иначе {ENV_PATH_KEY}.",
    )
    parser.add_argument(
        "--check-vanilla",
        action="store_true",
        help="Сверить ConversationKey с vanilla Dialog/*.xml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только сводка; файлы не писать.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать overlay в mod/Dialog.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Проверка XML/ref без файлов игры.",
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
        names = dialog_names(catalog)
        dialogs = catalog["dialogs"]
        if args.check_vanilla:
            game_path = args.game_path or env_game_path()
            if game_path is None:
                raise AllocError(
                    f"нужен --game-path или {ENV_PATH_KEY}"
                )
            vanilla = {str(x) for x in dialog_stems(game_path)}
            clash = [name for name in names if name in vanilla]
            if clash:
                raise AllocError(
                    "имя уже в vanilla Dialog: " + ", ".join(clash)
                )
        payloads: dict[str, str] = {}
        for name in names:
            spec = dialogs[name]
            xml_text = render_npc_dialog(registry, spec)
            root = parse_dialog_root(xml_text)
            if root.get("rootDialogID") != str(
                spec.get("rootDialogID", 1)
            ):
                raise DialogError(f"{name}: rootDialogID не совпал")
            payloads[name] = xml_text
    except (OSError, DialogError, AllocError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"OK dialogs={len(names)}")
    for name in names:
        print(f"  {name}.xml")
    if args.dry_run:
        print("dry-run: dialog not written")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, xml_text in payloads.items():
        path = args.output_dir / f"{name}.xml"
        path.write_text(xml_text, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
