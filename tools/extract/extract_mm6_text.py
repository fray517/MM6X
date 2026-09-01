"""Extract allowlisted text tables from MM6 Icons.lod.

Read-only towards the game install. Writes UTF-8 copies under
references/mm6/raw/ (gitignore). Does not dump full tables into git.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mm6_lod import LodError, Mm6Lod, decode_maybe_compressed

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_OUT = REPO_ROOT / "references" / "mm6" / "raw"
DEFAULT_REPORTS = REPO_ROOT / "reports"
LOD_NAME = "icons.lod"

# Slice + inventory tables. Not EVT, not graphics.
DEFAULT_NAMES = (
    "MapStats.txt",
    "NPCdata.txt",
    "npcnames.txt",
    "Quests.txt",
    "2DEvents.txt",
    "ITEMS.TXT",
    "MONSTERS.TXT",
)


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
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in "\"'"
        ):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def env_game_path() -> Path | None:
    raw = os.environ.get(ENV_PATH_KEY, "").strip().strip('"')
    if not raw:
        return None
    return Path(raw)


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


def find_data_dir(game_path: Path) -> Path:
    data = find_child(game_path, "Data")
    if data is not None and data.is_dir():
        return data
    return game_path


def find_lod(game_path: Path) -> Path | None:
    data_dir = find_data_dir(game_path)
    found = find_child(data_dir, LOD_NAME)
    if found is not None and found.is_file():
        return found
    return find_child(game_path, LOD_NAME)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def decode_text(payload: bytes, encoding: str) -> str:
    return payload.decode(encoding, errors="replace")


def parse_mapstats(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        if not cols[0].strip().isdigit():
            continue
        rows.append(
            {
                "id": int(cols[0].strip()),
                "name": cols[1].strip(),
                "file": cols[2].strip(),
            }
        )
    return rows


def write_mapstats_index(
    rows: list[dict[str, Any]],
    reports_dir: Path,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "mapstats_index.json"
    payload = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": "Icons.lod/MapStats.txt",
        "encoding": "cp1251->utf-8",
        "count": len(rows),
        "maps": rows,
        "note": "Derived index. Not a proprietary dump of other tables.",
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def extract_one(
    lod: Mm6Lod,
    name: str,
    encoding: str,
) -> dict[str, Any]:
    entry = lod.get(name)
    if entry is None:
        return {
            "requested": name,
            "ok": False,
            "error": "entry not found",
        }
    blob = lod.read_blob(entry.name)
    payload, how = decode_maybe_compressed(blob)
    text = decode_text(payload, encoding)
    return {
        "requested": name,
        "ok": True,
        "lod_name": entry.name,
        "blob_size": entry.size,
        "decoded_bytes": len(payload),
        "how": how,
        "text": text,
    }


def write_extracted(
    item: dict[str, Any],
    out_dir: Path,
    encoding: str,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = Path(item["lod_name"]).name
    txt_path = out_dir / safe
    meta_path = out_dir / f"{safe}.meta.json"
    txt_path.write_text(item["text"], encoding="utf-8")
    meta = {
        "lod": "Icons.lod",
        "entry": item["lod_name"],
        "source_encoding": encoding,
        "output_encoding": "utf-8",
        "how": item["how"],
        "blob_size": item["blob_size"],
        "decoded_bytes": item["decoded_bytes"],
        "created_utc": utc_now(),
        "evidence": "VERIFIED_LOCAL",
    }
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return txt_path, meta_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_text.py",
        description=(
            "Read-only extract of allowlisted .txt from MM6 Icons.lod."
        ),
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=f"Каталог MM6. Иначе {ENV_PATH_KEY} из .env.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Куда писать UTF-8 копии (gitignore).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS,
        help="Куда писать mapstats_index.json.",
    )
    parser.add_argument(
        "--name",
        action="append",
        dest="names",
        default=None,
        help="Имя записи lod. Можно повторять. Иначе allowlist.",
    )
    parser.add_argument(
        "--encoding",
        default="cp1251",
        help="Исходная кодировка таблиц (эта сборка: cp1251).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только список; файлы не писать.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
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
    lod_path = find_lod(game_path)
    if lod_path is None or not lod_path.is_file():
        print("Icons.lod не найден.", file=sys.stderr)
        return 2
    try:
        lod = Mm6Lod(lod_path)
    except LodError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    names = args.names or list(DEFAULT_NAMES)
    failed = 0
    map_rows: list[dict[str, Any]] | None = None
    for name in names:
        try:
            item = extract_one(lod, name, args.encoding)
        except LodError as exc:
            print(f"FAIL {name}: {exc}", file=sys.stderr)
            failed += 1
            continue
        if not item["ok"]:
            print(f"MISS {name}: {item['error']}", file=sys.stderr)
            failed += 1
            continue
        shown = item["lod_name"]
        how = item["how"]
        nbytes = item["decoded_bytes"]
        print(f"OK {shown} how={how} bytes={nbytes}")
        if shown.casefold() == "mapstats.txt":
            map_rows = parse_mapstats(item["text"])
        if args.dry_run:
            continue
        txt_path, meta_path = write_extracted(
            item,
            args.output_dir,
            args.encoding,
        )
        print(f"  wrote {txt_path}")
        print(f"  meta  {meta_path}")
    if map_rows is not None and not args.dry_run:
        index_path = write_mapstats_index(map_rows, args.reports_dir)
        print(f"index {index_path} maps={len(map_rows)}")
    elif map_rows is not None and args.dry_run:
        print(f"index (dry-run) maps={len(map_rows)}")
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
