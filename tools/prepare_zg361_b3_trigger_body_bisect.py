#!/usr/bin/env python3
"""Prepare the two one-real/one-false B3 trigger diagnostic candidates.

This is a no-launch diagnostic builder.  It derives both candidates from the
frozen r5 A projection, changes only its central scripted-trigger provider,
and emits hash-bound projection manifests and mutually unique live commands.
The candidates are never inputs to the production generator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
if str(MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(MOD_TOOLS))

import freeze_zg361_phase2_b3_no_launch as freeze
import zg361_phase2_product_projection as projection
from zg361_effect_sharding import top_level_effect_entries


EXPECTED_BASE_FILE_COUNT = 565
EXPECTED_BASE_TREE_SHA256 = (
    "50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f"
)
EXPECTED_BASE_MANIFEST_SHA256 = (
    "2052dada087a91273a3b15587a34b00c861cca543dbe14926026f3a2ba29b298"
)
EXPECTED_TRIGGER_SHA256 = (
    "ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7"
)
DEFAULT_OPEN_KAISHEK_JAR = Path(
    r"Z:\workspace\open_kaishek_t2_g2_war_loss_20260904"
    r"\kaishek-cli\target\kaishek-cli-0.1.0-SNAPSHOT.jar"
)
TRIGGER_RELATIVE = (
    "common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt"
)
CANDIDATE_READY = "zg361_p2c_m360_candidate_ready_trigger"
FROZEN_MANAGER_EXACT = "zg361_p2c_m360_frozen_manager_exact_trigger"
TARGET_NAMES = (CANDIDATE_READY, FROZEN_MANAGER_EXACT)
BOM = b"\xef\xbb\xbf"

VARIANTS = {
    "v1": {
        "real": CANDIDATE_READY,
        "stub": FROZEN_MANAGER_EXACT,
        "description": (
            "candidate_ready real body; frozen_manager_exact minimal false stub"
        ),
    },
    "v2": {
        "real": FROZEN_MANAGER_EXACT,
        "stub": CANDIDATE_READY,
        "description": (
            "candidate_ready minimal false stub; frozen_manager_exact real body "
            "whose internal call resolves to that stub"
        ),
    },
}


class BisectError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, *, relative_to: Path | None = None) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise BisectError(f"required file is missing: {resolved}")
    return {
        "path": (
            resolved.relative_to(relative_to.resolve()).as_posix()
            if relative_to is not None
            else str(resolved)
        ),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def tree_rows(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


def tree_delta(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    delta: list[dict[str, Any]] = []
    for relative in sorted(set(before) | set(after)):
        old = before.get(relative)
        new = after.get(relative)
        if old == new:
            continue
        delta.append(
            {
                "path": relative,
                "operation": (
                    "added" if old is None else "removed" if new is None else "replaced"
                ),
                "before": old,
                "after": new,
            }
        )
    return delta


def false_stub(name: str) -> str:
    return f"{name} = {{\n    always = no\n}}"


def parsed_blocks(payload: bytes) -> dict[str, str]:
    try:
        entries = top_level_effect_entries(payload)
    except (UnicodeError, ValueError) as error:
        raise BisectError(f"scripted-trigger parser rejected provider: {error}") from error
    names = tuple(entry.name for entry in entries)
    if names != TARGET_NAMES:
        raise BisectError(
            f"r5 A trigger provider definitions drifted: {names} != {TARGET_NAMES}"
        )
    return {entry.name: entry.block for entry in entries}


def render_variant(base_payload: bytes, *, real: str, stub: str) -> bytes:
    if not base_payload.startswith(BOM):
        raise BisectError("r5 A trigger provider is missing UTF-8 BOM")
    if b"# GENERATED FILE" not in base_payload:
        raise BisectError("r5 A trigger provider lost its generated-file marker")
    base_text = base_payload.decode("utf-8-sig")
    blocks = parsed_blocks(base_payload)
    if {real, stub} != set(TARGET_NAMES) or real == stub:
        raise BisectError("variant must select exactly one real and one stub body")
    rendered = base_text.replace(blocks[stub], false_stub(stub), 1)
    result = BOM + rendered.encode("utf-8")
    result_blocks = parsed_blocks(result)
    if result_blocks[real] != blocks[real]:
        raise BisectError(f"real trigger body changed in variant: {real}")
    if result_blocks[stub] != false_stub(stub):
        raise BisectError(f"false stub is not minimal in variant: {stub}")
    return result


def closure_summary(product_source: Path) -> dict[str, Any]:
    closure = freeze.central_effect_call_closure(product_source)
    summary = {
        "green": closure.get("green") is True,
        "reachable_effect_count": len(closure.get("reachable_effects", [])),
        "reachable_event_count": len(closure.get("reachable_events", [])),
        "reachable_trigger_count": len(closure.get("reachable_triggers", [])),
        "final_effect_definition_count": closure.get("material_projection", {}).get(
            "effect_definition_count"
        ),
        "final_event_definition_count": closure.get("material_projection", {}).get(
            "event_definition_count"
        ),
        "final_trigger_definition_count": closure.get("material_projection", {}).get(
            "trigger_definition_count"
        ),
        "missing_effects": closure.get("missing_effects", []),
        "missing_events": closure.get("missing_events", []),
        "missing_triggers": closure.get("missing_triggers", []),
        "material_missing_effects": closure.get("material_projection", {}).get(
            "missing_effects", []
        ),
        "material_missing_events": closure.get("material_projection", {}).get(
            "missing_events", []
        ),
        "material_missing_triggers": closure.get("material_projection", {}).get(
            "missing_triggers", []
        ),
    }
    if summary["green"] is not True:
        raise BisectError(f"diagnostic candidate closure is RED: {summary}")
    return summary


def run_preflight(
    *,
    python: Path,
    candidate: Path,
    manifest: Path,
    projection_name: str,
    dll: Path,
    injector: Path,
    pipe: str,
    ck3_exe: Path,
    runner_root: Path,
    log_path: Path,
) -> dict[str, Any]:
    argv = [
        str(python.resolve()),
        str((runner_root / "tools" / "run_zhongguo_acceptance.py").resolve()),
        "--preflight",
        "--phase2-live-batch",
        "--bridge-dll",
        str(dll.resolve()),
        "--bridge-injector",
        str(injector.resolve()),
        "--bridge-pipe",
        pipe,
        "--phase2-seed-contract",
        str(
            (runner_root / "tools" / "zg361_phase2_seed_contract.json").resolve()
        ),
        "--phase2-product-source",
        str(candidate.resolve()),
        "--phase2-product-projection",
        projection_name,
        "--phase2-product-projection-manifest",
        str(manifest.resolve()),
    ]
    environment = os.environ.copy()
    environment["XAR_CK3_EXE"] = str(ck3_exe.resolve())
    completed = subprocess.run(
        argv,
        cwd=runner_root.resolve(),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    log_path.write_text(
        completed.stdout + completed.stderr, encoding="utf-8", newline="\n"
    )
    green = (
        completed.returncode == 0
        and "ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN" in completed.stdout
    )
    result = {
        "green": green,
        "ck3_launched": False,
        "argv": argv,
        "returncode": completed.returncode,
        "log": file_record(log_path),
    }
    if not green:
        raise BisectError(f"formal no-launch preflight is RED: {result}")
    return result


def run_open_kaishek_parser(
    *, jar: Path, candidate: Path, profile: str, fixture: str, report_path: Path
) -> dict[str, Any]:
    if not jar.is_file():
        raise BisectError(f"open_kaishek jar is missing: {jar}")
    argv = [
        "java",
        "-jar",
        str(jar.resolve()),
        "preflight",
        "--root",
        str(candidate.resolve()),
        "--profile",
        profile,
        "--fixture",
        fixture,
    ]
    completed = subprocess.run(
        argv,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=180,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BisectError(
            f"open_kaishek emitted invalid JSON: {error}: {completed.stderr}"
        ) from error
    parser_row = payload.get("parser") if isinstance(payload, dict) else None
    root_scan = payload.get("root_scan") if isinstance(payload, dict) else None
    root_parser = root_scan.get("parser") if isinstance(root_scan, dict) else None
    provenance = payload.get("provenance") if isinstance(payload, dict) else None
    checks = {
        "parser_green": isinstance(parser_row, dict)
        and parser_row.get("status") == "GREEN"
        and parser_row.get("diagnostics") == 0,
        "root_parser_green": isinstance(root_parser, dict)
        and root_parser.get("status") == "GREEN"
        and root_parser.get("diagnostics") == 0,
        "offline_provenance": isinstance(provenance, dict)
        and provenance.get("mode") == "offline"
        and provenance.get("ck3_started") == "false"
        and provenance.get("save_mutated") == "false"
        and provenance.get("network_used") == "false",
    }
    report = {
        "schema_version": 1,
        "kind": "zg361_b3_mutually_exclusive_trigger_parser_preflight",
        "green": all(checks.values()),
        "ck3_launched": False,
        "argv": argv,
        "returncode": completed.returncode,
        "jar": file_record(jar),
        "checks": checks,
        "payload": payload,
        "stderr": completed.stderr,
        "boundary": (
            "Parser and root-parser GREEN prove syntax only. Profile-validator "
            "diagnostics are not treated as CK3 runtime certification."
        ),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if report["green"] is not True:
        raise BisectError(f"open_kaishek parser preflight is RED: {checks}")
    return {**report, "report": file_record(report_path)}


def live_command(
    *,
    live_root: Path,
    python: Path,
    candidate: Path,
    manifest: Path,
    projection_name: str,
    dll: Path,
    injector: Path,
    pipe: str,
    artifacts: Path,
) -> dict[str, Any]:
    argv = [
        str(python.resolve()),
        str((live_root / "tools" / "run_zhongguo_acceptance.py").resolve()),
        "--phase2-live-batch",
        "--bridge-dll",
        str(dll.resolve()),
        "--bridge-injector",
        str(injector.resolve()),
        "--bridge-pipe",
        pipe,
        "--phase2-seed-contract",
        str((live_root / "tools" / "zg361_phase2_seed_contract.json").resolve()),
        "--phase2-product-source",
        str(candidate.resolve()),
        "--phase2-product-projection",
        projection_name,
        "--phase2-product-projection-manifest",
        str(manifest.resolve()),
        "--artifacts-dir",
        str(artifacts.resolve()),
        "--discard-userdir",
    ]
    return {
        "authorized_by_preflight": True,
        "executed": False,
        "pipe": pipe,
        "artifacts": str(artifacts.resolve()),
        "argv": argv,
        "windows_command": subprocess.list2cmdline(argv),
    }


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    source = args.source.resolve()
    base_manifest = args.base_manifest.resolve()
    output = args.output.resolve()
    if output.exists():
        raise BisectError(f"fresh output directory already exists: {output}")
    if not source.is_dir() or not base_manifest.is_file():
        raise BisectError("frozen r5 A source or projection manifest is missing")
    if sha256_file(base_manifest) != EXPECTED_BASE_MANIFEST_SHA256:
        raise BisectError("frozen r5 A projection manifest SHA-256 drifted")
    base_rows = tree_rows(source)
    if len(base_rows) != EXPECTED_BASE_FILE_COUNT:
        raise BisectError(
            f"frozen r5 A file count drifted: {len(base_rows)} != "
            f"{EXPECTED_BASE_FILE_COUNT}"
        )
    base_spec = projection.load_projection(
        source,
        projection_name="b3-manager-governance-trigger-closure-r5-fecd2f2",
        manifest_path=base_manifest,
    )
    if base_spec.source_tree_sha256 != EXPECTED_BASE_TREE_SHA256:
        raise BisectError("frozen r5 A tree SHA-256 drifted")
    trigger_source = source / TRIGGER_RELATIVE
    if sha256_file(trigger_source) != EXPECTED_TRIGGER_SHA256:
        raise BisectError("frozen r5 A trigger provider SHA-256 drifted")
    base_payload = trigger_source.read_bytes()
    base_blocks = parsed_blocks(base_payload)

    output.mkdir(parents=True)
    variants: dict[str, Any] = {}
    used_pipes: set[str] = set()
    for variant_name, contract in VARIANTS.items():
        variant_root = output / variant_name
        candidate = variant_root / "product-source"
        projection_name = f"b3-r5-trigger-body-bisect-{variant_name}"
        projection.materialize_projection(
            source,
            candidate,
            projection_name=base_spec.name,
            manifest_path=base_manifest,
        )
        replacement = render_variant(
            base_payload,
            real=str(contract["real"]),
            stub=str(contract["stub"]),
        )
        (candidate / TRIGGER_RELATIVE).write_bytes(replacement)
        rows = tree_rows(candidate)
        delta = tree_delta(base_rows, rows)
        if len(rows) != EXPECTED_BASE_FILE_COUNT:
            raise BisectError(f"{variant_name} changed the frozen file count")
        if [item["path"] for item in delta] != [TRIGGER_RELATIVE]:
            raise BisectError(f"{variant_name} changed paths outside trigger provider")
        candidate_blocks = parsed_blocks(replacement)
        real = str(contract["real"])
        stub = str(contract["stub"])
        exact_calls_stub = CANDIDATE_READY in candidate_blocks[FROZEN_MANAGER_EXACT]
        if variant_name == "v2" and not exact_calls_stub:
            raise BisectError("V2 exact body no longer calls candidate_ready stub")
        manifest_path = variant_root / "projection.json"
        manifest_payload = projection.write_manifest(
            candidate, manifest_path, projection_name=projection_name
        )
        parser_report = run_open_kaishek_parser(
            jar=args.open_kaishek_jar.resolve(),
            candidate=candidate,
            profile=args.profile,
            fixture=args.fixture,
            report_path=variant_root / "open-kaishek-parser.json",
        )
        pipe = rf"\\.\pipe\xar_ck3_bridge_zg361_{secrets.token_hex(16)}"
        if pipe in used_pipes:
            raise BisectError("diagnostic pipes must be unique")
        used_pipes.add(pipe)
        preflight_path = variant_root / "formal-no-launch-preflight.txt"
        preflight = run_preflight(
            python=args.python,
            candidate=candidate,
            manifest=manifest_path,
            projection_name=projection_name,
            dll=args.dll,
            injector=args.injector,
            pipe=pipe,
            ck3_exe=args.ck3_exe,
            runner_root=args.live_root,
            log_path=preflight_path,
        )
        launch = live_command(
            live_root=args.live_root,
            python=args.python,
            candidate=candidate,
            manifest=manifest_path,
            projection_name=projection_name,
            dll=args.dll,
            injector=args.injector,
            pipe=pipe,
            artifacts=variant_root / "artifacts-live",
        )
        variants[variant_name] = {
            "status": "GREEN_NO_LAUNCH",
            "diagnostic_only": True,
            "production_candidate": False,
            "description": contract["description"],
            "candidate": str(candidate),
            "file_count": len(rows),
            "unchanged_file_count": len(rows) - len(delta),
            "bytes": sum(int(row["bytes"]) for row in rows.values()),
            "source_tree_sha256": manifest_payload["source_tree_sha256"],
            "projection_manifest": file_record(manifest_path),
            "delta": delta,
            "trigger_provider": {
                "record": file_record(candidate / TRIGGER_RELATIVE, relative_to=candidate),
                "definition_order": list(candidate_blocks),
                "definition_count": len(candidate_blocks),
                "real": real,
                "real_body_sha256": sha256_bytes(candidate_blocks[real].encode("utf-8")),
                "real_matches_frozen_r5_a": candidate_blocks[real] == base_blocks[real],
                "stub": stub,
                "stub_body_sha256": sha256_bytes(candidate_blocks[stub].encode("utf-8")),
                "stub_is_minimal_false": candidate_blocks[stub] == false_stub(stub),
                "frozen_manager_exact_calls_candidate_ready": exact_calls_stub,
            },
            "parser_green": True,
            "open_kaishek_parser": parser_report,
            "closure": closure_summary(candidate),
            "formal_no_launch_preflight": preflight,
            "launch": launch,
        }

    if variants["v1"]["launch"]["pipe"] == variants["v2"]["launch"]["pipe"]:
        raise BisectError("V1 and V2 live commands reuse a pipe")
    return {
        "schema_version": 1,
        "kind": "zg361_b3_trigger_body_bisect_no_launch_candidates",
        "status": "GREEN_NO_LAUNCH",
        "ck3_launched": False,
        "diagnostic_only": True,
        "production_candidate": False,
        "generator_changed": False,
        "purpose": (
            "Mutually exclusive trigger-body diagnosis complementary to the "
            "dual-false-stub candidate; never merge either product tree."
        ),
        "frozen_r5_a": {
            "source": str(source),
            "file_count": len(base_rows),
            "bytes": sum(int(row["bytes"]) for row in base_rows.values()),
            "source_tree_sha256": EXPECTED_BASE_TREE_SHA256,
            "projection_manifest": file_record(base_manifest),
            "trigger_provider": file_record(trigger_source, relative_to=source),
        },
        "invariants": {
            "candidate_file_count": EXPECTED_BASE_FILE_COUNT,
            "changed_paths": [TRIGGER_RELATIVE],
            "unchanged_files_per_candidate": EXPECTED_BASE_FILE_COUNT - 1,
            "variant_pipes_unique": True,
        },
        "inputs": {
            "python": file_record(args.python),
            "ck3_exe": file_record(args.ck3_exe),
            "bridge_dll": file_record(args.dll),
            "bridge_injector": file_record(args.injector),
            "open_kaishek_jar": file_record(args.open_kaishek_jar),
            "runner": file_record(
                args.live_root / "tools" / "run_zhongguo_acceptance.py",
                relative_to=args.live_root,
            ),
            "seed_contract": file_record(
                args.live_root / "tools" / "zg361_phase2_seed_contract.json",
                relative_to=args.live_root,
            ),
        },
        "variants": variants,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--injector", type=Path, required=True)
    parser.add_argument("--ck3-exe", type=Path, required=True)
    parser.add_argument("--live-root", type=Path, default=ROOT)
    parser.add_argument(
        "--open-kaishek-jar", type=Path, default=DEFAULT_OPEN_KAISHEK_JAR
    )
    parser.add_argument("--profile", default="ck3-1.19.0.6-zg361")
    parser.add_argument("--fixture", default="synthetic-361-014")
    args = parser.parse_args(argv)
    try:
        report = prepare(args)
        manifest = args.output.resolve() / "attempt-manifest.json"
        manifest.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        digest = sha256_file(manifest)
        (args.output.resolve() / "attempt-manifest.sha256").write_text(
            f"{digest}  attempt-manifest.json\n", encoding="ascii", newline="\n"
        )
    except (BisectError, projection.ProductProjectionError, OSError) as error:
        print(f"B3 trigger-body bisect preparation failed: {error}")
        return 2
    print(
        json.dumps(
            {
                "result": "GREEN_NO_LAUNCH",
                "ck3_launched": False,
                "output": str(args.output.resolve()),
                "manifest_sha256": digest,
                "variants": {
                    name: {
                        "tree_sha256": row["source_tree_sha256"],
                        "unchanged_files": row["unchanged_file_count"],
                        "command": row["launch"]["windows_command"],
                    }
                    for name, row in report["variants"].items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
