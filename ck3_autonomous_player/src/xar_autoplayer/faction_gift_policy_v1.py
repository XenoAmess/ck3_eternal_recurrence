"""Private, bounded choice for the exact-build faction gift observation.

Input names mirror FactionGiftMitigationObservationV1 and FactionGiftPreviewV1.
The caller must first obtain a complete, same-frame native enumeration. This
module neither queries CK3 nor submits a gameplay command.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping, Sequence, cast


_GOLD_SCALE = 100_000
_DEFINITION_KEY = "gift_interaction"


@dataclass(frozen=True)
class FactionGiftChoiceV1:
    status: str
    reason: str
    source_faction_id: int | None = None
    recipient_character_id: int | None = None
    membership_role: str | None = None
    snapshot_revision: int | None = None
    native_snapshot_revision: int | None = None
    date_raw: int | None = None
    player_character_id: int | None = None
    definition_stable_hash: int | None = None
    gold_cost_raw: int | None = None
    opinion_delta: int | None = None


def _integer(value: object, *, positive: bool = False) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if positive and value <= 0:
        return None
    return value


def _boolean(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def choose_faction_gift_v1(
    observations: Sequence[Mapping[str, object]],
    *,
    complete_native_enumeration: bool,
    minimum_gold_reserve_raw: int,
) -> FactionGiftChoiceV1:
    """Choose one already observed gift; never turn missing data into no-op.

    The returned IDs and preview values may form a typed action request, but
    the native action must recapture and validate all facts before submission.
    """
    reserve = _integer(minimum_gold_reserve_raw)
    if reserve is None or reserve < 0 or complete_native_enumeration is not True:
        return FactionGiftChoiceV1("unavailable", "enumeration_or_reserve_unproven")
    if not observations:
        return FactionGiftChoiceV1("no_legal_candidate", "complete_native_empty")

    frame: tuple[int, int, int, int, int] | None = None
    eligible: list[tuple[Fraction, int, int, int, int, Mapping[str, object], str]] = []
    legal_count = 0
    for observation in observations:
        if not isinstance(observation, Mapping):
            return FactionGiftChoiceV1("unavailable", "malformed_native_observation")
        if any(
            _boolean(observation.get(field)) is not True
            for field in (
                "available",
                "paused",
                "player_resources_query_complete",
                "source_faction_requery_complete",
                "recipient_identity_resolved",
                "recipient_opinion_query_complete",
                "source_faction_metrics_available",
            )
        ):
            return FactionGiftChoiceV1("unavailable", "native_observation_incomplete")

        revision = _integer(observation.get("snapshot_revision"), positive=True)
        native_revision = _integer(
            observation.get("native_snapshot_revision"), positive=True
        )
        date = _integer(observation.get("observed_date_raw"))
        player = _integer(observation.get("player_character_id"), positive=True)
        gold = _integer(observation.get("player_gold_raw"))
        gold_scale = _integer(observation.get("player_gold_scale"))
        source_id = _integer(
            observation.get("queried_source_faction_id"), positive=True
        )
        recipient = _integer(
            observation.get("recipient_character_id"), positive=True
        )
        target = _integer(
            observation.get("source_faction_target_character_id"), positive=True
        )
        if (
            None in (revision, native_revision, date, player, gold, source_id, recipient, target)
            or gold_scale != _GOLD_SCALE
            or _integer(observation.get("source_faction_power_raw")) is None
            or _integer(observation.get("source_faction_discontent_raw")) is None
            or _integer(observation.get("source_faction_metric_scale")) != _GOLD_SCALE
        ):
            return FactionGiftChoiceV1("unavailable", "native_identity_or_metric_unavailable")
        current_frame = (revision, native_revision, date, player, gold)
        if frame is None:
            frame = current_frame
        elif current_frame != frame:
            return FactionGiftChoiceV1("unavailable", "candidate_frame_drift")

        members = observation.get("source_faction_member_character_ids")
        leader = observation.get("source_faction_leader_character_id")
        if (
            not isinstance(members, (list, tuple))
            or any(_integer(member, positive=True) is None for member in members)
            or len(set(members)) != len(members)
            or (leader is not None and _integer(leader, positive=True) is None)
        ):
            return FactionGiftChoiceV1("unavailable", "faction_membership_unavailable")
        if (
            _boolean(observation.get("source_faction_present")) is None
            or _boolean(observation.get("source_faction_targeting_player")) is None
            or _boolean(observation.get("source_faction_at_war")) is None
            or _boolean(observation.get("recipient_alive")) is None
            or _boolean(observation.get("recipient_is_ai")) is None
            or _boolean(observation.get("recipient_is_direct_landed_vassal")) is None
            or _boolean(observation.get("gift_opinion_present")) is None
            or _integer(observation.get("recipient_opinion_of_player")) is None
        ):
            return FactionGiftChoiceV1("unavailable", "faction_or_recipient_state_unavailable")
        preview = observation.get("gift_preview")
        if not isinstance(preview, Mapping):
            return FactionGiftChoiceV1("unavailable", "gift_preview_unavailable")
        if any(
            _boolean(preview.get(field)) is None
            for field in ("available", "interaction_legal", "auto_accept")
        ):
            return FactionGiftChoiceV1("unavailable", "gift_legality_unavailable")
        definition_hash = _integer(
            preview.get("definition_stable_hash"), positive=True
        )
        if (
            preview.get("definition_key") != _DEFINITION_KEY
            or definition_hash is None
            or preview["available"] is not True
        ):
            return FactionGiftChoiceV1("unavailable", "gift_definition_unavailable")
        # A native legal rejection is a known candidate denial. No cost or
        # opinion effect is required for a command that cannot be sent.
        if preview["interaction_legal"] is False or preview["auto_accept"] is False:
            continue
        preview_cost = _integer(preview.get("gold_cost_raw"), positive=True)
        preview_delta = _integer(preview.get("opinion_delta"), positive=True)
        preview_scale = _integer(preview.get("gold_scale"))
        if None in (preview_cost, preview_delta) or preview_scale != _GOLD_SCALE:
            return FactionGiftChoiceV1("unavailable", "gift_value_unavailable")

        role = (
            "leader"
            if leader == recipient
            else "character_member"
            if recipient in members
            else None
        )
        if (
            observation["source_faction_present"] is not True
            or observation["source_faction_targeting_player"] is not True
            or target != player
            or observation["source_faction_at_war"] is True
            or role is None
            or observation["recipient_alive"] is not True
            or observation["recipient_is_ai"] is not True
            or observation["recipient_is_direct_landed_vassal"] is not True
            or observation["gift_opinion_present"] is not False
        ):
            continue
        legal_count += 1
        if gold - preview_cost < reserve:
            continue
        opinion = cast(int, observation["recipient_opinion_of_player"])
        eligible.append(
            (
                Fraction(preview_cost, preview_delta),
                0 if role == "leader" else 1,
                opinion,
                source_id,
                recipient,
                observation,
                role,
            )
        )

    if not eligible:
        if legal_count:
            return FactionGiftChoiceV1("budget_reject", "gold_reserve_not_satisfied")
        return FactionGiftChoiceV1("no_legal_candidate", "complete_native_no_legal_member")
    _, _, _, source_id, recipient, selected, role = min(
        eligible, key=lambda row: row[:5]
    )
    preview = cast(Mapping[str, object], selected["gift_preview"])
    return FactionGiftChoiceV1(
        "selected",
        "one_budgeted_native_legal_faction_member",
        source_faction_id=source_id,
        recipient_character_id=recipient,
        membership_role=role,
        snapshot_revision=selected["snapshot_revision"],
        native_snapshot_revision=selected["native_snapshot_revision"],
        date_raw=selected["observed_date_raw"],
        player_character_id=selected["player_character_id"],
        definition_stable_hash=preview["definition_stable_hash"],
        gold_cost_raw=preview["gold_cost_raw"],
        opinion_delta=preview["opinion_delta"],
    )
