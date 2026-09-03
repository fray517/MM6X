"""Build MMX loca.xml overlay from the ID registry + catalog.

Only MM6X keys. Does not copy vanilla loca. MMX stores paragraph
breaks as the two characters backslash + n (VERIFIED_LOCAL).
"""

from __future__ import annotations

import json
from typing import Any
from xml.etree import ElementTree as ET

DECL = '<?xml version="1.0" encoding="utf-8"?>'
COMMENT = "<!--Might & Magic - Legacy-->"
ROOT_OPEN = (
    "<Localization "
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
)
ROOT_CLOSE = "</Localization>"
LANGS = ("en", "ru")


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def loca_inner(text: str) -> str:
    """JSON newlines -> MMX \\n in element text."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return xml_escape(normalized).replace("\n", "\\n")


def loca_keys(registry: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for entry in registry.get("entries") or []:
        for slot in entry.get("slots") or []:
            if slot.get("namespace") != "loca":
                continue
            value = slot.get("value")
            if not isinstance(value, str) or not value:
                continue
            if value in seen:
                continue
            seen.add(value)
            keys.append(value)
    return keys


def load_json(path: Any) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_for_lang(
    catalog: dict[str, Any],
    keys: list[str],
    lang: str,
) -> list[tuple[str, str]]:
    strings = catalog.get("strings")
    if not isinstance(strings, dict):
        raise ValueError("catalog.strings должен быть объектом")
    rows: list[tuple[str, str]] = []
    missing: list[str] = []
    for key in keys:
        item = strings.get(key)
        if not isinstance(item, dict) or lang not in item:
            missing.append(key)
            continue
        text = item[lang]
        if not isinstance(text, str) or not text:
            missing.append(key)
            continue
        rows.append((key, text))
    if missing:
        raise ValueError(
            f"нет {lang} строк: {', '.join(missing)}"
        )
    return rows


def render_loca(rows: list[tuple[str, str]]) -> str:
    lines = [DECL, COMMENT, ROOT_OPEN]
    for key, text in rows:
        inner = loca_inner(text)
        lines.append(f'  <LocaData id="{key}">{inner}</LocaData>')
    lines.append(ROOT_CLOSE)
    lines.append("")
    return "\n".join(lines)


def parse_loca_ids(xml_text: str) -> list[str]:
    start = xml_text.find("<Localization")
    if start < 0:
        raise ValueError("нет Localization")
    root = ET.fromstring(xml_text[start:])
    if root.tag != "Localization":
        raise ValueError(f"корень {root.tag!r}, ждут Localization")
    ids: list[str] = []
    for child in root:
        if child.tag != "LocaData":
            raise ValueError(f"лишний тег {child.tag}")
        ident = child.get("id")
        if not ident:
            raise ValueError("LocaData без id")
        ids.append(ident)
    return ids


def run_self_test() -> None:
    assert loca_inner("a & b") == "a &amp; b"
    assert loca_inner("a\nb") == "a\\nb"
    xml = render_loca([("NPC_NAME_MM6_JANIS", "Janis")])
    assert parse_loca_ids(xml) == ["NPC_NAME_MM6_JANIS"]
    assert "<LocaData id=\"NPC_NAME_MM6_JANIS\">Janis</LocaData>" in xml
    registry = {
        "entries": [
            {
                "slots": [
                    {"namespace": "loca", "value": "A"},
                    {"namespace": "npc", "value": 1},
                    {"namespace": "loca", "value": "A"},
                    {"namespace": "loca", "value": "B"},
                ]
            }
        ]
    }
    assert loca_keys(registry) == ["A", "B"]
