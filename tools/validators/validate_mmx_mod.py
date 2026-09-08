"""Validate MM6X overlay связность: registry ↔ loca ↔ dialog ↔ CSV.

Читает каталоги/реестр и уже сгенерированный mod/. В игру не пишет.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

TOOLS = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TOOLS / "converters"))
sys.path.insert(0, str(TOOLS / "validators"))

from mmx_dialog import (  # noqa: E402
    dialog_names,
    load_json as load_dialog_json,
    parse_dialog_root,
    render_npc_dialog,
)
from mmx_ids import AllocError, registry_slot  # noqa: E402
from mmx_loca import (  # noqa: E402
    LANGS,
    catalog_for_lang,
    load_json as load_loca_json,
    merge_loca_keys,
    parse_loca_ids,
)
from mmx_staticdata import (  # noqa: E402
    TABLES,
    build_tables,
    load_json as load_sd_json,
    parse_csv_data,
)
from validate_id_registry import validate_registry  # noqa: E402

DEFAULT_REGISTRY = TOOLS / "converters" / "id_registry.json"
DEFAULT_LOCA_CATALOG = TOOLS / "converters" / "loca_catalog.json"
DEFAULT_DIALOG_CATALOG = (
    TOOLS / "converters" / "dialog_catalog.json"
)
DEFAULT_SD_CATALOG = (
    TOOLS / "converters" / "staticdata_catalog.json"
)
DEFAULT_MOD = REPO_ROOT / "mod"


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_values(
    registry: dict[str, Any],
    namespace: str,
) -> set[str]:
    found: set[str] = set()
    for entry in registry.get("entries") or []:
        for slot in entry.get("slots") or []:
            if slot.get("namespace") != namespace:
                continue
            value = slot.get("value")
            if value is None:
                continue
            found.add(str(value))
    return found


def walk_dialog_loca(node: Any, out: set[str]) -> None:
    if isinstance(node, dict):
        key = node.get("locaKey")
        if isinstance(key, str) and key:
            out.add(key)
        for value in node.values():
            walk_dialog_loca(value, out)
    elif isinstance(node, list):
        for item in node:
            walk_dialog_loca(item, out)


def walk_dialog_refs(
    node: Any,
    out: list[tuple[str, str]],
) -> None:
    if isinstance(node, dict):
        if "ref" in node and "slot" in node:
            ref = node.get("ref")
            slot = node.get("slot")
            if isinstance(ref, str) and isinstance(slot, str):
                out.append((ref, slot))
        for value in node.values():
            walk_dialog_refs(value, out)
    elif isinstance(node, list):
        for item in node:
            walk_dialog_refs(item, out)


def dialog_xml_loca_keys(xml_text: str) -> set[str]:
    root = parse_dialog_root(xml_text)
    keys: set[str] = set()
    for text in root.iter("text"):
        key = text.get("locaKey")
        if key:
            keys.add(key)
    return keys


def check_registry(
    registry: dict[str, Any],
    errors: list[str],
) -> None:
    for item in validate_registry(registry):
        _err(errors, f"registry: {item}")


def check_loca_catalog(
    registry: dict[str, Any],
    catalog: dict[str, Any],
    errors: list[str],
) -> list[str]:
    try:
        keys = merge_loca_keys(registry, catalog)
    except ValueError as exc:
        _err(errors, f"loca catalog: {exc}")
        return []
    for lang in LANGS:
        try:
            catalog_for_lang(catalog, keys, lang)
        except ValueError as exc:
            _err(errors, f"loca catalog/{lang}: {exc}")
    return keys


def check_mod_loca(
    mod_dir: Path,
    expected: list[str],
    errors: list[str],
) -> None:
    want = set(expected)
    for lang in LANGS:
        path = mod_dir / "Localisation" / lang / "loca.xml"
        if not path.is_file():
            _err(errors, f"нет {path}")
            continue
        try:
            ids = parse_loca_ids(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _err(errors, f"loca/{lang}: {exc}")
            continue
        have = set(ids)
        missing = sorted(want - have)
        extra = sorted(have - want)
        if missing:
            _err(
                errors,
                f"loca/{lang}: нет ключей {', '.join(missing)}",
            )
        if extra:
            _err(
                errors,
                f"loca/{lang}: лишние {', '.join(extra)}",
            )
        if len(ids) != len(have):
            _err(errors, f"loca/{lang}: дубликаты id")


def check_dialogs(
    registry: dict[str, Any],
    catalog: dict[str, Any],
    loca_keys: set[str],
    mod_dir: Path,
    errors: list[str],
) -> None:
    try:
        names = dialog_names(catalog)
    except Exception as exc:  # noqa: BLE001
        _err(errors, f"dialog catalog: {exc}")
        return
    dialogs = catalog.get("dialogs") or {}
    registry_dialogs = registry_values(registry, "dialog")
    for name in names:
        if name not in registry_dialogs:
            _err(
                errors,
                f"dialog {name}: нет в registry.dialog",
            )
        keys: set[str] = set()
        refs: list[tuple[str, str]] = []
        walk_dialog_loca(dialogs[name], keys)
        walk_dialog_refs(dialogs[name], refs)
        missing = sorted(keys - loca_keys)
        if missing:
            _err(
                errors,
                f"dialog {name}: нет loca "
                f"{', '.join(missing)}",
            )
        for ref, slot in refs:
            try:
                value = registry_slot(registry, ref, slot)
            except AllocError as exc:
                _err(errors, f"dialog {name}: {exc}")
                continue
            if value is None:
                _err(
                    errors,
                    f"dialog {name}: {ref}/{slot} null",
                )
        try:
            xml = render_npc_dialog(registry, dialogs[name])
            parse_dialog_root(xml)
        except Exception as exc:  # noqa: BLE001
            _err(errors, f"dialog {name} render: {exc}")
            continue
        path = mod_dir / "Dialog" / f"{name}.xml"
        if not path.is_file():
            _err(errors, f"нет {path}")
            continue
        try:
            disk = path.read_text(encoding="utf-8")
            disk_keys = dialog_xml_loca_keys(disk)
        except (OSError, ET.ParseError, ValueError) as exc:
            _err(errors, f"{path.name}: {exc}")
            continue
        if disk_keys != keys:
            _err(
                errors,
                f"{path.name}: locaKey != catalog",
            )
    orphan = sorted(registry_dialogs - set(names))
    for name in orphan:
        _err(
            errors,
            f"registry.dialog {name}: нет в dialog_catalog",
        )


def _col_index(header: list[str], name: str) -> int | None:
    try:
        return header.index(name)
    except ValueError:
        return None


def check_staticdata(
    registry: dict[str, Any],
    catalog: dict[str, Any],
    loca_keys: set[str],
    mod_dir: Path,
    errors: list[str],
) -> None:
    try:
        built = build_tables(registry, catalog)
    except Exception as exc:  # noqa: BLE001
        _err(errors, f"staticdata catalog: {exc}")
        return
    npc_ids = registry_values(registry, "npc")
    step_ids = registry_values(registry, "quest_step")
    obj_ids = registry_values(registry, "quest_objective")
    token_ids = registry_values(registry, "token")
    lore_ids = registry_values(registry, "lorebook")
    dialog_ids = registry_values(registry, "dialog")

    for name in TABLES:
        path = mod_dir / "StaticData" / name
        if not path.is_file():
            _err(errors, f"нет {path}")
            continue
        try:
            disk = path.read_text(encoding="utf-8")
        except OSError as exc:
            _err(errors, f"{name}: {exc}")
            continue
        if disk != built[name]:
            _err(
                errors,
                f"{name}: != regenerate из catalog",
            )
        header, rows = parse_csv_data(disk)
        sid_i = _col_index(header, "StaticID")
        if sid_i is None:
            _err(errors, f"{name}: нет StaticID")
            continue
        for row in rows:
            if sid_i >= len(row):
                _err(errors, f"{name}: короткая строка")
                continue
            sid = row[sid_i]
            if name == "NpcStaticData.csv":
                if sid not in npc_ids:
                    _err(errors, f"NPC {sid}: нет в registry")
                ck_i = _col_index(header, "ConversationKey")
                nk_i = _col_index(header, "NameKey")
                if ck_i is not None and ck_i < len(row):
                    conv = row[ck_i]
                    if conv not in dialog_ids:
                        _err(
                            errors,
                            f"NPC {sid}: dialog {conv!r}",
                        )
                if nk_i is not None and nk_i < len(row):
                    if row[nk_i] not in loca_keys:
                        _err(
                            errors,
                            f"NPC {sid}: NameKey "
                            f"{row[nk_i]!r}",
                        )
            elif name == "QuestSteps.csv":
                if sid not in step_ids:
                    _err(
                        errors,
                        f"QuestStep {sid}: нет в registry",
                    )
                obj_i = _col_index(header, "Objectives")
                npc_i = _col_index(header, "GivenByNPCID")
                tok_i = _col_index(header, "TokenID")
                if obj_i is not None and obj_i < len(row):
                    for part in row[obj_i].split(";"):
                        part = part.strip().strip('"')
                        if not part:
                            continue
                        oid = part.split(",", 1)[0]
                        if oid not in obj_ids:
                            _err(
                                errors,
                                f"QuestStep {sid}: "
                                f"obj {oid}",
                            )
                if npc_i is not None and npc_i < len(row):
                    if row[npc_i] not in npc_ids:
                        _err(
                            errors,
                            f"QuestStep {sid}: NPC "
                            f"{row[npc_i]}",
                        )
                if tok_i is not None and tok_i < len(row):
                    tok = row[tok_i]
                    if tok not in ("0", "") and tok not in token_ids:
                        _err(
                            errors,
                            f"QuestStep {sid}: Token {tok}",
                        )
            elif name == "QuestObjectives.csv":
                if sid not in obj_ids:
                    _err(
                        errors,
                        f"QuestObj {sid}: нет в registry",
                    )
                tok_i = _col_index(header, "TokenID")
                npc_i = _col_index(header, "NpcID")
                if tok_i is not None and tok_i < len(row):
                    tok = row[tok_i]
                    if tok not in ("0", "") and tok not in token_ids:
                        _err(
                            errors,
                            f"QuestObj {sid}: Token {tok}",
                        )
                if npc_i is not None and npc_i < len(row):
                    npc = row[npc_i]
                    if npc not in ("0", "") and npc not in npc_ids:
                        _err(
                            errors,
                            f"QuestObj {sid}: NPC {npc}",
                        )
            elif name == "Token.csv":
                if sid not in token_ids:
                    _err(errors, f"Token {sid}: нет в registry")
                name_i = _col_index(header, "Name")
                if name_i is not None and name_i < len(row):
                    if row[name_i] not in loca_keys:
                        _err(
                            errors,
                            f"Token {sid}: Name "
                            f"{row[name_i]!r}",
                        )
            elif name == "LoreBookStaticData.csv":
                if sid not in lore_ids:
                    _err(
                        errors,
                        f"LoreBook {sid}: нет в registry",
                    )
                for col in ("TitleKey", "TextKey", "AuthorKey"):
                    col_i = _col_index(header, col)
                    if col_i is None or col_i >= len(row):
                        continue
                    key = row[col_i]
                    if key and key not in loca_keys:
                        _err(
                            errors,
                            f"LoreBook {sid}: {col} {key!r}",
                        )


def validate_mod(
    *,
    registry_path: Path,
    loca_catalog: Path,
    dialog_catalog: Path,
    staticdata_catalog: Path,
    mod_dir: Path,
) -> list[str]:
    errors: list[str] = []
    for path in (
        registry_path,
        loca_catalog,
        dialog_catalog,
        staticdata_catalog,
    ):
        if not path.is_file():
            return [f"нет файла: {path}"]
    try:
        registry = _load(registry_path)
        loca_cat = load_loca_json(loca_catalog)
        dialog_cat = load_dialog_json(dialog_catalog)
        sd_cat = load_sd_json(staticdata_catalog)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"JSON: {exc}"]

    check_registry(registry, errors)
    expected = check_loca_catalog(registry, loca_cat, errors)
    loca_set = set(expected)
    if expected:
        check_mod_loca(mod_dir, expected, errors)
    check_dialogs(
        registry,
        dialog_cat,
        loca_set,
        mod_dir,
        errors,
    )
    check_staticdata(
        registry,
        sd_cat,
        loca_set,
        mod_dir,
        errors,
    )
    check_new_sorpigal_map(registry, mod_dir, errors)
    return errors


def check_new_sorpigal_map(
    registry: dict[str, Any],
    mod_dir: Path,
    errors: list[str],
) -> None:
    """Greybox New_Sorpigal.xml (M4-001) if present."""
    map_names = registry_values(registry, "map")
    if "New_Sorpigal" not in map_names:
        return
    path = mod_dir / "Maps" / "New_Sorpigal.xml"
    if not path.is_file():
        _err(errors, "нет mod/Maps/New_Sorpigal.xml (M4-001)")
        return
    try:
        text = path.read_text(encoding="utf-8")
        root = ET.fromstring(text)
    except (OSError, ET.ParseError) as exc:
        _err(errors, f"map New_Sorpigal: {exc}")
        return
    if root.tag != "Grid":
        _err(errors, "map New_Sorpigal: корень не Grid")
    name = root.findtext("Name")
    if name != "New_Sorpigal":
        _err(errors, f"map Name={name!r}")
    width = root.findtext("Width")
    height = root.findtext("Height")
    if width != "24" or height != "18":
        _err(errors, f"map size {width}x{height} != 24x18")
    slots = list(root.iter("Slot"))
    if len(slots) != 24 * 18:
        _err(errors, f"map slots={len(slots)} != 432")
    if "SpawnObjectType>PARTY" not in text:
        _err(errors, "map: нет PARTY")
    if "NPC_IDS,20000" not in text or "NPC_IDS,20001" not in text:
        _err(errors, "map: нет stub Janis/Andover NPC_IDS")
    if 'Enabled>false</Enabled>' not in text:
        _err(errors, "map: ожидается disabled gate ENTRANCE")


def run_self_test() -> None:
    registry = {
        "schema_version": 1,
        "id_band": {"floor": 20000, "ceil": 29999},
        "entries": [
            {
                "stable_id": "mm6.npc.demo",
                "kind": "npc",
                "slots": [
                    {
                        "namespace": "npc",
                        "value": 20000,
                        "status": "reserved",
                    },
                    {
                        "namespace": "dialog",
                        "value": "DemoDialog",
                        "status": "reserved",
                    },
                    {
                        "namespace": "loca",
                        "value": "NPC_NAME_DEMO",
                        "status": "reserved",
                    },
                ],
            }
        ],
    }
    assert not validate_registry(registry)
    assert registry_values(registry, "npc") == {"20000"}
    keys: set[str] = set()
    walk_dialog_loca(
        {"texts": [{"locaKey": "A"}], "entries": [{"locaKey": "B"}]},
        keys,
    )
    assert keys == {"A", "B"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_mmx_mod.py",
        description=(
            "Связность MM6X overlay (registry/loca/dialog/CSV)."
        ),
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
    )
    parser.add_argument(
        "--loca-catalog",
        type=Path,
        default=DEFAULT_LOCA_CATALOG,
    )
    parser.add_argument(
        "--dialog-catalog",
        type=Path,
        default=DEFAULT_DIALOG_CATALOG,
    )
    parser.add_argument(
        "--staticdata-catalog",
        type=Path,
        default=DEFAULT_SD_CATALOG,
    )
    parser.add_argument(
        "--mod-dir",
        type=Path,
        default=DEFAULT_MOD,
        help="Корень staged mod/.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Юнит-проверки без mod/.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        print("self-test OK")
        return 0
    errors = validate_mod(
        registry_path=args.registry,
        loca_catalog=args.loca_catalog,
        dialog_catalog=args.dialog_catalog,
        staticdata_catalog=args.staticdata_catalog,
        mod_dir=args.mod_dir,
    )
    if errors:
        print(f"FAIL ({len(errors)})", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    print(
        f"OK mod={args.mod_dir} "
        "registry/loca/dialog/staticdata связны"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
