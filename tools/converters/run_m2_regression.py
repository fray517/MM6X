"""M2 offline regression: fixtures → generate → validate → stage.

Does not touch the real MMX install. Uses vanilla_stub under fixtures.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "m2_demo"
EXPECTED = FIXTURE / "expected"
VANILLA_STUB = FIXTURE / "vanilla_stub"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TOOLS / "validators"))
sys.path.insert(0, str(TOOLS / "modding"))

from mmx_dialog import (  # noqa: E402
    dialog_names,
    load_json as load_dialog_json,
    render_npc_dialog,
)
from mmx_loca import (  # noqa: E402
    LANGS,
    catalog_for_lang,
    load_json as load_loca_json,
    merge_loca_keys,
    render_loca,
)
from mmx_manifest import (  # noqa: E402
    build_manifest,
    verify_manifest,
    write_manifest,
)
from mmx_staticdata import (  # noqa: E402
    TABLES,
    build_tables,
    load_json as load_sd_json,
)
from mmx_stage import (  # noqa: E402
    apply_actions,
    plan_from_manifest,
    restore_actions,
    write_json,
)
from validate_id_registry import validate_registry  # noqa: E402
from validate_mmx_mod import validate_mod  # noqa: E402


def _err(errors: list[str], message: str) -> None:
    errors.append(message)


def generate_mod(out_mod: Path) -> None:
    registry = json.loads(
        (FIXTURE / "id_registry.json").read_text(encoding="utf-8")
    )
    loca_cat = load_loca_json(FIXTURE / "loca_catalog.json")
    dialog_cat = load_dialog_json(FIXTURE / "dialog_catalog.json")
    sd_cat = load_sd_json(FIXTURE / "staticdata_catalog.json")

    keys = merge_loca_keys(registry, loca_cat)
    loca_root = out_mod / "Localisation"
    for lang in LANGS:
        rows = catalog_for_lang(loca_cat, keys, lang)
        folder = loca_root / lang
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "loca.xml").write_text(
            render_loca(rows),
            encoding="utf-8",
        )

    dialog_root = out_mod / "Dialog"
    dialog_root.mkdir(parents=True, exist_ok=True)
    for name in dialog_names(dialog_cat):
        xml = render_npc_dialog(registry, dialog_cat["dialogs"][name])
        (dialog_root / f"{name}.xml").write_text(xml, encoding="utf-8")

    sd_root = out_mod / "StaticData"
    sd_root.mkdir(parents=True, exist_ok=True)
    tables = build_tables(registry, sd_cat)
    for name in TABLES:
        (sd_root / name).write_text(tables[name], encoding="utf-8")

    write_manifest(out_mod / "build_manifest.json", build_manifest(out_mod))


def list_expected_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".gitkeep":
            continue
        files.append(path)
    return files


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def diff_trees(got: Path, want: Path) -> list[str]:
    errors: list[str] = []
    got_files = {
        p.relative_to(got).as_posix(): p
        for p in list_expected_files(got)
        if p.name != "build_manifest.json"
    }
    want_files = {
        p.relative_to(want).as_posix(): p
        for p in list_expected_files(want)
        if p.name != "build_manifest.json"
    }
    for rel in sorted(set(got_files) | set(want_files)):
        if rel not in want_files:
            _err(errors, f"лишний {rel}")
            continue
        if rel not in got_files:
            _err(errors, f"нет {rel}")
            continue
        a = got_files[rel].read_bytes()
        b = want_files[rel].read_bytes()
        if a != b:
            _err(errors, f"diff {rel}")
    return errors


def update_expected(got_mod: Path) -> None:
    if EXPECTED.exists():
        shutil.rmtree(EXPECTED)
    EXPECTED.mkdir(parents=True)
    for path in list_expected_files(got_mod):
        if path.name == "build_manifest.json":
            continue
        rel = path.relative_to(got_mod)
        dest = EXPECTED / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def check_stage(mod_dir: Path, work: Path) -> list[str]:
    errors: list[str] = []
    game_root = work / "game"
    copy_tree(VANILLA_STUB, game_root)
    data = game_root / "Might and Magic X Legacy_Data"
    backup = work / "backup"
    manifest = json.loads(
        (mod_dir / "build_manifest.json").read_text(encoding="utf-8")
    )
    try:
        actions = plan_from_manifest(mod_dir, manifest, data)
        apply_doc = apply_actions(
            actions=actions,
            mod_dir=mod_dir,
            backup_dir=backup,
            dry_run=False,
        )
        write_json(backup / "apply.json", apply_doc)
    except Exception as exc:  # noqa: BLE001
        return [f"stage: {exc}"]

    en = (
        data
        / "StreamingAssets"
        / "Localisation"
        / "en"
        / "loca.xml"
    ).read_text(encoding="utf-8")
    if 'id="KEEP_EN">keep en<' not in en:
        _err(errors, "stage: потерян KEEP_EN")
    if "NPC_NAME_MM6_DEMO" not in en:
        _err(errors, "stage: нет NPC_NAME_MM6_DEMO в en")

    token = (
        data / "StreamingAssets" / "StaticData" / "Token.csv"
    ).read_text(encoding="utf-8")
    if "TOKEN_VANILLA" not in token:
        _err(errors, "stage: потерян TOKEN_VANILLA")
    if "TOKEN_MM6_DEMO" not in token:
        _err(errors, "stage: нет TOKEN_MM6_DEMO")

    dialog = (
        data / "StreamingAssets" / "Dialog" / "Mm6DemoDialog.xml"
    )
    if not dialog.is_file():
        _err(errors, "stage: нет Mm6DemoDialog.xml")

    # Snapshot after stage, then restore must match pre-stage stub.
    try:
        restore_actions(
            apply_doc=apply_doc,
            backup_dir=backup,
            dry_run=False,
        )
    except Exception as exc:  # noqa: BLE001
        return errors + [f"restore: {exc}"]

    if dialog.exists():
        _err(errors, "restore: dialog не удалён")
    en2 = (
        data
        / "StreamingAssets"
        / "Localisation"
        / "en"
        / "loca.xml"
    ).read_text(encoding="utf-8")
    want_en = (
        VANILLA_STUB
        / "Might and Magic X Legacy_Data"
        / "StreamingAssets"
        / "Localisation"
        / "en"
        / "loca.xml"
    ).read_text(encoding="utf-8")
    if en2 != want_en:
        _err(errors, "restore: en loca != stub")
    return errors


def run_unit_self_tests() -> list[str]:
    errors: list[str] = []
    checks = [
        (
            "validate_id_registry",
            [
                sys.executable,
                str(TOOLS / "validators" / "validate_id_registry.py"),
                str(FIXTURE / "id_registry.json"),
            ],
        ),
        (
            "allocate_self_test",
            [
                sys.executable,
                str(HERE / "allocate_mmx_ids.py"),
                "--self-test",
            ],
        ),
        (
            "loca_self_test",
            [
                sys.executable,
                str(HERE / "generate_mmx_loca.py"),
                "--self-test",
            ],
        ),
        (
            "dialog_self_test",
            [
                sys.executable,
                str(HERE / "generate_mmx_dialog.py"),
                "--self-test",
            ],
        ),
        (
            "staticdata_self_test",
            [
                sys.executable,
                str(HERE / "generate_mmx_staticdata.py"),
                "--self-test",
            ],
        ),
        (
            "manifest_self_test",
            [
                sys.executable,
                str(HERE / "build_mmx_manifest.py"),
                "--self-test",
            ],
        ),
        (
            "stage_self_test",
            [
                sys.executable,
                str(TOOLS / "modding" / "stage_mmx_mod.py"),
                "--self-test",
            ],
        ),
        (
            "validate_mod_self_test",
            [
                sys.executable,
                str(TOOLS / "validators" / "validate_mmx_mod.py"),
                "--self-test",
            ],
        ),
    ]
    import subprocess

    for name, cmd in checks:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            _err(errors, f"{name}: {detail[:200]}")
    return errors


def run_regression(*, update: bool) -> list[str]:
    errors: list[str] = []
    if not FIXTURE.is_dir():
        return [f"нет fixture {FIXTURE}"]

    registry = json.loads(
        (FIXTURE / "id_registry.json").read_text(encoding="utf-8")
    )
    for item in validate_registry(registry):
        _err(errors, f"registry: {item}")

    with tempfile.TemporaryDirectory() as tmp_name:
        work = Path(tmp_name)
        mod_dir = work / "mod"
        mod_dir.mkdir()
        try:
            generate_mod(mod_dir)
        except Exception as exc:  # noqa: BLE001
            return errors + [f"generate: {exc}"]

        if update:
            update_expected(mod_dir)

        if not EXPECTED.is_dir() or not list_expected_files(EXPECTED):
            _err(
                errors,
                "нет expected/; запустите с --update-expected",
            )
        else:
            errors.extend(diff_trees(mod_dir, EXPECTED))

        man_errors = verify_manifest(
            mod_dir,
            json.loads(
                (mod_dir / "build_manifest.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        for item in man_errors:
            _err(errors, f"manifest: {item}")

        val_errors = validate_mod(
            registry_path=FIXTURE / "id_registry.json",
            loca_catalog=FIXTURE / "loca_catalog.json",
            dialog_catalog=FIXTURE / "dialog_catalog.json",
            staticdata_catalog=FIXTURE / "staticdata_catalog.json",
            mod_dir=mod_dir,
        )
        for item in val_errors:
            _err(errors, f"validate: {item}")

        errors.extend(check_stage(mod_dir, work / "stage"))

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_m2_regression.py",
        description="Offline M2 regression fixtures (no game write).",
    )
    parser.add_argument(
        "--update-expected",
        action="store_true",
        help="Перезаписать fixtures/m2_demo/expected/.",
    )
    parser.add_argument(
        "--skip-unit",
        action="store_true",
        help="Не гонять --self-test соседних CLI.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    if not args.skip_unit:
        errors.extend(run_unit_self_tests())
    errors.extend(run_regression(update=args.update_expected))
    if errors:
        print(f"FAIL ({len(errors)})", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    print("OK M2 regression fixtures")
    print(f"  fixture={FIXTURE}")
    print(f"  expected={EXPECTED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
