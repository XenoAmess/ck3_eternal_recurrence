"""Closed-input replay and synthetic binding regressions; no live qualification."""

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    query_player_lifestyle_stock_focus_combined_private_v1,
)
from xar_autoplayer.lifestyle_education_focus_scope_v1 import qualify_current_education_focus
from xar_autoplayer.lifestyle_formal_consumer import consume_lifestyle_private_query


FIXTURE = Path(__file__).with_name("fixtures") / "lifestyle_after_succession_4106_4107_v1.json"


def _inputs():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _snapshot(frame):
    return {**{k: v for k, v in frame.items() if k not in {"player_character_id", "actor_alive"}},
            "played_character": {"character_id": frame["player_character_id"], "alive": frame["actor_alive"]}}


def _consume(query, frame):
    return consume_lifestyle_private_query(
        {"selected_step": "life-advance", "phase": "native_war_wait", "reason": "ordinary legal continuation"},
        scope={"status": "admitted", "snapshot_revision": frame["native_revision"],
               "player_character_id": frame["player_character_id"], "at_peace": False},
        query=query,
    )


def _combined(inputs, *, snapshots=None, education=None):
    frame = inputs["frame"]
    driver = SimpleNamespace(
        take_internal_semantic_snapshot=Mock(side_effect=snapshots) if snapshots else Mock(return_value=_snapshot(frame)),
        query_child_education_focus_private_v1=Mock(return_value=education or inputs["education_query"]),
    )
    with patch(
        "xar_autoplayer.bridge.player_lifestyle_private_transport_v1.query_player_lifestyle_private_v1",
        return_value=inputs["state_query"],
    ):
        query = query_player_lifestyle_stock_focus_combined_private_v1(driver, expected_revision=frame["revision"])
    return query, driver


def test_closed_4106_4107_focus_fact_qualifies_without_target_definition_or_age_claim():
    inputs = _inputs()
    education, frame = inputs["education_query"], inputs["frame"]
    assert education["status"] == "unavailable"
    assert education["unavailable_reason"] == "education_definition_missing"
    assert education["native_legal"] is None
    result = qualify_current_education_focus(education, frame, expected_revision=2)
    assert result["current_focus_key"] == "education_intrigue"
    assert result["age_observed"] is False
    assert result["lifestyle_action_legal"] is None


@pytest.mark.parametrize("field,value", [
    ("native_revision", 3135), ("date_raw", 53188008),
    ("episode_run_id", "native-40526-old"), ("controller_full_id", 29829),
    ("paused", False),
])
def test_synthetic_stale_or_foreign_native_focus_source_is_not_applicable_proof(field, value):
    inputs = _inputs()
    inputs["education_query"]["source_frame"][field] = value
    assert qualify_current_education_focus(inputs["education_query"], inputs["frame"], expected_revision=2) is None


@pytest.mark.parametrize("change", ["unknown_key", "missing_focus", "other_build", "old_public"])
def test_synthetic_unknown_focus_or_missing_identity_remains_unavailable(change):
    inputs = _inputs()
    education = inputs["education_query"]
    if change == "unknown_key":
        education["current_focus"]["key"] = "stewardship_wealth_focus"
    elif change == "missing_focus":
        education["current_focus"] = {"available": False, "unavailable_reason": "unreadable", "presence": "", "key": None}
    elif change == "other_build":
        education["source_context"]["exe_sha256"] = "0" * 64
    else:
        education["source_public_revision"] = 2716
    assert qualify_current_education_focus(education, inputs["frame"], expected_revision=2) is None


def test_closed_inputs_follow_real_combined_consumer_seam_with_one_read_and_no_life_write():
    inputs = _inputs()
    query, driver = _combined(inputs)
    assert query["status"] == "education_focus_not_applicable"
    driver.query_child_education_focus_private_v1.assert_called_once_with(
        child_full_id=40526, target_key="education_stewardship", expected_revision=2)
    plan = _consume(query, inputs["frame"])
    assert plan["selected_step"] == "life-advance"
    assert plan["phase"] == "native_war_wait"
    assert plan["reason"] == "ordinary legal continuation"
    assert plan["lifestyle_native_error"] == inputs["state_query"]["native_error"]
    assert plan["lifestyle_query"]["education_focus_query"] == inputs["education_query"]
    assert "lifestyle_action" not in plan
    # The next ordinary plan is not exempted by a cached age or actor override.
    drift = deepcopy(query)
    drift["education_focus_query"]["current_focus"]["key"] = "stewardship_wealth_focus"
    assert _consume(drift, inputs["frame"])["selected_step"] is None


@pytest.mark.parametrize("error", ["native_sample_drift", None, {"untyped": "error"}])
def test_other_state_failures_do_not_probe_or_skip_life(error):
    inputs = _inputs()
    inputs["state_query"]["native_error"] = error
    query, driver = _combined(inputs)
    assert query["status"] == "current_state_unavailable"
    driver.query_child_education_focus_private_v1.assert_not_called()
    assert _consume(query, inputs["frame"])["selected_step"] is None


def test_native_frame_change_and_source_review_drift_cannot_continue():
    inputs = _inputs()
    before = _snapshot(inputs["frame"])
    after = {**before, "native_revision": 3137, "snapshot_id": "native:3137"}
    changed, driver = _combined(inputs, snapshots=[before, after])
    assert driver.query_child_education_focus_private_v1.call_count == 1
    assert _consume(changed, inputs["frame"])["selected_step"] is None
    query, _ = _combined(inputs)
    query["education_focus_scope"]["source_review"]["definition_sha256"] = "0" * 64
    assert _consume(query, inputs["frame"])["selected_step"] is None
    query, _ = _combined(inputs)
    foreign = {**inputs["frame"], "player_character_id": 29829}
    assert _consume(query, foreign)["selected_step"] is None
