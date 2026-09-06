"""Extract New Sorpigal encounter profile (MapStats + monster tiers).

Read-only. Does not copy sprite art. Includes D01 as quest-adjacent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mm6_encounters import (
    encounter_profile,
    parse_mapstats_rows,
    parse_monster_tiers,
    row_by_id,
)
from mm6_lod import LodError, Mm6Lod, decode_maybe_compressed

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH_KEY = "MM6_GAME_PATH"
DEFAULT_OUT = REPO_ROOT / "reports" / "encounters_oute3.json"
DEFAULT_CURATED = (
    REPO_ROOT / "references" / "mm6" / "new_sorpigal.encounters.json"
)
OUTDOOR_ID = 15
DUNGEON_ID = 16


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


def enrich_tiers(
    profile: dict[str, Any],
    monsters_txt: str,
) -> dict[str, Any]:
    item = dict(profile)
    enriched = []
    for slot in profile["monsters"]:
        entry = dict(slot)
        entry["tiers"] = parse_monster_tiers(
            monsters_txt,
            slot["pic_stem"],
        )
        enriched.append(entry)
    item["monsters"] = enriched
    return item


def curated_payload(
    outdoor: dict[str, Any],
    dungeon: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "id": "mm6.region.new_sorpigal.encounters",
        "region": "mm6.region.new_sorpigal",
        "evidence": "VERIFIED_LOCAL",
        "note": (
            "MapStats random encounters. Exact ODM spawn XY not "
            "decoded — placement on MMX grid is HYPOTHESIS "
            "(route town→Goblinwatch)."
        ),
        "outdoor": outdoor,
        "quest_dungeon": dungeon,
        "m4_design": {
            "required": True,
            "fidelity": "F1",
            "intent": (
                "At least one outdoor Goblin pack on the walk "
                "from Town Hall toward Goblinwatch entrance; "
                "optional PeasantM2 (mage apprentice) pack."
            ),
            "mmx_binding": "HYPOTHESIS — map Trigger MONSTER / spawn later",
            "d01_encounters": "M5 (not M4 greybox blocker)",
        },
    }


def run_self_test() -> None:
    sample = (
        "a\nb\n"
        "#\tName\tFile name\t#\tDay\tDays\t0-10\t0-10\t0-6\t%\t%\t%\t%\t"
        "Mon1 Pic\tMon 1\t1-5\t#\tMon2 Pic\tMon 2\t1-5\t#\t"
        "Mon3 Pic\tMon 3\t1-5\t#\tTrack\tMap Designer\n"
        "15\tNS\tOutE3.Odm\t0\t0\t168\t0\t1\t6\t10\t50\t50\t0\t"
        "Goblin\tГоблин\t1\t3-5\tPeasantM2\tУченик\t1\t3-5\t"
        "0\t0\t1\t1-4\t2\tPeter\n"
    )
    rows = parse_mapstats_rows(sample)
    row = row_by_id(rows, 15)
    assert row is not None
    profile = encounter_profile(row)
    assert profile["enc_chance_pct"] == 10
    assert len(profile["monsters"]) == 2
    assert profile["monsters"][0]["pic_stem"] == "Goblin"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_mm6_encounters.py",
        description="OutE3 (+D01) MapStats encounter slice.",
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
        ms_text, how_ms = read_txt(lod, "MapStats.txt")
        mon_text, how_mon = read_txt(lod, "MONSTERS.TXT")
    except (OSError, LodError, UnicodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    rows = parse_mapstats_rows(ms_text)
    out_row = row_by_id(rows, OUTDOOR_ID)
    dun_row = row_by_id(rows, DUNGEON_ID)
    if out_row is None or dun_row is None:
        print("нет MapStats #15/#16", file=sys.stderr)
        return 1

    outdoor = enrich_tiers(encounter_profile(out_row), mon_text)
    dungeon = enrich_tiers(encounter_profile(dun_row), mon_text)
    curated = curated_payload(outdoor, dungeon)
    report = {
        "schema_version": 1,
        "created_utc": utc_now(),
        "source": {
            "game_path": str(game),
            "icons_lod": str(icons),
            "mapstats_how": how_ms,
            "monsters_how": how_mon,
        },
        "evidence": "VERIFIED_LOCAL",
        **curated,
    }

    print(
        f"OK outdoor enc%={outdoor['enc_chance_pct']} "
        f"slots={len(outdoor['monsters'])} "
        f"d01 slots={len(dungeon['monsters'])}"
    )
    for slot in outdoor["monsters"]:
        print(
            f"  OutE3 M{slot['slot']}: {slot['pic_stem']} "
            f"{slot['name']} {slot['chance_pct']}% "
            f"n={slot['count_range']} tiers={len(slot['tiers'])}"
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
