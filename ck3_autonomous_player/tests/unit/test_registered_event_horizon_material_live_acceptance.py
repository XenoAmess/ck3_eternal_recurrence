from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_registered_event_horizon_material_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_registered_event_horizon_material_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


def _driver_state() -> dict[str, object]:
    return {
        "format_version": 2,
        "pipe_name": r"\\.\pipe\test",
        "episode_character_id": 27181,
        "episode_run_id": "native-test",
        "last_checkpoint": {
            "status": "saved",
            "sha256": "A" * 64,
            "date_raw": 53_155_680,
            "history_index": 30,
        },
    }


def test_source_checkpoint_anchor_requires_exact_hash_and_date(tmp_path: Path) -> None:
    path = tmp_path / "driver-state.json"
    path.write_text(json.dumps(_driver_state()), encoding="utf-8")

    anchor = HARNESS._source_checkpoint_anchor(
        path,
        expected_checkpoint_sha256="A" * 64,
        expected_date_raw=53_155_680,
    )
    assert anchor["episode_character_id"] == 27181
    assert anchor["checkpoint"]["history_index"] == 30

    with pytest.raises(RuntimeError, match="does not bind"):
        HARNESS._source_checkpoint_anchor(
            path,
            expected_checkpoint_sha256="A" * 64,
            expected_date_raw=53_155_681,
        )


def test_runner_uses_registry_for_preludes_and_material_target() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "recommend_registered_vanilla_event_option_v1(" in source
    assert "plan_registered_event_material_postcondition_v1(" in source
    assert "evaluate_registered_event_material_postcondition_v1(" in source
    assert '"maximum_ck3_launches": 1' in source
    assert '"war_actions": 0' in source
    assert '"maximum_date_raw": args.target_date_raw' in source
    resume = source.index('base._structured(resume, tool_name="ck3_execute_step:resume")')
    immediate_pause = source.index(
        '"ck3_execute_step", {"step": "pause-map"}', resume
    )
    paused_snapshot = source.index('label="paused-horizon"', immediate_pause)
    assert resume < immediate_pause < paused_snapshot


def test_exact_build_gate_requires_timeline_capabilities() -> None:
    capabilities = [
        HARNESS.material.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
        HARNESS.material.SELECT_EVENT_CAPABILITY,
        HARNESS.material.SAVE_CHECKPOINT_CAPABILITY,
        HARNESS.RESUME_CAPABILITY,
        HARNESS.PAUSE_CAPABILITY,
    ]
    payload = {
        "diagnostics": {
            "hello": {
                "expected_ck3_version": HARNESS.base.EXPECTED_GAME_VERSION,
                "game_adapter_id": HARNESS.base.EXPECTED_ADAPTER_ID,
                "game_adapter_status": "ready",
                "ck3_build_match": True,
                "expected_ck3_sha256": HARNESS.base.EXPECTED_EXECUTABLE_SHA256,
                "capabilities": capabilities,
            }
        },
        "bridge_capabilities": capabilities,
        "action_steps": [
            "save-checkpoint",
            "resume-map",
            "pause-map",
        ],
    }
    result = HARNESS._exact_build_proof(
        payload,
        managed_executable_sha256=HARNESS.base.EXPECTED_EXECUTABLE_SHA256,
        war_id=0,
    )
    assert result["ok"] is True

    payload["bridge_capabilities"] = [
        item for item in capabilities if item != HARNESS.RESUME_CAPABILITY
    ]
    result = HARNESS._exact_build_proof(
        payload,
        managed_executable_sha256=HARNESS.base.EXPECTED_EXECUTABLE_SHA256,
        war_id=0,
    )
    assert result["ok"] is False
