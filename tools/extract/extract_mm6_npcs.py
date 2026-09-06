"""Extract New Sorpigal NPC list (NPCdata on E3 houses).

Read-only. Uses topology house_ids. Shop proprietors from
2DEvents are listed separately (not NPCdata dialogue NPCs).
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
from mm6_npcs import (
    classify_npc,
    filter_npcs_on_houses,
    parse_npcdata,
    parse_npcprof,
    stable_id_for,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_TOPOLOGY = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.topology.json"
)
DEFAULT_OUT = REPO_ROOT / "reports" / "npcs_oute3.json"
DEFAULT_CURATED = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.npcs.json"
)


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


def read_txt(lod: Mm6Lod, name: str) -> tuple[str, str]:
    body, how = decode_maybe_compressed(lod.read_blob(name))
    return body.decode("cp1251"), how


def house_set(topology: dict[str, Any]) -> tuple[set[int], dict[int, str]]:
    houses: set[int] = set()
    names: dict[int, str] = {}
    for node in topology.get("nodes") or []:
        hid = node.get("house_id")
        if isinstance(hid, int):
            houses.add(hid)
            names[hid] = str(node.get("name") or "")
    for hid in topology.get("residence_house_ids") or []:
        if isinstance(hid, int):
            houses.add(hid)
            names.setdefault(hid, "Дом")
    return houses, names


def service_agents(topology: dict[str, Any]) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    for node in topology.get("nodes") or []:
        prop = (node.get("proprietor") or "").strip()
        if not prop:
            continue
        agents.append(
            {
                "house_id": node.get("house_id"),
                "house_name": node.get("name"),
                "house_type": node.get("type"),
                "proprietor": prop,
                "title": node.get("title") or "",
                "kind": "2d_proprietor",
                "evidence": "VERIFIED_LOCAL",
                "note": (
                    "Имя из 2DEvents, не строка NPCdata "
                    "(кроме Жанис #291)."
                ),
            }
        )
    return agents


def curated_payload(
    npcs: list[dict[str, Any]],
    agents: list[dict[str, Any]],
) -> dict[str, Any]:
    enriched = []
    by_f: dict[str, int] = {}
    for npc in npcs:
        item = dict(npc)
        item["fidelity"] = classify_npc(npc)
        sid = stable_id_for(npc)
        if sid:
            item["stable_id"] = sid
        by_f[item["fidelity"]] = by_f.get(item["fidelity"], 0) + 1
        enriched.append(item)
    return {
        "schema_version": 1,
        "id": "mm6.region.new_sorpigal.npcs",
        "region": "mm6.region.new_sorpigal",
        "evidence": "VERIFIED_LOCAL",
        "note": (
            "NPCdata rows whose 2D Location is an E3 house. "
            "Service UI proprietors listed under service_agents."
        ),
        "summary": {
            "npc_count": len(enriched),
            "by_fidelity": by_f,
            "service_agent_count": len(agents),
        },
        "npcs": enriched,
        "service_agents": agents,
        "m4_required": [
            item["mm6_npc_id"]
            for item in enriched
            if item["fidelity"] in {"F0", "F1"}
        ],
    }


def run_self_test() -> None:
    sample = (
        "hdr\n"
        "#\tName\tPic\tState\tFame\tRep\t2D Location\t"
        "1-76\tY\tY\tA\tB\tC\tNotes\n"
        "291\tЖанис\t1\t0\t0\t0\t89\t72\t0\t0\t3\t0\t0\tx\n"
        "9\tOther\t1\t0\t0\t0\t1\t0\t0\t0\t0\t0\t0\ty\n"
    )
    rows = parse_npcdata(sample)
    found = filter_npcs_on_houses(
        rows,
        {89},
        {72: "Клерк"},
        {89: "Ратуша"},
    )
    assert len(found) == 1
    assert found[0]["mm6_npc_id"] == 291
    assert classify_npc(found[0]) == "F0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_npcs.py",
        description="New Sorpigal NPC list from NPCdata (E3).",
    )
    parser.add_argument("--game-path", type=Path, default=None)
    parser.add_argument(
        "--topology",
        type=Path,
        default=DEFAULT_TOPOLOGY,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--write-curated",
        action="store_true",
        help="Обновить references/mm6/new_sorpigal.npcs.json",
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
    if not args.topology.is_file():
        print(f"нет topology: {args.topology}", file=sys.stderr)
        return 2

    try:
        topology = json.loads(
            args.topology.read_text(encoding="utf-8")
        )
        houses, house_names = house_set(topology)
        icons = resolve_icons(game.expanduser())
        lod = Mm6Lod(icons)
        npc_text, how_npc = read_txt(lod, "NPCdata.txt")
        prof_text, how_prof = read_txt(lod, "npcprof.txt")
    except (OSError, LodError, ValueError, UnicodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    professions = parse_npcprof(prof_text)
    npcs = filter_npcs_on_houses(
        parse_npcdata(npc_text),
        houses,
        professions,
        house_names,
    )
    agents = service_agents(topology)
    curated = curated_payload(npcs, agents)
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": {
            "game_path": str(game),
            "icons_lod": str(icons),
            "npcdata_how": how_npc,
            "npcprof_how": how_prof,
            "topology": str(args.topology),
        },
        "evidence": "VERIFIED_LOCAL",
        **curated,
    }

    summary = curated["summary"]
    print(
        f"OK npcs={summary['npc_count']} "
        f"by_f={summary['by_fidelity']} "
        f"agents={summary['service_agent_count']}"
    )
    for npc in curated["npcs"]:
        if npc["fidelity"] in {"F0", "F1", "F2"}:
            print(
                f"  [{npc['fidelity']}] #{npc['mm6_npc_id']} "
                f"{npc['name']} @ {npc['house_id']} "
                f"{npc['house_name']}"
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
