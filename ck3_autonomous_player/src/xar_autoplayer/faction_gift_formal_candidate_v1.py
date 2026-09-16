"""Read-only formal planning input for one exact-build faction gift candidate.

The source vector is enumerated by the private native bridge; its current v1
wire projects one selected direct landed member. This module never sends a
gift and never converts an absent vector into faction dissolution or effect.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from .faction_gift_policy_v1 import choose_faction_gift_v1


ROOT_STEP = "query-campaign-root-context-v1"
PRIVATE_QUERY_STEP = "private-query-faction-gift-member-v1"


def _int(value: object, *, positive: bool = False) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if positive and value <= 0:
        return None
    return value


def latest_same_frame_faction_root_v1(
    snapshot: Mapping[str, object], history: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Reuse a verified public root read only when it binds this paused frame."""
    actor = snapshot.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    if (
        snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
        or not isinstance(actor, Mapping) or actor.get("alive") is not True
        or _int(actor_id, positive=True) is None
        or _int(snapshot.get("native_revision"), positive=True) is None
        or _int(snapshot.get("date_raw")) is None
    ):
        return {"status": "frame_unavailable", "root": None}
    for row in reversed(history):
        if row.get("command") != ROOT_STEP or row.get("ok") is not True:
            continue
        result = row.get("result")
        context = result.get("campaign_root_context") if isinstance(result, Mapping) else None
        if not isinstance(context, Mapping):
            continue
        if not (
            result.get("status") == "available"
            and context.get("status") == "available"
            and context.get("snapshot_revision") == snapshot["native_revision"]
            and context.get("date_raw") == snapshot["date_raw"]
            and context.get("player_character_id") == actor_id
            and context.get("player_character_alive") is True
        ):
            continue
        government = context.get("government")
        if not isinstance(government, Mapping) or government.get("key") != "feudal_government":
            return {"status": "government_out_of_scope", "root": dict(context)}
        count = _int(context.get("player_targeting_faction_count"))
        direct = context.get("direct_landed_vassal_character_ids")
        if count is None or count < 0 or not isinstance(direct, list) or any(
            _int(character_id, positive=True) is None for character_id in direct
        ) or len(set(direct)) != len(direct):
            return {"status": "root_faction_facts_unknown", "root": dict(context)}
        return {"status": "known_empty" if count == 0 else "targeting_present",
                "root": dict(context)}
    return {"status": "same_frame_root_not_observed", "root": None}


def choose_private_faction_gift_candidate_v1(
    snapshot: Mapping[str, object], root: Mapping[str, object],
    private_result: Mapping[str, object], *, minimum_gold_reserve_raw: int,
) -> dict[str, object]:
    """Consume a native legal preview as one bounded candidate, no submit."""
    actor = snapshot.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    count = _int(root.get("player_targeting_faction_count"))
    if count is None or count <= 0:
        return {"status": "unavailable", "reason": "nonempty_targeting_vector_unproven"}
    if (
        private_result.get("step") != PRIVATE_QUERY_STEP
        or private_result.get("accepted") is not True
        or private_result.get("private_build") is not True
        or private_result.get("advertised") is not False
    ):
        return {"status": "unavailable", "reason": "private_query_envelope_unknown"}
    status = private_result.get("status")
    native = private_result.get("native")
    if status == "no_eligible_direct_vassal":
        # The exact targeting vector exists, but its native selector found no
        # direct landed recipient in the public same-frame vassal list.
        return {"status": "no_legal_candidate", "reason": "no_direct_landed_member"}
    if status != "preview_ready" or not isinstance(native, Mapping):
        return {"status": "unavailable", "reason": "native_preview_not_terminal"}
    if native.get("failure_flags") != 0 or native.get("completion") != "preview_ready":
        return {"status": "unavailable", "reason": "native_preview_receiver_red"}
    observation = native.get("observation")
    if not isinstance(observation, Mapping):
        return {"status": "unavailable", "reason": "native_observation_missing"}
    recipient = _int(observation.get("recipient_character_id"), positive=True)
    source = _int(observation.get("queried_source_faction_id"), positive=True)
    direct = root.get("direct_landed_vassal_character_ids")
    if (
        recipient is None or source is None or not isinstance(direct, list)
        or recipient not in direct
        or native.get("source_faction_id") != source
        or native.get("recipient_character_id") != recipient
        or observation.get("snapshot_revision") != snapshot.get("native_revision")
        or observation.get("observed_date_raw") != snapshot.get("date_raw")
        or observation.get("player_character_id") != actor_id
        or root.get("snapshot_revision") != snapshot.get("native_revision")
        or root.get("date_raw") != snapshot.get("date_raw")
        or root.get("player_character_id") != actor_id
    ):
        return {"status": "unavailable", "reason": "root_private_member_or_frame_mismatch"}
    choice = choose_faction_gift_v1(
        [observation], complete_native_enumeration=True,
        minimum_gold_reserve_raw=minimum_gold_reserve_raw,
    )
    result: dict[str, object] = {
        "status": choice.status, "reason": choice.reason,
        "observation": dict(observation),
        "candidate_source": "exact_full_targeting_vector_native_selected_one_direct_member",
        "public_capability_advertised": False,
        "gift_submission_enabled": False,
    }
    if choice.status == "selected":
        result["choice"] = {
            "source_faction_id": choice.source_faction_id,
            "recipient_character_id": choice.recipient_character_id,
            "membership_role": choice.membership_role,
            "snapshot_revision": choice.snapshot_revision,
            "native_snapshot_revision": choice.native_snapshot_revision,
            "date_raw": choice.date_raw,
            "player_character_id": choice.player_character_id,
            "definition_stable_hash": choice.definition_stable_hash,
            "gold_cost_raw": choice.gold_cost_raw,
            "opinion_delta": choice.opinion_delta,
            "minimum_gold_reserve_raw": minimum_gold_reserve_raw,
        }
    return result
