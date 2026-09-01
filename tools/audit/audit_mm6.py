"""Read-only audit of a Might and Magic VI install.

Does not write into the game directory. Hashes only the main exe
and records LOD / data inventory. Reports go to MM6X reports/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports"
ENV_PATH_KEY = "MM6_GAME_PATH"
CHUNK_SIZE = 1024 * 1024
MAX_LIST_FILES = 4000

EXE_NAMES = ("MM6.exe", "mm6.exe")
LOD_NAMES = (
    "icons.lod",
    "events.lod",
    "games.lod",
    "sprites.lod",
    "bitmaps.lod",
    "englishd.lod",
    "englisht.lod",
    "audio.lod",
    "sounds.lod",
)
STEAM_CLUES = (
    "steam_api.dll",
    "steam_api64.dll",
    "steam_appid.txt",
)
GOG_PREFIX = "goggame-"
UNPACKED_SUFFIXES = (".blv", ".odm", ".evt", ".txt", ".ddm")
LOD_INDEX_LIMIT = 8000
LOD_NAME_RE = re.compile(r"^[A-Za-z0-9._#+\-]+$")
LOD_INTEREST_SUFFIX = (".txt", ".evt", ".blv", ".odm")
PATCH_FILES = (
    "MM6patch.dll",
    "mm6text.dll",
    "mm6.ini",
    "mm6lang.ini",
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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_mtime(path: Path) -> str | None:
    try:
        stamp = path.stat().st_mtime
    except OSError:
        return None
    return datetime.fromtimestamp(stamp, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def rel_to(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


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


def iter_children(directory: Path) -> Iterator[Path]:
    if not directory.is_dir():
        return
    try:
        yield from sorted(
            directory.iterdir(),
            key=lambda item: item.name.casefold(),
        )
    except OSError:
        return


def file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def sha256_file(path: Path) -> tuple[str | None, str | None]:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        return None, str(exc)
    return digest.hexdigest(), None


def env_game_path() -> Path | None:
    raw = os.environ.get(ENV_PATH_KEY, "").strip().strip('"')
    if not raw:
        return None
    return Path(raw)


def describe_file(
    path: Path,
    root: Path,
    *,
    with_hash: bool = False,
) -> dict[str, Any]:
    info: dict[str, Any] = {
        "name": path.name,
        "relative": rel_to(path, root),
        "size": file_size(path),
        "mtime_utc": iso_mtime(path),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
    }
    if with_hash and path.is_file():
        digest, error = sha256_file(path)
        info["sha256"] = digest
        if error:
            info["hash_error"] = error
    return info


def find_exe(game_path: Path) -> Path | None:
    for name in EXE_NAMES:
        found = find_child(game_path, name)
        if found is not None and found.is_file():
            return found
    for child in iter_children(game_path):
        if child.is_file() and child.suffix.casefold() == ".exe":
            if child.name.casefold().startswith("mm6"):
                return child
    return None


def find_data_dir(game_path: Path) -> Path:
    data = find_child(game_path, "Data")
    if data is not None and data.is_dir():
        return data
    return game_path


def list_lods(
    directory: Path,
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for child in iter_children(directory):
        if not child.is_file():
            continue
        if child.suffix.casefold() != ".lod":
            continue
        key = child.name.casefold()
        if key in seen:
            continue
        seen.add(key)
        found.append(describe_file(child, root))
    expected = []
    names = {item["name"].casefold() for item in found}
    for name in LOD_NAMES:
        expected.append(
            {
                "name": name,
                "present": name.casefold() in names,
            }
        )
    return found, expected


def lod_dir_names(data: bytes, limit: int = LOD_INDEX_LIMIT) -> list[str]:
    names: list[str] = []
    offset = 0x120
    for _ in range(limit):
        rec = data[offset : offset + 32]
        if len(rec) < 32:
            break
        raw = rec[:16].split(b"\x00", 1)[0]
        if not raw:
            break
        try:
            name = raw.decode("ascii")
        except UnicodeDecodeError:
            break
        if not LOD_NAME_RE.match(name):
            break
        names.append(name)
        offset += 32
    return names


def catalog_lod(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return {"name": path.name, "error": str(exc)}
    sig = data[:4]
    names = lod_dir_names(data)
    suffixes: dict[str, int] = {}
    for name in names:
        suffix = ""
        if "." in name:
            suffix = "." + name.rsplit(".", 1)[-1].casefold()
        suffixes[suffix or "(none)"] = suffixes.get(suffix or "(none)", 0) + 1
    interest = [
        name
        for name in names
        if any(name.casefold().endswith(s) for s in LOD_INTEREST_SUFFIX)
    ]
    return {
        "name": path.name,
        "signature": sig.decode("latin-1", errors="replace"),
        "entry_count": len(names),
        "suffix_counts": suffixes,
        "source_entries": interest,
        "truncated": len(names) >= LOD_INDEX_LIMIT,
        "bodies_extracted": False,
    }


def patch_files(game_path: Path, root: Path) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for name in PATCH_FILES:
        path = find_child(game_path, name)
        if path is not None and path.is_file():
            found.append(describe_file(path, root))
    return found


def distribution_clues(game_path: Path) -> dict[str, Any]:
    steam = []
    for name in STEAM_CLUES:
        path = find_child(game_path, name)
        if path is not None:
            steam.append(path.name)
    gog = []
    for child in iter_children(game_path):
        if child.is_file() and child.name.casefold().startswith(
            GOG_PREFIX
        ):
            gog.append(child.name)
    kind = "unknown"
    if steam and not gog:
        kind = "steam"
    elif gog and not steam:
        kind = "gog"
    elif steam and gog:
        kind = "mixed"
    return {
        "kind": kind,
        "steam_files": steam,
        "gog_files": gog,
        "evidence": "VERIFIED_LOCAL" if steam or gog else "HYPOTHESIS",
    }


def unpacked_sources(
    data_dir: Path,
    root: Path,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    samples: dict[str, list[str]] = {}
    truncated = False
    seen = 0
    try:
        for current, dirnames, filenames in os.walk(data_dir):
            dirnames.sort(key=str.casefold)
            for name in sorted(filenames, key=str.casefold):
                path = Path(current) / name
                suffix = path.suffix.casefold()
                if suffix not in UNPACKED_SUFFIXES:
                    continue
                seen += 1
                if seen > MAX_LIST_FILES:
                    truncated = True
                    break
                counts[suffix] = counts.get(suffix, 0) + 1
                bucket = samples.setdefault(suffix, [])
                if len(bucket) < 12:
                    bucket.append(rel_to(path, root))
            if truncated:
                break
    except OSError:
        pass
    return {
        "counts": counts,
        "samples": samples,
        "truncated": truncated,
        "note": (
            "Имена unpacked файлов — inventory, не контент. "
            "В git не копировать."
        ),
    }


def top_level(game_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for child in iter_children(game_path):
        rows.append(
            {
                "name": child.name,
                "kind": "dir" if child.is_dir() else "file",
                "size": file_size(child) if child.is_file() else None,
            }
        )
    return rows


def render_markdown(report: dict[str, Any]) -> str:
    exe = report.get("executable") or {}
    clues = report.get("distribution") or {}
    lods = report.get("lod_files") or []
    expected = report.get("expected_lods") or []
    lines = [
        "# MM6 Local Installation Audit",
        f"Status: RUN {report.get('created_utc', '')}",
        "",
        "Read-only. Полный JSON: `reports/mm6_audit.json` (gitignore).",
        "",
        "## Game path",
        f"- Install: `{report.get('game_path')}`",
        f"- Data dir: `{report.get('data_dir')}`",
        f"- Evidence: {report.get('path_evidence', 'HYPOTHESIS')}",
        "",
        "## Executable",
    ]
    if exe:
        lines.append(
            f"- `{exe.get('name')}` size={exe.get('size')} "
            f"SHA-256 `{exe.get('sha256')}`"
        )
    else:
        lines.append("- MM6.exe не найден.")
    lines.extend(
        [
            "",
            "## Distribution",
            f"- kind: `{clues.get('kind')}`",
            f"- Evidence: {clues.get('evidence')}",
            "",
            "## LOD archives",
        ]
    )
    present = [item["name"] for item in expected if item.get("present")]
    missing = [
        item["name"] for item in expected if not item.get("present")
    ]
    lines.append(f"- present expected: {', '.join(present) or '—'}")
    lines.append(f"- missing expected: {', '.join(missing) or '—'}")
    lines.append(f"- lod count on disk: {len(lods)}")
    catalogs = report.get("lod_catalogs") or []
    if catalogs:
        lines.extend(["", "## LOD source index (names only)"])
        for cat in catalogs:
            lines.append(
                f"- `{cat.get('name')}`: {cat.get('entry_count')} entries"
            )
            sources = cat.get("source_entries") or []
            if sources:
                preview = ", ".join(sources[:24])
                extra = len(sources) - min(len(sources), 24)
                tail = f" … +{extra}" if extra > 0 else ""
                lines.append(f"  sources: {preview}{tail}")
    patches = report.get("patch_files") or []
    if patches:
        lines.extend(["", "## Patch / text overlay"])
        for item in patches:
            lines.append(f"- `{item.get('name')}` size={item.get('size')}")
    unpacked = report.get("unpacked") or {}
    lines.extend(["", "## Unpacked sources (if any)"])
    counts = unpacked.get("counts") or {}
    if counts:
        for suffix, count in sorted(counts.items()):
            lines.append(f"- `{suffix}`: {count}")
    else:
        lines.append("- нет .blv/.odm/.evt рядом с Data.")
    lines.extend(
        [
            "",
            "## Notes",
            "- Контент lod в git не копировать.",
            "- Дальше: NPC/quest/item extract в normalized JSON.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report(game_path: Path) -> dict[str, Any]:
    data_dir = find_data_dir(game_path)
    exe = find_exe(game_path)
    lods, expected = list_lods(data_dir, game_path)
    extra_root = []
    if data_dir != game_path:
        extra, _ = list_lods(game_path, game_path)
        extra_root = extra
    exe_info = None
    if exe is not None:
        exe_info = describe_file(exe, game_path, with_hash=True)
    catalogs = []
    for item in lods:
        rel = item.get("relative")
        if not rel:
            continue
        path = game_path / Path(rel)
        if path.is_file():
            catalogs.append(catalog_lod(path))
    return {
        "schema_version": 1,
        "created_utc": utc_now(),
        "game_path": str(game_path.resolve()),
        "data_dir": str(data_dir.resolve()),
        "path_evidence": "VERIFIED_LOCAL",
        "executable": exe_info,
        "distribution": distribution_clues(game_path),
        "patch_files": patch_files(game_path, game_path),
        "top_level": top_level(game_path),
        "lod_files": lods,
        "lod_files_root": extra_root,
        "expected_lods": expected,
        "lod_catalogs": catalogs,
        "unpacked": unpacked_sources(data_dir, game_path),
        "read_only": True,
    }


def write_reports(
    report: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "mm6_audit.json"
    md_path = output_dir / "MM6_AUDIT.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit_mm6.py",
        description=(
            "Read-only inventory of a Might and Magic VI install."
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
        default=DEFAULT_OUTPUT_DIR,
        help="Куда писать JSON/MD. По умолчанию reports/.",
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
    report = build_report(game_path)
    json_path, md_path = write_reports(report, args.output_dir)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    exe = report.get("executable")
    if exe and exe.get("sha256"):
        print(f"exe SHA-256: {exe['sha256']}")
    else:
        print("Предупреждение: MM6.exe не найден.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
