from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from verify_zg361_projects_metrics_no_launch_candidate import (  # noqa: E402
    CHECKPOINT_ALLOWLIST_ID,
    CHECKPOINT_STATES,
    EXPECTED_BASE_COMMIT,
    EXPECTED_EXE_SHA256,
    EXPECTED_PRODUCTION_FIX_COMMIT,
    PRIVATE_SWITCH,
    _native_source_fingerprint,
    verify_projects_metrics_no_launch_candidate,
)


def _write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode("utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "source"
    cmake = root / "ck3_autonomous_player/native_bridge/CMakeLists.txt"
    adapter = root / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp"
    abi = root / (
        "ck3_autonomous_player/native_bridge/research/"
        "zhongguo_projects_metrics_postcondition_v1_abi.json"
    )
    source_contract = root / (
        "ck3_autonomous_player/native_bridge/research/fixtures/"
        "zhongguo_projects_metrics_postcondition_v1_source_contract.json"
    )
    action = root / "tools/zg361_phase2_projects_metrics_action_contract.json"
    facade = root / (
        "ck3_autonomous_player/src/xar_autoplayer/bridge/"
        "zhongguo_projects_metrics_postcondition_contract.py"
    )
    _write(cmake, f"option(\n  {PRIVATE_SWITCH}\n  x\n  OFF\n)\n")
    _write(
        adapter,
        f"#if defined({PRIVATE_SWITCH})\n"
        "kZhongguoProjectsMetricsPostconditionV1Capability\n#endif\n",
    )
    _write(
        abi,
        json.dumps({
            "status": "static_and_fixture_ready_not_live",
            "readiness": {"production_live_ready": False},
            "private_candidate": {"production_advertisement_promoted": False},
        }),
    )
    _write(
        source_contract,
        json.dumps({
            "shared_wiring": "default_off_complete_not_advertised",
            "private_candidate_switch": PRIVATE_SWITCH,
        }),
    )
    _write(
        action,
        json.dumps({"visual_checkpoint_boundary": {
            "source_event": "zg361cp.26",
            "result_event": "zg361p3.229",
            "same_cell_as_background_provider": False,
        }}),
    )
    _write(facade, "def bind_projects_metrics_event_snapshots_v1():\n    pass\n")
    bridge = tmp_path / "build/xar_ck3_bridge.dll"
    injector = tmp_path / "build/xar_ck3_bridge_injector.exe"
    cache = tmp_path / "build/CMakeCache.txt"
    exe = tmp_path / "ck3.exe"
    _write(bridge, b"bridge")
    _write(injector, b"injector")
    _write(cache, f"{PRIVATE_SWITCH}:BOOL=ON\n")
    _write(exe, b"fixture-exe")
    frozen = {
        str(cmake.relative_to(root)).replace("\\", "/"): _sha(cmake),
        str(adapter.relative_to(root)).replace("\\", "/"): _sha(adapter),
    }
    manifest = tmp_path / "manifest.json"
    payload = {
        "schema_version": 1,
        "kind": "zg361_projects_metrics_no_launch_candidate",
        "readiness": "static-ready-live-pending",
        "source": {
            "base_commit": EXPECTED_BASE_COMMIT,
            "candidate_commit": "1" * 40,
            "frozen_files": frozen,
        },
        "build": {
            "bridge": {
                "path": str(bridge), "sha256": _sha(bridge),
                "bytes": bridge.stat().st_size,
            },
            "injector": {
                "path": str(injector), "sha256": _sha(injector),
                "bytes": injector.stat().st_size,
            },
            "cmake_cache_path": str(cache),
            "cmake_cache_sha256": _sha(cache),
        },
        "ck3_executable_path": str(exe),
        "event_binding": {
            "facade": "bind_projects_metrics_event_snapshots_v1",
            "source_event": "zg361cp.26",
            "result_event": "zg361p3.229",
        },
        "live_attempt": {
            "attempt_id": "fixture-absent-attempt",
            "path": str(tmp_path / "absent"),
            "status": "absent",
            "started": False,
            "consumed": False,
        },
        "formal_runner_registry_modified": False,
        "ck3_started": False,
        "live_proof_claimed": False,
        "action_ack_is_business_postcondition": False,
        "production_advertisement_ready": False,
    }
    _write(manifest, json.dumps(payload))
    return manifest, root


def _upgrade_to_v2(manifest: Path, root: Path, tmp_path: Path) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["schema_version"] = 2
    payload["production_contract"] = {
        "integrated_fix_commit": EXPECTED_PRODUCTION_FIX_COMMIT,
        "stage_order": [
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
        ],
        "checkpoint_state_v2": {
            "allowlist_id": CHECKPOINT_ALLOWLIST_ID,
            "available_states": CHECKPOINT_STATES,
            "source_capture_state": "cp26_ready_p3_absent",
            "registry_schema_version": 2,
        },
        "effect_boundary": {
            "target_max_per_file": 10,
            "hard_max_per_file": 20,
            "shard_count": 10,
            "max_effects_per_file": 1,
            "hard_limit_exceptions": [],
            "purpose_shards": {},
        },
    }
    attempt_id = payload["live_attempt"]["attempt_id"]
    bridge = payload["build"]["bridge"]["path"]
    injector = payload["build"]["injector"]["path"]
    payload["commands"] = {
        "ck3_launch": {
            "starts_ck3": True,
            "executed": False,
            "powershell": (
                f"run {payload['ck3_executable_path']} {bridge} {injector} "
                f"native-session --cold-start-checkpoint {attempt_id}"
            ),
        }
    }
    abi_path = root / (
        "ck3_autonomous_player/native_bridge/research/"
        "zhongguo_projects_metrics_postcondition_v1_abi.json"
    )
    abi = json.loads(abi_path.read_text(encoding="utf-8"))
    abi["allowlist_id"] = CHECKPOINT_ALLOWLIST_ID
    abi["readiness"]["checkpoint_state"] = " | ".join(CHECKPOINT_STATES)
    _write(abi_path, json.dumps(abi))
    _write(
        root / "tools/zg361_phase2_projects_metrics_source_checkpoint_contract.json",
        json.dumps({
            "schema_version": 2,
            "required_checkpoint": {
                "provider_checkpoint_state": "cp26_ready_p3_absent"
            },
            "registry": {"schema_version": 2},
        }),
    )
    _write(
        root / (
            "mod_zhongguo_style/common/scripted_effects/"
            "zg361_phase2_central_010_serial_pump_effects.txt"
        ),
        "else_if = { limit = { var:zg361_p2c_stage = 7 } "
        "zg361_p2c_stage_07_credit_project_effect = yes }\n"
        "else_if = { limit = { var:zg361_p2c_stage = 8 } "
        "zg361_p2c_stage_08_metrics_delivery_effect = yes }\n",
    )
    _write(
        root / (
            "mod_zhongguo_style/common/scripted_effects/"
            "zg361_phase2_central_007_stage07_09_effects.txt"
        ),
        "zg361_p2c_stage_07_credit_project_effect = { "
        "zg361_cp_open_portfolio_effect = yes }\n"
        "zg361_p2c_stage_08_metrics_delivery_effect = { "
        "zg361_p3_open_portfolio_effect = yes }\n",
    )
    _write(
        root / "mod_zhongguo_style/tools/gen_361_phase2_central_runtime.py",
        '(7, "credit_project", "zg361_cp_open_portfolio_effect")\n'
        '(8, "metrics_delivery", "zg361_p3_open_portfolio_effect")\n',
    )
    purpose_shards = payload["production_contract"]["effect_boundary"][
        "purpose_shards"
    ]
    for index in range(1, 11):
        relative = (
            "mod_zhongguo_style/common/scripted_effects/"
            f"purpose_{index:02d}_effects.txt"
        )
        _write(root / relative, f"effect_{index:02d} = {{ }}\n")
        purpose_shards[relative] = 1
    fingerprint, file_count = _native_source_fingerprint(
        root / "ck3_autonomous_player/native_bridge"
    )
    payload["source"]["native_source_fingerprint_sha256"] = fingerprint
    payload["source"]["native_source_file_count"] = file_count
    _write(manifest, json.dumps(payload))


def test_candidate_verifier_green_and_never_creates_attempt(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    monkeypatch.setattr(
        "verify_zg361_projects_metrics_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    report = verify_projects_metrics_no_launch_candidate(
        manifest, source_root=root, running_process_names=[]
    )
    assert report["result"] == "READY_TO_LIVE"
    assert report["ck3_started"] is False
    assert not (tmp_path / "absent").exists()


def test_candidate_verifier_rejects_ack_claim_and_consumed_attempt(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    monkeypatch.setattr(
        "verify_zg361_projects_metrics_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["action_ack_is_business_postcondition"] = True
    payload["live_attempt"]["consumed"] = True
    _write(manifest, json.dumps(payload))
    report = verify_projects_metrics_no_launch_candidate(
        manifest, source_root=root, running_process_names=[]
    )
    assert report["result"] == "RED"
    assert set(report["failed_checks"]) == {
        "future_live_attempt_unique_and_absent",
        "no_live_or_ack_claim",
    }


def test_candidate_verifier_rejects_running_process_and_hash_drift(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    monkeypatch.setattr(
        "verify_zg361_projects_metrics_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    _write(tmp_path / "build/xar_ck3_bridge.dll", b"changed")
    report = verify_projects_metrics_no_launch_candidate(
        manifest, source_root=root, running_process_names=["CK3.EXE"]
    )
    assert report["result"] == "RED"
    assert "paired_bridge_hash_matches" in report["failed_checks"]
    assert "ck3_and_injector_not_running" in report["failed_checks"]


def test_v2_candidate_binds_stage_checkpoint_effect_limit_and_launch_plan(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    _upgrade_to_v2(manifest, root, tmp_path)
    monkeypatch.setattr(
        "verify_zg361_projects_metrics_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    report = verify_projects_metrics_no_launch_candidate(
        manifest, source_root=root, running_process_names=[]
    )
    assert report["result"] == "READY_TO_LIVE"
    assert report["checks"]["production_stage7_precedes_stage8"] is True
    assert report["checks"]["checkpoint_state_v2_bound"] is True
    assert report["checks"]["purpose_effect_shards_within_limit"] is True
    assert report["checks"]["exact_ck3_command_frozen_not_executed"] is True


def test_v2_candidate_rejects_reversed_stage_overfull_shard_and_execution(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest, root = _fixture(tmp_path)
    _upgrade_to_v2(manifest, root, tmp_path)
    monkeypatch.setattr(
        "verify_zg361_projects_metrics_no_launch_candidate.EXPECTED_EXE_SHA256",
        _sha(tmp_path / "ck3.exe"),
    )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["production_contract"]["stage_order"].reverse()
    payload["production_contract"]["checkpoint_state_v2"]["allowlist_id"] = (
        "stale-v1"
    )
    first_shard = next(iter(
        payload["production_contract"]["effect_boundary"]["purpose_shards"]
    ))
    _write(
        root / first_shard,
        "".join(f"effect_{index:02d} = {{ }}\n" for index in range(11)),
    )
    payload["production_contract"]["effect_boundary"]["purpose_shards"][
        first_shard
    ] = 11
    payload["production_contract"]["effect_boundary"][
        "max_effects_per_file"
    ] = 11
    payload["commands"]["ck3_launch"]["executed"] = True
    _write(manifest, json.dumps(payload))
    report = verify_projects_metrics_no_launch_candidate(
        manifest, source_root=root, running_process_names=[]
    )
    assert report["result"] == "RED"
    assert {
        "production_stage7_precedes_stage8",
        "checkpoint_state_v2_bound",
        "purpose_effect_shards_within_limit",
        "exact_ck3_command_frozen_not_executed",
    }.issubset(report["failed_checks"])
