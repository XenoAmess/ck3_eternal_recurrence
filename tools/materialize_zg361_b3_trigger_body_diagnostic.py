#!/usr/bin/env python3
"""Materialize the one-off r5 B3 trigger-body diagnostic without launching CK3.

The candidate keeps every caller and both scripted-trigger names intact, but
replaces the two newly closed trigger bodies with ``always = no``.  It is a
diagnostic projection only: the output is external, hash-bound, and must never
be copied into the generator or production source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
for module_root in (ROOT / "tools", MOD_TOOLS):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))

import freeze_zg361_phase2_b3_no_launch as freeze  # noqa: E402
import zg361_phase2_product_projection as projection  # noqa: E402
from zg361_effect_sharding import top_level_effect_entries  # noqa: E402


BOM = b"\xef\xbb\xbf"
TARGET_RELATIVE = PurePosixPath(
    "common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt"
)
TARGETS = (
    "zg361_p2c_m360_candidate_ready_trigger",
    "zg361_p2c_m360_frozen_manager_exact_trigger",
)
EXPECTED_ABI = {
    TARGETS[0]: (
        "EXPECTED_OWNER",
        "EXPECTED_P2C_CASE",
        "EXPECTED_P2C_CYCLE",
    ),
    TARGETS[1]: (
        "EXPECTED_B1_CASE",
        "EXPECTED_B1_CYCLE",
        "EXPECTED_B1_SOURCE_HASH",
        "EXPECTED_B1_SOURCE_ID",
        "EXPECTED_MG_CASE",
        "EXPECTED_MG_CYCLE",
        "EXPECTED_MG_REVISION",
        "EXPECTED_MG_SOURCE_SERIAL",
        "EXPECTED_OWNER",
        "EXPECTED_P2C_CASE",
        "EXPECTED_P2C_CYCLE",
        "EXPECTED_QUOTA",
    ),
}
EXPECTED_EXTERNAL_CALLS = {TARGETS[0]: 3, TARGETS[1]: 3}
EXPECTED_SOURCE = {
    "file_count": 565,
    "bytes": 21_607_125,
    "tree_sha256": "50eca1ef14d30c613f6a6e59ccd244bc3b92ee5a4aedaf7bccd191af20b0475f",
    "target_bytes": 16_712,
    "target_sha256": "ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7",
}
PARAM_TOKEN_RE = re.compile(r"\$([A-Z][A-Z0-9_]*)\$")
PARAM_ASSIGN_RE = re.compile(r"(?m)^\s*([A-Z][A-Z0-9_]*)\s*=")
BRIDGE_PIPE_RE = re.compile(
    re.escape(r"\\.\pipe\xar_ck3_bridge_zg361_") + r"[0-9a-f]{32}"
)

DEFAULT_R5_ROOT = Path(
    r"Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z"
)
DEFAULT_OPEN_KAISHEK_JAR = Path(
    r"Z:\workspace\open_kaishek_t2_g2_war_loss_20260904"
    r"\kaishek-cli\target\kaishek-cli-0.1.0-SNAPSHOT.jar"
)
DEFAULT_RUNNER_PYTHON = Path(r"Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe")
DEFAULT_RUNNER = ROOT / "tools" / "run_zhongguo_acceptance.py"
EXPECTED_A2_RUNNER_SHA256 = (
    "2dd1067f7a0de9076cacc552bd2f786c00f1b04af9ef969eaa258ea2e7a747c6"
)
DEFAULT_SEED_CONTRACT = Path(
    r"Z:\ck3_mod_rewrite\_worktrees\b3-trigger-closure-r5"
    r"\tools\zg361_phase2_seed_contract.json"
)


class TriggerDiagnosticError(ValueError):
    """The requested candidate is not the frozen r5 one-file diagnostic."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _tree_rows(root: Path) -> dict[str, dict[str, object]]:
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


def _block_end(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index in range(opening, len(text)):
        char = text[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise TriggerDiagnosticError("unterminated scripted-trigger call block")


def _external_call_surface(
    root: Path,
    *,
    targets: Sequence[str] = TARGETS,
    excluded_relative: PurePosixPath = TARGET_RELATIVE,
) -> dict[str, list[dict[str, object]]]:
    rows = {name: [] for name in targets}
    patterns = {
        name: re.compile(rf"\b{re.escape(name)}\s*=\s*\{{") for name in targets
    }
    for path in sorted(root.rglob("*.txt")):
        relative = path.relative_to(root).as_posix()
        if relative == excluded_relative.as_posix():
            continue
        text = path.read_text(encoding="utf-8-sig")
        for name, pattern in patterns.items():
            for match in pattern.finditer(text):
                opening = text.find("{", match.start(), match.end())
                block = text[match.start() : _block_end(text, opening)]
                rows[name].append(
                    {
                        "path": relative,
                        "line": text.count("\n", 0, match.start()) + 1,
                        "parameters": sorted(set(PARAM_ASSIGN_RE.findall(block))),
                        "block_sha256": _sha256_bytes(block.encode("utf-8")),
                    }
                )
    return rows


def _render_false_body(name: str, abi: Sequence[str], newline: str) -> str:
    joined = ", ".join(abi)
    return newline.join(
        (
            f"{name} = {{",
            "    # DIAGNOSTIC ONLY; never copy this body into generated/production source.",
            f"    # Caller ABI remains unchanged and is intentionally unused here: {joined}",
            "    always = no",
            "}",
        )
    )


def _replace_target_bodies(source_payload: bytes) -> tuple[bytes, list[dict[str, object]]]:
    if not source_payload.startswith(BOM):
        raise TriggerDiagnosticError("target scripted-trigger owner lacks UTF-8 BOM")
    text = source_payload.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    entries = top_level_effect_entries(source_payload)
    if tuple(entry.name for entry in entries) != TARGETS:
        raise TriggerDiagnosticError(
            "target owner definition sequence changed: "
            f"{tuple(entry.name for entry in entries)!r} != {TARGETS!r}"
        )
    rows: list[dict[str, object]] = []
    rendered = text
    for entry in entries:
        observed_abi = tuple(sorted(set(PARAM_TOKEN_RE.findall(entry.block))))
        expected_abi = EXPECTED_ABI[entry.name]
        if observed_abi != expected_abi:
            raise TriggerDiagnosticError(
                f"{entry.name} parameter ABI changed: {observed_abi!r} != {expected_abi!r}"
            )
        replacement = _render_false_body(entry.name, expected_abi, newline)
        if rendered.count(entry.block) != 1:
            raise TriggerDiagnosticError(f"cannot uniquely replace {entry.name}")
        rendered = rendered.replace(entry.block, replacement, 1)
        rows.append(
            {
                "name": entry.name,
                "parameter_abi": list(expected_abi),
                "before_body_bytes": len(entry.block.encode("utf-8")),
                "before_body_sha256": _sha256_bytes(entry.block.encode("utf-8")),
                "after_body_bytes": len(replacement.encode("utf-8")),
                "after_body_sha256": _sha256_bytes(replacement.encode("utf-8")),
                "replacement": "always = no",
            }
        )
    return BOM + rendered.encode("utf-8"), rows


def _validate_call_surface(
    surface: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    expected_calls: Mapping[str, int] = EXPECTED_EXTERNAL_CALLS,
) -> None:
    for name in TARGETS:
        calls = surface.get(name, ())
        if len(calls) != expected_calls[name]:
            raise TriggerDiagnosticError(
                f"{name} external call count changed: {len(calls)} != {expected_calls[name]}"
            )
        for call in calls:
            parameters = tuple(call.get("parameters", ()))
            if parameters != EXPECTED_ABI[name]:
                raise TriggerDiagnosticError(
                    f"{name} call ABI changed at {call.get('path')}:{call.get('line')}: "
                    f"{parameters!r} != {EXPECTED_ABI[name]!r}"
                )


def _run_open_kaishek(
    jar: Path,
    candidate: Path,
    *,
    profile: str,
    fixture: str,
) -> dict[str, object]:
    jar = jar.resolve()
    if not jar.is_file():
        raise TriggerDiagnosticError(f"open_kaishek jar is missing: {jar}")
    command = [
        "java",
        "-jar",
        str(jar),
        "preflight",
        "--root",
        str(candidate),
        "--profile",
        profile,
        "--fixture",
        fixture,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise TriggerDiagnosticError(
            f"open_kaishek emitted invalid JSON: {error}; stderr={completed.stderr!r}"
        ) from error
    parser_row = payload.get("parser") if isinstance(payload, dict) else None
    root_parser = (
        payload.get("root_scan", {}).get("parser")
        if isinstance(payload, dict) and isinstance(payload.get("root_scan"), dict)
        else None
    )
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
    return {
        "schema_version": 1,
        "kind": "zg361_b3_trigger_body_diagnostic_open_kaishek",
        "result": "GREEN" if all(checks.values()) else "RED",
        "command": command,
        "exit_code": completed.returncode,
        "jar": str(jar),
        "jar_bytes": jar.stat().st_size,
        "jar_sha256": _sha256(jar),
        "checks": checks,
        "payload": payload,
        "stderr": completed.stderr,
        "boundary": (
            "Only parser/root-parser GREEN is required here. The profile validator may "
            "remain schema-only RED and is not CK3 runtime certification."
        ),
    }


def _powershell_command(argv: Sequence[str]) -> str:
    def quote(value: str) -> str:
        if not value or any(char.isspace() or char in "'`$" for char in value):
            return "'" + value.replace("'", "''") + "'"
        return value

    return " ".join(quote(value) for value in argv)


def _launch_contract(
    *,
    candidate: Path,
    projection_manifest: Path,
    projection_name: str,
    artifacts_dir: Path,
    runner_python: Path,
    runner: Path,
    bridge_dll: Path,
    bridge_injector: Path,
    seed_contract: Path,
    bridge_pipe: str,
    expected_runner_sha256: str | None,
) -> dict[str, object]:
    required = (runner_python, runner, bridge_dll, bridge_injector, seed_contract)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise TriggerDiagnosticError(f"launch dependency is missing: {missing}")
    if artifacts_dir.exists():
        raise TriggerDiagnosticError(f"diagnostic live artifact path already exists: {artifacts_dir}")
    if BRIDGE_PIPE_RE.fullmatch(bridge_pipe) is None:
        raise TriggerDiagnosticError(
            "bridge pipe must match the formal runner contract: "
            r"\\.\pipe\xar_ck3_bridge_zg361_<32 lowercase hex>"
        )
    runner_sha256 = _sha256(runner)
    if (
        expected_runner_sha256 is not None
        and runner_sha256 != expected_runner_sha256.lower()
    ):
        raise TriggerDiagnosticError(
            "runner does not match the A2 git-head runner content: "
            f"{runner_sha256} != {expected_runner_sha256.lower()}"
        )
    argv = [
        str(runner_python),
        str(runner),
        "--phase2-live-batch",
        "--bridge-dll",
        str(bridge_dll),
        "--bridge-injector",
        str(bridge_injector),
        "--bridge-pipe",
        bridge_pipe,
        "--phase2-seed-contract",
        str(seed_contract),
        "--phase2-product-source",
        str(candidate),
        "--phase2-product-projection",
        projection_name,
        "--phase2-product-projection-manifest",
        str(projection_manifest),
        "--artifacts-dir",
        str(artifacts_dir),
        "--discard-userdir",
    ]
    return {
        "unique": True,
        "executed": False,
        "argv": argv,
        "powershell_command": _powershell_command(argv),
        "artifacts_dir_absent": True,
        "ck3_started": False,
        "runner": {
            "path": str(runner),
            "bytes": runner.stat().st_size,
            "sha256": runner_sha256,
            "expected_a2_sha256": expected_runner_sha256,
            "matches_expected_a2": expected_runner_sha256 is None
            or runner_sha256 == expected_runner_sha256.lower(),
        },
    }


def materialize_candidate(
    *,
    source_root: Path,
    output_root: Path,
    manifest_path: Path,
    projection_manifest: Path,
    parser_report_path: Path,
    projection_name: str,
    artifacts_dir: Path,
    open_kaishek_jar: Path,
    profile: str,
    fixture: str,
    runner_python: Path,
    runner: Path,
    bridge_dll: Path,
    bridge_injector: Path,
    seed_contract: Path,
    bridge_pipe: str,
    expected_runner_sha256: str | None = None,
    expected_source: Mapping[str, object] | None = EXPECTED_SOURCE,
    expected_calls: Mapping[str, int] = EXPECTED_EXTERNAL_CALLS,
    parser_runner: Callable[..., dict[str, object]] = _run_open_kaishek,
    closure_builder: Callable[[Path], dict[str, object]] = freeze.central_effect_call_closure,
) -> dict[str, object]:
    source_root = source_root.resolve()
    output_root = output_root.resolve()
    manifest_path = manifest_path.resolve()
    projection_manifest = projection_manifest.resolve()
    parser_report_path = parser_report_path.resolve()
    artifacts_dir = artifacts_dir.resolve()
    if not source_root.is_dir():
        raise TriggerDiagnosticError(f"frozen r5 A source is missing: {source_root}")
    for path, label in (
        (output_root, "output"),
        (manifest_path, "diagnostic manifest"),
        (projection_manifest, "projection manifest"),
        (parser_report_path, "parser report"),
    ):
        if path.exists():
            raise TriggerDiagnosticError(f"{label} already exists: {path}")
    try:
        output_root.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise TriggerDiagnosticError("diagnostic output must not be inside source")
    for path in (manifest_path, projection_manifest, parser_report_path):
        try:
            path.relative_to(output_root)
        except ValueError:
            continue
        raise TriggerDiagnosticError("sidecars must be outside the diagnostic product tree")

    source_rows = _tree_rows(source_root)
    source_bytes = sum(int(row["bytes"]) for row in source_rows.values())
    source_tree_sha256 = projection._source_tree_digest(source_root)
    target_source = source_root / TARGET_RELATIVE
    if not target_source.is_file():
        raise TriggerDiagnosticError(f"target trigger owner is missing: {target_source}")
    if expected_source is not None:
        observed = {
            "file_count": len(source_rows),
            "bytes": source_bytes,
            "tree_sha256": source_tree_sha256,
            "target_bytes": target_source.stat().st_size,
            "target_sha256": _sha256(target_source),
        }
        if observed != dict(expected_source):
            raise TriggerDiagnosticError(
                f"source does not match frozen r5 A identity: {observed!r}"
            )

    source_calls = _external_call_surface(source_root)
    _validate_call_surface(source_calls, expected_calls=expected_calls)
    replacement, trigger_rows = _replace_target_bodies(target_source.read_bytes())
    shutil.copytree(source_root, output_root)
    target_output = output_root / TARGET_RELATIVE
    target_output.write_bytes(replacement)

    candidate_entries = top_level_effect_entries(target_output.read_bytes())
    candidate_calls = _external_call_surface(output_root)
    _validate_call_surface(candidate_calls, expected_calls=expected_calls)
    candidate_rows = _tree_rows(output_root)
    source_after_rows = _tree_rows(source_root)
    changed = sorted(
        path
        for path in source_rows
        if path not in candidate_rows or source_rows[path] != candidate_rows[path]
    )
    added = sorted(path for path in candidate_rows if path not in source_rows)
    removed = sorted(path for path in source_rows if path not in candidate_rows)
    closure = closure_builder(output_root)
    closure_green = bool(closure.get("green"))
    closure_missing = {
        kind: list(closure.get(kind, ()))
        for kind in ("missing_effects", "missing_events", "missing_triggers")
    }

    projection_payload = projection.write_manifest(
        output_root, projection_manifest, projection_name=projection_name
    )
    parser_report = parser_runner(
        open_kaishek_jar,
        output_root,
        profile=profile,
        fixture=fixture,
    )
    parser_report_path.parent.mkdir(parents=True, exist_ok=True)
    parser_report_path.write_text(
        json.dumps(parser_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    launch = _launch_contract(
        candidate=output_root,
        projection_manifest=projection_manifest,
        projection_name=projection_name,
        artifacts_dir=artifacts_dir,
        runner_python=runner_python.resolve(),
        runner=runner.resolve(),
        bridge_dll=bridge_dll.resolve(),
        bridge_injector=bridge_injector.resolve(),
        seed_contract=seed_contract.resolve(),
        bridge_pipe=bridge_pipe,
        expected_runner_sha256=expected_runner_sha256,
    )

    checks = {
        "source_tree_unchanged": source_after_rows == source_rows,
        "candidate_file_set_unchanged": set(candidate_rows) == set(source_rows),
        "only_target_owner_changed": changed == [TARGET_RELATIVE.as_posix()]
        and not added
        and not removed,
        "all_other_files_byte_identical": sum(
            source_rows[path] == candidate_rows[path]
            for path in source_rows
            if path != TARGET_RELATIVE.as_posix()
        )
        == len(source_rows) - 1,
        "trigger_names_preserved": tuple(entry.name for entry in candidate_entries)
        == TARGETS,
        "trigger_count_preserved": len(candidate_entries) == 2,
        "caller_surface_byte_identical": candidate_calls == source_calls,
        "caller_parameter_abi_preserved": all(
            all(tuple(call["parameters"]) == EXPECTED_ABI[name] for call in calls)
            for name, calls in candidate_calls.items()
        ),
        "replacement_bodies_are_minimal_false": all(
            "always = no" in entry.block
            and "always = yes" not in entry.block
            and PARAM_TOKEN_RE.search(entry.block) is None
            for entry in candidate_entries
        ),
        "closure_green": closure_green,
        "closure_missing_empty": all(not values for values in closure_missing.values()),
        "open_kaishek_parser_green": parser_report.get("result") == "GREEN",
        "projection_file_count_preserved": len(projection_payload["files"])
        == len(source_rows),
        "live_artifact_path_unused": not artifacts_dir.exists(),
        "runner_matches_a2_git_head": launch["runner"]["matches_expected_a2"],
    }
    diff_row = {
        "operation": "modified",
        "path": TARGET_RELATIVE.as_posix(),
        "before": source_rows[TARGET_RELATIVE.as_posix()],
        "after": candidate_rows[TARGET_RELATIVE.as_posix()],
    }
    receipt = {
        "schema_version": 1,
        "kind": "zg361_b3_trigger_body_always_false_diagnostic",
        "result": "GREEN" if all(checks.values()) else "RED",
        "diagnostic_only": True,
        "production_ready": False,
        "generator_change": False,
        "source": {
            "root": str(source_root),
            "file_count": len(source_rows),
            "bytes": source_bytes,
            "tree_sha256": source_tree_sha256,
        },
        "candidate": {
            "root": str(output_root),
            "file_count": len(candidate_rows),
            "unchanged_file_count": len(source_rows) - len(changed),
            "bytes": sum(int(row["bytes"]) for row in candidate_rows.values()),
            "tree_sha256": projection_payload["source_tree_sha256"],
            "formal_overlay_tree_sha256": projection_payload[
                "formal_overlay_tree_sha256"
            ],
            "file_list_sha256": projection_payload["file_list_sha256"],
        },
        "file_diff": {
            "changed_count": len(changed),
            "added_count": len(added),
            "removed_count": len(removed),
            "rows": [diff_row],
        },
        "triggers": trigger_rows,
        "external_call_surface": source_calls,
        "closure": {
            "green": closure_green,
            "missing": closure_missing,
            "effect_definition_count": closure.get("effect_definition_count"),
            "event_definition_count": closure.get("event_definition_count"),
            "trigger_definition_count": closure.get("trigger_definition_count"),
            "reachable_effect_count": closure.get("reachable_effect_count"),
            "reachable_event_count": closure.get("reachable_event_count"),
            "reachable_trigger_count": closure.get("reachable_trigger_count"),
        },
        "projection_manifest": {
            "path": str(projection_manifest),
            "sha256": _sha256(projection_manifest),
            "projection": projection_name,
        },
        "open_kaishek_report": {
            "path": str(parser_report_path),
            "sha256": _sha256(parser_report_path),
            "result": parser_report.get("result"),
            "jar_sha256": parser_report.get("jar_sha256"),
            "exit_code": parser_report.get("exit_code"),
        },
        "launch": launch,
        "checks": checks,
        "live_claimed": False,
        "ck3_started": False,
        "limitations": [
            "Both business trigger bodies intentionally return false, so this candidate cannot validate Phase2 gameplay semantics.",
            "A frontend change would isolate trigger-body parsing/evaluation cost; it would not prove which expression inside either original body is causal.",
            "A RED result would only rule out these two real bodies as a sufficient explanation for the shared frontend terminal absence.",
            "The candidate and its projection must remain outside generator and production source trees.",
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if receipt["result"] != "GREEN":
        raise TriggerDiagnosticError(f"materialized diagnostic failed checks: {checks}")
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_R5_ROOT / "product")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--projection-manifest", type=Path, required=True)
    parser.add_argument("--parser-report", type=Path, required=True)
    parser.add_argument(
        "--projection-name",
        default="b3-trigger-body-always-false-diagnostic-fecd2f2",
    )
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--open-kaishek-jar", type=Path, default=DEFAULT_OPEN_KAISHEK_JAR)
    parser.add_argument("--profile", default="ck3-1.19.0.6-zg361")
    parser.add_argument("--fixture", default="synthetic-361-014")
    parser.add_argument("--runner-python", type=Path, default=DEFAULT_RUNNER_PYTHON)
    parser.add_argument("--runner", type=Path, default=DEFAULT_RUNNER)
    parser.add_argument(
        "--expected-runner-sha256",
        default=EXPECTED_A2_RUNNER_SHA256,
        help="fail closed unless the selected runner matches the A2 git-head content",
    )
    parser.add_argument(
        "--bridge-dll",
        type=Path,
        default=DEFAULT_R5_ROOT / "native-build" / "xar_ck3_bridge.dll",
    )
    parser.add_argument(
        "--bridge-injector",
        type=Path,
        default=DEFAULT_R5_ROOT / "native-build" / "xar_ck3_bridge_injector.exe",
    )
    parser.add_argument("--seed-contract", type=Path, default=DEFAULT_SEED_CONTRACT)
    parser.add_argument("--bridge-pipe", required=True)
    args = parser.parse_args(argv)
    try:
        receipt = materialize_candidate(
            source_root=args.source_root,
            output_root=args.output_root,
            manifest_path=args.manifest,
            projection_manifest=args.projection_manifest,
            parser_report_path=args.parser_report,
            projection_name=args.projection_name,
            artifacts_dir=args.artifacts_dir,
            open_kaishek_jar=args.open_kaishek_jar,
            profile=args.profile,
            fixture=args.fixture,
            runner_python=args.runner_python,
            runner=args.runner,
            bridge_dll=args.bridge_dll,
            bridge_injector=args.bridge_injector,
            seed_contract=args.seed_contract,
            bridge_pipe=args.bridge_pipe,
            expected_runner_sha256=args.expected_runner_sha256,
        )
    except (TriggerDiagnosticError, OSError, UnicodeError, subprocess.SubprocessError) as error:
        print(f"RED: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    candidate = receipt["candidate"]
    print(
        "GREEN: "
        f"{candidate['file_count']} files; unchanged={candidate['unchanged_file_count']}; "
        "changed=1 trigger owner; parser/closure=GREEN; CK3 not started"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
