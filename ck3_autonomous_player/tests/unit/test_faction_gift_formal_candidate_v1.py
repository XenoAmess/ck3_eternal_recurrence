from __future__ import annotations

from pathlib import Path

from xar_autoplayer.bridge.faction_gift_plan_augmentation_v1 import (
    attach_faction_gift_private_candidate_v1,
)
from xar_autoplayer.faction_gift_formal_candidate_v1 import (
    choose_private_faction_gift_candidate_v1,
    latest_same_frame_faction_root_v1,
)
from xar_autoplayer.faction_gift_pending_v1 import begin_faction_gift_submission_v1


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:412", "revision": 412,
        "native_revision": 412, "date_raw": 53_789_952,
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 32904, "alive": True},
        "active_event": None, "pending_character_interaction": None,
        "one_life_terminal_reason": None,
    }


def root(count: int) -> dict[str, object]:
    return {
        "status": "available", "snapshot_revision": 412,
        "date_raw": 53_789_952, "player_character_id": 32904,
        "player_character_alive": True,
        "government": {"key": "feudal_government"},
        "player_targeting_faction_count": count,
        "direct_landed_vassal_character_ids": [33011, 33012],
    }


def history(count: int) -> list[dict[str, object]]:
    return [{"command": "query-campaign-root-context-v1", "ok": True,
             "result": {"status": "available", "campaign_root_context": root(count)}}]


def observation() -> dict[str, object]:
    return {
        "available": True, "paused": True,
        "snapshot_revision": 412, "native_snapshot_revision": 414,
        "observed_date_raw": 53_789_952,
        "player_resources_query_complete": True,
        "player_character_id": 32904, "player_gold_raw": 25_000_000,
        "player_gold_scale": 100_000,
        "source_faction_requery_complete": True,
        "queried_source_faction_id": 771, "source_faction_present": True,
        "source_faction_target_character_id": 32904,
        "source_faction_targeting_player": True,
        "source_faction_at_war": False,
        "source_faction_leader_character_id": 33011,
        "source_faction_member_character_ids": [33011],
        "source_faction_metrics_available": True,
        "source_faction_power_raw": 65_000_000,
        "source_faction_discontent_raw": 45_000_000,
        "source_faction_targeting_player": True,
        "source_faction_metric_scale": 100_000,
        "recipient_identity_resolved": True,
        "recipient_character_id": 33011,
        "recipient_alive": True, "recipient_is_ai": True,
        "recipient_is_direct_landed_vassal": True,
        "recipient_opinion_query_complete": True,
        "recipient_opinion_of_player": -40,
        "gift_opinion_present": False,
        "gift_preview": {
            "available": True, "definition_key": "gift_interaction",
            "definition_stable_hash": 1_234_567_890,
            "interaction_legal": True, "auto_accept": True,
            "gold_cost_raw": 7_500_000, "gold_scale": 100_000,
            "opinion_delta": 25,
        },
    }


def private_result() -> dict[str, object]:
    return {
        "step": "private-query-faction-gift-member-v1",
        "accepted": True, "private_build": True, "advertised": False,
        "status": "preview_ready",
        "native": {"completion": "preview_ready", "failure_flags": 0,
                   "source_faction_id": 771, "recipient_character_id": 33011,
                   "observation": observation()},
    }


def test_public_zero_is_known_empty_only_for_current_frame() -> None:
    assert latest_same_frame_faction_root_v1(snapshot(), history(0))["status"] == "known_empty"
    stale = snapshot()
    stale["native_revision"] = 413
    assert latest_same_frame_faction_root_v1(stale, history(0))["status"] == "same_frame_root_not_observed"


def test_private_preview_selects_one_budgeted_member_but_not_action() -> None:
    candidate = choose_private_faction_gift_candidate_v1(
        snapshot(), root(1), private_result(), minimum_gold_reserve_raw=10_000_000
    )
    assert candidate["status"] == "selected"
    assert candidate["choice"]["recipient_character_id"] == 33011
    assert candidate["choice"]["gold_cost_raw"] == 7_500_000
    assert candidate["gift_submission_enabled"] is False
    assert candidate["public_capability_advertised"] is False
    unknown = private_result()
    unknown["native"]["observation"]["source_faction_discontent_raw"] = None
    assert choose_private_faction_gift_candidate_v1(
        snapshot(), root(1), unknown, minimum_gold_reserve_raw=0
    )["status"] == "unavailable"
    absent_vector = private_result()
    absent_vector["status"] = "known_empty"
    assert choose_private_faction_gift_candidate_v1(
        snapshot(), root(1), absent_vector, minimum_gold_reserve_raw=0
    )["status"] == "unavailable"


class Driver:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.query_calls = 0

    def query_faction_gift_private_candidate_v1(self, **kwargs: object) -> dict[str, object]:
        self.query_calls += 1
        return {"status": "selected", "gift_submission_enabled": False,
                "public_capability_advertised": False}


def test_formal_plan_reads_only_on_peace_advance_and_pending_blocks_requery(tmp_path: Path) -> None:
    driver = Driver(tmp_path / "state")
    zero = {"plan": {"selected_step": "life-advance"},
            "_faction_gift_root_view_v1": {"status": "known_empty", "root": root(0)}}
    selected = attach_faction_gift_private_candidate_v1(
        zero, snapshot(), zero["_faction_gift_root_view_v1"],
        state_dir=driver.state_dir, query=driver.query_faction_gift_private_candidate_v1
    )
    assert selected["plan"]["faction_gift_private_candidate_v1"]["status"] == "known_empty"
    assert driver.query_calls == 0
    pending_plan = {"plan": {"selected_step": "life-advance"},
                    "_faction_gift_root_view_v1": {"status": "targeting_present", "root": root(1)}}
    selected = attach_faction_gift_private_candidate_v1(
        pending_plan, snapshot(), pending_plan["_faction_gift_root_view_v1"],
        state_dir=driver.state_dir, query=driver.query_faction_gift_private_candidate_v1
    )
    assert selected["plan"]["faction_gift_private_candidate_v1"]["status"] == "selected"
    assert driver.query_calls == 1
    begin_faction_gift_submission_v1(
        driver.state_dir, request_id="gift-real-1", episode_run_id="native-32904-a",
        source_round_id="R742", source_bridge_pid=12345,
        source_bridge_creation_date="2026-09-16T12:00:00Z",
        observation=observation(), minimum_gold_reserve_raw=10_000_000,
        checkpoint_sha256_before_submit="a" * 64,
    )
    unresolved = {"plan": {"selected_step": "life-advance"},
                  "_faction_gift_root_view_v1": {"status": "targeting_present", "root": root(1)}}
    selected = attach_faction_gift_private_candidate_v1(
        unresolved, snapshot(), unresolved["_faction_gift_root_view_v1"],
        state_dir=driver.state_dir, query=driver.query_faction_gift_private_candidate_v1
    )
    assert selected["plan"]["faction_gift_private_candidate_v1"]["status"] == "pending_recovery_required"
    assert driver.query_calls == 1
    forced = {"plan": {"selected_step": "event-option-1"},
              "_faction_gift_root_view_v1": {"status": "targeting_present", "root": root(1)}}
    assert attach_faction_gift_private_candidate_v1(
        forced, snapshot(), forced["_faction_gift_root_view_v1"],
        state_dir=driver.state_dir, query=driver.query_faction_gift_private_candidate_v1
    )["plan"]["selected_step"] == "event-option-1"
    assert driver.query_calls == 1
