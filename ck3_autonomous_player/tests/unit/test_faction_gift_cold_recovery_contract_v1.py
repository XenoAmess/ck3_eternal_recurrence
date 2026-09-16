from __future__ import annotations

from pathlib import Path

from xar_autoplayer.faction_gift_cold_recovery_contract_v1 import (
    evaluate_faction_gift_cold_recovery_v1,
)
from xar_autoplayer.faction_gift_pending_v1 import (
    begin_faction_gift_submission_v1,
    read_faction_gift_ledger_v1,
    resolve_faction_gift_after_cold_native_query_v1,
)


def pending(state: Path) -> dict[str, object]:
    native_observation = {
        "queried_source_faction_id": 771,
        "recipient_character_id": 33011,
        "snapshot_revision": 412, "native_snapshot_revision": 414,
        "observed_date_raw": 53_789_952,
        "player_character_id": 32904, "player_gold_raw": 25_000_000,
        "recipient_opinion_of_player": -40,
        "gift_opinion_present": False,
        "source_faction_power_raw": 65_000_000,
        "source_faction_discontent_raw": 45_000_000,
        "source_faction_targeting_player": True,
        "source_faction_member_character_ids": [33011],
        "gift_preview": {"gold_cost_raw": 7_500_000, "opinion_delta": 25},
    }
    return begin_faction_gift_submission_v1(
        state, request_id="gift-real-1", episode_run_id="native-32904-a",
        source_round_id="R742", source_bridge_pid=12345,
        source_bridge_creation_date="2026-09-16T12:00:00Z",
        observation=native_observation, minimum_gold_reserve_raw=10_000_000,
        checkpoint_sha256_before_submit="a" * 64,
    )["pending"]


def recovery() -> dict[str, object]:
    return {
        "schema_version": 1, "status": "independent_read_complete",
        "private_build": True, "advertised": False,
        "new_process_confirmed": True,
        "new_round_id": "R744", "new_bridge_pid": 23456,
        "new_bridge_creation_date": "2026-09-16T12:30:00Z",
        "episode_run_id": "native-32904-a",
        "paused": True, "map_ready": True,
        "independent_faction_storage_lookup_complete": True,
        "independent_recipient_lookup_complete": True,
        "selected_from_current_targeting_vector": False,
        "save_is_pre_action_checkpoint": False,
        "selected_save_sha256": "b" * 64,
        "post_observation": {
            "snapshot_revision": 1, "native_snapshot_revision": 2,
            "observed_date_raw": 53_789_952,
            "player_character_id": 32904,
            "player_resources_query_complete": True,
            "player_gold_raw": 17_500_000,
            "recipient_identity_resolved": True,
            "recipient_character_id": 33011,
        "recipient_alive": True,
        "recipient_opinion_query_complete": True,
        "recipient_opinion_of_player": -15,
            "gift_opinion_present": True,
            "gift_opinion_modifier_value": 25,
            "source_faction_requery_complete": True,
            "queried_source_faction_id": 771,
            "source_faction_present": False,
            "source_faction_metrics_available": False,
        },
    }


def test_new_process_revision_reset_and_absent_targeting_vector_are_not_shortcuts(tmp_path: Path) -> None:
    before = pending(tmp_path / "state")
    post = recovery()
    classified = evaluate_faction_gift_cold_recovery_v1(before, post)
    assert classified["status"] == "applied"
    assert classified["threat_resolved"] is True
    assert classified["action_retry_allowed"] is False
    post["independent_faction_storage_lookup_complete"] = False
    assert evaluate_faction_gift_cold_recovery_v1(before, post)["status"] == "unresolved"
    post["independent_faction_storage_lookup_complete"] = True
    post["new_round_id"] = "R742"
    assert evaluate_faction_gift_cold_recovery_v1(before, post)["status"] == "unresolved"


def test_unchanged_requires_exact_pre_action_save_and_same_entity_facts(tmp_path: Path) -> None:
    before = pending(tmp_path / "state")
    post = recovery()
    facts = post["post_observation"]
    facts.update(
        player_gold_raw=25_000_000, gift_opinion_present=False,
        gift_opinion_modifier_value=None,
        recipient_opinion_of_player=-40,
        source_faction_present=True,
        source_faction_targeting_player=True,
        source_faction_metrics_available=True,
        source_faction_power_raw=65_000_000,
        source_faction_discontent_raw=45_000_000,
        source_faction_member_character_ids=[33011],
    )
    post["save_is_pre_action_checkpoint"] = True
    post["selected_save_sha256"] = "a" * 64
    assert evaluate_faction_gift_cold_recovery_v1(before, post)["status"] == "unchanged"
    post["selected_save_sha256"] = "b" * 64
    assert evaluate_faction_gift_cold_recovery_v1(before, post)["status"] == "unresolved"
    post["selected_save_sha256"] = "a" * 64
    facts["source_faction_member_character_ids"] = None
    assert evaluate_faction_gift_cold_recovery_v1(before, post)["status"] == "unresolved"


def test_cold_unknown_preserves_pending_and_material_applied_retires_id(tmp_path: Path) -> None:
    state = tmp_path / "state"
    pending(state)
    post = recovery()
    post["independent_faction_storage_lookup_complete"] = False
    result = resolve_faction_gift_after_cold_native_query_v1(
        state, request_id="gift-real-1", recovery=post
    )
    assert result["status"] == "unresolved"
    assert read_faction_gift_ledger_v1(state)["pending"]["request_id"] == "gift-real-1"
    post["independent_faction_storage_lookup_complete"] = True
    result = resolve_faction_gift_after_cold_native_query_v1(
        state, request_id="gift-real-1", recovery=post
    )
    assert result["status"] == "applied"
    assert result["ledger"]["pending"] is None
    assert result["ledger"]["resolved_request_outcomes"] == {"gift-real-1": "applied"}
