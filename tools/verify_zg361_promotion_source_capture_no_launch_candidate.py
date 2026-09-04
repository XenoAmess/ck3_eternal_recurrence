#!/usr/bin/env python3
"""Verify the frozen promotion-source capture candidate without launching CK3."""

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
import sys
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
MOD_TOOLS = ROOT / "mod_zhongguo_style" / "tools"
if str(MOD_TOOLS) not in sys.path:
    sys.path.insert(0, str(MOD_TOOLS))

from zg361_effect_sharding import top_level_effect_entries  # noqa: E402


EXPECTED_BASE_COMMIT = "d53befaa4872662562f5db5d31757ca731e799e0"
EXPECTED_CANDIDATE_COMMIT = "366f30f0e899650582a7f76c8f0043ecc37e4887"
EXPECTED_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
QUERY_CAPABILITY = "game.command.query-zhongguo-promotion-source-progress-v1"
QUERY_TRANSPORT = (
    "game.contract.zhongguo-promotion-source-progress-v1-fail-closed"
)
ACTION_CAPABILITY = "game.command.activate-zhongguo-review-now-v1"
ACTION_TRANSPORT = "game.contract.zhongguo-review-now-action-v1-fail-closed"
LIVE_MODE = "--phase2-promotion-source-checkpoint-live"
LEGACY_EFFECT_FILES = (
    "zg361_feedback_promotion_pip_runtime_effects.txt",
    "zg361_generated_compensation_runtime_effects.txt",
)
STALE_COUNT_TESTS = (
    "combat_v3_source_contract_test.cpp",
    "zhongguo_ai_owned_case_snapshot_v1_source_contract_test.cpp",
    "zhongguo_case_snapshot_v1_source_contract_test.cpp",
    "zhongguo_b2_pip_snapshot_v1_source_contract_test.cpp",
    "zhongguo_incident_snapshot_v1_source_contract_test.cpp",
    "zhongguo_result_case_snapshot_v1_source_contract_test.cpp",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


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


def _native_source_fingerprint(root: Path) -> tuple[str, int]:
    native = root / "ck3_autonomous_player/native_bridge"
    files = [native / "CMakeLists.txt"]
    for tree in (native / "include", native / "src"):
        files.extend(
            path
            for path in tree.rglob("*")
            if path.is_file() and path.suffix in {".cpp", ".hpp", ".h", ".c"}
        )
    lines = []
    for path in sorted(files, key=lambda item: str(item.resolve()).lower()):
        relative = str(path.relative_to(native))
        lines.append(f"{relative}\0{_sha256(path)}")
    fingerprint = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return fingerprint.upper(), len(files)


def _effect_inventory(root: Path, pattern: str) -> dict[str, object]:
    effect_dir = root / "mod_zhongguo_style/common/scripted_effects"
    files = sorted(effect_dir.glob(pattern), key=lambda path: path.name)
    rows = []
    for path in files:
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "effect_count": len(top_level_effect_entries(path.read_bytes())),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    fingerprint_lines = [
        f"{row['path']}\0{row['effect_count']}\0{row['bytes']}\0{row['sha256']}"
        for row in rows
    ]
    counts = [int(row["effect_count"]) for row in rows]
    return {
        "files": rows,
        "file_count": len(rows),
        "effect_count": sum(counts),
        "minimum_effects_per_file": min(counts) if counts else 0,
        "maximum_effects_per_file": max(counts) if counts else 0,
        "fingerprint_sha256": hashlib.sha256(
            "\n".join(fingerprint_lines).encode("utf-8")
        ).hexdigest().upper(),
    }


def _adapter_default_off(header: str, adapter: str, game_adapter: str) -> bool:
    query_production_line = re.search(
        r"^\s*ck3_11906::kZhongguoPromotionSourceProgressV1Capability,\s*$",
        adapter,
        re.MULTILINE,
    )
    action_production_line = re.search(
        r"^\s*ck3_11906::kZhongguoReviewNowActionV1Capability,\s*$",
        adapter,
        re.MULTILINE,
    )
    query_default_off = re.search(
        r"kZhongguoPromotionSourceProgressV1ProductionCapabilityAdvertised\s*=\s*"
        r"false;",
        header,
    )
    action_default_off = re.search(
        r"kZhongguoReviewNowActionV1ProductionCapabilityAdvertised\s*=\s*false;",
        header,
    )
    return (
        query_default_off is not None
        and action_default_off is not None
        and query_production_line is None
        and action_production_line is None
        and "kZhongguoPromotionSourceProgressV1TransportCapability," in adapter
        and "kZhongguoReviewNowActionV1TransportCapability," in adapter
        and "kZhongguoPromotionSourceProgressV1TransportCapability" in game_adapter
        and "kZhongguoReviewNowActionV1TransportCapability" in game_adapter
    )


def _value_after(argv: list[str], flag: str) -> str | None:
    if argv.count(flag) != 1:
        return None
    index = argv.index(flag)
    return argv[index + 1] if index + 1 < len(argv) else None


def verify_promotion_source_capture_no_launch_candidate(
    manifest_path: Path,
    *,
    source_root: Path = ROOT,
    running_process_names: Iterable[str] | None = None,
) -> dict[str, object]:
    """Return one deterministic, read-only preflight report."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = _mapping(manifest.get("source"))
    build = _mapping(manifest.get("build"))
    bridge = _mapping(build.get("bridge"))
    injector = _mapping(build.get("injector"))
    attempt = _mapping(manifest.get("live_attempt"))
    command = _mapping(manifest.get("live_command"))
    effect_boundary = _mapping(manifest.get("effect_boundary"))
    query_action_boundary = _mapping(manifest.get("query_action_boundary"))
    player_gate = _mapping(manifest.get("player_gate"))
    choreography = _mapping(manifest.get("choreography"))
    frozen_files = _mapping(source.get("frozen_files"))

    native = source_root / "ck3_autonomous_player/native_bridge"
    header_path = native / "include/xar_bridge/zhongguo_promotion_source_progress_v1.hpp"
    adapter_path = native / "src/ck3_11906_adapter.cpp"
    game_adapter_path = native / "src/game_adapter.cpp"
    abi_path = native / "research/zhongguo_promotion_source_progress_v1_abi.json"
    contract_path = native / (
        "research/fixtures/zhongguo_promotion_source_progress_v1_source_contract.json"
    )
    action_gui_path = source_root / (
        "mod_zhongguo_style/common/scripted_guis/"
        "zg361_promotion_source_progress_guis.txt"
    )
    bridge_gui_path = source_root / "mod_zhongguo_style/gui/zg361_promotion_source_bridge.gui"
    entry_path = source_root / "tools/zg361_phase2_promotion_source_production_entry.py"
    capture_path = source_root / "tools/zg361_phase2_promotion_source_checkpoint_capture.py"
    seed_contract_path = source_root / "tools/zg361_phase2_seed_contract.json"

    header = header_path.read_text(encoding="utf-8-sig")
    adapter = adapter_path.read_text(encoding="utf-8-sig")
    game_adapter = game_adapter_path.read_text(encoding="utf-8-sig")
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    source_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    action_gui = action_gui_path.read_text(encoding="utf-8-sig")
    bridge_gui = bridge_gui_path.read_text(encoding="utf-8-sig")
    entry = entry_path.read_text(encoding="utf-8-sig")
    capture = capture_path.read_text(encoding="utf-8-sig")
    seed_contract = json.loads(seed_contract_path.read_text(encoding="utf-8"))

    bridge_path = Path(str(bridge.get("path", "")))
    injector_path = Path(str(injector.get("path", "")))
    cache_path = Path(str(build.get("cmake_cache_path", "")))
    exe_path = Path(str(manifest.get("ck3_executable_path", "")))
    attempt_path = Path(str(attempt.get("path", "")))
    cache = (
        cache_path.read_text(encoding="utf-8", errors="replace")
        if cache_path.is_file()
        else ""
    )
    process_names = {
        name.lower()
        for name in (
            running_process_names
            if running_process_names is not None
            else _running_process_names()
        )
    }

    frozen_file_checks: dict[str, bool] = {}
    for relative, expected in frozen_files.items():
        path = source_root / str(relative)
        frozen_file_checks[str(relative)] = (
            path.is_file()
            and isinstance(expected, str)
            and _sha256(path) == expected.upper()
        )

    native_fingerprint, native_file_count = _native_source_fingerprint(source_root)
    feedback = _effect_inventory(
        source_root, "zg361_feedback_promotion_pip_[0-9][0-9][0-9]_*.txt"
    )
    compensation = _effect_inventory(
        source_root, "zg361_compensation_[0-9][0-9]_*.txt"
    )
    expected_feedback = _mapping(effect_boundary.get("feedback_promotion_pip"))
    expected_compensation = _mapping(effect_boundary.get("compensation"))
    effect_dir = source_root / "mod_zhongguo_style/common/scripted_effects"

    argv_value = command.get("argv")
    argv = [str(value) for value in argv_value] if isinstance(argv_value, list) else []
    command_paths_match = (
        _value_after(argv, "--bridge-dll") == str(bridge_path)
        and _value_after(argv, "--bridge-injector") == str(injector_path)
        and _value_after(argv, "--artifacts-dir") == str(attempt_path)
        and _value_after(argv, "--phase2-seed-contract")
        == str(command.get("seed_contract_path"))
    )
    pipe = _value_after(argv, "--bridge-pipe")
    timeout = _value_after(
        argv, "--phase2-promotion-source-checkpoint-timeout-seconds"
    )
    execution_root = Path(str(command.get("execution_source_root", "")))
    expected_argv = [
        str(execution_root / "tools/.venv/Scripts/python.exe"),
        str(execution_root / "tools/run_zhongguo_acceptance.py"),
        "--artifacts-dir",
        str(attempt_path),
        LIVE_MODE,
        "--phase2-promotion-source-checkpoint-timeout-seconds",
        "600",
        "--bridge-dll",
        str(bridge_path),
        "--bridge-injector",
        str(injector_path),
        "--bridge-pipe",
        pipe or "",
        "--phase2-seed-contract",
        str(command.get("seed_contract_path")),
    ]
    production_capabilities = _mapping(abi.get("readiness"))

    repaired_tests = {
        name: "kBaseCapabilityCount = 78"
        in (native / "src" / name).read_text(encoding="utf-8-sig")
        for name in STALE_COUNT_TESTS
    }
    checks = {
        "manifest_identity": (
            manifest.get("schema_version") == 1
            and manifest.get("kind")
            == "zg361_promotion_source_capture_no_launch_candidate"
            and manifest.get("readiness") == "static-ready-live-pending"
        ),
        "integrated_b7_base_and_latest_candidate": (
            source.get("base_commit") == EXPECTED_BASE_COMMIT
            and source.get("candidate_commit") == EXPECTED_CANDIDATE_COMMIT
        ),
        "frozen_source_files_match": bool(frozen_file_checks)
        and all(frozen_file_checks.values()),
        "native_source_fingerprint_matches": (
            native_fingerprint
            == str(source.get("native_source_fingerprint_sha256", "")).upper()
            and native_file_count == source.get("native_source_file_count")
        ),
        "fresh_default_build_cache": (
            "CMAKE_BUILD_TYPE:STRING=Release" in cache
            and "XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1:BOOL=OFF"
            in cache
            and "XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1:BOOL=OFF"
            in cache
            and _sha256(cache_path)
            == str(build.get("cmake_cache_sha256", "")).upper()
            if cache_path.is_file()
            else False
        ),
        "frozen_bridge_pair_matches": (
            bridge_path.is_file()
            and bridge_path.name == "xar_ck3_bridge.dll"
            and bridge_path.stat().st_size == bridge.get("bytes")
            and _sha256(bridge_path) == str(bridge.get("sha256", "")).upper()
            and injector_path.is_file()
            and injector_path.name == "xar_ck3_bridge_injector.exe"
            and injector_path.stat().st_size == injector.get("bytes")
            and _sha256(injector_path) == str(injector.get("sha256", "")).upper()
        ),
        "exact_ck3_executable_matches": (
            exe_path.is_file() and _sha256(exe_path) == EXPECTED_EXE_SHA256
        ),
        "review_query_action_default_off": (
            _adapter_default_off(header, adapter, game_adapter)
            and query_action_boundary.get("query_production_advertised") is False
            and query_action_boundary.get("action_production_advertised") is False
            and query_action_boundary.get("transport_only_fail_closed") is True
            and query_action_boundary.get("provider_default_off") is True
            and query_action_boundary.get("readiness") == "live-pending"
            and query_action_boundary.get("ack_is_business_result") is False
            and abi.get("status") == "static_ready_default_off_live_pending"
            and production_capabilities.get("production_capability_advertised")
            is False
            and production_capabilities.get("production_live_ready") is False
            and source_contract.get("production_live_ready") is False
            and source_contract.get("ack_only") is True
            and QUERY_CAPABILITY not in adapter
            and ACTION_CAPABILITY not in adapter
            and QUERY_TRANSPORT in header
            and ACTION_TRANSPORT in header
        ),
        "played_player_non_ai_product_gate": (
            player_gate.get("scope") == "GetPlayer.MakeScope"
            and player_gate.get("is_ai") is False
            and player_gate.get("celestial_liege_required") is True
            and player_gate.get("review_business_valid_required") is True
            and player_gate.get("prestige_required") == 150
            and player_gate.get("prestige_cost") == 150
            and player_gate.get("pending_flag") == "zg361_review_now_pending"
            and action_gui.count("is_ai = no") >= 4
            and action_gui.count("zg361_is_celestial_liege_trigger = yes") >= 2
            and action_gui.count("zg361_review_now_business_valid_trigger = yes")
            >= 2
            and action_gui.count("prestige >= 150") >= 2
            and "add_prestige = -150" in action_gui
            and "add_character_flag = zg361_review_now_pending" in action_gui
            and "GetPlayer.MakeScope" in bridge_gui
            and "caller_character" not in bridge_gui
        ),
        "m146_option1_d1_m147_choreography": (
            choreography.get("start") == "real paused zg361pp.146"
            and choreography.get("action")
            == "select option index 1 through managed product service"
            and choreography.get("advance")
            == "at least D+1 through managed product service, bounded by 400 days"
            and choreography.get("target") == "real paused zg361pp.147"
            and choreography.get("action_ack_used_as_state_evidence") is False
            and choreography.get("provider_default_off_unchanged") is True
            and all(
                token in entry
                for token in (
                    'M146 = "zg361pp.146"',
                    'M147 = "zg361pp.147"',
                    "MAX_ADVANCE_DAYS = 400",
                    "service.select_event_option(",
                    "m146_date + HOURS_PER_DAY",
                    '"action_ack_used_as_state_evidence": False',
                    'evidence["readiness"] = "paused-real-zg361pp.147"',
                )
            )
            and "capture_promotion_source_checkpoint_v2" in capture
            and "promotion_compensation_provider_default_off_unchanged" in capture
        ),
        "effect_shards_match_manifest": (
            feedback["file_count"] == expected_feedback.get("file_count")
            and feedback["effect_count"] == expected_feedback.get("effect_count")
            and feedback["fingerprint_sha256"]
            == expected_feedback.get("fingerprint_sha256")
            and compensation["file_count"] == expected_compensation.get("file_count")
            and compensation["effect_count"]
            == expected_compensation.get("effect_count")
            and compensation["fingerprint_sha256"]
            == expected_compensation.get("fingerprint_sha256")
        ),
        "effect_shards_target_1_to_10_and_hard_max_20": (
            feedback["file_count"] == 39
            and feedback["minimum_effects_per_file"] >= 1
            and feedback["maximum_effects_per_file"] <= 10
            and feedback["maximum_effects_per_file"] <= 20
            and compensation["file_count"] == 25
            and compensation["minimum_effects_per_file"] >= 1
            and compensation["maximum_effects_per_file"] <= 10
            and compensation["maximum_effects_per_file"] <= 20
        ),
        "legacy_effect_monoliths_absent": not any(
            (effect_dir / name).exists() for name in LEGACY_EFFECT_FILES
        ),
        "stale_adapter_count_contracts_repaired": all(repaired_tests.values()),
        "fresh_native_tests_green": (
            _mapping(manifest.get("tests")).get("full_native")
            == {"result": "GREEN", "passed": 93, "failed": 0}
        ),
        "single_authorized_runner_command": (
            command.get("authorized_command_count") == 1
            and command.get("runner_owns_ck3_lifecycle") is True
            and argv == expected_argv
            and argv.count(LIVE_MODE) == 1
            and "--preflight" not in argv
            and not any("fixture" in value.lower() for value in argv)
            and not any(value.lower().endswith("ck3.exe") for value in argv)
            and command_paths_match
            and timeout == "600"
            and isinstance(pipe, str)
            and re.fullmatch(r"\\\\\.\\pipe\\xar_ck3_bridge_zg361_[0-9a-f]{32}", pipe)
            is not None
        ),
        "seed_contract_exact_and_ready": (
            seed_contract.get("ready") is True
            and _mapping(seed_contract.get("runtime")).get("game_version") == "1.19.0.6"
            and str(_mapping(seed_contract.get("runtime")).get("executable_sha256", "")).upper()
            == EXPECTED_EXE_SHA256
            and _sha256(seed_contract_path)
            == str(command.get("seed_contract_sha256", "")).upper()
        ),
        "future_live_attempt_unique_and_absent": (
            attempt.get("status") == "absent"
            and attempt.get("started") is False
            and attempt.get("consumed") is False
            and isinstance(attempt.get("attempt_id"), str)
            and bool(attempt.get("attempt_id"))
            and not attempt_path.exists()
        ),
        "no_production_or_shared_runner_change_claim": (
            manifest.get("production_files_modified_by_freeze") is False
            and manifest.get("formal_runner_modified_by_freeze") is False
        ),
        "no_launch_or_ack_result_claim": (
            manifest.get("ck3_started") is False
            and manifest.get("live_proof_claimed") is False
            and manifest.get("action_ack_is_business_postcondition") is False
            and manifest.get("production_advertisement_ready") is False
            and "ck3.exe" not in process_names
            and "xar_ck3_bridge_injector.exe" not in process_names
        ),
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    return {
        "schema_version": 1,
        "kind": "zg361_promotion_source_capture_no_launch_candidate_preflight",
        "result": "READY_TO_SERIAL_LIVE" if not failed else "RED",
        "readiness": "static-ready-live-pending" if not failed else "research",
        "checks": checks,
        "frozen_file_checks": frozen_file_checks,
        "effect_boundary": {
            "feedback_promotion_pip": {key: value for key, value in feedback.items() if key != "files"},
            "compensation": {key: value for key, value in compensation.items() if key != "files"},
        },
        "repaired_adapter_count_tests": repaired_tests,
        "failed_checks": failed,
        "attempt_id": attempt.get("attempt_id"),
        "attempt_path": str(attempt_path),
        "authorized_live_argv": argv,
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
    report = verify_promotion_source_capture_no_launch_candidate(
        args.manifest.resolve(), source_root=args.source_root.resolve()
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return (
        1
        if args.check and report["result"] != "READY_TO_SERIAL_LIVE"
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
