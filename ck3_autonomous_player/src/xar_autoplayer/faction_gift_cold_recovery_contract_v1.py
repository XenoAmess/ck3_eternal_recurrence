"""Typed material classifier for a faction gift after a real CK3 cold start.

The native recovery query is still missing. The caller must supply an exact
independent faction-storage/recipient/resource read from the new process;
the current targeting vector and the previous process ACK are never evidence
of application or dissolution. Revisions may reset across process starts.
"""

from __future__ import annotations

from typing import Mapping


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def evaluate_faction_gift_cold_recovery_v1(
    pending: Mapping[str, object], recovery: Mapping[str, object],
) -> dict[str, object]:
    """Return applied, unchanged or unresolved without a blind retry."""
    unknown = {"status": "unresolved", "action_retry_allowed": False,
               "public_capability_advertised": False}
    if not isinstance(pending, Mapping) or not isinstance(recovery, Mapping):
        return {**unknown, "reason": "typed_pending_or_recovery_missing"}
    post = recovery.get("post_observation")
    if not isinstance(post, Mapping):
        return {**unknown, "reason": "independent_post_observation_missing"}
    old_round = pending.get("source_round_id")
    new_round = recovery.get("new_round_id")
    old_pid = pending.get("source_bridge_pid")
    new_pid = recovery.get("new_bridge_pid")
    if not (
        recovery.get("schema_version") == 1
        and recovery.get("status") == "independent_read_complete"
        and recovery.get("private_build") is True
        and recovery.get("advertised") is False
        and recovery.get("new_process_confirmed") is True
        and isinstance(new_round, str) and new_round.startswith("R")
        and new_round[1:].isdigit() and new_round != old_round
        and _positive(old_pid) and _positive(new_pid)
        and isinstance(recovery.get("new_bridge_creation_date"), str)
        and recovery["new_bridge_creation_date"]
        and (new_pid, recovery["new_bridge_creation_date"]) != (
            old_pid, pending.get("source_bridge_creation_date")
        )
        and recovery.get("episode_run_id") == pending.get("episode_run_id")
        and recovery.get("paused") is True
        and recovery.get("map_ready") is True
        and _positive(post.get("snapshot_revision"))
        and _positive(post.get("native_snapshot_revision"))
        and post.get("observed_date_raw") == pending.get("pre_date_raw")
        and post.get("player_character_id") == pending.get("pre_player_character_id")
        and post.get("player_resources_query_complete") is True
        and post.get("recipient_identity_resolved") is True
        and post.get("recipient_character_id") == pending.get("recipient_character_id")
        and post.get("recipient_alive") is True
        and post.get("recipient_opinion_query_complete") is True
        and post.get("source_faction_requery_complete") is True
        and post.get("queried_source_faction_id") == pending.get("source_faction_id")
        and recovery.get("independent_faction_storage_lookup_complete") is True
        and recovery.get("independent_recipient_lookup_complete") is True
        and recovery.get("selected_from_current_targeting_vector") is False
        and _nonnegative(post.get("player_gold_raw"))
        and isinstance(post.get("gift_opinion_present"), bool)
        and isinstance(post.get("source_faction_present"), bool)
    ):
        return {**unknown, "reason": "process_or_independent_entity_facts_unproven"}
    # These exact engine facts can classify effect even when the old faction
    # ceased targeting the player; disappearance of the vector alone cannot.
    expected_gold = pending.get("pre_player_gold_raw")
    expected_cost = pending.get("gold_cost_raw")
    expected_delta = pending.get("opinion_delta")
    if not (_nonnegative(expected_gold) and _positive(expected_cost)
            and _positive(expected_delta)):
        return {**unknown, "reason": "persisted_material_baseline_unknown"}
    if (
        post.get("player_gold_raw") == expected_gold - expected_cost
        and post.get("gift_opinion_present") is True
        and post.get("gift_opinion_modifier_value") == expected_delta
        and (
            post.get("source_faction_present") is False
            or post.get("source_faction_metrics_available") is True
        )
    ):
        members_after = post.get("source_faction_member_character_ids")
        threat_resolved: bool | None = (
            True if post.get("source_faction_present") is False
            else (
                not (
                    post.get("source_faction_targeting_player") is True
                    and pending.get("recipient_character_id") in members_after
                )
                if isinstance(members_after, list)
                and isinstance(post.get("source_faction_targeting_player"), bool)
                else None
            )
        )
        return {
            "status": "applied", "reason": "independent_gold_gift_and_faction_readback",
            "action_retry_allowed": False, "public_capability_advertised": False,
            "request_id": pending.get("request_id"), "new_round_id": new_round,
            "new_bridge_pid": new_pid,
            "new_bridge_creation_date": recovery["new_bridge_creation_date"],
            "post_observation": dict(post),
            "threat_resolved": threat_resolved,
        }
    save_before_action = recovery.get("save_is_pre_action_checkpoint") is True
    same_checkpoint = (
        recovery.get("selected_save_sha256") ==
        pending.get("checkpoint_sha256_before_submit")
    )
    members = post.get("source_faction_member_character_ids")
    if (
        save_before_action and same_checkpoint
        and post.get("player_gold_raw") == expected_gold
        and post.get("gift_opinion_present") is False
        and post.get("gift_opinion_modifier_value") is None
        and post.get("recipient_opinion_of_player") == pending.get("pre_recipient_opinion_of_player")
        and post.get("source_faction_present") is True
        and post.get("source_faction_targeting_player") is True
        and post.get("source_faction_metrics_available") is True
        and post.get("source_faction_power_raw") == pending.get("pre_source_faction_power_raw")
        and post.get("source_faction_discontent_raw") == pending.get("pre_source_faction_discontent_raw")
        and isinstance(members, list)
        and members == pending.get("pre_source_faction_member_character_ids")
    ):
        return {
            "status": "unchanged", "reason": "pre_action_save_and_independent_world_facts_match",
            "action_retry_allowed": True, "public_capability_advertised": False,
            "request_id": pending.get("request_id"), "new_round_id": new_round,
            "new_bridge_pid": new_pid,
        }
    return {**unknown, "reason": "material_outcome_not_distinguishable"}
