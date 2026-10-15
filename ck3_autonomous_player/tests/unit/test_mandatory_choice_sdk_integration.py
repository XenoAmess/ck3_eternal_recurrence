"""Consume actual offline C++ wire fixtures through SDK normalization and policy."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.native_driver import (
    NativeProtocolState, _life_advance_new_modal_hint, _life_advance_progressed,
)
from xar_autoplayer.bridge.mandatory_choice_transport_v1 import frame_from_snapshot
from xar_autoplayer.mandatory_choice_planning_v1 import (
    QUERY_CAPABILITY, QUERY_STEP, SELECT_STEP, plan_native_mandatory_choice_v1,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mandatory_choice_v1"
HINT = {"status": "present", "owner_verified": True,
        "source": "application_main_pump_observed_modal_receiver",
        "opaque_root_id": "0xabcd", "max_observation_age_ms": 2000}


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _published_snapshot(wire: dict, *, event: dict | None = None) -> dict:
    binding = wire["result"]["mandatory_choice"]["frame_binding"]
    state = NativeProtocolState(r"\\.\pipe\offline-mandatory-choice-fixture")
    state.ingest({"protocol_version": 1, "type": "hello",
                  "pid": binding["game_pid"],
                  "connection_generation": binding["connection_generation"],
                  "capabilities": ["game.state.snapshot", QUERY_CAPABILITY]})
    state._public_revision = binding["revision"] - 1
    state.ingest({"protocol_version": 1, "type": "state_snapshot",
                  "snapshot_id": binding["snapshot_id"],
                  "revision": binding["native_revision"],
                  "state": {"date_raw": binding["date_raw"], "history": [],
                            "active_wars": [], "player_armies": [],
                            "played_character": {"character_id": binding["actor_character_id"],
                                                 "alive": True},
                            "active_event": event,
                            "top_exclusive_modal_choice_hint": copy.deepcopy(HINT)}})
    snapshot = {**state.semantic_snapshot(), "episode_run_id": binding["episode_run_id"]}
    assert frame_from_snapshot(snapshot) == binding
    return snapshot


def _plan(wire: dict, snapshot: dict) -> dict | None:
    return plan_native_mandatory_choice_v1(
        [{"command": QUERY_STEP, "ok": wire["ok"], "result": wire["result"]}],
        snapshot=snapshot, action_steps={QUERY_STEP, SELECT_STEP},
        bridge_capabilities={QUERY_CAPABILITY})


def test_cpp_query_wire_selects_real_token_but_not_business_credit():
    wire = _fixture("native-query.json")
    planned = _plan(wire, _published_snapshot(wire))
    assert planned["selected_step"] == SELECT_STEP
    assert planned["unknown_mandatory_choice_v1"]["selection"]["action_token"] == (
        wire["result"]["mandatory_choice"]["choices"][0]["action_token"])
    assert planned["unknown_mandatory_choice_v1"]["material_effects_verified"] is False
    select = _fixture("native-select.json")["result"]
    assert select["mandatory_choice_postcondition"]["old_instance"] == (
        wire["result"]["mandatory_choice"]["window_instance_id"])


def test_cpp_event_overlay_requires_exact_independent_native_root_relation():
    overlay = _fixture("native-query-event-overlay.json")
    same = _fixture("native-query-event-same-root.json")
    snapshot = _published_snapshot(overlay, event={"instance_id": 42})
    assert _plan(overlay, snapshot)["selected_step"] == SELECT_STEP
    assert _plan(same, snapshot) is None
    for key, wrong in (("typed_window_instance_id", 43),
                       ("owner_verified", False),
                       ("source", "unqualified"),
                       ("top_opaque_root_id", "0xdead")):
        changed = copy.deepcopy(overlay)
        changed["result"]["mandatory_choice"]["typed_window_relation"][key] = wrong
        assert _plan(changed, snapshot) is None


def test_new_modal_interrupt_does_not_cross_pid_or_typed_event():
    wire = _fixture("native-query.json")
    current = _published_snapshot(wire)
    starting = copy.deepcopy(current)
    starting["revision"] -= 1
    starting["top_exclusive_modal_choice_hint"]["status"] = "absent"
    starting["top_exclusive_modal_choice_hint"]["opaque_root_id"] = None
    assert _life_advance_new_modal_hint(current, starting) == HINT
    assert _life_advance_progressed(current, starting) is True
    wrong = copy.deepcopy(current)
    wrong["diagnostics"]["bridge_pid"] += 1
    assert _life_advance_new_modal_hint(wrong, starting) is None
    typed = copy.deepcopy(current)
    typed["active_event"] = {"instance_id": 42}
    assert _life_advance_new_modal_hint(typed, starting) is None
