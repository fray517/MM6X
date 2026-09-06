"""Extract New Sorpigal (OutE3) topology slice from MM6.

Read-only. Writes reports/topology_oute3.json (gitignore) and
optionally refreshes references/mm6/new_sorpigal.topology.json
(curated, no proprietary blobs).
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
from mm6_topology import (
    edges_from_evt_slice,
    filter_map,
    nodes_from_2devents,
    parse_2devents_tsv,
    summarize_topology,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_REPORTS = REPO_ROOT / "reports"
DEFAULT_EVT = DEFAULT_REPORTS / "evt_slice.json"
DEFAULT_OUT = DEFAULT_REPORTS / "topology_oute3.json"
DEFAULT_CURATED = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.topology.json"
)
MAP_CODE = "E3"

# Known MapStats destinations for EVT maps (this install).
MAP_TITLES = {
    "D01.blv": ("mm6.dungeon.goblinwatch", "Дозор гоблинов"),
    "D02.blv": ("mm6.dungeon.abandoned_temple", "Заброшенный храм"),
    "D18.Blv": ("mm6.dungeon.garik_forge", "Кузница Гарика"),
    "OutB3.Odm": ("mm6.region.dragonsand", "Драконсэнд"),
}


def load_env(start: Path | None = None) -> None:
    here = (start or REPO_ROOT).resolve()
    for folder in (here, *here.parents):
        candidate = folder / ".env"
        if candidate.is_file():
            env_file = candidate
            break
    else:
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


def resolve_icons(game: Path) -> Path:
    data = find_child(game, "Data") or find_child(game, "data")
    root = data or game
    for name in ("Icons.lod", "icons.lod"):
        path = find_child(root, name)
        if path and path.is_file():
            return path
    raise FileNotFoundError("Icons.lod не найден")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def load_oute3_evt(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for item in payload.get("maps") or []:
        if str(item.get("stem", "")).upper() == "OUTE3":
            return item
    raise ValueError(f"в {path} нет maps stem=OUTE3")


def annotate_edges(
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for edge in edges:
        item = dict(edge)
        key = str(item.get("to_map") or "")
        # case-insensitive match
        match = None
        for cand, meta in MAP_TITLES.items():
            if cand.casefold() == key.casefold():
                match = meta
                break
        if match:
            item["to_stable_id"] = match[0]
            item["to_title"] = match[1]
        out.append(item)
    return out


def curated_payload(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    services = [
        n for n in nodes if n["role"] not in {"residence", "other"}
    ]
    residences = [n for n in nodes if n["role"] == "residence"]
    return {
        "schema_version": 1,
        "id": "mm6.region.new_sorpigal",
        "mapstats_id": 15,
        "map_file": "OutE3.Odm",
        "map_code_2d": "E3",
        "title": "Нью-Сорпигаль",
        "evidence": "VERIFIED_LOCAL",
        "note": (
            "Только топология (узлы/переходы). Координаты ODM "
            "не извлечены — относительный layout HYPOTHESIS "
            "до decode OutE3.Odm."
        ),
        "summary": summary,
        "nodes": services,
        "residence_house_ids": [n["house_id"] for n in residences],
        "edges": annotate_edges(edges),
        "encounter_table": {
            "source": "MapStats.txt #15",
            "mon1": "Goblin / Гоблин",
            "mon2": "PeasantM2 / Ученик мага",
            "evidence": "VERIFIED_LOCAL",
        },
        "travel_notes": [
            {
                "hub_house_id": 48,
                "kind": "stables",
                "schedule_a": "Castle Ironfist D3,M,W,F,2",
                "dest_mapstats": "OutD3.Odm Замок Айронфист",
            },
            {
                "hub_house_id": 57,
                "kind": "boats",
                "schedule_a": "Mist E2,Tu,Th,Sa,3",
                "dest_mapstats": "OutE2.Odm Остров Тумана",
            },
        ],
    }


def run_self_test() -> None:
    sample = (
        "title\n"
        "#\t#\tType\tMap\tPicture\tName\tProprieter Name\t"
        "Title\tPicture\tState\tRep\tPer\tVal\tA\tB\tC\n"
        "89\t89\tTown Hall\tE3\t0\tРатуша\tЖанис\tклерк\t"
        "0\t0\t0\t0\t0\t\t\t\n"
        "2\t2\tWeapon Shop\tD2\t0\tOther\tX\tY\t"
        "0\t0\t0\t0\t0\t\t\t\n"
    )
    rows = parse_2devents_tsv(sample)
    e3 = filter_map(rows, "E3")
    assert len(e3) == 1
    nodes = nodes_from_2devents(e3)
    assert nodes[0]["house_id"] == 89
    assert nodes[0]["role"] == "quest_hub"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_topology.py",
        description="OutE3 topology slice (2DEvents + EVT).",
    )
    parser.add_argument("--game-path", type=Path, default=None)
    parser.add_argument(
        "--evt-slice",
        type=Path,
        default=DEFAULT_EVT,
        help="reports/evt_slice.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        help="Полный отчёт (gitignore reports/).",
    )
    parser.add_argument(
        "--write-curated",
        action="store_true",
        help="Обновить references/mm6/new_sorpigal.topology.json",
    )
    parser.add_argument(
        "--curated-output",
        type=Path,
        default=DEFAULT_CURATED,
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    load_env(REPO_ROOT)
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        print("self-test OK")
        return 0

    game = args.game_path or env_game_path()
    if game is None or not game.is_dir():
        print(
            f"нужен --game-path или {ENV_PATH_KEY}",
            file=sys.stderr,
        )
        return 2
    if not args.evt_slice.is_file():
        print(
            f"нет {args.evt_slice}; сначала extract_mm6_evt.py",
            file=sys.stderr,
        )
        return 2

    try:
        icons = resolve_icons(game.expanduser())
        lod = Mm6Lod(icons)
        blob = lod.read_blob("2DEvents.txt")
        body, how = decode_maybe_compressed(blob)
        text = body.decode("cp1251")
        oute3 = load_oute3_evt(args.evt_slice)
    except (OSError, LodError, ValueError, UnicodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    rows = filter_map(parse_2devents_tsv(text), MAP_CODE)
    nodes = nodes_from_2devents(rows)
    edges = edges_from_evt_slice(oute3)
    summary = summarize_topology(nodes, edges)
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": {
            "game_path": str(game),
            "icons_lod": str(icons),
            "decode": how,
            "evt_slice": str(args.evt_slice),
            "map_code": MAP_CODE,
        },
        "evidence": "VERIFIED_LOCAL",
        "summary": summary,
        "nodes": nodes,
        "edges": annotate_edges(edges),
    }
    curated = curated_payload(nodes, edges, summary)

    print(
        f"OK E3 nodes={summary['node_count']} "
        f"edges={summary['edge_count']} "
        f"by_role={summary['by_role']}"
    )
    for edge in curated["edges"]:
        print(
            f"  transition e{edge['event_id']} "
            f"house={edge.get('house_id')} → {edge.get('to_map')}"
        )

    if args.dry_run:
        print("dry-run: files not written")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.output}")
    if args.write_curated:
        args.curated_output.parent.mkdir(parents=True, exist_ok=True)
        args.curated_output.write_text(
            json.dumps(curated, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.curated_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
