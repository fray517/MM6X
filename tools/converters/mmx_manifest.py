"""Build/verify MM6X mod build_manifest.json.

Inventory of staged overlay files + SHA-256. Does not touch the game.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHUNK = 1024 * 1024
SKIP_NAMES = {
    "README.md",
    "build_manifest.json",
    ".gitkeep",
}
KIND_BY_PREFIX = (
    ("Localisation/", "loca"),
    ("Dialog/", "dialog"),
    ("StaticData/", "staticdata"),
)


class ManifestError(ValueError):
    """Invalid mod tree or manifest."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def classify_kind(rel_posix: str) -> str | None:
    for prefix, kind in KIND_BY_PREFIX:
        if rel_posix.startswith(prefix):
            return kind
    return None


def stage_rel(rel_posix: str) -> str:
    return f"StreamingAssets/{rel_posix}"


def iter_mod_files(mod_dir: Path) -> list[Path]:
    if not mod_dir.is_dir():
        raise ManifestError(f"нет каталога {mod_dir}")
    files: list[Path] = []
    for path in sorted(mod_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        files.append(path)
    return files


def file_entry(mod_dir: Path, path: Path) -> dict[str, Any]:
    rel = path.relative_to(mod_dir).as_posix()
    kind = classify_kind(rel)
    if kind is None:
        raise ManifestError(f"неизвестный путь {rel}")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if sha256_file(path) != digest:
        raise ManifestError(f"hash race {rel}")
    return {
        "path": rel,
        "kind": kind,
        "size": len(data),
        "sha256": digest,
        "stage_rel": stage_rel(rel),
    }


def build_manifest(mod_dir: Path) -> dict[str, Any]:
    entries = [file_entry(mod_dir, path) for path in iter_mod_files(mod_dir)]
    if not entries:
        raise ManifestError(f"пустой mod: {mod_dir}")
    by_kind: dict[str, int] = {}
    for item in entries:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    return {
        "schema_version": 1,
        "created_utc": utc_now(),
        "mod_id": "mm6x",
        "note": (
            "MM6X staged overlay. Not installed until stage CLI. "
            "stage_rel is relative to game Data dir."
        ),
        "counts": by_kind,
        "files": entries,
    }


def verify_manifest(
    mod_dir: Path,
    manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version должен быть 1")
    listed = manifest.get("files")
    if not isinstance(listed, list) or not listed:
        return ["files: нужен непустой список"]
    expected = {
        path.relative_to(mod_dir).as_posix()
        for path in iter_mod_files(mod_dir)
    }
    seen: set[str] = set()
    for index, item in enumerate(listed):
        prefix = f"files[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: не объект")
            continue
        rel = item.get("path")
        if not isinstance(rel, str) or not rel:
            errors.append(f"{prefix}: нет path")
            continue
        if rel in seen:
            errors.append(f"{prefix}: дубликат {rel}")
        seen.add(rel)
        path = mod_dir / Path(*rel.split("/"))
        if not path.is_file():
            errors.append(f"{prefix}: нет файла {rel}")
            continue
        try:
            current = file_entry(mod_dir, path)
        except ManifestError as exc:
            errors.append(f"{prefix}: {exc}")
            continue
        for key in ("kind", "size", "sha256", "stage_rel"):
            if item.get(key) != current[key]:
                errors.append(
                    f"{prefix}.{key}: manifest != disk"
                )
    missing = sorted(expected - seen)
    extra = sorted(seen - expected)
    for rel in missing:
        errors.append(f"на диске нет в manifest: {rel}")
    for rel in extra:
        errors.append(f"в manifest нет на диске: {rel}")
    return errors


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_self_test(tmp: Path) -> None:
    (tmp / "Dialog").mkdir(parents=True)
    sample = tmp / "Dialog" / "Demo.xml"
    sample.write_text("<x/>\n", encoding="utf-8")
    (tmp / "README.md").write_text("doc\n", encoding="utf-8")
    payload = build_manifest(tmp)
    assert payload["counts"] == {"dialog": 1}
    assert payload["files"][0]["path"] == "Dialog/Demo.xml"
    assert payload["files"][0]["stage_rel"].startswith(
        "StreamingAssets/"
    )
    write_manifest(tmp / "build_manifest.json", payload)
    assert not verify_manifest(tmp, payload)
    sample.write_text("<y/>\n", encoding="utf-8")
    assert verify_manifest(tmp, payload)
