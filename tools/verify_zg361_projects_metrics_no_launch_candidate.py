#!/usr/bin/env python3
"""Verify a frozen projects/metrics bridge pair without starting CK3.

This verifier is deliberately read-only.  It binds the private default-OFF
adapter switch, the already existing source/result event facade, the action
cell contract, the exact-build binaries, and one still-absent future attempt.
It never creates the attempt directory and never promotes production
readiness.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY = "game.command.query-zhongguo-projects-metrics-postcondition-v1"
PRIVATE_SWITCH = "XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1"
EXPECTED_BASE_COMMIT = "13d78c6dedb3da866d075fa0ce70cb2c4307dcb5"
EXPECTED_PRODUCTION_FIX_COMMIT = (
    "953634265ebf298cec3f2cf3065060e577dc8d17"
)
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
SOURCE_EVENT = "zg361cp.26"
RESULT_EVENT = "zg361p3.229"
CHECKPOINT_ALLOWLIST_ID = "zg361-cp26-direct-p3m229-lineage-v2"
CHECKPOINT_STATES = [
    "cp26_ready_p3_absent",
    "p3_initialized_source_not_ready",
    "p3_source_ready_result_pending",
    "p3_result_committed",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _top_level_definition_count(payload: str) -> int:
    """Count Clausewitz definitions without treating unindented body rows as roots."""

    depth = 0
    count = 0
    for raw_line in payload.splitlines():
        line = raw_line.split("#", 1)[0]
        if depth == 0 and re.match(r"^[A-Za-z0-9_]+\s*=\s*\{", line):
            count += 1
        depth += line.count("{") - line.count("}")
        if depth < 0:
            return -1
    return count if depth == 0 else -1


def _native_source_fingerprint(native_root: Path) -> tuple[str, int]:
    files = [native_root / "CMakeLists.txt"]
    for tree in ("include", "src"):
        files.extend(
            path
            for path in (native_root / tree).rglob("*")
            if path.is_file() and path.suffix in {".cpp", ".hpp", ".h", ".c"}
        )
    files.sort(key=lambda path: str(path))
    lines = [
        f"{path.relative_to(native_root)}\0{_sha256(path)}" for path in files
    ]
    payload = "\n".join(lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper(), len(files)


def _running_process_names() -> list[str]:
    if os.name != "nt":
        return []
    completed = subprocess.run(
        ["tasklist.exe", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return ["<process-inventory-unavailable>"]
    return [
        row[0].strip().lower()
        for row in csv.reader(io.StringIO(completed.stdout))
        if row
    ]


def verify_projects_metrics_no_launch_candidate(
    manifest_path: Path,
    *,
    source_root: Path = ROOT,
    running_process_names: Iterable[str] | None = None,
) -> dict[str, object]:
    """Return a deterministic no-launch report for one frozen candidate."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_schema = manifest.get("schema_version")
    v2_manifest = manifest_schema == 2
    source = _mapping(manifest.get("source"))
    build = _mapping(manifest.get("build"))
    attempt = _mapping(manifest.get("live_attempt"))
    boundary = _mapping(manifest.get("event_binding"))
    production = _mapping(manifest.get("production_contract"))
    stage_order = production.get("stage_order")
    checkpoint_v2 = _mapping(production.get("checkpoint_state_v2"))
    effect_boundary = _mapping(production.get("effect_boundary"))
    commands = _mapping(manifest.get("commands"))
    ck3_launch = _mapping(commands.get("ck3_launch"))
    bridge = _mapping(build.get("bridge"))
    injector = _mapping(build.get("injector"))
    frozen_files = _mapping(source.get("frozen_files"))

    cmake_path = source_root / "ck3_autonomous_player/native_bridge/CMakeLists.txt"
    adapter_path = (
        source_root
        / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
    )
    abi_path = (
        source_root
        / "ck3_autonomous_player/native_bridge/research/"
        "zhongguo_projects_metrics_postcondition_v1_abi.json"
    )
    source_contract_path = (
        source_root
        / "ck3_autonomous_player/native_bridge/research/fixtures/"
        "zhongguo_projects_metrics_postcondition_v1_source_contract.json"
    )
    action_contract_path = (
        source_root / "tools/zg361_phase2_projects_metrics_action_contract.json"
    )
    facade_path = (
        source_root
        / "ck3_autonomous_player/src/xar_autoplayer/bridge/"
        "zhongguo_projects_metrics_postcondition_contract.py"
    )
    capture_contract_path = (
        source_root
        / "tools/zg361_phase2_projects_metrics_source_checkpoint_contract.json"
    )
    pump_path = (
        source_root
        / "mod_zhongguo_style/common/scripted_effects/"
        "zg361_phase2_central_010_serial_pump_effects.txt"
    )
    stage_path = (
        source_root
        / "mod_zhongguo_style/common/scripted_effects/"
        "zg361_phase2_central_007_stage07_09_effects.txt"
    )
    generator_path = (
        source_root
        / "mod_zhongguo_style/tools/gen_361_phase2_central_runtime.py"
    )

    cmake = cmake_path.read_text(encoding="utf-8")
    adapter = adapter_path.read_text(encoding="utf-8")
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    source_contract = json.loads(source_contract_path.read_text(encoding="utf-8"))
    action_contract = json.loads(action_contract_path.read_text(encoding="utf-8"))
    capture_contract = (
        json.loads(capture_contract_path.read_text(encoding="utf-8"))
        if v2_manifest
        else {}
    )
    facade = facade_path.read_text(encoding="utf-8")
    pump = pump_path.read_text(encoding="utf-8-sig") if v2_manifest else ""
    stages = stage_path.read_text(encoding="utf-8-sig") if v2_manifest else ""
    generator = generator_path.read_text(encoding="utf-8") if v2_manifest else ""

    bridge_path = Path(str(bridge.get("path", "")))
    injector_path = Path(str(injector.get("path", "")))
    cache_path = Path(str(build.get("cmake_cache_path", "")))
    attempt_path = Path(str(attempt.get("path", "")))
    exe_path = Path(str(manifest.get("ck3_executable_path", "")))
    process_names = {
        value.lower()
        for value in (
            running_process_names
            if running_process_names is not None
            else _running_process_names()
        )
    }

    option_match = re.search(
        rf"option\(\s*{PRIVATE_SWITCH}\s*.*?\s+OFF\s*\)",
        cmake,
        re.DOTALL,
    )
    guarded_capability = re.search(
        rf"#if defined\({PRIVATE_SWITCH}\).*?"
        r"kZhongguoProjectsMetricsPostconditionV1Capability.*?#endif",
        adapter,
        re.DOTALL,
    )
    cache_text = cache_path.read_text(encoding="utf-8", errors="replace") if (
        cache_path.is_file()
    ) else ""

    frozen_file_checks: dict[str, bool] = {}
    for relative, expected in frozen_files.items():
        path = source_root / str(relative)
        frozen_file_checks[str(relative)] = (
            path.is_file()
            and isinstance(expected, str)
            and _sha256(path) == expected.upper()
        )

    visual = _mapping(action_contract.get("visual_checkpoint_boundary"))
    expected_stage_order = [
        {
            "stage": 7,
            "purpose": "credit_project",
            "effect": "zg361_p2c_stage_07_credit_project_effect",
            "adapter": "zg361_cp_open_portfolio_effect",
        },
        {
            "stage": 8,
            "purpose": "metrics_delivery",
            "effect": "zg361_p2c_stage_08_metrics_delivery_effect",
            "adapter": "zg361_p3_open_portfolio_effect",
        },
    ]
    stage7_dispatch = (
        "var:zg361_p2c_stage = 7 } "
        "zg361_p2c_stage_07_credit_project_effect = yes"
    )
    stage8_dispatch = (
        "var:zg361_p2c_stage = 8 } "
        "zg361_p2c_stage_08_metrics_delivery_effect = yes"
    )
    purpose_shards = effect_boundary.get("purpose_shards")
    shard_checks: dict[str, bool] = {}
    shard_counts: list[int] = []
    if isinstance(purpose_shards, Mapping):
        for relative, recorded_count in purpose_shards.items():
            shard_path = source_root / str(relative)
            if shard_path.is_file():
                payload = shard_path.read_text(encoding="utf-8-sig")
                observed_count = _top_level_definition_count(payload)
            else:
                observed_count = -1
            shard_checks[str(relative)] = (
                isinstance(recorded_count, int)
                and recorded_count == observed_count
                and 1 <= observed_count <= 10
                and observed_count <= 20
            )
            shard_counts.append(observed_count)
    launch_command = str(ck3_launch.get("powershell", ""))
    native_fingerprint, native_file_count = _native_source_fingerprint(
        source_root / "ck3_autonomous_player/native_bridge"
    )
    checks = {
        "manifest_identity": (
            manifest_schema in (1, 2)
            and manifest.get("kind")
            == "zg361_projects_metrics_no_launch_candidate"
            and manifest.get("readiness") == "static-ready-live-pending"
        ),
        "base_commit_exact": source.get("base_commit") == EXPECTED_BASE_COMMIT,
        "candidate_commit_pinned": bool(
            re.fullmatch(r"[0-9a-f]{40}", str(source.get("candidate_commit", "")))
        ),
        "frozen_source_files_match": bool(frozen_file_checks)
        and all(frozen_file_checks.values()),
        "native_source_fingerprint_matches": (
            not v2_manifest
            or (
                source.get("native_source_fingerprint_sha256")
                == native_fingerprint
                and source.get("native_source_file_count") == native_file_count
            )
        ),
        "private_switch_default_off": option_match is not None,
        "private_capability_guarded": guarded_capability is not None,
        "candidate_cache_opted_in": (
            f"{PRIVATE_SWITCH}:BOOL=ON" in cache_text
        ),
        "candidate_cache_hash_matches": (
            cache_path.is_file()
            and _sha256(cache_path)
            == str(build.get("cmake_cache_sha256", "")).upper()
        ),
        "paired_bridge_hash_matches": (
            bridge_path.is_file()
            and _sha256(bridge_path) == str(bridge.get("sha256", "")).upper()
            and bridge_path.stat().st_size == bridge.get("bytes")
            and bridge_path.name == "xar_ck3_bridge.dll"
        ),
        "paired_injector_hash_matches": (
            injector_path.is_file()
            and _sha256(injector_path)
            == str(injector.get("sha256", "")).upper()
            and injector_path.stat().st_size == injector.get("bytes")
            and injector_path.name == "xar_ck3_bridge_injector.exe"
        ),
        "exact_ck3_executable_matches": (
            exe_path.is_file() and _sha256(exe_path) == EXPECTED_EXE_SHA256
        ),
        "abi_remains_not_live": (
            abi.get("status") == "static_and_fixture_ready_not_live"
            and _mapping(abi.get("readiness")).get("production_live_ready")
            is False
            and _mapping(abi.get("private_candidate")).get(
                "production_advertisement_promoted"
            )
            is False
        ),
        "source_contract_candidate_only": (
            source_contract.get("shared_wiring")
            == "default_off_complete_not_advertised"
            and source_contract.get("private_candidate_switch")
            == PRIVATE_SWITCH
        ),
        "event_binding_reuses_existing_facade": (
            "def bind_projects_metrics_event_snapshots_v1(" in facade
            and boundary.get("facade")
            == "bind_projects_metrics_event_snapshots_v1"
            and boundary.get("source_event") == SOURCE_EVENT
            and boundary.get("result_event") == RESULT_EVENT
            and visual.get("source_event") == SOURCE_EVENT
            and visual.get("result_event") == RESULT_EVENT
            and visual.get("same_cell_as_background_provider") is False
        ),
        "production_stage7_precedes_stage8": (
            not v2_manifest
            or (
                stage_order == expected_stage_order
                and stage7_dispatch in pump
                and stage8_dispatch in pump
                and pump.index(stage7_dispatch) < pump.index(stage8_dispatch)
                and "zg361_cp_open_portfolio_effect" in stages
                and "zg361_p3_open_portfolio_effect" in stages
                and '(7, "credit_project", "zg361_cp_open_portfolio_effect")'
                in generator
                and '(8, "metrics_delivery", "zg361_p3_open_portfolio_effect")'
                in generator
            )
        ),
        "checkpoint_state_v2_bound": (
            not v2_manifest
            or (
                production.get("integrated_fix_commit")
                == EXPECTED_PRODUCTION_FIX_COMMIT
                and checkpoint_v2.get("allowlist_id")
                == CHECKPOINT_ALLOWLIST_ID
                and checkpoint_v2.get("available_states")
                == CHECKPOINT_STATES
                and checkpoint_v2.get("source_capture_state")
                == "cp26_ready_p3_absent"
                and checkpoint_v2.get("registry_schema_version") == 2
                and abi.get("allowlist_id") == CHECKPOINT_ALLOWLIST_ID
                and _mapping(abi.get("readiness")).get("checkpoint_state")
                == " | ".join(CHECKPOINT_STATES)
                and capture_contract.get("schema_version") == 2
                and _mapping(capture_contract.get("required_checkpoint")).get(
                    "provider_checkpoint_state"
                )
                == "cp26_ready_p3_absent"
                and _mapping(capture_contract.get("registry")).get(
                    "schema_version"
                )
                == 2
            )
        ),
        "purpose_effect_shards_within_limit": (
            not v2_manifest
            or (
                effect_boundary.get("target_max_per_file") == 10
                and effect_boundary.get("hard_max_per_file") == 20
                and effect_boundary.get("hard_limit_exceptions") == []
                and effect_boundary.get("shard_count") == 10
                and isinstance(purpose_shards, Mapping)
                and len(purpose_shards) == 10
                and bool(shard_checks)
                and all(shard_checks.values())
                and max(shard_counts, default=-1)
                == effect_boundary.get("max_effects_per_file")
                and max(shard_counts, default=21) <= 10
            )
        ),
        "exact_ck3_command_frozen_not_executed": (
            not v2_manifest
            or (
                ck3_launch.get("executed") is False
                and ck3_launch.get("starts_ck3") is True
                and "native-session" in launch_command
                and "--cold-start-checkpoint" in launch_command
                and str(bridge_path) in launch_command
                and str(injector_path) in launch_command
                and str(manifest.get("ck3_executable_path", ""))
                .replace("/binaries/ck3.exe", "")
                .replace("\\binaries\\ck3.exe", "")
                in launch_command
                and str(attempt.get("attempt_id", "")) in launch_command
            )
        ),
        "formal_registry_not_modified": (
            manifest.get("formal_runner_registry_modified") is False
            and not any("run_zhongguo_acceptance.py" in key for key in frozen_files)
        ),
        "future_live_attempt_unique_and_absent": (
            attempt.get("status") == "absent"
            and attempt.get("started") is False
            and attempt.get("consumed") is False
            and isinstance(attempt.get("attempt_id"), str)
            and bool(attempt.get("attempt_id"))
            and bool(str(attempt_path))
            and not attempt_path.exists()
        ),
        "ck3_and_injector_not_running": (
            "ck3.exe" not in process_names
            and "xar_ck3_bridge_injector.exe" not in process_names
        ),
        "no_live_or_ack_claim": (
            manifest.get("ck3_started") is False
            and manifest.get("live_proof_claimed") is False
            and manifest.get("action_ack_is_business_postcondition") is False
            and manifest.get("production_advertisement_ready") is False
        ),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_projects_metrics_no_launch_candidate_preflight",
        "result": "READY_TO_LIVE" if not failed else "RED",
        "readiness": "static-ready-live-pending" if not failed else "research",
        "checks": checks,
        "frozen_file_checks": frozen_file_checks,
        "purpose_shard_checks": shard_checks,
        "failed_checks": failed,
        "bridge_sha256": (
            _sha256(bridge_path) if bridge_path.is_file() else None
        ),
        "injector_sha256": (
            _sha256(injector_path) if injector_path.is_file() else None
        ),
        "attempt_id": attempt.get("attempt_id"),
        "attempt_path": str(attempt_path),
        "ck3_started": False,
        "live_proof_claimed": False,
        "production_advertisement_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = verify_projects_metrics_no_launch_candidate(
        args.manifest.resolve(), source_root=args.source_root.resolve()
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.check and report["result"] != "READY_TO_LIVE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
