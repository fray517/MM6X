"""Safe backup/restore and one-entry Russian localisation test.

The only game file this tool may write is ru/loca.xml, and only after
--yes-i-understand. Backups live in the MM6X repo, not in the install.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MMX_GAME_PATH"
DATA_DIR_NAME = "Might and Magic X Legacy_Data"
LOCA_REL_PARTS = (
    "StreamingAssets",
    "Localisation",
    "ru",
    "loca.xml",
)
TEST_KEY = "Gui/Mainmenu/Options"
TEST_PREFIX = "MM6X TEST \u2014 "
CHUNK_SIZE = 1024 * 1024
DEFAULT_BACKUP_DIR = REPO_ROOT / "backups" / "mmx" / "loca-ru"
REPORTS_DIR = REPO_ROOT / "reports"


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
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def env_game_path() -> Path | None:
    raw = os.environ.get(ENV_PATH_KEY, "").strip().strip('"')
    if not raw:
        return None
    return Path(raw)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def resolve_data_dir(game_path: Path) -> Path:
    exact = find_child(game_path, DATA_DIR_NAME)
    if exact is not None and exact.is_dir():
        return exact
    raise FileNotFoundError(
        f"Не найден каталог '{DATA_DIR_NAME}' в {game_path}"
    )


def resolve_loca(game_path: Path) -> Path:
    current = resolve_data_dir(game_path)
    for part in LOCA_REL_PARTS:
        nxt = find_child(current, part)
        if nxt is None:
            raise FileNotFoundError(
                f"Не найден '{part}' относительно {current}"
            )
        current = nxt
    if not current.is_file():
        raise FileNotFoundError(f"Нет файла: {current}")
    return current.resolve()


def assert_allowed_loca(game_path: Path, target: Path) -> None:
    try:
        rel = target.resolve().relative_to(game_path.resolve())
    except ValueError as exc:
        raise PermissionError(
            "Цель вне каталога игры; запись запрещена."
        ) from exc
    expected = Path(DATA_DIR_NAME, *LOCA_REL_PARTS)
    if rel.as_posix().casefold() != expected.as_posix().casefold():
        raise PermissionError(
            "Разрешён только ru/loca.xml. "
            f"Получено: {rel.as_posix()}"
        )


def read_text_preserve(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    has_bom = data.startswith(b"\xef\xbb\xbf")
    return data.decode("utf-8-sig"), has_bom


def encode_text(text: str, has_bom: bool) -> bytes:
    payload = text.encode("utf-8")
    if has_bom:
        payload = b"\xef\xbb\xbf" + payload
    return payload


def loca_inner_xml(text: str, key: str) -> str:
    start_tag = f'<LocaData id="{key}">'
    start = text.find(start_tag)
    if start < 0:
        raise KeyError(f"Ключ не найден: {key}")
    value_start = start + len(start_tag)
    value_end = text.find("</LocaData>", value_start)
    if value_end < 0:
        raise ValueError(f"Нет закрывающего тега для {key}")
    inner = text[value_start:value_end]
    if "<" in inner:
        raise ValueError(f"Вложенная разметка у {key}, отказ.")
    return inner


def replace_loca_inner(text: str, key: str, new_inner: str) -> str:
    start_tag = f'<LocaData id="{key}">'
    start = text.find(start_tag)
    if start < 0:
        raise KeyError(f"Ключ не найден: {key}")
    if text.find(start_tag, start + 1) != -1:
        raise ValueError(f"Ключ встречается больше одного раза: {key}")
    value_start = start + len(start_tag)
    value_end = text.find("</LocaData>", value_start)
    if value_end < 0:
        raise ValueError(f"Нет закрывающего тега для {key}")
    return text[:value_start] + new_inner + text[value_end:]


def count_loca_entries(text: str) -> int:
    root = ET.fromstring(text)
    return sum(1 for child in root if child.tag == "LocaData")


def proposed_value(original_inner: str) -> str:
    if original_inner.startswith(TEST_PREFIX):
        return original_inner
    return TEST_PREFIX + original_inner


def backup_paths(backup_dir: Path) -> tuple[Path, Path]:
    return backup_dir / "loca.xml", backup_dir / "manifest.json"


def load_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def classify_state(
    current_sha: str,
    original_inner: str,
    backup_sha: str | None,
) -> str:
    if backup_sha is None:
        if original_inner.startswith(TEST_PREFIX):
            return "TEST_PATCHED"
        return "NO_BACKUP"
    if current_sha == backup_sha:
        return "ORIGINAL"
    if original_inner.startswith(TEST_PREFIX):
        return "TEST_PATCHED"
    return "UNKNOWN"


def cmd_backup(
    loca: Path,
    backup_dir: Path,
    force: bool,
) -> int:
    copy_path, manifest_path = backup_paths(backup_dir)
    if copy_path.exists() or manifest_path.exists():
        if not force:
            print(
                "Backup уже есть. Повторная запись только с --force.\n"
                f"  {backup_dir}",
                file=sys.stderr,
            )
            return 2
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive = backup_dir.parent / f"{backup_dir.name}.{stamp}"
        backup_dir.rename(archive)
        print(f"Прежний backup сохранён: {archive}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    data = loca.read_bytes()
    copy_path.write_bytes(data)
    digest = sha256_bytes(data)
    if sha256_file(copy_path) != digest:
        print("Backup повреждён сразу после записи.", file=sys.stderr)
        return 1
    manifest = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "relative_target": (
            Path(DATA_DIR_NAME, *LOCA_REL_PARTS).as_posix()
        ),
        "size": len(data),
        "sha256": digest,
        "test_key": TEST_KEY,
        "read_only_source": True,
    }
    write_json(manifest_path, manifest)
    print(f"Backup: {copy_path}")
    print(f"SHA-256: {digest}")
    print(f"Manifest: {manifest_path}")
    return 0


def cmd_status(
    loca: Path,
    backup_dir: Path,
) -> int:
    current_sha = sha256_file(loca)
    text, _ = read_text_preserve(loca)
    inner = loca_inner_xml(text, TEST_KEY)
    copy_path, manifest_path = backup_paths(backup_dir)
    manifest = load_manifest(manifest_path)
    backup_sha = None
    if copy_path.is_file():
        backup_sha = sha256_file(copy_path)
        if manifest and manifest.get("sha256") not in (None, backup_sha):
            print(
                "Внимание: SHA-256 копии и manifest не совпадают.",
                file=sys.stderr,
            )
    elif manifest:
        backup_sha = manifest.get("sha256")
    state = classify_state(current_sha, inner, backup_sha)
    payload = {
        "target": str(loca),
        "test_key": TEST_KEY,
        "current_sha256": current_sha,
        "original_backup_sha256": backup_sha,
        "state": state,
        "current_value": inner,
    }
    print(f"target: {loca}")
    print(f"key: {TEST_KEY}")
    print(f"current SHA-256: {current_sha}")
    print(f"backup SHA-256: {backup_sha or '—'}")
    print(f"state: {state}")
    print(f"value: {inner}")
    write_json(REPORTS_DIR / "loca_status.json", payload)
    return 0


def cmd_prepare(game_path: Path, loca: Path, backup_dir: Path) -> int:
    text, has_bom = read_text_preserve(loca)
    inner = loca_inner_xml(text, TEST_KEY)
    proposed = proposed_value(inner)
    current_sha = sha256_file(loca)
    copy_path, manifest_path = backup_paths(backup_dir)
    backup_sha = None
    if copy_path.is_file():
        backup_sha = sha256_file(copy_path)
    payload = {
        "dry_run": True,
        "modified_game": False,
        "test_key": TEST_KEY,
        "original_value": inner,
        "proposed_value": proposed,
        "source_game_path": str(game_path.resolve()),
        "target": str(loca),
        "backup_dir": str(backup_dir),
        "backup_present": copy_path.is_file(),
        "has_utf8_bom": has_bom,
        "current_sha256": current_sha,
        "backup_sha256": backup_sha,
        "why_safe": (
            "Кнопка главного меню «Параметры», не квест/NPC/предмет "
            "и не строка старта движка."
        ),
    }
    print("PREPARE (игра не изменяется)")
    print(f"  key: {TEST_KEY}")
    print(f"  original: {inner}")
    print(f"  proposed: {proposed}")
    print(f"  target: {loca}")
    print(f"  backup: {backup_dir}")
    print(f"  current SHA-256: {current_sha}")
    print(f"  backup SHA-256: {backup_sha or 'нет backup'}")
    write_json(REPORTS_DIR / "loca_prepare.json", payload)
    print(f"  report: {REPORTS_DIR / 'loca_prepare.json'}")
    return 0


def cmd_apply(
    loca: Path,
    backup_dir: Path,
    understand: bool,
) -> int:
    if not understand:
        print(
            "Отказ: нет --yes-i-understand. Файл игры не изменён.",
            file=sys.stderr,
        )
        return 2
    copy_path, manifest_path = backup_paths(backup_dir)
    if not copy_path.is_file() or not manifest_path.is_file():
        print("Сначала выполните backup.", file=sys.stderr)
        return 2
    original_bytes = copy_path.read_bytes()
    backup_sha = sha256_bytes(original_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != backup_sha:
        print("Manifest backup не совпадает с копией.", file=sys.stderr)
        return 1
    current_bytes = loca.read_bytes()
    current_sha = sha256_bytes(current_bytes)
    if current_sha != backup_sha:
        print(
            "Текущий loca.xml не совпадает с backup. Патч отказан.\n"
            f"  current: {current_sha}\n"
            f"  backup:  {backup_sha}",
            file=sys.stderr,
        )
        return 2
    text, has_bom = read_text_preserve(loca)
    before_count = count_loca_entries(text)
    inner = loca_inner_xml(text, TEST_KEY)
    if inner.startswith(TEST_PREFIX):
        print("Ключ уже пропатчен. Отказ.", file=sys.stderr)
        return 2
    new_inner = proposed_value(inner)
    patched = replace_loca_inner(text, TEST_KEY, new_inner)
    after_count = count_loca_entries(patched)
    if after_count != before_count:
        print("Число LocaData изменилось. Отказ.", file=sys.stderr)
        return 1
    if loca_inner_xml(patched, TEST_KEY) != new_inner:
        print("Патч не применился к ключу. Отказ.", file=sys.stderr)
        return 1
    out_bytes = encode_text(patched, has_bom)
    try:
        loca.write_bytes(out_bytes)
    except PermissionError:
        print(
            "Нет прав записи в Program Files. "
            "Запустите PowerShell от имени администратора.",
            file=sys.stderr,
        )
        return 1
    new_sha = sha256_file(loca)
    op = {
        "schema_version": 1,
        "operation": "apply-localisation-test",
        "created_utc": utc_now(),
        "test_key": TEST_KEY,
        "original_value": inner,
        "new_value": new_inner,
        "before_sha256": current_sha,
        "after_sha256": new_sha,
        "target_relative": Path(DATA_DIR_NAME, *LOCA_REL_PARTS).as_posix(),
        "backup_sha256": backup_sha,
    }
    write_json(backup_dir / "apply.json", op)
    write_json(REPORTS_DIR / "loca_apply.json", op)
    print("APPLY ok")
    print(f"  key: {TEST_KEY}")
    print(f"  new SHA-256: {new_sha}")
    print(f"  manifest: {backup_dir / 'apply.json'}")
    return 0


def cmd_restore(
    loca: Path,
    backup_dir: Path,
    understand: bool,
) -> int:
    if not understand:
        print(
            "Отказ: нет --yes-i-understand. Файл игры не изменён.",
            file=sys.stderr,
        )
        return 2
    copy_path, manifest_path = backup_paths(backup_dir)
    if not copy_path.is_file():
        print("Нет backup loca.xml.", file=sys.stderr)
        return 2
    original = copy_path.read_bytes()
    expected = sha256_bytes(original)
    manifest = load_manifest(manifest_path) or {}
    if manifest.get("sha256") not in (None, expected):
        print("Manifest SHA-256 не совпадает с копией.", file=sys.stderr)
        return 1
    try:
        loca.write_bytes(original)
    except PermissionError:
        print(
            "Нет прав записи в Program Files. "
            "Запустите PowerShell от имени администратора.",
            file=sys.stderr,
        )
        return 1
    restored = sha256_file(loca)
    ok = restored == expected
    op = {
        "schema_version": 1,
        "operation": "restore-localisation-test",
        "created_utc": utc_now(),
        "expected_sha256": expected,
        "restored_sha256": restored,
        "success": ok,
    }
    write_json(backup_dir / "restore.json", op)
    write_json(REPORTS_DIR / "loca_restore.json", op)
    if ok:
        print("RESTORE ok")
        print(f"  SHA-256: {restored}")
        return 0
    print("RESTORE FAILED: хеш не совпал с backup.", file=sys.stderr)
    print(f"  expected: {expected}")
    print(f"  actual:   {restored}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mmx_mod.py",
        description=(
            "Backup/restore and one-entry Russian localisation test. "
            "Writes game files only with --yes-i-understand."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "PowerShell:\n"
            "  python tools\\modding\\mmx_mod.py --game-path "
            "\"C:\\Games\\MMX\" prepare-localisation-test"
        ),
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"Каталог MMX. Иначе {ENV_PATH_KEY} из .env.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Каталог backup внутри репозитория.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_backup = sub.add_parser(
        "backup",
        help="Скопировать ru/loca.xml в backups/.",
    )
    p_backup.add_argument(
        "--force",
        action="store_true",
        help="Прежний backup уходит в архив, затем пишется новый.",
    )
    sub.add_parser("status", help="ORIGINAL / TEST_PATCHED / UNKNOWN.")
    sub.add_parser(
        "prepare-localisation-test",
        help="Показать ключ и правку, не менять игру.",
    )
    p_apply = sub.add_parser(
        "apply-localisation-test",
        help="Патч одной строки. Нужен --yes-i-understand.",
    )
    p_apply.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в ru/loca.xml.",
    )
    p_restore = sub.add_parser(
        "restore-localisation-test",
        help="Вернуть точные байты backup.",
    )
    p_restore.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в ru/loca.xml.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
    game_path = args.game_path or env_game_path()
    if game_path is None:
        print(
            "Укажите --game-path или "
            f"{ENV_PATH_KEY} в .env.",
            file=sys.stderr,
        )
        return 2
    game_path = game_path.expanduser()
    if not game_path.is_dir():
        print(f"Каталог не найден: {game_path}", file=sys.stderr)
        return 2
    try:
        loca = resolve_loca(game_path)
        assert_allowed_loca(game_path, loca)
    except (FileNotFoundError, PermissionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    backup_dir = args.backup_dir
    if not backup_dir.is_absolute():
        backup_dir = (Path.cwd() / backup_dir).resolve()
    command = args.command
    if command == "backup":
        return cmd_backup(loca, backup_dir, getattr(args, "force", False))
    if command == "status":
        return cmd_status(loca, backup_dir)
    if command == "prepare-localisation-test":
        return cmd_prepare(game_path, loca, backup_dir)
    if command == "apply-localisation-test":
        return cmd_apply(
            loca,
            backup_dir,
            getattr(args, "yes_i_understand", False),
        )
    if command == "restore-localisation-test":
        return cmd_restore(
            loca,
            backup_dir,
            getattr(args, "yes_i_understand", False),
        )
    print(f"Неизвестная команда: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
