"""Build MMX Dialog XML for MM6X slice NPCs.

VERIFIED_SOURCE: vanilla DunstanDialog / TorstenDialog patterns.
"""

from __future__ import annotations

import json
from typing import Any
from xml.etree import ElementTree as ET

from mmx_ids import AllocError, registry_slot

NS = "http://www.w3.org/2001/XMLSchema-instance"
XSD = "http://www.w3.org/2001/XMLSchema"
DECL = '<?xml version="1.0" encoding="utf-8"?>'


class DialogError(ValueError):
    """Invalid dialog tree or registry slot."""


def resolve_ref(
    registry: dict[str, Any],
    stable_id: str,
    namespace: str,
) -> Any:
    try:
        value = registry_slot(registry, stable_id, namespace)
    except AllocError as exc:
        raise DialogError(str(exc)) from exc
    if value is None:
        raise DialogError(
            f"слот {stable_id} {namespace} не назначен"
        )
    return value


def _resolve_attr(
    registry: dict[str, Any],
    key: str,
    raw: Any,
) -> str:
    if isinstance(raw, dict) and "ref" in raw:
        slot = raw.get("slot")
        if not slot:
            raise DialogError(f"нет slot у ref для {key}")
        return str(resolve_ref(registry, raw["ref"], slot))
    return str(raw)


def _attr_line(attrs: dict[str, str]) -> str:
    if not attrs:
        return ""
    parts = [f'{key}="{val}"' for key, val in attrs.items()]
    return " " + " ".join(parts)


def render_condition(
    registry: dict[str, Any],
    item: dict[str, Any],
    indent: str,
) -> str:
    attrs: dict[str, str] = {"xsi:type": item["type"]}
    if "failState" in item:
        attrs["failState"] = str(item["failState"])
    for key in (
        "questID",
        "objectiveID",
        "tokenID",
        "npcID",
        "map",
        "class",
        "race",
        "gender",
        "dayTime",
        "repairType",
        "privilegeID",
        "rewardID",
    ):
        if key not in item:
            continue
        attrs[key] = _resolve_attr(registry, key, item[key])
    return f"{indent}<condition{_attr_line(attrs)} />"


def render_function(
    registry: dict[str, Any],
    item: dict[str, Any],
    indent: str,
) -> str:
    attrs: dict[str, str] = {"xsi:type": item["type"]}
    for key in (
        "dialogID",
        "questID",
        "objectiveID",
        "tokenID",
        "npcID",
        "targetSpawnerID",
        "containerID",
        "mapName",
        "conditionTarget",
        "price",
        "failState",
    ):
        if key not in item:
            continue
        attrs[key] = _resolve_attr(registry, key, item[key])
    return f"{indent}<function{_attr_line(attrs)} />"


def render_dialog(
    registry: dict[str, Any],
    node: dict[str, Any],
    indent: str,
) -> list[str]:
    attrs: dict[str, str] = {"id": str(node["id"])}
    for key in node:
        if key.startswith("hide"):
            attrs[key] = str(node[key])
    if "randomText" in node:
        attrs["randomText"] = str(node["randomText"])
    if "fakeNpcID" in node:
        attrs["fakeNpcID"] = str(node["fakeNpcID"])
    lines = [f"{indent}<dialog{_attr_line(attrs)}>"]
    pad = indent + "\t"
    for text in node.get("texts") or []:
        conditions = text.get("conditions") or []
        if not conditions:
            lines.append(
                f'{pad}<text locaKey="{text["locaKey"]}" />'
            )
            continue
        lines.append(f'{pad}<text locaKey="{text["locaKey"]}">')
        for cond in conditions:
            lines.append(render_condition(registry, cond, pad + "\t"))
        lines.append(f"{pad}</text>")
    for entry in node.get("entries") or []:
        lines.append(f"{pad}<entry>")
        inner = pad + "\t"
        lines.append(
            f'{inner}<text locaKey="{entry["locaKey"]}" />'
        )
        for cond in entry.get("conditions") or []:
            lines.append(render_condition(registry, cond, inner))
        for func in entry.get("functions") or []:
            lines.append(render_function(registry, func, inner))
        lines.append(f"{pad}</entry>")
    lines.append(f"{indent}</dialog>")
    return lines


def render_npc_dialog(
    registry: dict[str, Any],
    spec: dict[str, Any],
) -> str:
    root_id = str(spec.get("rootDialogID", 1))
    lines = [
        DECL,
        (
            f'<NpcConversationStaticData rootDialogID="{root_id}" '
            f'xmlns:xsi="{NS}" xmlns:xsd="{XSD}">'
        ),
    ]
    for offer_id in spec.get("offers") or []:
        lines.append(f'\t<offer id="{offer_id}" />')
    for node in spec.get("dialogs") or []:
        lines.extend(render_dialog(registry, node, "\t"))
    lines.append("</NpcConversationStaticData>")
    lines.append("")
    return "\n".join(lines)


def load_json(path: Any) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_dialog_root(xml_text: str) -> ET.Element:
    start = xml_text.find("<NpcConversationStaticData")
    if start < 0:
        raise DialogError("нет NpcConversationStaticData")
    return ET.fromstring(xml_text[start:])


def dialog_names(catalog: dict[str, Any]) -> list[str]:
    dialogs = catalog.get("dialogs")
    if not isinstance(dialogs, dict):
        raise DialogError("catalog.dialogs должен быть объектом")
    return sorted(dialogs.keys())


def run_self_test() -> None:
    registry = {
        "entries": [
            {
                "stable_id": "mm6.quest_stage.new_sorpigal.goblinwatch.accept",
                "slots": [
                    {"namespace": "quest_step", "value": 20000},
                ],
            },
            {
                "stable_id": "mm6.item.goblinwatch.key",
                "slots": [
                    {"namespace": "token", "value": 20001},
                ],
            },
        ]
    }
    spec = {
        "rootDialogID": 1,
        "dialogs": [
            {
                "id": 1,
                "texts": [{"locaKey": "X"}],
                "entries": [
                    {
                        "locaKey": "Y",
                        "functions": [
                            {
                                "type": "QuestFunction",
                                "questID": {
                                    "ref": (
                                        "mm6.quest_stage."
                                        "new_sorpigal.goblinwatch.accept"
                                    ),
                                    "slot": "quest_step",
                                },
                                "dialogID": 2,
                            }
                        ],
                    }
                ],
            }
        ],
    }
    xml = render_npc_dialog(registry, spec)
    root = parse_dialog_root(xml)
    func = root.find(".//function")
    assert func is not None
    assert func.get("questID") == "20000"
    assert 'xsi:type="QuestFunction"' in xml
    assert "<condition" not in xml or "xmlns:xsi" not in xml.split(
        "<condition",
        1,
    )[-1][:80]
