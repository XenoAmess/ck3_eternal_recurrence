"""Strict contract for journal-backed, post-battle transition observation."""

from __future__ import annotations

import copy
from typing import Final


QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY: Final = (
    "game.command.query-battle-terminal-transition-v1"
)
QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX: Final = (
    "query-battle-terminal-transition-v1-"
)
BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE: Final = (
    "production_exact_battle_terminal_transition"
)

_TOP_FIELDS: Final = {
    "schema_version",
    "contract_stage",
    "status",
    "unavailable_reason",
    "battle_terminal_transition_ready",
    "snapshot_revision",
    "observed_date_raw",
    "prior_combat_id",
    "subject_public_cunit_id",
    "terminal_journal",
    "prior",
    "removal",
    "subject",
    "successor",
}
_JOURNAL_FIELDS: Final = {
    "requested_after_sequence",
    "oldest_available_sequence",
    "latest_sequence",
    "event_sequence",
    "event_status",
}
_PRIOR_FIELDS: Final = {
    "combat_id",
    "terminal_kind",
    "terminal_date_raw",
    "suppress_normal_result_envelopes",
    "phase_raw",
    "phase_day",
    "winner_raw",
    "finalized_before",
    "daily_guard_raw",
    "province_id",
    "battle_result_id",
    "wipe_raw",
    "attacker_primary_participant_character_id",
    "defender_primary_participant_character_id",
    "attacker_public_cunit_ids_in_stored_order",
    "defender_public_cunit_ids_in_stored_order",
    "battle_warscore",
}
_WARSCORE_FIELDS: Final = {
    "status",
    "war_id",
    "war_battle_row_index",
    "value_raw_q100000",
    "winner_is_war_attacker",
    "combat_side0_is_war_attacker",
    "attacker_relative_delta_raw_q100000",
}
_REMOVAL_FIELDS: Final = {
    "prior_combat_strictly_resolves",
    "prior_province_strictly_resolves",
    "prior_province_contains_prior_combat_id",
    "result_strictly_resolves",
    "result_relevant_player_count",
}
_SUBJECT_FIELDS: Final = {
    "exists",
    "current_province_id",
    "native_carmy_id",
    "combat_backlink_id",
    "active_combat_id",
    "movement_or_retreat_state_raw",
    "move_target_province_id",
    "route_province_ids_in_stored_order",
    "ai_membership_status",
    "coordinator_id",
    "unit_stack_stored_index",
    "subunit_stored_index",
    "blocked_by_active_combat",
}
_SUCCESSOR_FIELDS: Final = {
    "state",
    "matching_combat_ids_in_native_order",
    "selected_successor_combat_id",
    "participant_overlap_public_cunit_ids_in_prior_order",
}
_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_paused",
    "invalid_request",
    "journal_gap",
    "identity_unavailable",
    "state_changed",
    "bounds_exceeded",
}
_TERMINAL_KINDS: Final = {
    "active_not_terminal",
    "normal_result",
    "no_normal_result",
    "unavailable_after_removal",
}
_SUCCESSOR_STATES: Final = {
    "no_successor",
    "residual_new_combat",
    "subject_missing",
    "subject_retreating",
    "subject_assignment_reopened",
    "unavailable",
}
_AI_MEMBERSHIP_STATUSES: Final = {
    "none",
    "observed",
    "unavailable",
}


def _integer(
    value: object,
    field: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(
            f"{field} must be an integer in [{minimum}, {maximum}]"
        )
    return value


def _positive_int32(value: object, field: str) -> int:
    return _integer(value, field, minimum=1, maximum=2**31 - 1)


def _optional_positive_int32(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, field)


def _optional_integer(
    value: object,
    field: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    if value is None:
        return None
    return _integer(value, field, minimum=minimum, maximum=maximum)


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _optional_boolean(value: object, field: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, field)


def _exact_dict(
    value: object,
    field: str,
    fields: set[str],
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{field} must contain exactly the v1 fields")
    return value


def _ordered_positive_ids(
    value: object,
    field: str,
    *,
    unique: bool,
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result = [
        _positive_int32(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    ]
    if unique and len(result) != len(set(result)):
        raise ValueError(f"{field} must not contain duplicate full IDs")
    return result


def query_battle_terminal_transition_v1_step(
    prior_combat_id: int,
    subject_public_cunit_id: int,
    after_terminal_sequence: int | None = None,
) -> str:
    """Encode the two exact identities and optional journal cursor."""

    prior_combat_id = _positive_int32(prior_combat_id, "prior_combat_id")
    subject_public_cunit_id = _positive_int32(
        subject_public_cunit_id, "subject_public_cunit_id"
    )
    cursor_wire = 0
    if after_terminal_sequence is not None:
        cursor_wire = _integer(
            after_terminal_sequence,
            "after_terminal_sequence",
            minimum=1,
            maximum=2**64 - 1,
        )
    return (
        f"{QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX}"
        f"{prior_combat_id}-{subject_public_cunit_id}-{cursor_wire}"
    )


def parse_query_battle_terminal_transition_v1_step(
    step: object,
) -> tuple[int, int, int | None] | None:
    """Parse only the canonical decimal wire spelling; zero means no cursor."""

    if not isinstance(step, str) or not step.startswith(
        QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX
    ):
        return None
    suffix = step.removeprefix(
        QUERY_BATTLE_TERMINAL_TRANSITION_V1_STEP_PREFIX
    )
    parts = suffix.split("-")
    if len(parts) != 3:
        return None
    if any(
        not part.isascii()
        or not part.isdecimal()
        or (part.startswith("0") and part != "0")
        for part in parts
    ):
        return None
    try:
        prior_combat_id, subject_public_cunit_id, cursor_wire = map(int, parts)
    except ValueError:
        return None
    if not (
        1 <= prior_combat_id <= 2**31 - 1
        and 1 <= subject_public_cunit_id <= 2**31 - 1
        and 0 <= cursor_wire <= 2**64 - 1
    ):
        return None
    return (
        prior_combat_id,
        subject_public_cunit_id,
        cursor_wire if cursor_wire > 0 else None,
    )


def _normalize_journal(
    value: object,
    *,
    expected_after_terminal_sequence: int | None,
) -> dict[str, object]:
    journal = _exact_dict(
        value, "battle_terminal_transition.terminal_journal", _JOURNAL_FIELDS
    )
    requested = _optional_integer(
        journal.get("requested_after_sequence"),
        "battle_terminal_transition.terminal_journal.requested_after_sequence",
        minimum=1,
        maximum=2**64 - 1,
    )
    if requested != expected_after_terminal_sequence:
        raise ValueError("terminal journal cursor binding changed")
    oldest = _integer(
        journal.get("oldest_available_sequence"),
        "battle_terminal_transition.terminal_journal.oldest_available_sequence",
        minimum=0,
        maximum=2**64 - 1,
    )
    latest = _integer(
        journal.get("latest_sequence"),
        "battle_terminal_transition.terminal_journal.latest_sequence",
        minimum=0,
        maximum=2**64 - 1,
    )
    event_sequence = _optional_integer(
        journal.get("event_sequence"),
        "battle_terminal_transition.terminal_journal.event_sequence",
        minimum=1,
        maximum=2**64 - 1,
    )
    event_status = journal.get("event_status")
    if event_status not in {"not_observed", "observed"}:
        raise ValueError("terminal journal event_status is invalid")
    if (oldest == 0) is not (latest == 0):
        raise ValueError("terminal journal empty cursor bounds disagree")
    if oldest > latest:
        raise ValueError("terminal journal cursor bounds are reversed")
    if event_status == "observed":
        if event_sequence is None:
            raise ValueError("observed terminal journal event lacks sequence")
        if not oldest <= event_sequence <= latest:
            raise ValueError("terminal event sequence is outside ring bounds")
        if requested is not None and event_sequence <= requested:
            raise ValueError("terminal event does not follow requested cursor")
    elif event_sequence is not None:
        raise ValueError("not-observed terminal journal invented an event")
    return {
        **journal,
        "requested_after_sequence": requested,
        "oldest_available_sequence": oldest,
        "latest_sequence": latest,
        "event_sequence": event_sequence,
        "event_status": event_status,
    }


def _normalize_warscore(value: object) -> dict[str, object]:
    warscore = _exact_dict(
        value,
        "battle_terminal_transition.prior.battle_warscore",
        _WARSCORE_FIELDS,
    )
    status = warscore.get("status")
    if status not in {"recorded", "not_recorded_by_native", "unavailable"}:
        raise ValueError("battle warscore status is invalid")
    optional_keys = _WARSCORE_FIELDS - {"status"}
    if status != "recorded":
        if any(warscore.get(key) is not None for key in optional_keys):
            raise ValueError("non-recorded battle warscore invented native state")
        return dict(warscore)
    war_id = _positive_int32(
        warscore.get("war_id"),
        "battle_terminal_transition.prior.battle_warscore.war_id",
    )
    row_index = _integer(
        warscore.get("war_battle_row_index"),
        "battle_terminal_transition.prior.battle_warscore."
        "war_battle_row_index",
        minimum=0,
        maximum=2**31 - 1,
    )
    value_raw = _integer(
        warscore.get("value_raw_q100000"),
        "battle_terminal_transition.prior.battle_warscore."
        "value_raw_q100000",
        minimum=0,
        maximum=2**63 - 1,
    )
    winner_is_war_attacker = _boolean(
        warscore.get("winner_is_war_attacker"),
        "battle_terminal_transition.prior.battle_warscore."
        "winner_is_war_attacker",
    )
    combat_side0_is_war_attacker = _boolean(
        warscore.get("combat_side0_is_war_attacker"),
        "battle_terminal_transition.prior.battle_warscore."
        "combat_side0_is_war_attacker",
    )
    relative_delta = _integer(
        warscore.get("attacker_relative_delta_raw_q100000"),
        "battle_terminal_transition.prior.battle_warscore."
        "attacker_relative_delta_raw_q100000",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    expected_delta = value_raw if winner_is_war_attacker else -value_raw
    if relative_delta != expected_delta:
        raise ValueError("battle warscore attacker-relative sign is invalid")
    return {
        **warscore,
        "war_id": war_id,
        "war_battle_row_index": row_index,
        "value_raw_q100000": value_raw,
        "winner_is_war_attacker": winner_is_war_attacker,
        "combat_side0_is_war_attacker": combat_side0_is_war_attacker,
        "attacker_relative_delta_raw_q100000": relative_delta,
    }


def _normalize_prior(
    value: object,
    *,
    expected_prior_combat_id: int,
    event_status: str,
) -> dict[str, object]:
    prior = _exact_dict(
        value, "battle_terminal_transition.prior", _PRIOR_FIELDS
    )
    combat_id = _positive_int32(
        prior.get("combat_id"), "battle_terminal_transition.prior.combat_id"
    )
    if combat_id != expected_prior_combat_id:
        raise ValueError("prior CombatID binding changed")
    terminal_kind = prior.get("terminal_kind")
    if terminal_kind not in _TERMINAL_KINDS:
        raise ValueError("prior terminal_kind is invalid")
    terminal_date_raw = _optional_integer(
        prior.get("terminal_date_raw"),
        "battle_terminal_transition.prior.terminal_date_raw",
        minimum=0,
        maximum=2**31 - 1,
    )
    suppress = _optional_boolean(
        prior.get("suppress_normal_result_envelopes"),
        "battle_terminal_transition.prior."
        "suppress_normal_result_envelopes",
    )
    phase_raw = _optional_integer(
        prior.get("phase_raw"),
        "battle_terminal_transition.prior.phase_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    phase_day = _optional_integer(
        prior.get("phase_day"),
        "battle_terminal_transition.prior.phase_day",
        minimum=0,
        maximum=2**31 - 1,
    )
    winner_raw = _optional_integer(
        prior.get("winner_raw"),
        "battle_terminal_transition.prior.winner_raw",
        minimum=-1,
        maximum=1,
    )
    finalized_before = _optional_boolean(
        prior.get("finalized_before"),
        "battle_terminal_transition.prior.finalized_before",
    )
    daily_guard_raw = _optional_integer(
        prior.get("daily_guard_raw"),
        "battle_terminal_transition.prior.daily_guard_raw",
        minimum=0,
        maximum=255,
    )
    province_id = _optional_positive_int32(
        prior.get("province_id"),
        "battle_terminal_transition.prior.province_id",
    )
    battle_result_id = _optional_positive_int32(
        prior.get("battle_result_id"),
        "battle_terminal_transition.prior.battle_result_id",
    )
    wipe_raw = _optional_boolean(
        prior.get("wipe_raw"), "battle_terminal_transition.prior.wipe_raw"
    )
    attacker_character = _optional_positive_int32(
        prior.get("attacker_primary_participant_character_id"),
        "battle_terminal_transition.prior."
        "attacker_primary_participant_character_id",
    )
    defender_character = _optional_positive_int32(
        prior.get("defender_primary_participant_character_id"),
        "battle_terminal_transition.prior."
        "defender_primary_participant_character_id",
    )
    attacker_ids_value = prior.get(
        "attacker_public_cunit_ids_in_stored_order"
    )
    defender_ids_value = prior.get(
        "defender_public_cunit_ids_in_stored_order"
    )
    attacker_ids = (
        None
        if attacker_ids_value is None
        else _ordered_positive_ids(
            attacker_ids_value,
            "battle_terminal_transition.prior."
            "attacker_public_cunit_ids_in_stored_order",
            unique=True,
        )
    )
    defender_ids = (
        None
        if defender_ids_value is None
        else _ordered_positive_ids(
            defender_ids_value,
            "battle_terminal_transition.prior."
            "defender_public_cunit_ids_in_stored_order",
            unique=True,
        )
    )
    if (
        attacker_ids is not None
        and defender_ids is not None
        and set(attacker_ids) & set(defender_ids)
    ):
        raise ValueError("prior terminal side CUnit partitions overlap")
    warscore = _normalize_warscore(prior.get("battle_warscore"))

    observed_fields = (
        terminal_date_raw,
        suppress,
        phase_raw,
        phase_day,
        winner_raw,
        finalized_before,
        daily_guard_raw,
        province_id,
        attacker_character,
        defender_character,
        attacker_ids,
        defender_ids,
    )
    if event_status == "observed":
        if terminal_kind not in {"normal_result", "no_normal_result"}:
            raise ValueError("observed terminal event has non-terminal kind")
        if any(item is None for item in observed_fields):
            raise ValueError("observed terminal event omitted canonical state")
        expected_suppress = terminal_kind == "no_normal_result"
        if suppress is not expected_suppress:
            raise ValueError("terminal kind disagrees with observed suppress flag")
    elif terminal_kind == "active_not_terminal":
        current_fields = (
            phase_raw,
            phase_day,
            winner_raw,
            finalized_before,
            daily_guard_raw,
            province_id,
            attacker_character,
            defender_character,
            attacker_ids,
            defender_ids,
        )
        if (
            terminal_date_raw is not None
            or suppress is not None
            or any(item is None for item in current_fields)
        ):
            raise ValueError(
                "active_not_terminal omitted current combat state or invented "
                "a suppress flag"
            )
        if finalized_before is not False or daily_guard_raw != 0:
            raise ValueError("active_not_terminal is finalized or being ticked")
        if battle_result_id is None and wipe_raw is not None:
            raise ValueError("active combat wipe state lacks a strict ResultID")
        if warscore["status"] != "unavailable":
            raise ValueError("active combat invented terminal battle warscore")
    else:
        if terminal_kind != "unavailable_after_removal":
            raise ValueError("unobserved terminal state invented terminal kind")
        removed_fields = (
            terminal_date_raw,
            suppress,
            phase_raw,
            phase_day,
            winner_raw,
            finalized_before,
            daily_guard_raw,
            province_id,
            battle_result_id,
            wipe_raw,
            attacker_character,
            defender_character,
            attacker_ids,
            defender_ids,
        )
        if any(item is not None for item in removed_fields):
            raise ValueError("removed unobserved terminal state invented data")
        if warscore["status"] != "unavailable":
            raise ValueError("unobserved terminal state invented battle warscore")
    return {
        **prior,
        "combat_id": combat_id,
        "terminal_kind": terminal_kind,
        "terminal_date_raw": terminal_date_raw,
        "suppress_normal_result_envelopes": suppress,
        "phase_raw": phase_raw,
        "phase_day": phase_day,
        "winner_raw": winner_raw,
        "finalized_before": finalized_before,
        "daily_guard_raw": daily_guard_raw,
        "province_id": province_id,
        "battle_result_id": battle_result_id,
        "wipe_raw": wipe_raw,
        "attacker_primary_participant_character_id": attacker_character,
        "defender_primary_participant_character_id": defender_character,
        "attacker_public_cunit_ids_in_stored_order": attacker_ids,
        "defender_public_cunit_ids_in_stored_order": defender_ids,
        "battle_warscore": warscore,
    }


def _normalize_removal(value: object) -> dict[str, object]:
    removal = _exact_dict(
        value, "battle_terminal_transition.removal", _REMOVAL_FIELDS
    )
    prior_resolves = _boolean(
        removal.get("prior_combat_strictly_resolves"),
        "battle_terminal_transition.removal."
        "prior_combat_strictly_resolves",
    )
    province_resolves = _optional_boolean(
        removal.get("prior_province_strictly_resolves"),
        "battle_terminal_transition.removal."
        "prior_province_strictly_resolves",
    )
    province_contains = _optional_boolean(
        removal.get("prior_province_contains_prior_combat_id"),
        "battle_terminal_transition.removal."
        "prior_province_contains_prior_combat_id",
    )
    result_resolves = _optional_boolean(
        removal.get("result_strictly_resolves"),
        "battle_terminal_transition.removal.result_strictly_resolves",
    )
    relevant_count = _optional_integer(
        removal.get("result_relevant_player_count"),
        "battle_terminal_transition.removal.result_relevant_player_count",
        minimum=0,
        maximum=2**31 - 1,
    )
    if province_resolves is not True and province_contains is not None:
        raise ValueError("unresolved prior Province invented membership")
    if result_resolves is not True and relevant_count is not None:
        raise ValueError("unresolved ResultID invented relevant-player count")
    return {
        **removal,
        "prior_combat_strictly_resolves": prior_resolves,
        "prior_province_strictly_resolves": province_resolves,
        "prior_province_contains_prior_combat_id": province_contains,
        "result_strictly_resolves": result_resolves,
        "result_relevant_player_count": relevant_count,
    }


def _normalize_subject(value: object) -> dict[str, object]:
    subject = _exact_dict(
        value, "battle_terminal_transition.subject", _SUBJECT_FIELDS
    )
    exists = _boolean(
        subject.get("exists"), "battle_terminal_transition.subject.exists"
    )
    normalized: dict[str, object] = {**subject, "exists": exists}
    positive_fields = (
        "current_province_id",
        "native_carmy_id",
        "combat_backlink_id",
        "active_combat_id",
        "move_target_province_id",
        "coordinator_id",
    )
    for key in positive_fields:
        normalized[key] = _optional_positive_int32(
            subject.get(key), f"battle_terminal_transition.subject.{key}"
        )
    normalized["movement_or_retreat_state_raw"] = _optional_integer(
        subject.get("movement_or_retreat_state_raw"),
        "battle_terminal_transition.subject.movement_or_retreat_state_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    route_value = subject.get("route_province_ids_in_stored_order")
    normalized["route_province_ids_in_stored_order"] = (
        None
        if route_value is None
        else _ordered_positive_ids(
            route_value,
            "battle_terminal_transition.subject."
            "route_province_ids_in_stored_order",
            unique=False,
        )
    )
    ai_membership_status = subject.get("ai_membership_status")
    if ai_membership_status not in _AI_MEMBERSHIP_STATUSES:
        raise ValueError("subject AI membership status is invalid")
    normalized["ai_membership_status"] = ai_membership_status
    for key in ("unit_stack_stored_index", "subunit_stored_index"):
        normalized[key] = _optional_integer(
            subject.get(key),
            f"battle_terminal_transition.subject.{key}",
            minimum=0,
            maximum=2**31 - 1,
        )
    normalized["blocked_by_active_combat"] = _optional_boolean(
        subject.get("blocked_by_active_combat"),
        "battle_terminal_transition.subject.blocked_by_active_combat",
    )
    optional_values = [
        normalized[key]
        for key in _SUBJECT_FIELDS - {"exists", "ai_membership_status"}
    ]
    if not exists and any(item is not None for item in optional_values):
        raise ValueError("missing subject invented current native state")
    membership_values = (
        normalized["coordinator_id"],
        normalized["unit_stack_stored_index"],
        normalized["subunit_stored_index"],
    )
    if not exists and ai_membership_status != "none":
        raise ValueError("missing subject has AI membership")
    if ai_membership_status == "observed":
        if any(item is None for item in membership_values):
            raise ValueError("observed subject AI membership is incomplete")
    elif any(item is not None for item in membership_values):
        raise ValueError("unobserved subject invented AI membership identity")
    if (
        normalized["blocked_by_active_combat"] is True
        and normalized["active_combat_id"] is None
    ):
        raise ValueError("active-combat blocker lacks strict CombatID")
    return normalized


def _normalize_successor(
    value: object,
    *,
    prior: dict[str, object],
    subject: dict[str, object],
) -> dict[str, object]:
    successor = _exact_dict(
        value, "battle_terminal_transition.successor", _SUCCESSOR_FIELDS
    )
    state = successor.get("state")
    if state not in _SUCCESSOR_STATES:
        raise ValueError("battle successor state is invalid")
    matching = _ordered_positive_ids(
        successor.get("matching_combat_ids_in_native_order"),
        "battle_terminal_transition.successor."
        "matching_combat_ids_in_native_order",
        unique=True,
    )
    selected = _optional_positive_int32(
        successor.get("selected_successor_combat_id"),
        "battle_terminal_transition.successor.selected_successor_combat_id",
    )
    overlap = _ordered_positive_ids(
        successor.get("participant_overlap_public_cunit_ids_in_prior_order"),
        "battle_terminal_transition.successor."
        "participant_overlap_public_cunit_ids_in_prior_order",
        unique=True,
    )
    if selected is not None and selected not in matching:
        raise ValueError("selected successor is absent from native matches")
    attacker = prior.get("attacker_public_cunit_ids_in_stored_order")
    defender = prior.get("defender_public_cunit_ids_in_stored_order")
    if isinstance(attacker, list) and isinstance(defender, list):
        prior_order = [*attacker, *defender]
        overlap_positions = [
            prior_order.index(item) if item in prior_order else -1
            for item in overlap
        ]
        if -1 in overlap_positions or overlap_positions != sorted(
            overlap_positions
        ):
            raise ValueError("successor overlap is not a prior-order subset")
    if state == "residual_new_combat" and (
        selected is None
        or not matching
        or not overlap
        or subject.get("exists") is not True
        or subject.get("active_combat_id") != selected
        or subject.get("blocked_by_active_combat") is not True
    ):
        raise ValueError("residual successor lacks exact identity overlap")
    if state != "residual_new_combat" and (
        selected is not None or overlap
    ):
        raise ValueError("non-residual successor invented a selection")
    if state == "subject_missing" and (
        subject.get("exists") is not False or matching
    ):
        raise ValueError("subject-missing successor disagrees with subject")
    movement_state = subject.get("movement_or_retreat_state_raw")
    movement_state = movement_state if isinstance(movement_state, int) else 0
    if state == "subject_retreating" and (
        subject.get("exists") is not True
        or subject.get("active_combat_id") is not None
        or subject.get("blocked_by_active_combat") is not False
        or movement_state <= 0
    ):
        raise ValueError("retreating successor lacks independent retreat state")
    if state == "subject_assignment_reopened" and (
        subject.get("exists") is not True
        or subject.get("blocked_by_active_combat") is not False
        or subject.get("active_combat_id") is not None
        or movement_state > 0
        or subject.get("ai_membership_status") != "observed"
        or matching
    ):
        raise ValueError("assignment-reopened successor lacks observed membership")
    if state == "no_successor" and (
        subject.get("exists") is not True
        or subject.get("ai_membership_status") != "none"
        or subject.get("active_combat_id") is not None
        or subject.get("blocked_by_active_combat") is True
        or movement_state > 0
        or matching
        or selected is not None
        or overlap
    ):
        raise ValueError("no-successor state lacks complete negative evidence")
    return {
        **successor,
        "state": state,
        "matching_combat_ids_in_native_order": matching,
        "selected_successor_combat_id": selected,
        "participant_overlap_public_cunit_ids_in_prior_order": overlap,
    }


def normalize_battle_terminal_transition_v1(
    value: object,
    *,
    expected_prior_combat_id: int,
    expected_subject_public_cunit_id: int,
    expected_after_terminal_sequence: int | None,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one journal-backed frame without inferring terminal kind."""

    expected_prior_combat_id = _positive_int32(
        expected_prior_combat_id, "expected_prior_combat_id"
    )
    expected_subject_public_cunit_id = _positive_int32(
        expected_subject_public_cunit_id,
        "expected_subject_public_cunit_id",
    )
    if expected_after_terminal_sequence is not None:
        expected_after_terminal_sequence = _integer(
            expected_after_terminal_sequence,
            "expected_after_terminal_sequence",
            minimum=1,
            maximum=2**64 - 1,
        )
    expected_observed_date_raw = _integer(
        expected_observed_date_raw,
        "expected_observed_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    expected_snapshot_revision = _integer(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    frame = _exact_dict(value, "battle_terminal_transition", _TOP_FIELDS)
    if frame.get("schema_version") != 1:
        raise ValueError("battle_terminal_transition.schema_version must be 1")
    if (
        frame.get("contract_stage")
        != BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE
    ):
        raise ValueError("battle_terminal_transition.contract_stage is invalid")
    status = frame.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError("battle_terminal_transition.status is invalid")
    ready = _boolean(
        frame.get("battle_terminal_transition_ready"),
        "battle_terminal_transition.battle_terminal_transition_ready",
    )
    if ready is not (status == "available"):
        raise ValueError("battle terminal transition readiness disagrees with status")
    revision = _integer(
        frame.get("snapshot_revision"),
        "battle_terminal_transition.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    observed_date_raw = _integer(
        frame.get("observed_date_raw"),
        "battle_terminal_transition.observed_date_raw",
        minimum=-(2**31),
        maximum=2**31 - 1,
    )
    prior_combat_id = _positive_int32(
        frame.get("prior_combat_id"),
        "battle_terminal_transition.prior_combat_id",
    )
    subject_public_cunit_id = _positive_int32(
        frame.get("subject_public_cunit_id"),
        "battle_terminal_transition.subject_public_cunit_id",
    )
    if revision != expected_snapshot_revision:
        raise ValueError("battle terminal transition revision binding changed")
    if observed_date_raw != expected_observed_date_raw:
        raise ValueError("battle terminal transition date binding changed")
    if prior_combat_id != expected_prior_combat_id:
        raise ValueError("battle terminal transition CombatID binding changed")
    if subject_public_cunit_id != expected_subject_public_cunit_id:
        raise ValueError("battle terminal transition CUnitID binding changed")

    reason = frame.get("unavailable_reason")
    if status == "unavailable":
        if reason not in _UNAVAILABLE_REASONS:
            raise ValueError("battle terminal unavailable_reason is invalid")
        journal = _normalize_journal(
            frame.get("terminal_journal"),
            expected_after_terminal_sequence=expected_after_terminal_sequence,
        )
        if (
            journal["event_status"] != "not_observed"
            or journal["event_sequence"] is not None
        ):
            raise ValueError("unavailable transition invented terminal event")
        if any(
            frame.get(key) is not None
            for key in ("prior", "removal", "subject", "successor")
        ):
            raise ValueError("unavailable terminal transition invented native state")
        return {**copy.deepcopy(frame), "terminal_journal": journal}
    if reason is not None:
        raise ValueError("available terminal transition has unavailable_reason")

    journal = _normalize_journal(
        frame.get("terminal_journal"),
        expected_after_terminal_sequence=expected_after_terminal_sequence,
    )
    prior = _normalize_prior(
        frame.get("prior"),
        expected_prior_combat_id=expected_prior_combat_id,
        event_status=str(journal["event_status"]),
    )
    removal = _normalize_removal(frame.get("removal"))
    subject = _normalize_subject(frame.get("subject"))
    successor = _normalize_successor(
        frame.get("successor"), prior=prior, subject=subject
    )
    if (
        prior["terminal_kind"] == "active_not_terminal"
        and removal["prior_combat_strictly_resolves"] is not True
    ):
        raise ValueError("active_not_terminal does not strictly resolve")
    if (
        prior["terminal_kind"] == "unavailable_after_removal"
        and removal["prior_combat_strictly_resolves"] is not False
    ):
        raise ValueError("unavailable_after_removal still strictly resolves")
    return {
        **frame,
        "unavailable_reason": None,
        "snapshot_revision": revision,
        "observed_date_raw": observed_date_raw,
        "prior_combat_id": prior_combat_id,
        "subject_public_cunit_id": subject_public_cunit_id,
        "terminal_journal": journal,
        "prior": prior,
        "removal": removal,
        "subject": subject,
        "successor": successor,
    }
