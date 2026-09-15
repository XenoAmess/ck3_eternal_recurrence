from __future__ import annotations

import copy

from xar_autoplayer.faction_gift_policy_v1 import choose_faction_gift_v1


def _require(condition: bool) -> None:
    if not condition:
        raise AssertionError("faction gift contract assertion failed")


def _observation(
    *,
    source_id: int = 771,
    recipient_id: int = 33011,
    leader_id: int | None = 33011,
    cost_raw: int = 7_500_000,
    opinion_delta: int = 25,
    opinion: int = -40,
) -> dict[str, object]:
    return {
        "available": True,
        "paused": True,
        "snapshot_revision": 412,
        "native_snapshot_revision": 414,
        "observed_date_raw": 53_789_952,
        "player_resources_query_complete": True,
        "player_character_id": 32904,
        "player_gold_raw": 25_000_000,
        "player_gold_scale": 100_000,
        "source_faction_requery_complete": True,
        "queried_source_faction_id": source_id,
        "source_faction_present": True,
        "source_faction_target_character_id": 32904,
        "source_faction_targeting_player": True,
        "source_faction_at_war": False,
        "source_faction_leader_character_id": leader_id,
        "source_faction_member_character_ids": [recipient_id],
        "source_faction_metrics_available": True,
        "source_faction_power_raw": 65_000_000,
        "source_faction_discontent_raw": 45_000_000,
        "source_faction_metric_scale": 100_000,
        "recipient_identity_resolved": True,
        "recipient_character_id": recipient_id,
        "recipient_alive": True,
        "recipient_is_ai": True,
        "recipient_is_direct_landed_vassal": True,
        "recipient_opinion_query_complete": True,
        "recipient_opinion_of_player": opinion,
        "gift_opinion_present": False,
        "gift_preview": {
            "available": True,
            "definition_key": "gift_interaction",
            "definition_stable_hash": 1_234_567_890,
            "interaction_legal": True,
            "auto_accept": True,
            "gold_cost_raw": cost_raw,
            "gold_scale": 100_000,
            "opinion_delta": opinion_delta,
        },
    }


def test_selects_one_native_legal_member_with_budget_and_stable_role() -> None:
    more_expensive = _observation(
        source_id=772,
        recipient_id=33012,
        leader_id=None,
        cost_raw=12_000_000,
        opinion_delta=20,
    )
    leader = _observation()
    choice = choose_faction_gift_v1(
        [more_expensive, leader],
        complete_native_enumeration=True,
        minimum_gold_reserve_raw=10_000_000,
    )
    _require(choice.status == "selected")
    _require((choice.source_faction_id, choice.recipient_character_id) == (771, 33011))
    _require(choice.membership_role == "leader")
    _require((choice.snapshot_revision, choice.native_snapshot_revision) == (412, 414))
    _require((choice.gold_cost_raw, choice.opinion_delta) == (7_500_000, 25))


def test_missing_enumeration_or_unknown_truth_is_not_empty() -> None:
    _require(choose_faction_gift_v1(
        [], complete_native_enumeration=False, minimum_gold_reserve_raw=0
    ).status == "unavailable")
    unknown = _observation()
    unknown["gift_opinion_present"] = None
    _require(choose_faction_gift_v1(
        [unknown], complete_native_enumeration=True, minimum_gold_reserve_raw=0
    ).status == "unavailable")
    metric_unknown = _observation()
    metric_unknown["source_faction_discontent_raw"] = None
    _require(choose_faction_gift_v1(
        [metric_unknown], complete_native_enumeration=True, minimum_gold_reserve_raw=0
    ).status == "unavailable")


def test_native_denial_and_existing_modifier_are_known_rejections() -> None:
    denied = _observation()
    preview = copy.deepcopy(denied["gift_preview"])
    _require(isinstance(preview, dict))
    preview["interaction_legal"] = False
    preview["gold_cost_raw"] = 0
    preview["opinion_delta"] = 0
    denied["gift_preview"] = preview
    _require(choose_faction_gift_v1(
        [denied], complete_native_enumeration=True, minimum_gold_reserve_raw=0
    ).status == "no_legal_candidate")

    repeated = _observation()
    repeated["gift_opinion_present"] = True
    _require(choose_faction_gift_v1(
        [repeated], complete_native_enumeration=True, minimum_gold_reserve_raw=0
    ).status == "no_legal_candidate")


def test_gold_reserve_rejects_without_forming_action() -> None:
    choice = choose_faction_gift_v1(
        [_observation()],
        complete_native_enumeration=True,
        minimum_gold_reserve_raw=20_000_000,
    )
    _require(choice.status == "budget_reject")
    _require(choice.recipient_character_id is None)


def test_frame_drift_and_faction_war_do_not_form_faction_gift() -> None:
    another = _observation(source_id=772, recipient_id=33012)
    another["native_snapshot_revision"] = 415
    _require(choose_faction_gift_v1(
        [_observation(), another],
        complete_native_enumeration=True,
        minimum_gold_reserve_raw=0,
    ).status == "unavailable")

    at_war = _observation()
    at_war["source_faction_at_war"] = True
    _require(choose_faction_gift_v1(
        [at_war], complete_native_enumeration=True, minimum_gold_reserve_raw=0
    ).status == "no_legal_candidate")
