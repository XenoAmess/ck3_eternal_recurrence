"""Focused checks for the one-event GEN-034 horizon runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "native_bridge" / "research"))
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_gen034_white_peace_horizon_registered_event.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_gen034_white_peace_horizon_registered_event", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


def test_exact_build_adds_event_selection_gate() -> None:
    capabilities = {
        "action_steps": ["select-event-option-1"],
        "bridge_capabilities": [],
    }
    original = HARNESS.horizon._exact_build_proof
    try:
        HARNESS.horizon._exact_build_proof = lambda *args, **kwargs: {
            "checks": {"base": True},
            "ok": True,
        }
        proof = HARNESS._exact_build_proof(
            capabilities,
            managed_executable_sha256="A" * 64,
            war_id=33_554_473,
        )
    finally:
        HARNESS.horizon._exact_build_proof = original
    assert proof["ok"] is True
    assert proof["checks"]["select_event_option_step"] is True


def test_history_requires_every_declared_command_to_succeed() -> None:
    before = {"native_command_history": [{"command": "old", "ok": True}]}
    commands = [
        "resume-map",
        "pause-map",
        "query-current-event-window-context-v1",
        "select-event-option-1",
        "resume-map",
        "pause-map",
        "query-war-termination-options-33554473",
        "save-checkpoint",
    ]
    rows = [
        *before["native_command_history"],
        *({"command": command, "ok": True} for command in commands),
    ]
    assert HARNESS.horizon._history_checks(
        before,
        {"native_command_history": rows},
        expected_commands=commands,
    )["exact_command_delta"]
    rows[4]["ok"] = False
    assert not HARNESS.horizon._history_checks(
        before,
        {"native_command_history": rows},
        expected_commands=commands,
    )["exact_command_delta"]


def test_source_is_bounded_to_one_event_and_no_war_exit() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"maximum_event_continuations": 1' in source
    assert '"ck3_query_current_event_window_context_v1"' in source
    assert '"ck3_select_event_option"' in source
    assert '"ck3_query_war_termination_options"' in source
    assert '"surrender-war-N"' in source
    assert '"offer-white-peace-N"' in source
    assert '"enforce-demands-N"' in source
    assert '"ck3_surrender_war"' not in source
    assert '"ck3_offer_white_peace"' not in source
    assert '"ck3_enforce_demands"' not in source
