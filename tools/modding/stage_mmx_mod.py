"""Stage / restore MM6X overlay into MMX install (merge + backup).

Default is --dry-run. Real write needs --stage/--restore and
--yes-i-understand. Partial loca/CSV are merged into vanilla files.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "converters"))
sys.path.insert(0, str(TOOLS / "modding"))

from mmx_mod import (  # noqa: E402
    env_game_path,
    load_env,
    resolve_data_dir,
    sha256_file,
)
from mmx_stage import (  # noqa: E402
    StageError,
    apply_actions,
    plan_from_manifest,
    restore_actions,
    run_self_test,
    write_json,
)

DEFAULT_MOD = REPO_ROOT / "mod"
DEFAULT_BACKUP = REPO_ROOT / "backups" / "mmx" / "mm6x-overlay"
ENV_PATH_KEY = "MMX_GAME_PATH"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stage_mmx_mod.py",
        description=(
            "Merge MM6X mod/ into MMX StreamingAssets. "
            "Default: dry-run."
        ),
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"MMX install. Иначе {ENV_PATH_KEY}.",
    )
    parser.add_argument(
        "--mod-dir",
        type=Path,
        default=DEFAULT_MOD,
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="build_manifest.json (default: mod/…).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="План без записи (по умолчанию).",
    )
    mode.add_argument(
        "--stage",
        action="store_true",
        help="Merge overlay в игру.",
    )
    mode.add_argument(
        "--restore",
        action="store_true",
        help="Откат из backup.",
    )
    mode.add_argument(
        "--status",
        action="store_true",
        help="Есть ли apply.json / backup.",
    )
    mode.add_argument(
        "--self-test",
        action="store_true",
    )
    parser.add_argument(
        "--yes-i-understand",
        action="store_true",
        help="Разрешить запись в установку MMX.",
    )
    return parser


def resolve_game(args: argparse.Namespace) -> Path:
    load_env(REPO_ROOT)
    game = args.game_path or env_game_path()
    if game is None:
        raise StageError(
            f"Укажите --game-path или {ENV_PATH_KEY} в .env"
        )
    if not game.is_dir():
        raise StageError(f"нет каталога игры: {game}")
    return game


def cmd_status(backup_dir: Path) -> int:
    apply_path = backup_dir / "apply.json"
    files_dir = backup_dir / "files"
    if not apply_path.is_file():
        print(f"NO_APPLY {backup_dir}")
        return 0
    doc = json.loads(apply_path.read_text(encoding="utf-8"))
    n = len(doc.get("actions") or [])
    print(f"STAGED actions={n} backup={backup_dir}")
    if files_dir.is_dir():
        print(f"  files={len(list(files_dir.iterdir()))}")
    created = doc.get("created_utc")
    if created:
        print(f"  created_utc={created}")
    return 0


def print_plan(actions: list[dict]) -> None:
    for action in actions:
        mode = action.get("mode")
        existed = action.get("existed")
        print(
            f"  [{action['kind']}] {mode} "
            f"{action['stage_rel']} existed={existed}"
        )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        with tempfile.TemporaryDirectory() as tmp:
            run_self_test(Path(tmp))
        print("self-test OK")
        return 0

    if args.status:
        return cmd_status(args.backup_dir)

    if not (
        args.dry_run
        or args.stage
        or args.restore
    ):
        args.dry_run = True

    writing = bool(
        (args.stage or args.restore) and args.yes_i_understand
    )
    if (args.stage or args.restore) and not args.yes_i_understand:
        print(
            "без --yes-i-understand: только план (dry-run)"
        )

    try:
        game = resolve_game(args)
        data_dir = resolve_data_dir(game)
    except (StageError, FileNotFoundError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.restore:
        apply_path = args.backup_dir / "apply.json"
        if not apply_path.is_file():
            print(f"нет {apply_path}", file=sys.stderr)
            return 2
        try:
            doc = json.loads(
                apply_path.read_text(encoding="utf-8")
            )
            logs = restore_actions(
                apply_doc=doc,
                backup_dir=args.backup_dir,
                dry_run=not writing,
            )
        except (OSError, json.JSONDecodeError, StageError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        for line in logs:
            print(line)
        if not writing:
            print("dry-run: restore not applied")
        else:
            # Clear backup so a following --stage can run.
            import shutil

            if args.backup_dir.is_dir():
                shutil.rmtree(args.backup_dir)
            print("OK restore")
            print(f"cleared backup {args.backup_dir}")
        return 0

    if args.dry_run and not args.stage:
        # fall through to plan with dry
        pass

    manifest_path = args.manifest or (
        args.mod_dir / "build_manifest.json"
    )
    if not manifest_path.is_file():
        print(f"нет manifest: {manifest_path}", file=sys.stderr)
        return 2
    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        actions = plan_from_manifest(
            args.mod_dir,
            manifest,
            data_dir,
        )
    except (OSError, json.JSONDecodeError, StageError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"plan actions={len(actions)} game={game}")
    print_plan(actions)

    try:
        # dry_run=True: merge in memory, no disk writes
        apply_actions(
            actions=actions,
            mod_dir=args.mod_dir,
            backup_dir=args.backup_dir,
            dry_run=True,
        )
    except (OSError, StageError) as exc:
        print(f"FAIL merge preview: {exc}", file=sys.stderr)
        return 1

    if not writing:
        print("dry-run: game not modified")
        return 0

    apply_path = args.backup_dir / "apply.json"
    if apply_path.is_file():
        print(
            "Backup уже есть. Сначала --restore, "
            "или удалите backups/mmx/mm6x-overlay.",
            file=sys.stderr,
        )
        return 2

    try:
        apply_doc = apply_actions(
            actions=actions,
            mod_dir=args.mod_dir,
            backup_dir=args.backup_dir,
            dry_run=False,
        )
        apply_doc["created_utc"] = utc_now()
        apply_doc["game_path"] = str(game)
        apply_doc["manifest"] = str(manifest_path)
        apply_doc["manifest_sha256"] = sha256_file(manifest_path)
        write_json(apply_path, apply_doc)
    except (OSError, StageError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"OK stage backup={args.backup_dir}")
    print(f"  apply={apply_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
