"""Saved-scope failure may retain source identity without licensing a choice."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.event_window_context_contract import (
    normalize_current_event_window_context_v1,
)


FIXTURE = (Path(__file__).resolve().parents[1] / "fixtures" / "mandatory_choice_v1"
           / "p09-event53-unavailable-typed-query.json")


def _context():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["typed_result"][
        "current_event_window_context"]


def _normal(value):
    return normalize_current_event_window_context_v1(
        value, expected_event_instance_id=53,
        expected_date_raw=53292912, expected_snapshot_revision=2638)


def test_actual_p09_unavailable_stays_non_actionable():
    actual = _context()
    assert _normal(actual) == actual
    assert actual["options"] is None


def test_twice_read_partial_identity_still_has_no_scopes_or_choices():
    partial = _context()
    partial.update(event_definition_key="stewardship_general.1054",
                   calculated_event_id=21054, runtime_stats_ordinal=3)
    partial["readiness"]["event_definition_identity_ready"] = True
    parsed = _normal(partial)
    assert parsed["status"] == "unavailable"
    assert parsed["event_definition_key"] == "stewardship_general.1054"
    assert parsed["options"] is None
    assert parsed["root_scope"] is None
    assert parsed["saved_scopes"] is None


def test_actual_cpp_serializer_partial_identity_wire_is_non_actionable():
    native = json.loads((FIXTURE.parent / "native-event-window-partial-identity-synthetic.json")
                        .read_text(encoding="utf-8"))
    parsed = normalize_current_event_window_context_v1(
        native, expected_event_instance_id=16_777_257,
        expected_date_raw=741_221, expected_snapshot_revision=17)
    assert parsed == native
    assert parsed["readiness"]["event_definition_identity_ready"] is True
    assert parsed["status"] == "unavailable"
    assert parsed["options"] is None
    assert parsed["root_scope"] is None


@pytest.mark.parametrize("change", [
    lambda value: value.update(unavailable_reason="other_unavailable"),
    lambda value: value["readiness"].update(option_presentation_ready=True),
    lambda value: value.update(options=[]),
    lambda value: value.update(window_match_count=1),
    lambda value: value.update(calculated_event_id=None),
    lambda value: value.update(event_definition_key="\ud800"),
])
def test_partial_identity_rejects_changed_reason_or_actionable_fields(change):
    partial = _context()
    partial.update(event_definition_key="stewardship_general.1054",
                   calculated_event_id=21054, runtime_stats_ordinal=3)
    partial["readiness"]["event_definition_identity_ready"] = True
    changed = copy.deepcopy(partial)
    change(changed)
    with pytest.raises(ValueError):
        _normal(changed)
