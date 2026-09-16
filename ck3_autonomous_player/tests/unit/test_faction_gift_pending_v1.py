from __future__ import annotations

from pathlib import Path

import pytest

from xar_autoplayer.faction_gift_pending_v1 import (
    begin_faction_gift_submission_v1,
    complete_faction_gift_after_independent_receipt_v1,
    faction_gift_ledger_path,
    mark_faction_gift_ack_pending_v1,
    mark_faction_gift_restore_requery_v1,
    read_faction_gift_ledger_v1,
)


def observation() -> dict[str, object]:
    return {
        "queried_source_faction_id": 771,
        "recipient_character_id": 33011,
        "snapshot_revision": 412,
        "native_snapshot_revision": 414,
        "observed_date_raw": 53_789_952,
        "player_character_id": 32904,
        "player_gold_raw": 25_000_000,
        "recipient_opinion_of_player": -40,
        "gift_opinion_present": False,
        "source_faction_power_raw": 65_000_000,
        "source_faction_discontent_raw": 45_000_000,
        "source_faction_member_character_ids": [33011],
        "source_faction_targeting_player": True,
        "gift_preview": {"gold_cost_raw": 7_500_000, "opinion_delta": 25},
    }


def begin(state: Path, *, request_id: str = "gift-real-1") -> dict[str, object]:
    return begin_faction_gift_submission_v1(
        state, request_id=request_id, episode_run_id="native-32904-a",
        source_round_id="R742", source_bridge_pid=12345,
        source_bridge_creation_date="2026-09-16T12:00:00Z",
        observation=observation(), minimum_gold_reserve_raw=10_000_000,
        checkpoint_sha256_before_submit="a" * 64,
    )


def receipt() -> dict[str, object]:
    return {
        "schema_version": 1, "request_id": "gift-real-1", "status": "mitigated",
        "postcondition_verified": True, "mitigation_applied": True,
        "source_faction_id": 771, "recipient_character_id": 33011,
        "player_character_id": 32904,
        "post_snapshot_revision": 413, "post_native_snapshot_revision": 415,
        "post_observed_date_raw": 53_789_952,
        "post_player_gold_raw": 17_500_000,
        "post_gift_opinion_present": True,
        "post_gift_opinion_modifier_value": 25,
        "source_faction_present": True,
        "recipient_still_in_source_faction": True,
    }


def test_pending_identity_survives_reload_and_blocks_second_submit(tmp_path: Path) -> None:
    state = tmp_path / "state"
    ledger = begin(state)
    assert ledger["pending"]["status"] == "submission_started_unconfirmed"
    assert faction_gift_ledger_path(state).is_file()
    assert read_faction_gift_ledger_v1(state)["pending"]["request_id"] == "gift-real-1"
    with pytest.raises(ValueError, match="already unresolved"):
        begin(state, request_id="gift-real-2")
    with pytest.raises(ValueError, match="pending submission"):
        mark_faction_gift_ack_pending_v1(
            state, request_id="gift-real-1", ack={"request_id": "gift-real-1", "status": "applied"}
        )
    ack = {"request_id": "gift-real-1", "status": "submitted_verification_pending",
           "verification_pending": True, "source_faction_id": 771,
           "recipient_character_id": 33011}
    assert mark_faction_gift_ack_pending_v1(
        state, request_id="gift-real-1", ack=ack
    )["pending"]["status"] == "submitted_verification_pending"
    assert mark_faction_gift_restore_requery_v1(
        state, request_id="gift-real-1"
    )["pending"]["status"] == "restore_requery_required"
    assert read_faction_gift_ledger_v1(state)["pending"] is not None


def test_independent_receipt_must_match_material_post_state(tmp_path: Path) -> None:
    state = tmp_path / "state"
    begin(state)
    wrong = receipt()
    wrong["post_player_gold_raw"] = 25_000_000
    with pytest.raises(ValueError, match="independent post-state"):
        complete_faction_gift_after_independent_receipt_v1(
            state, request_id="gift-real-1", receipt=wrong
        )
    assert read_faction_gift_ledger_v1(state)["pending"] is not None
    complete = complete_faction_gift_after_independent_receipt_v1(
        state, request_id="gift-real-1", receipt=receipt()
    )
    assert complete["pending"] is None
    assert complete["resolved_request_outcomes"] == {"gift-real-1": "applied"}
    with pytest.raises(ValueError, match="already resolved"):
        begin(state)


def test_invalid_pre_submit_input_does_not_replace_ledger(tmp_path: Path) -> None:
    state = tmp_path / "state"
    bad = observation()
    bad["pre_gift_opinion_present"] = None
    bad["gift_opinion_present"] = None
    with pytest.raises(ValueError, match="incomplete"):
        begin_faction_gift_submission_v1(
            state, request_id="gift-unknown", episode_run_id="native-32904-a",
            source_round_id="R742", source_bridge_pid=12345,
            source_bridge_creation_date="2026-09-16T12:00:00Z",
            observation=bad, minimum_gold_reserve_raw=0,
            checkpoint_sha256_before_submit="a" * 64,
        )
    assert not faction_gift_ledger_path(state).exists()


def test_budget_reserve_is_checked_before_durable_submit_identity(tmp_path: Path) -> None:
    state = tmp_path / "state"
    over_budget = observation()
    over_budget["gift_preview"]["gold_cost_raw"] = 20_000_000
    with pytest.raises(ValueError, match="incomplete"):
        begin_faction_gift_submission_v1(
            state, request_id="gift-over-budget", episode_run_id="native-32904-a",
            source_round_id="R742", source_bridge_pid=12345,
            source_bridge_creation_date="2026-09-16T12:00:00Z",
            observation=over_budget, minimum_gold_reserve_raw=10_000_000,
            checkpoint_sha256_before_submit="a" * 64,
        )
    assert not faction_gift_ledger_path(state).exists()
