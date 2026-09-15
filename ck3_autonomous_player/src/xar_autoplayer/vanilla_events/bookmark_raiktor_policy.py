"""Source-reviewed choice for Robert's exact-build Raiktor war event.

This consumer uses the typed current-event-window projection and an optional
same-frame native war-entry assessment. It never treats a missing assessment
as weak Byzantine power or selects the first displayed option by default.
"""

from __future__ import annotations

from collections.abc import Mapping

from ..bridge.war_entry_contract import query_war_entry_assessments_step

EVENT_KEY = "bookmark.1071"
_GOLD_SCALE = 100_000
_GOLD_MINIMUM_RAW = 100 * _GOLD_SCALE
_CLAIM_MARGIN_NUMERATOR = 5
_CLAIM_MARGIN_DENOMINATOR = 4


def _positive_character_id(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and 0 < value <= 2**31 - 1:
        return value
    return None


def _character_scope_id(value: object) -> int | None:
    if not isinstance(value, Mapping) or value.get("type_key") != "character":
        return None
    identity = value.get("typed_identity")
    if not isinstance(identity, Mapping) or identity.get("status") != "available":
        return None
    return _positive_character_id(identity.get("character_id"))


def _blocked(reason: str) -> dict[str, object]:
    return {"status": "blocked", "reason": reason, "selected_native_option_index": None}


def recommend_robert_raiktor_option_v1(
    event_context: Mapping[str, object],
    snapshot: Mapping[str, object],
    *,
    war_entry_assessments: Mapping[int, Mapping[str, object]],
    action_steps: set[str],
    cross_run_focus: str | None,
    event_scope_query_supported: bool = False,
) -> dict[str, object] | None:
    """Recommend authored A only on a large observed margin; otherwise C.

    Return ``None`` solely for other event keys. A matching but incomplete
    Raiktor projection returns a non-action result and cannot enter the
    generic native-order fallback.
    """

    if event_context.get("event_definition_key") != EVENT_KEY:
        return None
    if (
        event_context.get("status") != "available"
        or event_context.get("window_match_count") != 1
        or not isinstance(snapshot.get("active_event"), Mapping)
        or snapshot["active_event"].get("option_count") != 3
    ):
        return _blocked("raiktor_event_identity_or_option_count_drift")

    played = snapshot.get("played_character")
    played_id = (
        _positive_character_id(played.get("character_id"))
        if isinstance(played, Mapping)
        else None
    )
    root_id = _character_scope_id(event_context.get("root_scope"))
    if played_id is None or root_id != played_id:
        return _blocked("raiktor_event_player_root_unavailable_or_mismatch")

    scopes = event_context.get("saved_scopes")
    if not isinstance(scopes, list):
        return _blocked("raiktor_event_saved_scopes_unavailable")
    named: dict[str, int] = {}
    for row in scopes:
        if not isinstance(row, Mapping) or not isinstance(row.get("name"), str):
            continue
        name = row["name"]
        if name not in {"byz_emperor", "raiktor"}:
            continue
        character_id = _character_scope_id(row.get("scope"))
        if character_id is None or name in named:
            return _blocked("raiktor_event_saved_character_scope_drift")
        named[name] = character_id
    if set(named) != {"byz_emperor", "raiktor"} or named["byz_emperor"] == played_id:
        return _blocked("raiktor_event_saved_character_scope_drift")

    options = event_context.get("options")
    if not isinstance(options, list) or len(options) != 3:
        return _blocked("raiktor_event_options_unavailable_or_drifted")
    by_native: dict[int, Mapping[str, object]] = {}
    for row in options:
        if not isinstance(row, Mapping):
            return _blocked("raiktor_event_options_unavailable_or_drifted")
        index = row.get("native_option_index")
        if isinstance(index, bool) or not isinstance(index, int) or index in by_native:
            return _blocked("raiktor_event_options_unavailable_or_drifted")
        by_native[index] = row
    if set(by_native) != {0, 1, 2}:
        return _blocked("raiktor_event_options_unavailable_or_drifted")
    decline = by_native[2]
    if decline.get("shown") is not True or decline.get("enabled") is not True:
        return _blocked("raiktor_no_war_option_not_legal")

    gold = snapshot.get("played_character_gold")
    gold_raw = gold.get("raw") if isinstance(gold, Mapping) else None
    gold_known = bool(
        isinstance(gold_raw, int)
        and not isinstance(gold_raw, bool)
        and gold.get("scale") == _GOLD_SCALE
    )
    active_wars = snapshot.get("active_wars")
    war_conflict = not isinstance(active_wars, list) or len(active_wars) > 0
    target_id = named["byz_emperor"]
    assessment = war_entry_assessments.get(target_id)
    power_margin_ready = False
    power_margin_raw: int | None = None
    if isinstance(assessment, Mapping):
        actor_base = assessment.get("actor_power_base_raw")
        target_total = assessment.get("target_power_total_raw")
        if (
            isinstance(actor_base, int)
            and not isinstance(actor_base, bool)
            and isinstance(target_total, int)
            and not isinstance(target_total, bool)
            and actor_base >= 0
            and target_total >= 0
        ):
            power_margin_raw = actor_base - target_total
            power_margin_ready = (
                actor_base * _CLAIM_MARGIN_DENOMINATOR
                >= target_total * _CLAIM_MARGIN_NUMERATOR
            )

    claim = by_native[0]
    claim_legal = claim.get("shown") is True and claim.get("enabled") is True
    high_value_opportunity = bool(
        claim_legal
        and gold_known
        and gold_raw >= _GOLD_MINIMUM_RAW
        and not war_conflict
        and cross_run_focus not in {"marriage", "succession"}
    )
    if high_value_opportunity and assessment is None:
        declarations = snapshot.get("declarable_wars")
        target_declarable = bool(
            isinstance(declarations, list)
            and any(
                isinstance(row, Mapping)
                and row.get("target_character_id") == target_id
                for row in declarations
            )
        )
        query_step = query_war_entry_assessments_step([target_id])
        if (target_declarable or event_scope_query_supported) and query_step in action_steps:
            return {
                "status": "query_required",
                "reason": "read same-frame native Byzantine strategic power before a claim war",
                "selected_step": query_step,
                "selected_native_option_index": None,
                "target_character_id": target_id,
                "raiktor_character_id": named["raiktor"],
            }
    if high_value_opportunity and power_margin_ready:
        return {
            "status": "recommended",
            "reason": "source-reviewed claim war with a >=25% native own-power margin",
            "selected_native_option_index": 0,
            "target_character_id": target_id,
            "raiktor_character_id": named["raiktor"],
            "native_power_margin_raw": power_margin_raw,
            "source_capture_required_for_gen034_d": True,
        }
    return {
        "status": "recommended",
        "reason": (
            "decline the special war: budget, conflicting goals, option legality "
            "or same-frame own-power margin is not sufficient"
        ),
        "selected_native_option_index": 2,
        "target_character_id": target_id,
        "raiktor_character_id": named["raiktor"],
        "native_power_margin_raw": power_margin_raw,
        "native_power_observed": assessment is not None,
        "source_capture_required_for_gen034_d": False,
    }


__all__ = ["EVENT_KEY", "recommend_robert_raiktor_option_v1"]
