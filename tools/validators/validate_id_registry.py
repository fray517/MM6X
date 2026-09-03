"""Validate MM6X id_registry.json (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "converters"))
sys.path.insert(0, str(TOOLS / "validators"))

from mmx_ids import (  # noqa: E402
    BAND_CEIL,
    BAND_FLOOR,
    NAMESPACES,
)
from validate_mm6_model import ID_RE, KINDS  # noqa: E402

DEFAULT_REGISTRY = TOOLS / "converters" / "id_registry.json"
SLOT_KEYS = ("namespace", "value", "status")
STATUSES = ("unassigned", "reserved", "bound")
ENTRY_KEYS = ("stable_id", "kind", "slots")


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_slot(
    slot: Any,
    prefix: str,
    errors: list[str],
    seen: dict[str, set[str]],
) -> None:
    if not isinstance(slot, dict):
        _err(errors, f"{prefix}: не объект")
        return
    extra = set(slot) - set(SLOT_KEYS)
    if extra:
        _err(errors, f"{prefix}: лишние поля {sorted(extra)}")
    for key in SLOT_KEYS:
        if key not in slot:
            _err(errors, f"{prefix}: нет {key}")
            return
    namespace = slot["namespace"]
    if namespace not in NAMESPACES:
        _err(errors, f"{prefix}.namespace: {namespace!r}")
        return
    status = slot["status"]
    if status not in STATUSES:
        _err(errors, f"{prefix}.status: {status!r}")
    value = slot["value"]
    kind = NAMESPACES[namespace]["kind"]
    if status == "unassigned":
        if value is not None:
            _err(errors, f"{prefix}: unassigned должен быть value=null")
        return
    if value is None:
        _err(errors, f"{prefix}: reserved/bound нужен value")
        return
    if kind == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            _err(errors, f"{prefix}.value: нужен int")
            return
        if value < BAND_FLOOR or value > BAND_CEIL:
            _err(errors, f"{prefix}.value: вне полосы {value}")
    elif not isinstance(value, str) or not value:
        _err(errors, f"{prefix}.value: нужна непустая строка")
        return
    key = str(value).casefold()
    bucket = seen.setdefault(namespace, set())
    if key in bucket:
        _err(errors, f"{prefix}: дубликат {namespace}={value!r}")
    else:
        bucket.add(key)


def validate_registry(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["корень должен быть объектом"]
    if payload.get("schema_version") != 1:
        _err(errors, "schema_version должен быть 1")
    band = payload.get("id_band")
    if not isinstance(band, dict):
        _err(errors, "id_band: нужен объект")
    else:
        if band.get("floor") != BAND_FLOOR:
            _err(errors, f"id_band.floor должен быть {BAND_FLOOR}")
        if band.get("ceil") != BAND_CEIL:
            _err(errors, f"id_band.ceil должен быть {BAND_CEIL}")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        _err(errors, "entries: нужен непустой список")
        return errors
    seen_ids: set[str] = set()
    seen_slots: dict[str, set[str]] = {}
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            _err(errors, f"{prefix}: не объект")
            continue
        extra = set(entry) - set(ENTRY_KEYS)
        if extra:
            _err(errors, f"{prefix}: лишние поля {sorted(extra)}")
        for key in ENTRY_KEYS:
            if key not in entry:
                _err(errors, f"{prefix}: нет {key}")
                break
        else:
            ident = entry["stable_id"]
            kind = entry["kind"]
            if not isinstance(ident, str) or not ID_RE.match(ident):
                _err(errors, f"{prefix}.stable_id: {ident!r}")
            elif ident in seen_ids:
                _err(errors, f"{prefix}.stable_id дубликат {ident}")
            else:
                seen_ids.add(ident)
                expected = ident.split(".")[1]
                if kind != expected:
                    _err(
                        errors,
                        f"{prefix}: kind {kind!r} != {expected!r}",
                    )
            if kind not in KINDS:
                _err(errors, f"{prefix}.kind: {kind!r}")
            slots = entry["slots"]
            if not isinstance(slots, list):
                _err(errors, f"{prefix}.slots: не список")
            else:
                for slot_i, slot in enumerate(slots):
                    validate_slot(
                        slot,
                        f"{prefix}.slots[{slot_i}]",
                        errors,
                        seen_slots,
                    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_id_registry.py",
        description="Проверка MM6X id_registry.json.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="JSON registry. По умолчанию converters/id_registry.json.",
    )
    args = parser.parse_args(argv)
    path = args.path
    if not path.is_file():
        print(f"Нет файла: {path}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Не прочитан JSON: {exc}", file=sys.stderr)
        return 2
    errors = validate_registry(payload)
    if errors:
        print(f"FAIL {path} ({len(errors)})", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    count = len(payload["entries"])
    print(f"OK {path} entries={count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
