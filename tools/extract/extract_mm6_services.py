"""Extract New Sorpigal buildings/services from 2DEvents (E3).

Read-only. Curated JSON has stock/hours; no proprietary art.
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
from mm6_services import (
    building_from_2d_row,
    buildings_from_rows,
    fidelity_for_building,
    summarize_buildings,
)
from mm6_topology import filter_map, parse_2devents_tsv

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_OUT = REPO_ROOT / "reports" / "services_oute3.json"
DEFAULT_CURATED = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.services.json"
)
MAP_CODE = "E3"


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


def curated_payload(
    buildings: list[dict[str, Any]],
) -> dict[str, Any]:
    services = [b for b in buildings if b["role"] != "residence"]
    residences = [b for b in buildings if b["role"] == "residence"]
    m4 = [
        b["house_id"]
        for b in services
        if b["fidelity"] in {"F0", "F1"}
    ]
    m4_stub = [
        b["house_id"]
        for b in services
        if b["fidelity"] == "F2"
    ]
    return {
        "schema_version": 1,
        "id": "mm6.region.new_sorpigal.services",
        "region": "mm6.region.new_sorpigal",
        "map_code_2d": MAP_CODE,
        "evidence": "VERIFIED_LOCAL",
        "note": (
            "2DEvents buildings on E3. Stock A/B/C and hours "
            "are MM6 shop params, not MMX prices."
        ),
        "summary": summarize_buildings(buildings),
        "m4_required_houses": m4,
        "m4_stub_ok_houses": m4_stub,
        "buildings": services,
        "residence_house_ids": [b["house_id"] for b in residences],
        "mmx_notes": [
            "Town Hall / Tavern / Goblinwatch gate = landmarks + NPC.",
            "Shops/guilds/temple/bank/training = service shells later.",
            "Do not copy MM6 item tables; keep category + stock labels.",
        ],
    }


def run_self_test() -> None:
    row = {
        "#": "89",
        "Type": "Town Hall",
        "Name": "Ратуша",
        "Proprieter Name": "Жанис",
        "Title": "клерк",
        "Open": "10",
        "Closed": "14",
        "A": "",
        "B": "",
        "C": "",
        "Val": "",
        "Notes:": "",
    }
    item = building_from_2d_row(row)
    assert item is not None
    assert item["category"] == "town_hall"
    assert item["fidelity"] == "F0"
    assert fidelity_for_building(1, "service") == "F3"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_services.py",
        description="E3 buildings/services from 2DEvents.",
    )
    parser.add_argument("--game-path", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--write-curated", action="store_true")
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

    try:
        icons = resolve_icons(game.expanduser())
        lod = Mm6Lod(icons)
        body, how = decode_maybe_compressed(
            lod.read_blob("2DEvents.txt")
        )
        text = body.decode("cp1251")
    except (OSError, LodError, UnicodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    rows = filter_map(parse_2devents_tsv(text), MAP_CODE)
    buildings = buildings_from_rows(rows)
    curated = curated_payload(buildings)
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": {
            "game_path": str(game),
            "icons_lod": str(icons),
            "decode": how,
            "map_code": MAP_CODE,
        },
        "evidence": "VERIFIED_LOCAL",
        **curated,
    }

    summary = curated["summary"]
    print(
        f"OK buildings={summary['building_count']} "
        f"services={summary['non_residence']} "
        f"by_f={summary['by_fidelity_non_residence']}"
    )
    for item in curated["buildings"]:
        if item["fidelity"] in {"F0", "F1", "F2"}:
            print(
                f"  [{item['fidelity']}] #{item['house_id']} "
                f"{item['category']} {item['name']} "
                f"{item['open_hour']}-{item['closed_hour']}"
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
