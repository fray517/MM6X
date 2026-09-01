"""Safe backup/restore for M0 loca, StaticData, Dialog and Map proofs.

Writes a game file only after --yes-i-understand, and only the file of
the active subcommand. Backups live in the MM6X repo, not the install.
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
DEFAULT_SD_BACKUP_DIR = (
    REPO_ROOT / "backups" / "mmx" / "staticdata-potions"
)
REPORTS_DIR = REPO_ROOT / "reports"
SD_REL_PARTS = (
    "StreamingAssets",
    "StaticData",
    "Potions.csv",
)
SD_COPY_NAME = "Potions.csv"
SD_NEEDLE_ORIGINAL = (
    "1,POTION_HEALTH_MINOR,ITM_consumable_potion_health_1,45,"
)
SD_NEEDLE_PATCHED = (
    "1,POTION_HEALTH_MINOR,ITM_consumable_potion_health_1,9999,"
)
SD_ORIGINAL_PRICE = "45"
SD_TEST_PRICE = "9999"
SD_COMMANDS = {
    "backup-staticdata",
    "status-staticdata",
    "prepare-staticdata-test",
    "apply-staticdata-test",
    "restore-staticdata-test",
}
DEFAULT_DL_BACKUP_DIR = (
    REPO_ROOT / "backups" / "mmx" / "dialog-johara"
)
DL_REL_PARTS = (
    "StreamingAssets",
    "Dialog",
    "JoharaDialog.xml",
)
DL_COPY_NAME = "JoharaDialog.xml"
DL_NEEDLE_ORIGINAL = (
    '<dialog id="1" randomText="false" fakeNpcID="0">\n'
    '\t\t<text locaKey="DIALOG_TEXT_JOHARA_1" />'
)
DL_NEEDLE_PATCHED = (
    '<dialog id="1" randomText="false" fakeNpcID="0">\n'
    '\t\t<text locaKey="DIALOG_TEXT_JOHARA_5" />'
)
DL_ORIGINAL_KEY = "DIALOG_TEXT_JOHARA_1"
DL_TEST_KEY = "DIALOG_TEXT_JOHARA_5"
DL_COMMANDS = {
    "backup-dialog",
    "status-dialog",
    "prepare-dialog-test",
    "apply-dialog-test",
    "restore-dialog-test",
}
DEFAULT_MP_BACKUP_DIR = (
    REPO_ROOT / "backups" / "mmx" / "map-sorpigal"
)
MP_REL_PARTS = (
    "StreamingAssets",
    "Maps",
    "Sorpigal.xml",
)
MP_COPY_NAME = "Sorpigal.xml"
MP_NEEDLE_ORIGINAL = (
    '<Slot Height="-6.87566376" '
    'Terrain="PASSABLE NO_PARTY_BARK" '
    'TerrainSound="NONE" MapArea="NONE">'
)
MP_NEEDLE_PATCHED = (
    '<Slot Height="-6.87566376" '
    'Terrain="BLOCKED" '
    'TerrainSound="NONE" MapArea="NONE">'
)
MP_ORIGINAL_TERRAIN = "PASSABLE NO_PARTY_BARK"
MP_TEST_TERRAIN = "BLOCKED"
MP_SLOT = "X=29 Y=19"
MP_COMMANDS = {
    "backup-map",
    "status-map",
    "prepare-map-test",
    "apply-map-test",
    "restore-map-test",
}


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


def resolve_rel(game_path: Path, parts: tuple[str, ...]) -> Path:
    current = resolve_data_dir(game_path)
    for part in parts:
        nxt = find_child(current, part)
        if nxt is None:
            raise FileNotFoundError(
                f"Не найден '{part}' относительно {current}"
            )
        current = nxt
    if not current.is_file():
        raise FileNotFoundError(f"Нет файла: {current}")
    return current.resolve()


def assert_allowed(
    game_path: Path,
    target: Path,
    expected_parts: tuple[str, ...],
    label: str,
) -> None:
    try:
        rel = target.resolve().relative_to(game_path.resolve())
    except ValueError as exc:
        raise PermissionError(
            "Цель вне каталога игры; запись запрещена."
        ) from exc
    expected = Path(DATA_DIR_NAME, *expected_parts)
    if rel.as_posix().casefold() != expected.as_posix().casefold():
        raise PermissionError(
            f"Разрешён только {label}. Получено: {rel.as_posix()}"
        )


def resolve_loca(game_path: Path) -> Path:
    return resolve_rel(game_path, LOCA_REL_PARTS)


def assert_allowed_loca(game_path: Path, target: Path) -> None:
    assert_allowed(game_path, target, LOCA_REL_PARTS, "ru/loca.xml")


def resolve_staticdata(game_path: Path) -> Path:
    return resolve_rel(game_path, SD_REL_PARTS)


def assert_allowed_staticdata(game_path: Path, target: Path) -> None:
    assert_allowed(game_path, target, SD_REL_PARTS, "Potions.csv")


def resolve_dialog(game_path: Path) -> Path:
    return resolve_rel(game_path, DL_REL_PARTS)


def assert_allowed_dialog(game_path: Path, target: Path) -> None:
    assert_allowed(
        game_path,
        target,
        DL_REL_PARTS,
        "Dialog/JoharaDialog.xml",
    )


def resolve_map(game_path: Path) -> Path:
    return resolve_rel(game_path, MP_REL_PARTS)


def assert_allowed_map(game_path: Path, target: Path) -> None:
    assert_allowed(
        game_path,
        target,
        MP_REL_PARTS,
        "Maps/Sorpigal.xml",
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


def backup_paths(
    backup_dir: Path,
    copy_name: str = "loca.xml",
) -> tuple[Path, Path]:
    return backup_dir / copy_name, backup_dir / "manifest.json"


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
    source: Path,
    backup_dir: Path,
    force: bool,
    copy_name: str,
    relative_target: str,
    extra: dict[str, Any] | None = None,
) -> int:
    copy_path, manifest_path = backup_paths(backup_dir, copy_name)
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
    data = source.read_bytes()
    copy_path.write_bytes(data)
    digest = sha256_bytes(data)
    if sha256_file(copy_path) != digest:
        print("Backup повреждён сразу после записи.", file=sys.stderr)
        return 1
    manifest = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "relative_target": relative_target,
        "size": len(data),
        "sha256": digest,
        "read_only_source": True,
    }
    if extra:
        manifest.update(extra)
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
    target: Path,
    backup_dir: Path,
    understand: bool,
    copy_name: str,
) -> int:
    if not understand:
        print(
            "Отказ: нет --yes-i-understand. Файл игры не изменён.",
            file=sys.stderr,
        )
        return 2
    copy_path, manifest_path = backup_paths(backup_dir, copy_name)
    if not copy_path.is_file():
        print(f"Нет backup {copy_name}.", file=sys.stderr)
        return 2
    original = copy_path.read_bytes()
    expected = sha256_bytes(original)
    manifest = load_manifest(manifest_path) or {}
    if manifest.get("sha256") not in (None, expected):
        print("Manifest SHA-256 не совпадает с копией.", file=sys.stderr)
        return 1
    try:
        target.write_bytes(original)
    except PermissionError:
        print(
            "Нет прав записи в Program Files. "
            "Запустите PowerShell от имени администратора.",
            file=sys.stderr,
        )
        return 1
    restored = sha256_file(target)
    ok = restored == expected
    op = {
        "schema_version": 1,
        "operation": "restore",
        "created_utc": utc_now(),
        "copy_name": copy_name,
        "expected_sha256": expected,
        "restored_sha256": restored,
        "success": ok,
    }
    write_json(backup_dir / "restore.json", op)
    if copy_name == SD_COPY_NAME:
        report_name = "staticdata_restore.json"
    elif copy_name == DL_COPY_NAME:
        report_name = "dialog_restore.json"
    elif copy_name == MP_COPY_NAME:
        report_name = "map_restore.json"
    else:
        report_name = "loca_restore.json"
    write_json(REPORTS_DIR / report_name, op)
    if ok:
        print("RESTORE ok")
        print(f"  SHA-256: {restored}")
        return 0
    print("RESTORE FAILED: хеш не совпал с backup.", file=sys.stderr)
    print(f"  expected: {expected}")
    print(f"  actual:   {restored}")
    return 1


def sd_price_state(text: str) -> str:
    has_orig = text.count(SD_NEEDLE_ORIGINAL)
    has_test = text.count(SD_NEEDLE_PATCHED)
    if has_orig == 1 and has_test == 0:
        return "ORIGINAL"
    if has_orig == 0 and has_test == 1:
        return "TEST_PATCHED"
    return "UNKNOWN"


def cmd_sd_status(csv_path: Path, backup_dir: Path) -> int:
    current_sha = sha256_file(csv_path)
    text, _ = read_text_preserve(csv_path)
    copy_path, manifest_path = backup_paths(backup_dir, SD_COPY_NAME)
    backup_sha = None
    if copy_path.is_file():
        backup_sha = sha256_file(copy_path)
    elif manifest_path.is_file():
        manifest = load_manifest(manifest_path) or {}
        backup_sha = manifest.get("sha256")
    needle_state = sd_price_state(text)
    if backup_sha is None:
        state = "NO_BACKUP" if needle_state != "TEST_PATCHED" else (
            "TEST_PATCHED"
        )
    elif current_sha == backup_sha:
        state = "ORIGINAL"
    else:
        state = needle_state if needle_state != "ORIGINAL" else "UNKNOWN"
    price = SD_TEST_PRICE if needle_state == "TEST_PATCHED" else (
        SD_ORIGINAL_PRICE if needle_state == "ORIGINAL" else "?"
    )
    payload = {
        "target": str(csv_path),
        "file": SD_COPY_NAME,
        "row": "StaticID=1 POTION_HEALTH_MINOR Price",
        "current_sha256": current_sha,
        "original_backup_sha256": backup_sha,
        "state": state,
        "current_price": price,
    }
    print(f"target: {csv_path}")
    print("field: Potions.csv StaticID=1 Price")
    print(f"current SHA-256: {current_sha}")
    print(f"backup SHA-256: {backup_sha or '—'}")
    print(f"state: {state}")
    print(f"price: {price}")
    write_json(REPORTS_DIR / "staticdata_status.json", payload)
    return 0


def cmd_sd_prepare(
    game_path: Path,
    csv_path: Path,
    backup_dir: Path,
) -> int:
    text, has_bom = read_text_preserve(csv_path)
    current_sha = sha256_file(csv_path)
    copy_path, _ = backup_paths(backup_dir, SD_COPY_NAME)
    backup_sha = sha256_file(copy_path) if copy_path.is_file() else None
    payload = {
        "dry_run": True,
        "modified_game": False,
        "file": SD_COPY_NAME,
        "field": "StaticID=1 Price",
        "original_value": SD_ORIGINAL_PRICE,
        "proposed_value": SD_TEST_PRICE,
        "source_game_path": str(game_path.resolve()),
        "target": str(csv_path),
        "backup_dir": str(backup_dir),
        "backup_present": copy_path.is_file(),
        "has_utf8_bom": has_bom,
        "current_sha256": current_sha,
        "backup_sha256": backup_sha,
        "verify_in_game": (
            "Sorpigal, Johara (ItemOffers 20: POTION,1). "
            "Цена minor health potion 45 -> 9999."
        ),
        "needle_state": sd_price_state(text),
    }
    print("PREPARE StaticData (игра не изменяется)")
    print(f"  file: {SD_COPY_NAME}")
    print("  field: StaticID=1 Price")
    print(f"  original: {SD_ORIGINAL_PRICE}")
    print(f"  proposed: {SD_TEST_PRICE}")
    print(f"  target: {csv_path}")
    print(f"  backup: {backup_dir}")
    print(f"  current SHA-256: {current_sha}")
    print(f"  backup SHA-256: {backup_sha or 'нет backup'}")
    write_json(REPORTS_DIR / "staticdata_prepare.json", payload)
    print(f"  report: {REPORTS_DIR / 'staticdata_prepare.json'}")
    return 0


def cmd_sd_apply(
    csv_path: Path,
    backup_dir: Path,
    understand: bool,
) -> int:
    if not understand:
        print(
            "Отказ: нет --yes-i-understand. Файл игры не изменён.",
            file=sys.stderr,
        )
        return 2
    copy_path, manifest_path = backup_paths(backup_dir, SD_COPY_NAME)
    if not copy_path.is_file() or not manifest_path.is_file():
        print("Сначала выполните backup-staticdata.", file=sys.stderr)
        return 2
    original_bytes = copy_path.read_bytes()
    backup_sha = sha256_bytes(original_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != backup_sha:
        print("Manifest backup не совпадает с копией.", file=sys.stderr)
        return 1
    current_sha = sha256_file(csv_path)
    if current_sha != backup_sha:
        print(
            "Текущий Potions.csv не совпадает с backup. Патч отказан.\n"
            f"  current: {current_sha}\n"
            f"  backup:  {backup_sha}",
            file=sys.stderr,
        )
        return 2
    text, has_bom = read_text_preserve(csv_path)
    if text.count(SD_NEEDLE_ORIGINAL) != 1:
        print("Ожидалась ровно одна исходная строка зелья.", file=sys.stderr)
        return 1
    patched = text.replace(SD_NEEDLE_ORIGINAL, SD_NEEDLE_PATCHED, 1)
    if sd_price_state(patched) != "TEST_PATCHED":
        print("Патч цены не применился. Отказ.", file=sys.stderr)
        return 1
    if patched.count("\n") != text.count("\n"):
        print("Число строк CSV изменилось. Отказ.", file=sys.stderr)
        return 1
    out_bytes = encode_text(patched, has_bom)
    try:
        csv_path.write_bytes(out_bytes)
    except PermissionError:
        print(
            "Нет прав записи в Program Files. "
            "Запустите PowerShell от имени администратора.",
            file=sys.stderr,
        )
        return 1
    new_sha = sha256_file(csv_path)
    op = {
        "schema_version": 1,
        "operation": "apply-staticdata-test",
        "created_utc": utc_now(),
        "file": SD_COPY_NAME,
        "field": "StaticID=1 Price",
        "original_value": SD_ORIGINAL_PRICE,
        "new_value": SD_TEST_PRICE,
        "before_sha256": current_sha,
        "after_sha256": new_sha,
        "target_relative": Path(DATA_DIR_NAME, *SD_REL_PARTS).as_posix(),
        "backup_sha256": backup_sha,
    }
    write_json(backup_dir / "apply.json", op)
    write_json(REPORTS_DIR / "staticdata_apply.json", op)
    print("APPLY ok")
    print("  field: Potions.csv StaticID=1 Price 45 -> 9999")
    print(f"  new SHA-256: {new_sha}")
    print(f"  manifest: {backup_dir / 'apply.json'}")
    return 0


def dl_key_state(text: str) -> str:
    has_orig = text.count(DL_NEEDLE_ORIGINAL)
    has_test = text.count(DL_NEEDLE_PATCHED)
    if has_orig == 1 and has_test == 0:
        return "ORIGINAL"
    if has_orig == 0 and has_test == 1:
        return "TEST_PATCHED"
    return "UNKNOWN"


def cmd_dl_status(dialog_path: Path, backup_dir: Path) -> int:
    current_sha = sha256_file(dialog_path)
    text, _ = read_text_preserve(dialog_path)
    copy_path, manifest_path = backup_paths(backup_dir, DL_COPY_NAME)
    backup_sha = None
    if copy_path.is_file():
        backup_sha = sha256_file(copy_path)
    elif manifest_path.is_file():
        manifest = load_manifest(manifest_path) or {}
        backup_sha = manifest.get("sha256")
    needle_state = dl_key_state(text)
    if backup_sha is None:
        state = (
            "TEST_PATCHED"
            if needle_state == "TEST_PATCHED"
            else "NO_BACKUP"
        )
    elif current_sha == backup_sha:
        state = "ORIGINAL"
    else:
        state = (
            needle_state if needle_state != "ORIGINAL" else "UNKNOWN"
        )
    loca_key = (
        DL_TEST_KEY if needle_state == "TEST_PATCHED"
        else DL_ORIGINAL_KEY if needle_state == "ORIGINAL"
        else "?"
    )
    payload = {
        "target": str(dialog_path),
        "file": DL_COPY_NAME,
        "field": "dialog id=1 text locaKey",
        "current_sha256": current_sha,
        "original_backup_sha256": backup_sha,
        "state": state,
        "current_loca_key": loca_key,
    }
    print(f"target: {dialog_path}")
    print("field: JoharaDialog.xml dialog id=1 locaKey")
    print(f"current SHA-256: {current_sha}")
    print(f"backup SHA-256: {backup_sha or '—'}")
    print(f"state: {state}")
    print(f"locaKey: {loca_key}")
    write_json(REPORTS_DIR / "dialog_status.json", payload)
    return 0


def cmd_dl_prepare(
    game_path: Path,
    dialog_path: Path,
    backup_dir: Path,
) -> int:
    text, has_bom = read_text_preserve(dialog_path)
    current_sha = sha256_file(dialog_path)
    copy_path, _ = backup_paths(backup_dir, DL_COPY_NAME)
    backup_sha = (
        sha256_file(copy_path) if copy_path.is_file() else None
    )
    payload = {
        "dry_run": True,
        "modified_game": False,
        "file": DL_COPY_NAME,
        "field": "dialog id=1 text locaKey",
        "original_value": DL_ORIGINAL_KEY,
        "proposed_value": DL_TEST_KEY,
        "source_game_path": str(game_path.resolve()),
        "target": str(dialog_path),
        "backup_dir": str(backup_dir),
        "backup_present": copy_path.is_file(),
        "has_utf8_bom": has_bom,
        "current_sha256": current_sha,
        "backup_sha256": backup_sha,
        "verify_in_game": (
            "Sorpigal, Johara. Первая реплика должна быть "
            "DIALOG_TEXT_JOHARA_5 (тренировка), не приветствие."
        ),
        "needle_state": dl_key_state(text),
    }
    print("PREPARE Dialog (игра не изменяется)")
    print(f"  file: {DL_COPY_NAME}")
    print("  field: dialog id=1 locaKey")
    print(f"  original: {DL_ORIGINAL_KEY}")
    print(f"  proposed: {DL_TEST_KEY}")
    print(f"  target: {dialog_path}")
    print(f"  backup: {backup_dir}")
    print(f"  current SHA-256: {current_sha}")
    print(f"  backup SHA-256: {backup_sha or 'нет backup'}")
    write_json(REPORTS_DIR / "dialog_prepare.json", payload)
    print(f"  report: {REPORTS_DIR / 'dialog_prepare.json'}")
    return 0


def cmd_dl_apply(
    dialog_path: Path,
    backup_dir: Path,
    understand: bool,
) -> int:
    if not understand:
        print(
            "Отказ: нет --yes-i-understand. Файл игры не изменён.",
            file=sys.stderr,
        )
        return 2
    copy_path, manifest_path = backup_paths(backup_dir, DL_COPY_NAME)
    if not copy_path.is_file() or not manifest_path.is_file():
        print("Сначала выполните backup-dialog.", file=sys.stderr)
        return 2
    original_bytes = copy_path.read_bytes()
    backup_sha = sha256_bytes(original_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != backup_sha:
        print("Manifest backup не совпадает с копией.", file=sys.stderr)
        return 1
    current_sha = sha256_file(dialog_path)
    if current_sha != backup_sha:
        print(
            "Текущий JoharaDialog.xml не совпадает с backup. "
            "Патч отказан.\n"
            f"  current: {current_sha}\n"
            f"  backup:  {backup_sha}",
            file=sys.stderr,
        )
        return 2
    text, has_bom = read_text_preserve(dialog_path)
    if text.count(DL_NEEDLE_ORIGINAL) != 1:
        print(
            "Ожидалась ровно одна исходная реплика Johara.",
            file=sys.stderr,
        )
        return 1
    patched = text.replace(DL_NEEDLE_ORIGINAL, DL_NEEDLE_PATCHED, 1)
    if dl_key_state(patched) != "TEST_PATCHED":
        print("Патч locaKey не применился. Отказ.", file=sys.stderr)
        return 1
    if patched.count("\n") != text.count("\n"):
        print("Число строк XML изменилось. Отказ.", file=sys.stderr)
        return 1
    out_bytes = encode_text(patched, has_bom)
    try:
        dialog_path.write_bytes(out_bytes)
    except PermissionError:
        print(
            "Нет прав записи в Program Files. "
            "Запустите PowerShell от имени администратора.",
            file=sys.stderr,
        )
        return 1
    new_sha = sha256_file(dialog_path)
    op = {
        "schema_version": 1,
        "operation": "apply-dialog-test",
        "created_utc": utc_now(),
        "file": DL_COPY_NAME,
        "field": "dialog id=1 text locaKey",
        "original_value": DL_ORIGINAL_KEY,
        "new_value": DL_TEST_KEY,
        "before_sha256": current_sha,
        "after_sha256": new_sha,
        "target_relative": Path(
            DATA_DIR_NAME, *DL_REL_PARTS
        ).as_posix(),
        "backup_sha256": backup_sha,
    }
    write_json(backup_dir / "apply.json", op)
    write_json(REPORTS_DIR / "dialog_apply.json", op)
    print("APPLY ok")
    print(
        f"  field: dialog id=1 {DL_ORIGINAL_KEY} -> {DL_TEST_KEY}"
    )
    print(f"  new SHA-256: {new_sha}")
    print(f"  manifest: {backup_dir / 'apply.json'}")
    return 0


def mp_terrain_state(text: str) -> str:
    has_orig = text.count(MP_NEEDLE_ORIGINAL)
    has_test = text.count(MP_NEEDLE_PATCHED)
    if has_orig == 1 and has_test == 0:
        return "ORIGINAL"
    if has_orig == 0 and has_test == 1:
        return "TEST_PATCHED"
    return "UNKNOWN"


def cmd_mp_status(map_path: Path, backup_dir: Path) -> int:
    current_sha = sha256_file(map_path)
    text, _ = read_text_preserve(map_path)
    copy_path, manifest_path = backup_paths(backup_dir, MP_COPY_NAME)
    backup_sha = None
    if copy_path.is_file():
        backup_sha = sha256_file(copy_path)
    elif manifest_path.is_file():
        manifest = load_manifest(manifest_path) or {}
        backup_sha = manifest.get("sha256")
    needle_state = mp_terrain_state(text)
    if backup_sha is None:
        state = (
            "TEST_PATCHED"
            if needle_state == "TEST_PATCHED"
            else "NO_BACKUP"
        )
    elif current_sha == backup_sha:
        state = "ORIGINAL"
    else:
        state = (
            needle_state if needle_state != "ORIGINAL" else "UNKNOWN"
        )
    terrain = (
        MP_TEST_TERRAIN if needle_state == "TEST_PATCHED"
        else MP_ORIGINAL_TERRAIN if needle_state == "ORIGINAL"
        else "?"
    )
    payload = {
        "target": str(map_path),
        "file": MP_COPY_NAME,
        "field": f"Slot {MP_SLOT} Terrain",
        "current_sha256": current_sha,
        "original_backup_sha256": backup_sha,
        "state": state,
        "current_terrain": terrain,
    }
    print(f"target: {map_path}")
    print(f"field: Sorpigal.xml Slot {MP_SLOT} Terrain")
    print(f"current SHA-256: {current_sha}")
    print(f"backup SHA-256: {backup_sha or '—'}")
    print(f"state: {state}")
    print(f"terrain: {terrain}")
    write_json(REPORTS_DIR / "map_status.json", payload)
    return 0


def cmd_mp_prepare(
    game_path: Path,
    map_path: Path,
    backup_dir: Path,
) -> int:
    text, has_bom = read_text_preserve(map_path)
    current_sha = sha256_file(map_path)
    copy_path, _ = backup_paths(backup_dir, MP_COPY_NAME)
    backup_sha = (
        sha256_file(copy_path) if copy_path.is_file() else None
    )
    payload = {
        "dry_run": True,
        "modified_game": False,
        "file": MP_COPY_NAME,
        "field": f"Slot {MP_SLOT} Terrain",
        "original_value": MP_ORIGINAL_TERRAIN,
        "proposed_value": MP_TEST_TERRAIN,
        "source_game_path": str(game_path.resolve()),
        "target": str(map_path),
        "backup_dir": str(backup_dir),
        "backup_present": copy_path.is_file(),
        "has_utf8_bom": has_bom,
        "current_sha256": current_sha,
        "backup_sha256": backup_sha,
        "verify_in_game": (
            "Новая игра, спавн 31,19 лицом на запад. "
            "Второй шаг вперёд (клетка 29,19) должен упереться в стену."
        ),
        "needle_state": mp_terrain_state(text),
    }
    print("PREPARE Map (игра не изменяется)")
    print(f"  file: {MP_COPY_NAME}")
    print(f"  field: Slot {MP_SLOT} Terrain")
    print(f"  original: {MP_ORIGINAL_TERRAIN}")
    print(f"  proposed: {MP_TEST_TERRAIN}")
    print(f"  target: {map_path}")
    print(f"  backup: {backup_dir}")
    print(f"  current SHA-256: {current_sha}")
    print(f"  backup SHA-256: {backup_sha or 'нет backup'}")
    write_json(REPORTS_DIR / "map_prepare.json", payload)
    print(f"  report: {REPORTS_DIR / 'map_prepare.json'}")
    return 0


def cmd_mp_apply(
    map_path: Path,
    backup_dir: Path,
    understand: bool,
) -> int:
    if not understand:
        print(
            "Отказ: нет --yes-i-understand. Файл игры не изменён.",
            file=sys.stderr,
        )
        return 2
    copy_path, manifest_path = backup_paths(backup_dir, MP_COPY_NAME)
    if not copy_path.is_file() or not manifest_path.is_file():
        print("Сначала выполните backup-map.", file=sys.stderr)
        return 2
    original_bytes = copy_path.read_bytes()
    backup_sha = sha256_bytes(original_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != backup_sha:
        print("Manifest backup не совпадает с копией.", file=sys.stderr)
        return 1
    current_sha = sha256_file(map_path)
    if current_sha != backup_sha:
        print(
            "Текущий Sorpigal.xml не совпадает с backup. "
            "Патч отказан.\n"
            f"  current: {current_sha}\n"
            f"  backup:  {backup_sha}",
            file=sys.stderr,
        )
        return 2
    text, has_bom = read_text_preserve(map_path)
    if text.count(MP_NEEDLE_ORIGINAL) != 1:
        print(
            "Ожидалась ровно одна исходная клетка 29,19.",
            file=sys.stderr,
        )
        return 1
    patched = text.replace(MP_NEEDLE_ORIGINAL, MP_NEEDLE_PATCHED, 1)
    if mp_terrain_state(patched) != "TEST_PATCHED":
        print("Патч Terrain не применился. Отказ.", file=sys.stderr)
        return 1
    if patched.count("\n") != text.count("\n"):
        print("Число строк XML изменилось. Отказ.", file=sys.stderr)
        return 1
    out_bytes = encode_text(patched, has_bom)
    try:
        map_path.write_bytes(out_bytes)
    except PermissionError:
        print(
            "Нет прав записи в Program Files. "
            "Запустите PowerShell от имени администратора.",
            file=sys.stderr,
        )
        return 1
    new_sha = sha256_file(map_path)
    op = {
        "schema_version": 1,
        "operation": "apply-map-test",
        "created_utc": utc_now(),
        "file": MP_COPY_NAME,
        "field": f"Slot {MP_SLOT} Terrain",
        "original_value": MP_ORIGINAL_TERRAIN,
        "new_value": MP_TEST_TERRAIN,
        "before_sha256": current_sha,
        "after_sha256": new_sha,
        "target_relative": Path(
            DATA_DIR_NAME, *MP_REL_PARTS
        ).as_posix(),
        "backup_sha256": backup_sha,
    }
    write_json(backup_dir / "apply.json", op)
    write_json(REPORTS_DIR / "map_apply.json", op)
    print("APPLY ok")
    print(
        f"  field: Slot {MP_SLOT} {MP_ORIGINAL_TERRAIN} -> "
        f"{MP_TEST_TERRAIN}"
    )
    print(f"  new SHA-256: {new_sha}")
    print(f"  manifest: {backup_dir / 'apply.json'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mmx_mod.py",
        description=(
            "Backup/restore for loca, StaticData, Dialog and Map tests. "
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
        default=None,
        help="Каталог backup. По умолчанию backups/mmx/<test>/.",
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
    p_sd_backup = sub.add_parser(
        "backup-staticdata",
        help="Скопировать Potions.csv в backups/.",
    )
    p_sd_backup.add_argument(
        "--force",
        action="store_true",
        help="Прежний backup уходит в архив, затем пишется новый.",
    )
    sub.add_parser(
        "status-staticdata",
        help="ORIGINAL / TEST_PATCHED / UNKNOWN для Potions.csv.",
    )
    sub.add_parser(
        "prepare-staticdata-test",
        help="Показать правку цены зелья, не менять игру.",
    )
    p_sd_apply = sub.add_parser(
        "apply-staticdata-test",
        help="Price 45→9999. Нужен --yes-i-understand.",
    )
    p_sd_apply.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в Potions.csv.",
    )
    p_sd_restore = sub.add_parser(
        "restore-staticdata-test",
        help="Вернуть точные байты backup Potions.csv.",
    )
    p_sd_restore.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в Potions.csv.",
    )
    p_dl_backup = sub.add_parser(
        "backup-dialog",
        help="Скопировать JoharaDialog.xml в backups/.",
    )
    p_dl_backup.add_argument(
        "--force",
        action="store_true",
        help="Прежний backup уходит в архив, затем пишется новый.",
    )
    sub.add_parser(
        "status-dialog",
        help="ORIGINAL / TEST_PATCHED / UNKNOWN для Johara.",
    )
    sub.add_parser(
        "prepare-dialog-test",
        help="Показать правку locaKey Johara, не менять игру.",
    )
    p_dl_apply = sub.add_parser(
        "apply-dialog-test",
        help="Johara greeting locaKey. Нужен --yes-i-understand.",
    )
    p_dl_apply.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в JoharaDialog.xml.",
    )
    p_dl_restore = sub.add_parser(
        "restore-dialog-test",
        help="Вернуть точные байты backup JoharaDialog.xml.",
    )
    p_dl_restore.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в JoharaDialog.xml.",
    )
    p_mp_backup = sub.add_parser(
        "backup-map",
        help="Скопировать Sorpigal.xml в backups/.",
    )
    p_mp_backup.add_argument(
        "--force",
        action="store_true",
        help="Прежний backup уходит в архив, затем пишется новый.",
    )
    sub.add_parser(
        "status-map",
        help="ORIGINAL / TEST_PATCHED / UNKNOWN для Sorpigal.xml.",
    )
    sub.add_parser(
        "prepare-map-test",
        help="Показать правку Terrain клетки, не менять игру.",
    )
    p_mp_apply = sub.add_parser(
        "apply-map-test",
        help="Клетка 29,19 → BLOCKED. Нужен --yes-i-understand.",
    )
    p_mp_apply.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в Sorpigal.xml.",
    )
    p_mp_restore = sub.add_parser(
        "restore-map-test",
        help="Вернуть точные байты backup Sorpigal.xml.",
    )
    p_mp_restore.add_argument(
        "--yes-i-understand",
        dest="yes_i_understand",
        action="store_true",
        help="Разрешить запись в Sorpigal.xml.",
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
    command = args.command
    if args.backup_dir is not None:
        backup_dir = args.backup_dir
    elif command in SD_COMMANDS:
        backup_dir = DEFAULT_SD_BACKUP_DIR
    elif command in DL_COMMANDS:
        backup_dir = DEFAULT_DL_BACKUP_DIR
    elif command in MP_COMMANDS:
        backup_dir = DEFAULT_MP_BACKUP_DIR
    else:
        backup_dir = DEFAULT_BACKUP_DIR
    if not backup_dir.is_absolute():
        backup_dir = (Path.cwd() / backup_dir).resolve()
    understand = getattr(args, "yes_i_understand", False)
    force = getattr(args, "force", False)
    try:
        if command in SD_COMMANDS:
            target = resolve_staticdata(game_path)
            assert_allowed_staticdata(game_path, target)
        elif command in DL_COMMANDS:
            target = resolve_dialog(game_path)
            assert_allowed_dialog(game_path, target)
        elif command in MP_COMMANDS:
            target = resolve_map(game_path)
            assert_allowed_map(game_path, target)
        else:
            target = resolve_loca(game_path)
            assert_allowed_loca(game_path, target)
    except (FileNotFoundError, PermissionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    loca_rel = Path(DATA_DIR_NAME, *LOCA_REL_PARTS).as_posix()
    sd_rel = Path(DATA_DIR_NAME, *SD_REL_PARTS).as_posix()
    dl_rel = Path(DATA_DIR_NAME, *DL_REL_PARTS).as_posix()
    mp_rel = Path(DATA_DIR_NAME, *MP_REL_PARTS).as_posix()
    if command == "backup":
        return cmd_backup(
            target,
            backup_dir,
            force,
            "loca.xml",
            loca_rel,
            {"test_key": TEST_KEY},
        )
    if command == "status":
        return cmd_status(target, backup_dir)
    if command == "prepare-localisation-test":
        return cmd_prepare(game_path, target, backup_dir)
    if command == "apply-localisation-test":
        return cmd_apply(target, backup_dir, understand)
    if command == "restore-localisation-test":
        return cmd_restore(target, backup_dir, understand, "loca.xml")
    if command == "backup-staticdata":
        return cmd_backup(
            target,
            backup_dir,
            force,
            SD_COPY_NAME,
            sd_rel,
            {"field": "StaticID=1 Price", "original": SD_ORIGINAL_PRICE},
        )
    if command == "status-staticdata":
        return cmd_sd_status(target, backup_dir)
    if command == "prepare-staticdata-test":
        return cmd_sd_prepare(game_path, target, backup_dir)
    if command == "apply-staticdata-test":
        return cmd_sd_apply(target, backup_dir, understand)
    if command == "restore-staticdata-test":
        return cmd_restore(target, backup_dir, understand, SD_COPY_NAME)
    if command == "backup-dialog":
        return cmd_backup(
            target,
            backup_dir,
            force,
            DL_COPY_NAME,
            dl_rel,
            {
                "field": "dialog id=1 locaKey",
                "original": DL_ORIGINAL_KEY,
            },
        )
    if command == "status-dialog":
        return cmd_dl_status(target, backup_dir)
    if command == "prepare-dialog-test":
        return cmd_dl_prepare(game_path, target, backup_dir)
    if command == "apply-dialog-test":
        return cmd_dl_apply(target, backup_dir, understand)
    if command == "restore-dialog-test":
        return cmd_restore(
            target, backup_dir, understand, DL_COPY_NAME
        )
    if command == "backup-map":
        return cmd_backup(
            target,
            backup_dir,
            force,
            MP_COPY_NAME,
            mp_rel,
            {
                "field": f"Slot {MP_SLOT} Terrain",
                "original": MP_ORIGINAL_TERRAIN,
            },
        )
    if command == "status-map":
        return cmd_mp_status(target, backup_dir)
    if command == "prepare-map-test":
        return cmd_mp_prepare(game_path, target, backup_dir)
    if command == "apply-map-test":
        return cmd_mp_apply(target, backup_dir, understand)
    if command == "restore-map-test":
        return cmd_restore(
            target, backup_dir, understand, MP_COPY_NAME
        )
    print(f"Неизвестная команда: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
