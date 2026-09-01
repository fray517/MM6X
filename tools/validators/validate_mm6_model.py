"""Validate a normalized MM6 model JSON file (stdlib only)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = (
    REPO_ROOT / "tools" / "validators" / "fixtures"
    / "mm6_model_example.json"
)

KINDS = (
    "region",
    "location",
    "map_node",
    "route",
    "npc",
    "dialogue",
    "quest",
    "quest_stage",
    "item",
    "monster",
    "encounter",
    "dungeon",
    "secret",
    "trainer",
    "shop",
    "travel_link",
)
KIND_GROUP = "|".join(KINDS)
ID_RE = re.compile(
    r"^mm6\.(" + KIND_GROUP + r")\.[a-z0-9_]+(?:\.[a-z0-9_]+)*$"
)
EVIDENCE = ("VERIFIED_LOCAL", "VERIFIED_SOURCE", "HYPOTHESIS")
FIDELITY = ("F0", "F1", "F2", "F3")
MMX_STATUS = ("unassigned", "reserved", "bound")
SOURCE_KEYS = ("container", "entry", "id", "evidence")
TARGET_KEYS = ("id", "status")
ENTITY_KEYS = (
    "id",
    "kind",
    "title",
    "mm6_source",
    "mmx_target",
    "fidelity",
    "related",
    "notes",
)


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_entity(
    entity: Any,
    index: int,
    errors: list[str],
    seen: set[str],
) -> None:
    prefix = f"entities[{index}]"
    if not isinstance(entity, dict):
        _err(errors, f"{prefix}: не объект")
        return
    extra = set(entity) - set(ENTITY_KEYS)
    if extra:
        _err(errors, f"{prefix}: лишние поля {sorted(extra)}")
    for key in ENTITY_KEYS:
        if key not in entity:
            _err(errors, f"{prefix}: нет поля {key}")
            return
    ident = entity["id"]
    kind = entity["kind"]
    if not isinstance(ident, str) or not ID_RE.match(ident):
        _err(errors, f"{prefix}.id: плохой stable id: {ident!r}")
    elif ident in seen:
        _err(errors, f"{prefix}.id: дубликат {ident}")
    else:
        seen.add(ident)
        expected_kind = ident.split(".")[1]
        if kind != expected_kind:
            _err(
                errors,
                f"{prefix}: kind {kind!r} != id kind {expected_kind!r}",
            )
    if kind not in KINDS:
        _err(errors, f"{prefix}.kind: неизвестный {kind!r}")
    if not isinstance(entity["title"], str) or not entity["title"]:
        _err(errors, f"{prefix}.title: нужна непустая строка")
    source = entity["mm6_source"]
    if not isinstance(source, dict):
        _err(errors, f"{prefix}.mm6_source: не объект")
    else:
        if set(source) != set(SOURCE_KEYS):
            _err(errors, f"{prefix}.mm6_source: состав полей")
        elif source["evidence"] not in EVIDENCE:
            _err(errors, f"{prefix}.mm6_source.evidence")
    target = entity["mmx_target"]
    if not isinstance(target, dict):
        _err(errors, f"{prefix}.mmx_target: не объект")
    else:
        if set(target) != set(TARGET_KEYS):
            _err(errors, f"{prefix}.mmx_target: состав полей")
        elif target["status"] not in MMX_STATUS:
            _err(errors, f"{prefix}.mmx_target.status")
    if entity["fidelity"] not in FIDELITY:
        _err(errors, f"{prefix}.fidelity")
    related = entity["related"]
    if not isinstance(related, list):
        _err(errors, f"{prefix}.related: не список")
    else:
        for item in related:
            if not isinstance(item, str) or not ID_RE.match(item):
                _err(errors, f"{prefix}.related: {item!r}")
    if not isinstance(entity["notes"], str):
        _err(errors, f"{prefix}.notes: не строка")


def validate_model(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["корень должен быть объектом"]
    if payload.get("schema_version") != 1:
        _err(errors, "schema_version должен быть 1")
    entities = payload.get("entities")
    if not isinstance(entities, list) or not entities:
        _err(errors, "entities: нужен непустой список")
        return errors
    seen: set[str] = set()
    for index, entity in enumerate(entities):
        validate_entity(entity, index, errors, seen)
    known = seen
    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            continue
        related = entity.get("related") or []
        if not isinstance(related, list):
            continue
        for item in related:
            if isinstance(item, str) and item not in known:
                _err(
                    errors,
                    f"entities[{index}].related: нет сущности {item}",
                )
    return errors


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_mm6_model.py",
        description="Проверка normalized MM6 JSON.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="JSON модели. По умолчанию example fixture.",
    )
    args = parser.parse_args(argv)
    path = args.path
    if not path.is_file():
        print(f"Нет файла: {path}", file=sys.stderr)
        return 2
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Не прочитан JSON: {exc}", file=sys.stderr)
        return 2
    errors = validate_model(payload)
    if errors:
        print(f"FAIL {path} ({len(errors)})", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    count = len(payload["entities"])
    print(f"OK {path} entities={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
