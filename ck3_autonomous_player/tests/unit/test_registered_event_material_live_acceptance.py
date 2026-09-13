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
    / "run_registered_event_material_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_registered_event_material_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


def _context() -> dict[str, object]:
    return {
        "status": "available",
        "date_raw": 53_783_472,
        "current_event_instance_id": 1075,
        "event_definition_key": "trait_specific.8001",
    }


def _state(intervening: str = "query-safe-v1") -> dict[str, object]:
    checkpoint_hash = "A" * 64
    return {
        "last_checkpoint": {
            "history_index": 12,
            "sha256": checkpoint_hash,
            "date_raw": 53_783_472,
        },
        "command_history": [
            {
                "index": 10,
                "command": "query-current-event-window-context-v1",
                "ok": True,
                "result": {
                    "accepted": True,
                    "status": "available",
                    "current_event_window_context": _context(),
                },
            },
            {"index": 11, "command": intervening, "ok": True, "result": {}},
            {
                "index": 12,
                "command": "save-checkpoint",
                "ok": True,
                "result": {
                    "accepted": True,
                    "checkpoint": {
                        "sha256": checkpoint_hash,
                        "date_raw": 53_783_472,
                    },
                },
            },
        ],
    }


def test_source_anchor_allows_only_read_only_rows_before_save(tmp_path: Path) -> None:
    path = tmp_path / "driver-state.json"
    path.write_text(json.dumps(_state()), encoding="utf-8")

    result = HARNESS._source_event_anchor(
        path,
        expected_checkpoint_sha256="A" * 64,
        expected_date_raw=53_783_472,
        expected_event_key="trait_specific.8001",
    )

    assert result["event_instance_id"] == 1075
    assert result["intervening_read_only_commands"] == ["query-safe-v1"]
    assert len(result["anchor_sha256"]) == 64

    path.write_text(json.dumps(_state("resume-map")), encoding="utf-8")
    with pytest.raises(RuntimeError, match="separated.*mutation"):
        HARNESS._source_event_anchor(
            path,
            expected_checkpoint_sha256="A" * 64,
            expected_date_raw=53_783_472,
            expected_event_key="trait_specific.8001",
        )


def test_runner_source_limits_the_live_command_set() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'await client.call_tool("ck3_auto_turn", {})' in source
    assert 'await client.call_tool(\n                "ck3_save_checkpoint"' in source
    assert '"fresh_event_context_queries": 1' in source
    assert '"event_selections": 1' in source
    assert '"time_advanced": False' in source
    assert '"war_actions": 0' in source


def test_nested_mcp_error_preserves_the_concrete_failure() -> None:
    error = ExceptionGroup(
        "task group",
        [RuntimeError("material observation unavailable")],
    )
    assert HARNESS._format_sequence_error(error) == (
        "ExceptionGroup: task group (1 sub-exception) "
        "[RuntimeError: material observation unavailable]"
    )
