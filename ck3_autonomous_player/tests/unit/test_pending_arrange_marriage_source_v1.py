"""Synthetic metadata bindings; no native calls or new reply permission."""
from copy import deepcopy

import pytest

from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.pending_arrange_marriage_source_v1 import (
    KEY, KEY_HASH, SOURCE_SHA256, source_reviewed_arrange_marriage_evidence_v1 as review,
)


def case():
    return ({"build": {"version": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256},
             "definition": {"canonical_key": KEY, "deterministic_key_hash": KEY_HASH},
             "provenance": {"backend_id": CK3_12004.backend_id("pending-character-interaction-context-v1")}},
            {"classification": "marriage_special_reject_only", "domain": "marriage_alliance",
             "source": "common/character_interactions/00_marriage_interactions.txt",
             "source_sha256": "HISTORICAL_11906", "required_send_option_count": 6,
             "known_decline_effects": ["historical_decline"]})


def test_current_source_metadata_keeps_reject_only_and_history():
    context, historical = case()
    before = deepcopy(historical)
    result = review(context, historical)
    assert historical == before and result is not historical
    assert result["classification"] == historical["classification"]
    assert result["required_send_option_count"] == 6
    assert result["source_sha256"] == SOURCE_SHA256
    knowledge = result["source_knowledge"]
    assert knowledge["status"] == "offline-source-reviewed"
    assert knowledge["historical_source_sha256"] == "HISTORICAL_11906"
    assert knowledge["accept_outcome_qualified"] is False
    assert knowledge["loaded_definition_bytes_verified"] is False
    assert knowledge["material_effects_verified"] is False
    assert "puppet_or_actor:if_grand_wedding_promise_pending:remove_variable" in result["known_decline_effects"]


@pytest.mark.parametrize("field", ["version", "exe", "key", "hash", "backend"])
def test_other_build_or_identity_keeps_unmodified_historical_evidence(field):
    context, historical = case()
    if field == "version":
        context["build"]["version"] = "1.19.0.6"
    elif field == "exe":
        context["build"]["exe_sha256"] = "0" * 64
    elif field == "key":
        context["definition"]["canonical_key"] = "unknown_interaction"
    elif field == "hash":
        context["definition"]["deterministic_key_hash"] += 1
    else:
        context["provenance"]["backend_id"] = "unknown"
    assert review(context, historical) is historical


def test_metadata_cannot_register_an_unclassified_definition():
    context, _ = case()
    assert review(context, None) is None


def test_public_marriage_block_retains_diagnosis_and_continues_ordinary_core():
    from test_gameplay_bridge import _arrange_marriage_context_result, _plan_for_pending_context
    result = _arrange_marriage_context_result(selected_option_index=1)
    before = deepcopy(result)
    plan = _plan_for_pending_context(result, action_steps=(
        "accept-pending-character-interaction", "reject-pending-character-interaction", "save-checkpoint"))
    assert plan["selected_step"] == "save-checkpoint"
    diagnosis = plan["deferred_pending_interaction"]
    assert diagnosis["selected_step"] is None
    assert "marriage_zero_option_vector_mismatch" in diagnosis["decision"]["blocked_reasons"]
    assert plan["notification_continuation"]["interaction_submission"] is False
    assert plan["notification_continuation"]["observed_notification_cleared"] is False
    assert result == before


def test_public_current_build_uses_current_source_and_still_rejects():
    from test_gameplay_bridge import _arrange_marriage_context_result, _plan_for_pending_context
    result = _arrange_marriage_context_result()
    context = result["pending_character_interaction_context"]
    current, _ = case()
    context.update(current)
    plan = _plan_for_pending_context(result, action_steps=(
        "accept-pending-character-interaction", "reject-pending-character-interaction"))
    assert plan["selected_step"] == "reject-pending-character-interaction"
    classification = plan["decision"]["definition_classification"]
    assert classification["policy"] == "ck3-1.20.0.4-explicit-marriage-special-reject-only-v1"
    assert classification["evidence"]["source_sha256"] == SOURCE_SHA256


def test_marriage_ordinary_projection_cannot_offer_reply_or_query():
    from xar_autoplayer.pending_arrange_marriage_source_v1 import continue_without_blocked_marriage_reply_v1
    blocked = {"phase": "pending_character_interaction_degraded_blocked", "selected_step": None,
        "decision": {"classification": "known_marriage_special", "pending_interaction_id": -123,
                     "definition_classification": {"definition_key": KEY}}}
    snapshot = {"pending_character_interaction": {"instance_id": -123, "auto_accept_notification": False}}
    def ordinary(projection, steps):
        assert projection["pending_character_interaction"] is None
        assert steps == ("life-advance",)
        return {"phase": "ordinary", "selected_step": "accept-pending-character-interaction"}
    result = continue_without_blocked_marriage_reply_v1(blocked, snapshot=snapshot,
        action_steps=("life-advance", "accept-pending-character-interaction",
                      "reject-pending-character-interaction", "block-pending-character-interaction",
                      "acknowledge-pending-character-interaction", "query-pending-character-interaction-context-v1"),
        choose_ordinary=ordinary)
    assert result is blocked


@pytest.mark.parametrize("event_key", ["active_event", "current_event", "top_exclusive_modal_choice_hint"])
def test_marriage_projection_never_hides_a_real_event(event_key):
    from xar_autoplayer.pending_arrange_marriage_source_v1 import continue_without_blocked_marriage_reply_v1
    blocked = {"phase": "pending_character_interaction_degraded_blocked", "selected_step": None,
        "decision": {"classification": "known_marriage_special", "pending_interaction_id": -123,
                     "definition_classification": {"definition_key": KEY}}}
    snapshot = {"pending_character_interaction": {"instance_id": -123, "auto_accept_notification": False},
                event_key: {"instance_id": 7, "status": "present"}}
    def forbidden(*args):
        raise AssertionError("ordinary projection must not hide an event")
    assert continue_without_blocked_marriage_reply_v1(blocked, snapshot=snapshot,
        action_steps=("life-advance",), choose_ordinary=forbidden) is blocked
