"""Extract New Sorpigal exits/travel (topology + evt_slice).

Does not read the game install if reports/topology already exist.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mm6_travel import (
    build_exits,
    build_return_links,
    build_scheduled_travel,
    parse_hub_schedule,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TOPOLOGY = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.topology.json"
)
DEFAULT_EVT = REPO_ROOT / "reports" / "evt_slice.json"
DEFAULT_OUT = REPO_ROOT / "reports" / "travel_oute3.json"
DEFAULT_CURATED = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.travel.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def load_d01_moves(evt_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(evt_path.read_text(encoding="utf-8"))
    for item in payload.get("maps") or []:
        if str(item.get("stem", "")).upper() == "D01":
            return list(item.get("move_to_map") or [])
    return []


def curated_payload(
    topology: dict[str, Any],
    d01_moves: list[dict[str, Any]],
) -> dict[str, Any]:
    exits = build_exits(list(topology.get("edges") or []))
    returns = build_return_links(d01_moves)
    hubs = build_scheduled_travel(
        list(topology.get("travel_notes") or [])
    )
    m4 = [
        item["id"]
        for item in exits + returns
        if item.get("fidelity") == "F0"
    ]
    return {
        "schema_version": 1,
        "id": "mm6.region.new_sorpigal.travel",
        "region": "mm6.region.new_sorpigal",
        "evidence": "VERIFIED_LOCAL",
        "note": (
            "Outbound OUTE3.EVT MoveToMap + D01 return + "
            "stables/boats schedules. Spawn XYZ are MM6 coords, "
            "not MMX cells."
        ),
        "summary": {
            "outbound_exits": len(exits),
            "return_links": len(returns),
            "scheduled_hubs": len(hubs),
        },
        "m4_required": m4,
        "exits_outbound": exits,
        "exits_return": returns,
        "scheduled_travel": hubs,
        "m4_design": {
            "required_links": [
                "Town ↔ Goblinwatch (#171 / D01 e51)",
            ],
            "stub_ok": [
                "D02 / D18 entrances",
                "OutB3 outdoor edge",
                "Stables → Ironfist",
                "Boats → Mist",
            ],
        },
    }


def run_self_test() -> None:
    parsed = parse_hub_schedule("Castle Ironfist D3,M,W,F,2")
    assert parsed["map_code"] == "D3"
    assert parsed["days"] == ["M", "W", "F"]
    assert parsed["cost"] == 2
    mist = parse_hub_schedule("Mist E2,Tu,Th,Sa,3")
    assert mist["map_code"] == "E2"
    assert mist["days"] == ["Tu", "Th", "Sa"]
    edges = [
        {
            "kind": "map_transition",
            "from": "mm6.region.new_sorpigal",
            "event_id": 101,
            "house_id": 171,
            "to_map": "D01.blv",
            "spawn": {"x": 1, "y": 2, "z": 3},
            "to_stable_id": "mm6.dungeon.goblinwatch",
            "to_title": "Дозор",
            "evidence": "VERIFIED_LOCAL",
        }
    ]
    exits = build_exits(edges)
    assert exits[0]["fidelity"] == "F0"
    assert exits[0]["requires_item"] == 489


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_travel.py",
        description="New Sorpigal exits/travel curated JSON.",
    )
    parser.add_argument(
        "--topology",
        type=Path,
        default=DEFAULT_TOPOLOGY,
    )
    parser.add_argument(
        "--evt-slice",
        type=Path,
        default=DEFAULT_EVT,
    )
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
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        print("self-test OK")
        return 0

    if not args.topology.is_file():
        print(f"нет {args.topology}", file=sys.stderr)
        return 2
    if not args.evt_slice.is_file():
        print(
            f"нет {args.evt_slice}; сначала extract_mm6_evt.py",
            file=sys.stderr,
        )
        return 2

    try:
        topology = json.loads(
            args.topology.read_text(encoding="utf-8")
        )
        d01_moves = load_d01_moves(args.evt_slice)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    curated = curated_payload(topology, d01_moves)
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": {
            "topology": str(args.topology),
            "evt_slice": str(args.evt_slice),
        },
        "evidence": "VERIFIED_LOCAL",
        **curated,
    }

    summary = curated["summary"]
    print(
        f"OK exits={summary['outbound_exits']} "
        f"returns={summary['return_links']} "
        f"hubs={summary['scheduled_hubs']}"
    )
    for item in curated["exits_outbound"]:
        if item["fidelity"] in {"F0", "F2"}:
            print(
                f"  [{item['fidelity']}] e{item['event_id']} "
                f"→ {item['to_map']} ({item.get('to_title')})"
            )
    for item in curated["exits_return"]:
        print(
            f"  [F0] return e{item['event_id']} "
            f"→ {item['to_map']}"
        )
    for hub in curated["scheduled_travel"]:
        sched = hub["schedule"]
        print(
            f"  [F2] {hub['kind']} #{hub['house_id']} "
            f"→ {hub['dest_title']} "
            f"{sched.get('days')} cost={sched.get('cost')}"
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
