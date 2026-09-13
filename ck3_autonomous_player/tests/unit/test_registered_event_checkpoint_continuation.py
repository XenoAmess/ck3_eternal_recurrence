from __future__ import annotations

import importlib.util
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
    / "run_registered_event_checkpoint_continuation.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_registered_event_checkpoint_continuation", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


PLAYER = 29_829


def _scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "type_key": "character",
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def _snapshot() -> dict[str, object]:
    return {
        "active_event": {
            "instance_id": 7,
            "options": [{"option_number": 1}],
        }
    }


def _context(*, neighbor_id: int = 33_422) -> dict[str, object]:
    rows = (
        ("councillor", 32_716),
        ("councillor_liege", PLAYER),
        ("chancellor", 32_716),
        ("active_councillor", 32_716),
        ("neighbor", neighbor_id),
    )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": "chancellor_task.1104",
        "root_scope": _scope(PLAYER),
        "saved_scopes": [
            {"name": name, "name_identifier": index + 1, "scope": _scope(value)}
            for index, (name, value) in enumerate(rows)
        ],
        "options": [
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
        ],
    }


def test_runner_accepts_only_the_registered_exact_projection() -> None:
    result = HARNESS._recommend_exact_registered_option(
        snapshot=_snapshot(),
        event_context=_context(),
        expected_event_key="chancellor_task.1104",
        expected_character_id=PLAYER,
    )

    assert result["status"] == "recommended"
    assert result["selected_option_number"] == 1
    assert result["selected_native_option_index"] == 0


def test_runner_rejects_event_identity_or_relationship_drift() -> None:
    with pytest.raises(RuntimeError, match="requested event key"):
        HARNESS._recommend_exact_registered_option(
            snapshot=_snapshot(),
            event_context=_context(),
            expected_event_key="different.1",
            expected_character_id=PLAYER,
        )

    with pytest.raises(RuntimeError, match="did not authorize"):
        HARNESS._recommend_exact_registered_option(
            snapshot=_snapshot(),
            event_context=_context(neighbor_id=32_716),
            expected_event_key="chancellor_task.1104",
            expected_character_id=PLAYER,
        )


def test_runner_source_forbids_time_and_war_exit_commands() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"ck3_select_event_option"' in source
    assert '"ck3_query_current_event_window_context_v1"' in source
    assert '"step": "resume-map"' not in source
    assert '"step": "life-advance"' not in source
    assert '"step": "offer-white-peace-' not in source
    assert '"step": "surrender-war-' not in source


def test_runner_preserves_nested_mcp_failure_reason() -> None:
    error = ExceptionGroup(
        "unhandled errors in a TaskGroup",
        [RuntimeError("application-main event-window query timed out")],
    )

    assert HARNESS._format_sequence_error(error) == (
        "ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception) "
        "[RuntimeError: application-main event-window query timed out]"
    )
