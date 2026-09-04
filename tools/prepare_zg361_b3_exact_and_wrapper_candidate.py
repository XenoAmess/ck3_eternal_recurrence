#!/usr/bin/env python3
"""Freeze the B3 exact-trigger explicit-AND production candidate.

The candidate is derived from the frozen r5 A product tree.  It replaces only
the generated Central scripted-trigger provider and proves that the replacement
is the byte-exact r5 provider with one transformation: the existing top-level
body of ``zg361_p2c_m360_frozen_manager_exact_trigger`` is nested under one
explicit ``AND`` block.  This command performs no CK3 launch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MOD_ROOT = ROOT / "mod_zhongguo_style"
MOD_TOOLS = MOD_ROOT / "tools"
if str(MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(MOD_TOOLS))

import prepare_zg361_b3_trigger_body_bisect as bisect
import zg361_phase2_product_projection as projection


BASE_PROJECTION = "b3-manager-governance-trigger-closure-r5-fecd2f2"
EXPECTED_BASE_FILE_COUNT = bisect.EXPECTED_BASE_FILE_COUNT
EXPECTED_BASE_TREE_SHA256 = bisect.EXPECTED_BASE_TREE_SHA256
EXPECTED_BASE_MANIFEST_SHA256 = bisect.EXPECTED_BASE_MANIFEST_SHA256
EXPECTED_BASE_TRIGGER_SHA256 = bisect.EXPECTED_TRIGGER_SHA256
EXPECTED_RUNNER_SHA256 = bisect.EXPECTED_RUNNER_SHA256
TRIGGER_RELATIVE = bisect.TRIGGER_RELATIVE
EXACT_TRIGGER = bisect.FROZEN_MANAGER_EXACT
CANDIDATE_TRIGGER = bisect.CANDIDATE_READY
BOM = bisect.BOM


class CandidateError(RuntimeError):
    pass


def file_record(path: Path, *, relative_to: Path | None = None) -> dict[str, Any]:
    return bisect.file_record(path, relative_to=relative_to)


def sha256_file(path: Path) -> str:
    return bisect.sha256_file(path)


def explicit_and_wrapper(block: str) -> str:
    """Return the sole authorized AST-shape transform for the exact trigger."""

    lines = block.splitlines()
    expected_head = f"{EXACT_TRIGGER} = {{"
    if len(lines) < 3 or lines[0] != expected_head or lines[-1] != "}":
        raise CandidateError("frozen exact trigger has an unexpected outer shape")
    body = lines[1:-1]
    if not body or any(not line.startswith("    ") for line in body if line):
        raise CandidateError("frozen exact trigger body indentation drifted")
    return "\n".join((lines[0], "    AND = {", *("    " + line for line in body), "    }", "}"))


def semantic_delta(base_payload: bytes, candidate_payload: bytes) -> dict[str, Any]:
    if not base_payload.startswith(BOM) or not candidate_payload.startswith(BOM):
        raise CandidateError("trigger providers must retain UTF-8 BOM")
    if b"# GENERATED FILE" not in candidate_payload:
        raise CandidateError("candidate trigger provider lost GENERATED FILE header")
    base_blocks = bisect.parsed_blocks(base_payload)
    candidate_blocks = bisect.parsed_blocks(candidate_payload)
    expected_exact = explicit_and_wrapper(base_blocks[EXACT_TRIGGER])
    if candidate_blocks[CANDIDATE_TRIGGER] != base_blocks[CANDIDATE_TRIGGER]:
        raise CandidateError("candidate_ready changed in the production candidate")
    if candidate_blocks[EXACT_TRIGGER] != expected_exact:
        raise CandidateError("exact trigger differs from the sole explicit-AND transform")
    base_text = base_payload.decode("utf-8-sig")
    expected_payload = BOM + base_text.replace(
        base_blocks[EXACT_TRIGGER], expected_exact, 1
    ).encode("utf-8")
    if candidate_payload != expected_payload:
        raise CandidateError("provider contains changes outside the exact-trigger wrapper")

    expected_sets = {
        name: sorted(bisect.EXPECTED_ABI[name]) for name in bisect.TARGET_NAMES
    }
    observed_sets = {
        name: sorted(bisect.placeholder_set(candidate_blocks[name]))
        for name in bisect.TARGET_NAMES
    }
    provider_placeholders = sorted(bisect.placeholder_set(candidate_payload))
    expected_provider_placeholders = sorted(bisect.EXPECTED_PROVIDER_PLACEHOLDERS)
    if observed_sets != expected_sets or provider_placeholders != expected_provider_placeholders:
        raise CandidateError("scripted-trigger placeholder ABI drifted")
    if "always = no" in candidate_blocks[EXACT_TRIGGER]:
        raise CandidateError("production candidate must not contain a false stub")
    return {
        "green": True,
        "single_variable": "frozen_manager_exact_top_level_explicit_and_wrapper",
        "candidate_ready_byte_identical": True,
        "exact_conditions_byte_identical_after_unwrap": True,
        "exact_call_graph_unchanged": True,
        "false_stub_present": False,
        "expected_placeholder_sets": expected_sets,
        "observed_placeholder_sets": observed_sets,
        "definition_placeholder_sets_match_expected": True,
        "expected_provider_placeholder_set": expected_provider_placeholders,
        "observed_provider_placeholder_set": provider_placeholders,
        "provider_placeholder_set_matches_expected": True,
        "base_exact_body_sha256": hashlib.sha256(
            base_blocks[EXACT_TRIGGER].encode("utf-8")
        ).hexdigest(),
        "candidate_exact_body_sha256": hashlib.sha256(
            candidate_blocks[EXACT_TRIGGER].encode("utf-8")
        ).hexdigest(),
    }


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    value = completed.stdout.strip().lower()
    if completed.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise CandidateError("cannot bind candidate to Git HEAD")
    return value


def run_static(python: Path) -> list[dict[str, Any]]:
    commands = (
        [str(python.resolve()), "mod_zhongguo_style/tools/gen_361_phase2_central_runtime.py", "--check"],
        [str(python.resolve()), "mod_zhongguo_style/tools/test_zg361_phase2_central_runtime.py"],
        [str(python.resolve()), "-O", "mod_zhongguo_style/tools/test_zg361_phase2_central_runtime.py"],
        [str(python.resolve()), "tools/test_prepare_zg361_b3_exact_and_wrapper_candidate.py"],
        [str(python.resolve()), "-O", "tools/test_prepare_zg361_b3_exact_and_wrapper_candidate.py"],
    )
    rows: list[dict[str, Any]] = []
    for argv in commands:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        row = {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "green": completed.returncode == 0,
        }
        rows.append(row)
        if not row["green"]:
            raise CandidateError(f"static command failed: {argv}")
    return rows


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    source = args.source.resolve()
    base_manifest = args.base_manifest.resolve()
    output = args.output.resolve()
    generated_provider = MOD_ROOT / TRIGGER_RELATIVE
    runner_path = args.live_root.resolve() / "tools" / "run_zhongguo_acceptance.py"
    if output.exists():
        raise CandidateError(f"fresh output directory already exists: {output}")
    if not source.is_dir() or not base_manifest.is_file():
        raise CandidateError("frozen r5 A source or projection manifest is missing")
    if sha256_file(base_manifest) != EXPECTED_BASE_MANIFEST_SHA256:
        raise CandidateError("frozen r5 A projection manifest SHA-256 drifted")
    if sha256_file(runner_path) != EXPECTED_RUNNER_SHA256:
        raise CandidateError("A2 formal runner SHA-256 drifted")

    base_spec = projection.load_projection(
        source,
        projection_name=BASE_PROJECTION,
        manifest_path=base_manifest,
    )
    if base_spec.source_tree_sha256 != EXPECTED_BASE_TREE_SHA256:
        raise CandidateError("frozen r5 A tree SHA-256 drifted")
    base_rows = bisect.tree_rows(source)
    if len(base_rows) != EXPECTED_BASE_FILE_COUNT:
        raise CandidateError("frozen r5 A file count drifted")
    base_provider = source / TRIGGER_RELATIVE
    if sha256_file(base_provider) != EXPECTED_BASE_TRIGGER_SHA256:
        raise CandidateError("frozen r5 A trigger provider SHA-256 drifted")
    proof = semantic_delta(base_provider.read_bytes(), generated_provider.read_bytes())

    output.mkdir(parents=True)
    candidate = output / "product-source"
    projection.materialize_projection(
        source,
        candidate,
        projection_name=base_spec.name,
        manifest_path=base_manifest,
    )
    shutil.copyfile(generated_provider, candidate / TRIGGER_RELATIVE)
    candidate_rows = bisect.tree_rows(candidate)
    delta = bisect.tree_delta(base_rows, candidate_rows)
    if len(candidate_rows) != EXPECTED_BASE_FILE_COUNT:
        raise CandidateError("candidate changed the frozen r5 A file count")
    if [row["path"] for row in delta] != [TRIGGER_RELATIVE]:
        raise CandidateError("candidate changed a product file outside the trigger provider")

    projection_name = args.projection
    projection_path = output / "projection.json"
    projection_payload = projection.write_manifest(
        candidate, projection_path, projection_name=projection_name
    )
    closure = bisect.closure_summary(candidate)
    parser_report = bisect.run_open_kaishek_parser(
        jar=args.open_kaishek_jar.resolve(),
        candidate=candidate,
        profile=args.profile,
        fixture=args.fixture,
        report_path=output / "open-kaishek-parser.json",
    )
    static_checks = run_static(args.python)
    pipe = rf"\\.\pipe\xar_ck3_bridge_zg361_{secrets.token_hex(16)}"
    preflight = bisect.run_preflight(
        python=args.python,
        candidate=candidate,
        manifest=projection_path,
        projection_name=projection_name,
        dll=args.dll,
        injector=args.injector,
        pipe=pipe,
        ck3_exe=args.ck3_exe,
        runner_root=args.live_root,
        log_path=output / "formal-no-launch-preflight.txt",
    )
    artifacts = output / "artifacts-live"
    if artifacts.exists():
        raise CandidateError("no-launch freeze unexpectedly created live artifacts")
    launch = bisect.live_command(
        live_root=args.live_root,
        python=args.python,
        candidate=candidate,
        manifest=projection_path,
        projection_name=projection_name,
        dll=args.dll,
        injector=args.injector,
        pipe=pipe,
        artifacts=artifacts,
    )

    return {
        "schema_version": 1,
        "kind": "zg361_b3_exact_trigger_explicit_and_no_launch_candidate",
        "status": "GREEN_NO_LAUNCH",
        "readiness": "production-candidate-live-pending",
        "production_candidate": True,
        "ck3_launched": False,
        "source_commit": git_head(),
        "purpose": (
            "Single-variable AST-shape experiment: retain every production "
            "condition, parameter and call while replacing the exact trigger's "
            "implicit top-level conjunction with one explicit AND wrapper."
        ),
        "root_cause_boundary": (
            "V1/V2 live isolated the exact trigger body. This candidate tests "
            "its AST shape; it does not claim file size as the startup cause."
        ),
        "frozen_r5_a": {
            "source": str(source),
            "projection_manifest": file_record(base_manifest),
            "file_count": len(base_rows),
            "source_tree_sha256": EXPECTED_BASE_TREE_SHA256,
            "trigger_provider": file_record(base_provider, relative_to=source),
        },
        "candidate": {
            "source": str(candidate),
            "file_count": len(candidate_rows),
            "unchanged_file_count": len(candidate_rows) - len(delta),
            "bytes": sum(int(row["bytes"]) for row in candidate_rows.values()),
            "source_tree_sha256": projection_payload["source_tree_sha256"],
            "projection_manifest": file_record(projection_path),
            "trigger_provider": file_record(candidate / TRIGGER_RELATIVE, relative_to=candidate),
            "delta": delta,
            "only_expected_generated_file_changed": True,
            "semantic_delta": proof,
            "closure": closure,
            "parser_green": True,
            "open_kaishek_parser": parser_report,
        },
        "static_checks": static_checks,
        "formal_no_launch_preflight": preflight,
        "inputs": {
            "generator": file_record(
                MOD_ROOT / "tools" / "gen_361_phase2_central_runtime.py",
                relative_to=ROOT,
            ),
            "generated_provider": file_record(generated_provider, relative_to=ROOT),
            "python": file_record(args.python),
            "runner": file_record(runner_path, relative_to=args.live_root),
            "bridge_dll": file_record(args.dll),
            "bridge_injector": file_record(args.injector),
            "ck3_exe": file_record(args.ck3_exe),
            "open_kaishek_jar": file_record(args.open_kaishek_jar),
        },
        "launch": launch,
        "claims": {
            "frontend_green": False,
            "gameplay_acceptance_executed": False,
            "artifacts_live_exists": False,
            "file_size_root_cause_claimed": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--projection", required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--injector", type=Path, required=True)
    parser.add_argument("--ck3-exe", type=Path, required=True)
    parser.add_argument("--live-root", type=Path, required=True)
    parser.add_argument(
        "--open-kaishek-jar", type=Path, default=bisect.DEFAULT_OPEN_KAISHEK_JAR
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
    except (
        CandidateError,
        bisect.BisectError,
        projection.ProductProjectionError,
        OSError,
    ) as error:
        print(f"B3 exact-trigger explicit-AND preparation failed: {error}")
        return 2
    print(
        json.dumps(
            {
                "result": report["status"],
                "ck3_launched": False,
                "output": str(args.output.resolve()),
                "manifest_sha256": digest,
                "tree_sha256": report["candidate"]["source_tree_sha256"],
                "unchanged_files": report["candidate"]["unchanged_file_count"],
                "command": report["launch"]["windows_command"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
