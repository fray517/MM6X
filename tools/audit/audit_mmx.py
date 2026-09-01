"""Read-only audit of a Might & Magic X: Legacy install.

Does not write into the game directory. Hashes only executables
and key DLLs, then writes JSON/Markdown reports.
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
ENV_PATH_KEY = "MMX_GAME_PATH"
DATA_DIR_NAME = "Might and Magic X Legacy_Data"
CHUNK_SIZE = 1024 * 1024
MAX_TREE_FILES = 2000
MAX_LIST_FILES = 5000
GGM_READ_LIMIT = 4 * 1024 * 1024

KEY_ASSEMBLIES = (
    "Legacy.Core.dll",
    "Legacy.Framework.dll",
    "Legacy.Game.dll",
)
EXTRA_HASH_DLLS = (
    "UnityEngine.dll",
    "Assembly-CSharp.dll",
)
STEAM_CLUE_NAMES = (
    "steam_api.dll",
    "steam_api64.dll",
    "steam_appid.txt",
)
UBISOFT_CLUE_NAMES = (
    "upc_r2_loader.dll",
    "upc_r2_loader64.dll",
    "uplay_r1.dll",
    "uplay_r1_loader64.dll",
    "uplay_r1_loader.dll",
)
MODKIT_TOKENS = (
    "modkit",
    "moddingkit",
    "modding-kit",
    "modding_kit",
    "mmxlegacy",
    "mmxl",
    "mapeditor",
)
UNITY_VERSION_RE = re.compile(
    rb"(?:^|[^0-9])"
    rb"("
    rb"[45]\.\d+\.\d+[fpab]\d+"
    rb"|"
    rb"20\d{2}\.\d+\.\d+[fpab]\d+"
    rb")"
    rb"(?:[^0-9]|$)"
)


def load_env(start: Path | None = None) -> None:
    """Load KEY=VALUE from .env without overriding the process env.

    Looks at start/.env, then walks parents. Needed so MMX_GAME_PATH
    can live in the project .env instead of a hardcoded install path.
    """
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
        yield from sorted(directory.iterdir(), key=lambda p: p.name.casefold())
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


def env_game_path() -> Path | None:
    raw = os.environ.get(ENV_PATH_KEY, "").strip().strip('"')
    if not raw:
        return None
    return Path(raw)


def find_data_directory(game_path: Path) -> Path | None:
    exact = find_child(game_path, DATA_DIR_NAME)
    if exact is not None and exact.is_dir():
        return exact
    fallback: list[Path] = []
    for child in iter_children(game_path):
        if not child.is_dir():
            continue
        if not child.name.casefold().endswith("_data"):
            continue
        has_sa = find_child(child, "StreamingAssets") is not None
        has_managed = find_child(child, "Managed") is not None
        if has_sa or has_managed:
            fallback.append(child)
    if len(fallback) == 1:
        return fallback[0]
    if fallback:
        return fallback[0]
    return None


def find_root_executables(game_path: Path) -> list[Path]:
    found: list[Path] = []
    for child in iter_children(game_path):
        if child.is_file() and child.suffix.casefold() == ".exe":
            found.append(child)
    return found


def find_named(directory: Path, names: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for name in names:
        child = find_child(directory, name)
        if child is not None:
            found.append(child)
    return found


def looks_like_modkit(name: str) -> bool:
    folded = name.casefold().replace(" ", "")
    return any(token in folded for token in MODKIT_TOKENS)


def extract_unity_version(data_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "version_candidate": None,
        "evidence": None,
        "sources_checked": [],
        "candidates": [],
    }

    def scan(name: str) -> None:
        path = find_child(data_dir, name)
        if path is None or not path.is_file():
            return
        result["sources_checked"].append(path.name)
        try:
            data = path.read_bytes()[:GGM_READ_LIMIT]
        except OSError:
            return
        matches = [
            item.decode("ascii", errors="ignore")
            for item in UNITY_VERSION_RE.findall(data)
        ]
        for item in matches:
            if item not in result["candidates"]:
                result["candidates"].append(item)

    scan("globalgamemanagers")
    scan("mainData")
    unique = result["candidates"]
    if unique:
        result["version_candidate"] = unique[0]
        result["evidence"] = "HYPOTHESIS"
    boot = find_child(data_dir, "boot.config")
    if boot is not None and boot.is_file():
        result["sources_checked"].append(boot.name)
        result["boot_config"] = True
    else:
        result["boot_config"] = False
    result["globalgamemanagers"] = (
        "globalgamemanagers" in result["sources_checked"]
    )
    result["main_data"] = "mainData" in result["sources_checked"]
    return result


def walk_files(
    root: Path,
    *,
    max_files: int,
) -> tuple[list[Path], bool]:
    collected: list[Path] = []
    truncated = False
    try:
        for current, dirnames, filenames in os.walk(root):
            dirnames.sort(key=str.casefold)
            for name in sorted(filenames, key=str.casefold):
                collected.append(Path(current) / name)
                if len(collected) >= max_files:
                    truncated = True
                    return collected, truncated
    except OSError:
        return collected, truncated
    return collected, truncated


def inventory_tree(
    directory: Path,
    game_path: Path,
    *,
    max_files: int = MAX_TREE_FILES,
) -> dict[str, Any]:
    files, truncated = walk_files(directory, max_files=max_files)
    top_level: list[dict[str, Any]] = []
    for child in iter_children(directory):
        entry: dict[str, Any] = {
            "name": child.name,
            "kind": "dir" if child.is_dir() else "file",
            "size": file_size(child) if child.is_file() else None,
        }
        if child.is_dir():
            nested, _ = walk_files(child, max_files=MAX_LIST_FILES)
            entry["file_count"] = len(nested)
        top_level.append(entry)
    return {
        "found": True,
        "relative": rel_to(directory, game_path),
        "top_level": top_level,
        "file_count": len(files),
        "truncated": truncated,
        "files": [rel_to(path, game_path) for path in files],
    }


def inventory_files(
    directory: Path,
    game_path: Path,
) -> dict[str, Any]:
    files, truncated = walk_files(directory, max_files=MAX_LIST_FILES)
    return {
        "found": True,
        "relative": rel_to(directory, game_path),
        "file_count": len(files),
        "truncated": truncated,
        "files": [
            describe_file(path, game_path)
            for path in files
        ],
    }


def inventory_localisation(
    directory: Path,
    game_path: Path,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for child in iter_children(directory):
        if child.is_dir():
            nested, truncated = walk_files(
                child,
                max_files=MAX_LIST_FILES,
            )
            entries.append(
                {
                    "name": child.name,
                    "kind": "dir",
                    "file_count": len(nested),
                    "truncated": truncated,
                    "files": [
                        rel_to(path, game_path) for path in nested
                    ],
                }
            )
        elif child.is_file():
            entries.append(describe_file(child, game_path))
    return {
        "found": True,
        "relative": rel_to(directory, game_path),
        "entries": entries,
    }


def inventory_managed(
    directory: Path,
    game_path: Path,
) -> dict[str, Any]:
    dlls: list[dict[str, Any]] = []
    key_map: dict[str, dict[str, Any]] = {}
    hash_names = {
        name.casefold()
        for name in (*KEY_ASSEMBLIES, *EXTRA_HASH_DLLS)
    }
    for child in iter_children(directory):
        if not child.is_file():
            continue
        if child.suffix.casefold() != ".dll":
            continue
        hashed = child.name.casefold() in hash_names
        info = describe_file(child, game_path, with_hash=hashed)
        dlls.append(info)
        for key_name in KEY_ASSEMBLIES:
            if child.name.casefold() == key_name.casefold():
                key_map[key_name] = info
    for key_name in KEY_ASSEMBLIES:
        key_map.setdefault(
            key_name,
            {
                "name": key_name,
                "found": False,
            },
        )
        if "found" not in key_map[key_name]:
            key_map[key_name]["found"] = True
    return {
        "found": True,
        "relative": rel_to(directory, game_path),
        "dll_count": len(dlls),
        "dlls": dlls,
        "key_assemblies": key_map,
    }


def detect_modding_kit(
    game_path: Path,
    data_dir: Path | None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def consider(path: Path) -> None:
        marker = str(path.resolve()).casefold()
        if marker in seen or not looks_like_modkit(path.name):
            return
        seen.add(marker)
        candidates.append(
            {
                "name": path.name,
                "relative": rel_to(path, game_path),
                "kind": "dir" if path.is_dir() else "file",
                "size": file_size(path) if path.is_file() else None,
            }
        )

    search_roots = [game_path]
    parent = game_path.parent
    if parent != game_path:
        search_roots.append(parent)
    if data_dir is not None:
        search_roots.append(data_dir)
    for root in search_roots:
        for child in iter_children(root):
            consider(child)
    return {
        "candidates": candidates,
        "searched_roots": [rel_to(root, game_path) for root in search_roots],
    }


def collect_hash_targets(
    game_path: Path,
    managed_dir: Path | None,
) -> list[Path]:
    targets: list[Path] = []
    targets.extend(find_root_executables(game_path))
    targets.extend(find_named(game_path, STEAM_CLUE_NAMES))
    targets.extend(find_named(game_path, UBISOFT_CLUE_NAMES))
    if managed_dir is not None:
        for name in (*KEY_ASSEMBLIES, *EXTRA_HASH_DLLS):
            child = find_child(managed_dir, name)
            if child is not None and child.is_file():
                targets.append(child)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in targets:
        marker = str(path.resolve()).casefold()
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(path)
    return unique


def build_observations(report: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if not report["game"]["data_directory_found"]:
        notes.append(
            "Каталог Unity *_Data не найден. Это может быть не MMX."
        )
    if not report["executables"]:
        notes.append("В корне установки нет .exe.")
    keys = report["managed"].get("key_assemblies", {})
    for name in KEY_ASSEMBLIES:
        info = keys.get(name) or {}
        if not info.get("found"):
            notes.append(f"{name} не найден в Managed.")
    dist = report["distribution"]
    if dist["steam_clues"] and dist["ubisoft_clues"]:
        notes.append(
            "Есть признаки и Steam, и Ubisoft. Сборки не смешивать."
        )
    elif dist["steam_clues"]:
        notes.append("Признаки Steam-дистрибуции.")
    elif dist["ubisoft_clues"]:
        notes.append("Признаки Ubisoft-дистрибуции.")
    if not report["modding_kit"]["candidates"]:
        notes.append(
            "Явных ModdingKit/editor-кандидатов рядом с игрой нет."
        )
    extra = report["streaming_assets"].get("top_level") or []
    known = {"staticdata", "dialog", "localisation", "localization"}
    other = [
        item["name"]
        for item in extra
        if item.get("kind") == "dir"
        and item["name"].casefold() not in known
    ]
    if other:
        notes.append(
            "Дополнительные каталоги StreamingAssets: "
            + ", ".join(other)
        )
    notes.append(
        "Аудит только читал файлы. Каталог игры не изменялся."
    )
    return notes


def audit_install(game_path: Path) -> dict[str, Any]:
    data_dir = find_data_directory(game_path)
    streaming = None
    static_data = None
    dialog = None
    localisation = None
    managed = None
    if data_dir is not None:
        streaming = find_child(data_dir, "StreamingAssets")
        managed = find_child(data_dir, "Managed")
        if streaming is not None:
            static_data = find_child(streaming, "StaticData")
            dialog = find_child(streaming, "Dialog")
            localisation = find_child(streaming, "Localisation")
            if localisation is None:
                localisation = find_child(streaming, "Localization")
    executables = [
        describe_file(path, game_path, with_hash=True)
        for path in find_root_executables(game_path)
    ]
    steam_clues = [
        describe_file(path, game_path, with_hash=path.is_file())
        for path in find_named(game_path, STEAM_CLUE_NAMES)
    ]
    ubisoft_clues = [
        describe_file(path, game_path, with_hash=path.is_file())
        for path in find_named(game_path, UBISOFT_CLUE_NAMES)
    ]
    hashed = [
        describe_file(path, game_path, with_hash=True)
        for path in collect_hash_targets(game_path, managed)
    ]
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_utc": utc_now(),
        "tool": "tools/audit/audit_mmx.py",
        "read_only": True,
        "game": {
            "path": str(game_path.resolve()),
            "exists": game_path.is_dir(),
            "data_directory": (
                rel_to(data_dir, game_path) if data_dir else None
            ),
            "data_directory_found": data_dir is not None,
            "expected_data_directory": DATA_DIR_NAME,
        },
        "executables": executables,
        "distribution": {
            "steam_clues": steam_clues,
            "ubisoft_clues": ubisoft_clues,
        },
        "unity": (
            extract_unity_version(data_dir)
            if data_dir is not None
            else {
                "version_candidate": None,
                "evidence": None,
                "sources_checked": [],
            }
        ),
        "streaming_assets": (
            inventory_tree(streaming, game_path)
            if streaming is not None
            else {"found": False}
        ),
        "static_data": (
            inventory_files(static_data, game_path)
            if static_data is not None
            else {"found": False}
        ),
        "dialog": (
            inventory_files(dialog, game_path)
            if dialog is not None
            else {"found": False}
        ),
        "localisation": (
            inventory_localisation(localisation, game_path)
            if localisation is not None
            else {"found": False}
        ),
        "managed": (
            inventory_managed(managed, game_path)
            if managed is not None
            else {
                "found": False,
                "dlls": [],
                "key_assemblies": {
                    name: {"name": name, "found": False}
                    for name in KEY_ASSEMBLIES
                },
            }
        ),
        "modding_kit": detect_modding_kit(game_path, data_dir),
        "hashed_files": hashed,
    }
    report["observations"] = build_observations(report)
    return report


def md_bool(value: bool) -> str:
    return "yes" if value else "no"


def write_markdown(report: dict[str, Any], path: Path) -> None:
    game = report["game"]
    unity = report["unity"]
    managed = report["managed"]
    lines: list[str] = [
        "# MMX Local Installation Audit",
        "Status: GENERATED",
        "",
        "Отчёт read-only аудита. Файлы игры не изменялись.",
        "",
        "## Game path",
        "",
        f"- Path: `{game['path']}`",
        f"- Unity data dir found: {md_bool(game['data_directory_found'])}",
        f"- Data directory: `{game.get('data_directory') or '—'}`",
        f"- Expected name: `{game['expected_data_directory']}`",
        "- Evidence: VERIFIED_LOCAL",
        "",
        "## Build / distribution",
        "",
        f"- Unity version candidate: "
        f"`{unity.get('version_candidate') or '—'}`",
        f"- Unity evidence: {unity.get('evidence') or '—'}",
        f"- globalgamemanagers: "
        f"{md_bool(bool(unity.get('globalgamemanagers')))}",
        f"- boot.config: {md_bool(bool(unity.get('boot_config')))}",
        "",
        "### Steam clues",
        "",
    ]
    steam = report["distribution"]["steam_clues"]
    if steam:
        for item in steam:
            lines.append(f"- `{item['relative']}` size={item.get('size')}")
    else:
        lines.append("- none")
    lines.extend(["", "### Ubisoft clues", ""])
    ubisoft = report["distribution"]["ubisoft_clues"]
    if ubisoft:
        for item in ubisoft:
            lines.append(f"- `{item['relative']}` size={item.get('size')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Executables and key hashes", ""])
    lines.append("| File | Size | SHA-256 |")
    lines.append("|---|---:|---|")
    hashed = report.get("hashed_files") or []
    if not hashed:
        lines.append("| — | — | — |")
    for item in hashed:
        digest = item.get("sha256") or item.get("hash_error") or "—"
        size = item.get("size")
        lines.append(
            f"| `{item['relative']}` | {size if size is not None else '—'} "
            f"| `{digest}` |"
        )
    sa = report["streaming_assets"]
    lines.extend(["", "## StreamingAssets", ""])
    if not sa.get("found"):
        lines.append("Not found.")
    else:
        lines.append(f"- Path: `{sa['relative']}`")
        lines.append(f"- Listed files: {sa.get('file_count')}")
        lines.append(f"- Truncated: {md_bool(bool(sa.get('truncated')))}")
        lines.append("")
        for item in sa.get("top_level") or []:
            extra = ""
            if item.get("kind") == "dir":
                extra = f" ({item.get('file_count')} files)"
            lines.append(f"- `{item['name']}` — {item['kind']}{extra}")
    for title, key in (
        ("StaticData", "static_data"),
        ("Dialog", "dialog"),
    ):
        block = report[key]
        lines.extend(["", f"## {title}", ""])
        if not block.get("found"):
            lines.append("Not found.")
            continue
        lines.append(f"- Path: `{block['relative']}`")
        lines.append(f"- Files: {block.get('file_count')}")
        lines.append("")
        for item in block.get("files") or []:
            lines.append(f"- `{item['relative']}` ({item.get('size')} bytes)")
    loc = report["localisation"]
    lines.extend(["", "## Localisation", ""])
    if not loc.get("found"):
        lines.append("Not found.")
    else:
        lines.append(f"- Path: `{loc['relative']}`")
        lines.append("")
        for entry in loc.get("entries") or []:
            if entry.get("kind") == "dir":
                lines.append(
                    f"- `{entry['name']}` / {entry.get('file_count')} files"
                )
                for rel in entry.get("files") or []:
                    lines.append(f"  - `{rel}`")
            else:
                lines.append(
                    f"- `{entry.get('relative')}` "
                    f"({entry.get('size')} bytes)"
                )
    lines.extend(["", "## Managed assemblies", ""])
    if not managed.get("found"):
        lines.append("Not found.")
    else:
        lines.append(f"- Path: `{managed['relative']}`")
        lines.append(f"- DLL count: {managed.get('dll_count')}")
        lines.append("")
        lines.append("### Key assemblies")
        lines.append("")
        for name in KEY_ASSEMBLIES:
            info = (managed.get("key_assemblies") or {}).get(name) or {}
            if info.get("found"):
                lines.append(
                    f"- `{name}` size={info.get('size')} "
                    f"sha256=`{info.get('sha256') or '—'}`"
                )
            else:
                lines.append(f"- `{name}` — missing")
        lines.append("")
        lines.append("### All DLLs")
        lines.append("")
        for item in managed.get("dlls") or []:
            extra = ""
            if item.get("sha256"):
                extra = f" sha256=`{item['sha256']}`"
            lines.append(
                f"- `{item['relative']}` ({item.get('size')} bytes){extra}"
            )
    kit = report["modding_kit"]
    lines.extend(["", "## ModdingKit / editor", ""])
    candidates = kit.get("candidates") or []
    if not candidates:
        lines.append("No likely ModdingKit/editor candidates.")
    else:
        for item in candidates:
            lines.append(f"- `{item['relative']}` ({item['kind']})")
    lines.extend(["", "## Observations", ""])
    for note in report.get("observations") or []:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            f"Generated UTC: {report.get('generated_utc')}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="audit_mmx.py",
        description=(
            "Read-only audit of a Might & Magic X: Legacy install. "
            "Game files are never modified."
        ),
        epilog=(
            "PowerShell example:\n"
            "  python tools\\audit\\audit_mmx.py "
            "--game-path "
            "\"D:\\Games\\Might & Magic X - Legacy\""
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        default=None,
        help=(
            "MMX installation directory. Overrides "
            f"{ENV_PATH_KEY} from .env."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for mmx_audit.json and MMX_AUDIT.md.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = parse_args(argv)
    game_path = args.game_path or env_game_path()
    if game_path is None:
        print(
            "Укажите --game-path или задайте "
            f"{ENV_PATH_KEY} в .env.",
            file=sys.stderr,
        )
        return 2
    game_path = game_path.expanduser()
    if not game_path.exists():
        print(f"Каталог не найден: {game_path}", file=sys.stderr)
        return 2
    if not game_path.is_dir():
        print(f"Ожидался каталог: {game_path}", file=sys.stderr)
        return 2
    report = audit_install(game_path)
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "mmx_audit.json"
    md_path = output_dir / "MMX_AUDIT.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown(report, md_path)
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
