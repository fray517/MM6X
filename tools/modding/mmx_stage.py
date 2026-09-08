"""Merge MM6X overlay into MMX StreamingAssets (backup + restore).

Partial loca/CSV must be merged, never wholesale-replaced.
Dialog files are copied as new or overwrite-with-backup.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
from pathlib import Path
from typing import Any

from mmx_manifest import sha256_file, verify_manifest

LOCA_ENTRY_RE = re.compile(
    r'<LocaData id="([^"]+)">(.*?)</LocaData>',
    re.DOTALL,
)


class StageError(ValueError):
    """Invalid stage plan or merge."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_text_preserve(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    has_bom = data.startswith(b"\xef\xbb\xbf")
    return data.decode("utf-8-sig"), has_bom


def encode_text(text: str, has_bom: bool) -> bytes:
    payload = text.encode("utf-8")
    if has_bom:
        payload = b"\xef\xbb\xbf" + payload
    return payload


def parse_loca_map(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in LOCA_ENTRY_RE.finditer(text):
        key = match.group(1)
        if key in found:
            raise StageError(f"дубликат loca {key}")
        found[key] = match.group(2)
    return found


def merge_loca(vanilla: str, overlay: str) -> tuple[str, list[str]]:
    """Upsert overlay keys into vanilla loca XML text."""
    overlay_map = parse_loca_map(overlay)
    if not overlay_map:
        raise StageError("overlay loca пуст")
    keys = sorted(overlay_map)
    text = vanilla
    missing: list[str] = []
    for key in keys:
        inner = overlay_map[key]
        start_tag = f'<LocaData id="{key}">'
        start = text.find(start_tag)
        if start < 0:
            missing.append(key)
            continue
        if text.find(start_tag, start + 1) != -1:
            raise StageError(f"дубликат в vanilla: {key}")
        value_start = start + len(start_tag)
        value_end = text.find("</LocaData>", value_start)
        if value_end < 0:
            raise StageError(f"нет закрытия {key}")
        text = text[:value_start] + inner + text[value_end:]
    if missing:
        close = "</Localization>"
        idx = text.rfind(close)
        if idx < 0:
            raise StageError("нет </Localization>")
        block = "".join(
            f'  <LocaData id="{key}">{overlay_map[key]}'
            f"</LocaData>\n"
            for key in missing
        )
        text = text[:idx] + block + text[idx:]
    return text, keys


def parse_csv_table(
    text: str,
) -> tuple[list[str], list[str], list[list[str]]]:
    comments: list[str] = []
    data_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            comments.append(line)
            continue
        data_lines.append(line)
    if not data_lines:
        raise StageError("CSV без данных")
    rows = list(csv.reader(io.StringIO("\n".join(data_lines))))
    header = rows[0]
    return comments, header, rows[1:]


def render_csv_table(
    comments: list[str],
    header: list[str],
    rows: list[list[str]],
) -> str:
    buf = io.StringIO(newline="")
    for line in comments:
        buf.write(line.rstrip("\n") + "\n")
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def merge_csv(vanilla: str, overlay: str) -> tuple[str, list[str]]:
    """Replace/append overlay rows by StaticID; keep vanilla header."""
    v_comments, v_header, v_rows = parse_csv_table(vanilla)
    _, o_header, o_rows = parse_csv_table(overlay)
    if [str(c) for c in o_header] != [str(c) for c in v_header]:
        raise StageError(
            f"header mismatch: overlay={o_header!r} "
            f"vanilla={v_header!r}"
        )
    try:
        sid_i = v_header.index("StaticID")
    except ValueError as exc:
        raise StageError("нет StaticID") from exc
    index: dict[str, int] = {}
    for i, row in enumerate(v_rows):
        if sid_i >= len(row):
            raise StageError("короткая vanilla-строка")
        index[row[sid_i]] = i
    touched: list[str] = []
    for row in o_rows:
        if sid_i >= len(row):
            raise StageError("короткая overlay-строка")
        sid = row[sid_i]
        touched.append(sid)
        if sid in index:
            v_rows[index[sid]] = row
        else:
            index[sid] = len(v_rows)
            v_rows.append(row)
    return render_csv_table(v_comments, v_header, v_rows), touched


def resolve_stage_target(
    data_dir: Path,
    stage_rel: str,
) -> Path:
    parts = stage_rel.split("/")
    if not parts or parts[0] != "StreamingAssets":
        raise StageError(
            f"stage_rel вне StreamingAssets: {stage_rel}"
        )
    current = data_dir
    for part in parts:
        nxt = None
        wanted = part.casefold()
        if current.is_dir():
            for child in current.iterdir():
                if child.name.casefold() == wanted:
                    nxt = child
                    break
        if nxt is None:
            if part == parts[-1]:
                return (current / part).resolve()
            raise StageError(f"нет каталога {part} в {current}")
        current = nxt
    return current.resolve()


def assert_under_data(data_dir: Path, target: Path) -> None:
    try:
        target.resolve().relative_to(data_dir.resolve())
    except ValueError as exc:
        raise StageError(
            "цель вне Data; запись запрещена"
        ) from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def plan_from_manifest(
    mod_dir: Path,
    manifest: dict[str, Any],
    data_dir: Path,
) -> list[dict[str, Any]]:
    errors = verify_manifest(mod_dir, manifest)
    if errors:
        raise StageError("; ".join(errors[:5]))
    actions: list[dict[str, Any]] = []
    for item in manifest["files"]:
        rel = item["path"]
        kind = item["kind"]
        stage_rel = item["stage_rel"]
        src = mod_dir / Path(*rel.split("/"))
        if not src.is_file():
            raise StageError(f"нет источника {rel}")
        if sha256_file(src) != item["sha256"]:
            raise StageError(f"sha mismatch {rel}")
        target = resolve_stage_target(data_dir, stage_rel)
        assert_under_data(data_dir, target)
        existed = target.is_file()
        action: dict[str, Any] = {
            "kind": kind,
            "path": rel,
            "stage_rel": stage_rel,
            "source_sha256": item["sha256"],
            "target": str(target),
            "existed": existed,
        }
        if kind in ("dialog", "map"):
            action["mode"] = "copy"
        elif kind == "loca":
            action["mode"] = "merge_keys"
            if not existed:
                raise StageError(
                    f"нет vanilla loca для merge: {stage_rel}"
                )
        elif kind == "staticdata":
            action["mode"] = "merge_rows"
            if not existed:
                raise StageError(
                    f"нет vanilla CSV для merge: {stage_rel}"
                )
        elif kind == "config":
            action["mode"] = "patch_start"
            if not existed:
                raise StageError(
                    f"нет vanilla config для patch: {stage_rel}"
                )
        else:
            raise StageError(f"unknown kind {kind}")
        actions.append(action)
    return actions


START_LINE_RE = re.compile(
    r'(?m)^(\s*start\s*=\s*)"[^"]*"'
)


def parse_config_start(overlay: str) -> str:
    """Read start map name from overlay config fragment."""
    match = START_LINE_RE.search(overlay)
    if not match:
        raise StageError("overlay config: нет start = \"...\"")
    # Re-parse quoted value
    line = match.group(0)
    value = re.search(r'"([^"]*)"', line)
    if not value:
        raise StageError("overlay config: пустой start")
    name = value.group(1).strip()
    if not name:
        raise StageError("overlay config: start пуст")
    return name


def patch_config_start(vanilla: str, start_map: str) -> str:
    """Replace only the [map] start= line (VERIFIED_LOCAL schema)."""
    patched, count = START_LINE_RE.subn(
        rf'\1"{start_map}"',
        vanilla,
        count=1,
    )
    if count != 1:
        raise StageError(
            "vanilla config.txt: не найден ровно один start ="
        )
    return patched


def _backup_name(stage_rel: str) -> str:
    return stage_rel.replace("/", "__")


def apply_actions(
    *,
    actions: list[dict[str, Any]],
    mod_dir: Path,
    backup_dir: Path,
    dry_run: bool,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if not dry_run:
        backup_dir.mkdir(parents=True, exist_ok=True)
        (backup_dir / "files").mkdir(parents=True, exist_ok=True)

    for action in actions:
        kind = action["kind"]
        src = mod_dir / Path(*action["path"].split("/"))
        target = Path(action["target"])
        record = dict(action)
        if kind in ("dialog", "map"):
            if action["existed"]:
                data = target.read_bytes()
                digest = sha256_bytes(data)
                record["backup_sha256"] = digest
                record["backup"] = _backup_name(
                    action["stage_rel"]
                )
                if not dry_run:
                    dest = backup_dir / "files" / record["backup"]
                    dest.write_bytes(data)
            else:
                record["backup"] = None
                record["backup_sha256"] = None
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
                if sha256_file(target) != action["source_sha256"]:
                    raise StageError(
                        f"после copy sha != source {target}"
                    )
            records.append(record)
            continue

        vanilla_text, has_bom = read_text_preserve(target)
        overlay_text, _ = read_text_preserve(src)
        digest = sha256_bytes(
            encode_text(vanilla_text, has_bom)
        )
        record["backup_sha256"] = digest
        record["backup"] = _backup_name(action["stage_rel"])
        record["has_bom"] = has_bom
        if kind == "loca":
            merged, keys = merge_loca(vanilla_text, overlay_text)
            record["keys"] = keys
        elif kind == "staticdata":
            merged, sids = merge_csv(vanilla_text, overlay_text)
            record["static_ids"] = sids
        elif kind == "config":
            start_map = parse_config_start(overlay_text)
            merged = patch_config_start(vanilla_text, start_map)
            record["start"] = start_map
        else:
            raise StageError(f"unexpected merge kind {kind}")
        if not dry_run:
            dest = backup_dir / "files" / record["backup"]
            dest.write_bytes(encode_text(vanilla_text, has_bom))
            target.write_bytes(encode_text(merged, has_bom))
        records.append(record)

    return {
        "schema_version": 1,
        "actions": records,
    }


def restore_actions(
    *,
    apply_doc: dict[str, Any],
    backup_dir: Path,
    dry_run: bool,
) -> list[str]:
    """Restore from backup. Returns log lines."""
    logs: list[str] = []
    actions = apply_doc.get("actions")
    if not isinstance(actions, list):
        raise StageError("apply.json: нет actions")
    for action in reversed(actions):
        target = Path(action["target"])
        kind = action["kind"]
        if kind in ("dialog", "map") and not action.get("existed"):
            if target.is_file():
                logs.append(f"delete {target}")
                if not dry_run:
                    target.unlink()
            else:
                logs.append(f"already absent {target}")
            continue
        backup_name = action.get("backup")
        if not backup_name:
            raise StageError(
                f"нет backup для {action.get('path')}"
            )
        backup_path = backup_dir / "files" / backup_name
        if not backup_path.is_file():
            raise StageError(f"нет файла backup {backup_path}")
        data = backup_path.read_bytes()
        expected = action.get("backup_sha256")
        if expected and sha256_bytes(data) != expected:
            raise StageError(
                f"backup sha mismatch {backup_name}"
            )
        logs.append(f"restore {target}")
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return logs


def run_self_test(tmp: Path) -> None:
    from mmx_manifest import build_manifest, write_manifest

    vanilla_loca = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<Localization>\n"
        '  <LocaData id="KEEP">keep</LocaData>\n'
        "</Localization>\n"
    )
    overlay_loca = (
        "<Localization>\n"
        '  <LocaData id="NEW">new</LocaData>\n'
        '  <LocaData id="KEEP">changed</LocaData>\n'
        "</Localization>\n"
    )
    merged, keys = merge_loca(vanilla_loca, overlay_loca)
    assert "NEW" in keys and "KEEP" in keys
    assert 'id="KEEP">changed<' in merged
    assert 'id="NEW">new<' in merged

    vanilla_csv = "# comment\nStaticID,Name\n1,A\n2,B\n"
    overlay_csv = "# overlay\nStaticID,Name\n2,B2\n3,C\n"
    out, sids = merge_csv(vanilla_csv, overlay_csv)
    assert sids == ["2", "3"]
    assert "2,B2" in out and "3,C" in out and "1,A" in out

    vanilla_cfg = '[map]\nstart = "Sorpigal"\nmaxLevel = 50\n'
    assert parse_config_start('start = "New_Sorpigal"\n') == (
        "New_Sorpigal"
    )
    patched = patch_config_start(vanilla_cfg, "New_Sorpigal")
    assert 'start = "New_Sorpigal"' in patched
    assert "maxLevel = 50" in patched

    data = tmp / "Might and Magic X Legacy_Data"
    sa = data / "StreamingAssets"
    (sa / "Dialog").mkdir(parents=True)
    (sa / "Localisation" / "en").mkdir(parents=True)
    (sa / "StaticData").mkdir(parents=True)
    (sa / "Localisation" / "en" / "loca.xml").write_text(
        vanilla_loca,
        encoding="utf-8",
    )
    (sa / "StaticData" / "Token.csv").write_text(
        vanilla_csv,
        encoding="utf-8",
    )

    mod = tmp / "mod"
    (mod / "Dialog").mkdir(parents=True)
    (mod / "Localisation" / "en").mkdir(parents=True)
    (mod / "StaticData").mkdir(parents=True)
    (mod / "Dialog" / "Mm6Demo.xml").write_text(
        "<NpcConversationStaticData/>\n",
        encoding="utf-8",
    )
    (mod / "Localisation" / "en" / "loca.xml").write_text(
        overlay_loca,
        encoding="utf-8",
    )
    (mod / "StaticData" / "Token.csv").write_text(
        overlay_csv,
        encoding="utf-8",
    )
    manifest = build_manifest(mod)
    write_manifest(mod / "build_manifest.json", manifest)
    actions = plan_from_manifest(mod, manifest, data)
    assert len(actions) == 3
    backup = tmp / "backup"
    apply_doc = apply_actions(
        actions=actions,
        mod_dir=mod,
        backup_dir=backup,
        dry_run=False,
    )
    write_json(backup / "apply.json", apply_doc)
    loca_now = (sa / "Localisation" / "en" / "loca.xml").read_text(
        encoding="utf-8"
    )
    assert 'id="NEW">new<' in loca_now
    assert (sa / "Dialog" / "Mm6Demo.xml").is_file()
    restore_actions(
        apply_doc=apply_doc,
        backup_dir=backup,
        dry_run=False,
    )
    assert not (sa / "Dialog" / "Mm6Demo.xml").exists()
    restored = (
        sa / "Localisation" / "en" / "loca.xml"
    ).read_text(encoding="utf-8")
    assert restored == vanilla_loca
