"""Persistent one-life episode summaries used by the gameplay policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .bridge.event_contract import (
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
)
from .bridge.declaration_contract import (
    QUERY_DECLARABLE_WARS_STEP,
    declare_war_step,
)
from .bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
)
from .bridge.battle_control_contract import (
    normalize_battle_control_snapshot_v1,
    parse_query_battle_control_snapshot_v1_step,
    query_battle_control_snapshot_v1_step,
)
from .bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    normalize_battle_terminal_transition_v1,
    parse_query_battle_terminal_transition_v1_step,
    query_battle_terminal_transition_v1_step,
)
from .bridge.war_entry_contract import (
    FIXED_POINT_SCALE as WAR_ENTRY_FIXED_POINT_SCALE,
    normalize_war_entry_assessments,
    query_war_entry_assessments_step,
)
from .bridge.marriage_contract import (
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
    arrange_marriage_step,
    observed_marriage_status,
    parse_arrange_marriage_step,
)
from .bridge.pending_character_interaction_context_contract import (
    ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    normalize_pending_interaction_id,
)
from .bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from .bridge.settlement_contract import ONE_LIFE_SETTLEMENT_CAPABILITY
from .bridge.war_contract import (
    MAX_ROUTE_CONTACT_HOSTILE_IDS,
    RAISE_TROOPS_STEP,
    advance_route_contact_horizon_step,
    battle_decision_epoch_advance_step,
    controllable_armies,
    disband_army_step,
    enemy_primary_default_raise_province_ids,
    enforce_demands_step,
    enemy_armies_from_wars,
    is_life_advance_step,
    merge_armies_step,
    move_army_step,
    offer_white_peace_step,
    parse_merge_armies_step,
    parse_battle_decision_epoch_advance_step,
    parse_move_army_step,
    parse_preview_move_army_step,
    parse_query_route_contact_horizon_step,
    parse_split_army_half_step,
    parse_start_assault_step,
    parse_stop_assault_step,
    preview_move_army_step,
    query_route_contact_horizon_step,
    query_war_termination_options_step,
    query_war_termination_terms_step,
    stationary_province_contact_free_in_horizon,
    start_assault_step,
    stop_assault_step,
    unavoidable_current_province_contact_in_horizon,
    war_objective_province_ids,
)
from .environment import write_json_atomic
from .errors import AgentError
from .runtime import utc_now
from .simulation.battle_terminal_cruise_policy import (
    assess_battle_terminal_cruise,
)


ONE_LIFE_STRATEGY_RELATIVE_PATH = Path("strategy") / "one-life-history.json"
_EMPTY_MARRIAGE_QUERY_LIMIT = 3
_MARRIAGE_RETRY_QUERY_LIMIT = 3
_MARRIAGE_PROPOSAL_MAX_ADVANCES = 7
_MARRIAGE_PROPOSAL_MAX_GAME_DAYS = 30
_NATIVE_MOVE_INTENT_MAX_GAME_DAYS = 90
_NATIVE_CONTACT_STALE_GAME_DAYS = 14
_NATIVE_CONTACT_MAX_PROBES = 2
_NATIVE_COLLISION_COOLDOWN_GAME_DAYS = 90
_NATIVE_DEFEAT_SCORE_DROP = 20
_NATIVE_RETREAT_MAX_GAME_DAYS = 30
_NATIVE_SIEGE_STALL_GAME_DAYS = 7
_NATIVE_MOVE_RETRY_BACKOFF_DAYS = (7, 14, 30)
_WHITE_PEACE_PROPOSAL_COOLDOWN_RAW = 30 * 24
_BATTLE_DECISION_EPOCH_ADVANCE_STEP = "battle-decision-epoch-advance"
_BATTLE_TERMINAL_CRUISE_STEP = "battle-terminal-cruise"
_BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS = 45
_BATTLE_SENTINEL_MAX_WATCH_ARMIES = 64
_NATIVE_ENEMY_TARGET_MILESTONES_DAYS = (7, 14)
_ACCEPT_PENDING_CHARACTER_INTERACTION_STEP = (
    "accept-pending-character-interaction"
)
_REJECT_PENDING_CHARACTER_INTERACTION_STEP = (
    "reject-pending-character-interaction"
)
_BLOCK_PENDING_CHARACTER_INTERACTION_STEP = (
    "block-pending-character-interaction"
)
_PENDING_REPLY_STEPS = {
    "accept": _ACCEPT_PENDING_CHARACTER_INTERACTION_STEP,
    "reject": _REJECT_PENDING_CHARACTER_INTERACTION_STEP,
    "block": _BLOCK_PENDING_CHARACTER_INTERACTION_STEP,
    "acknowledge": ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
}
_KNOWN_WAR_EXIT_INTERACTION_KEYS = {
    "end_war_attacker_victory_interaction",
    "end_war_attacker_white_peace_interaction",
    "end_war_attacker_defeat_interaction",
}
_DEGRADED_ORDINARY_INTERACTION_ALLOWLIST = {
    "spar_with_knight_interaction": {
        "classification": "ordinary_non_war_nonreligious",
        "source": (
            "common/character_interactions/00_tradition_interactions.txt"
        ),
        "source_sha256": (
            "E3B7330D8DFD9C82522D65629B6DD991D319B76B41C388CE483E351D829391E3"
        ),
    },
    "pay_ransom_interaction": {
        "classification": "ordinary_non_war_nonreligious",
        "domain": "prison_ransom",
        "war_sensitive": True,
        "source": "common/character_interactions/00_prison_interactions.txt",
        "source_sha256": (
            "3E05C94CDCE4D42CCE8256D2D79CD78FEB1C9D5B79DAA64AA8243AA0C658F22B"
        ),
    },
}
_DEGRADED_MARRIAGE_REJECT_ONLY_ALLOWLIST = {
    "arrange_marriage_interaction": {
        "classification": "marriage_special_reject_only",
        "domain": "marriage_alliance",
        "source": "common/character_interactions/00_marriage_interactions.txt",
        "source_sha256": (
            "681A9B669E5A16642A197B6FE16085193DFBB99A398D0E20E86173F5AC6DE219"
        ),
        "required_send_option_count": 6,
        "known_decline_effects": [
            "marriage_interaction.0011",
            "secondary_actor:player_declined_marriage:5y",
        ],
    },
}


def _expanded_command_rows(
    commands: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Flatten bounded auto-runs into the same history used by one-step turns."""
    expanded: list[dict[str, object]] = []
    for row in commands:
        if not isinstance(row, dict):
            continue
        command = row.get("command")
        if isinstance(command, str) and (
            command == "auto-run"
            or (
                command.startswith("auto-run ")
                and command.removeprefix("auto-run ").isdigit()
            )
        ):
            result = row.get("result")
            turns = result.get("turns") if isinstance(result, dict) else None
            if isinstance(turns, list):
                for turn in turns:
                    if isinstance(turn, dict):
                        expanded.append({**turn, "index": len(expanded) + 1})
                continue
        expanded.append({**row, "index": len(expanded) + 1})
    return expanded


def _effective_command(row: dict[str, object]) -> str | None:
    command = row.get("command")
    if command != "auto-turn":
        return command if isinstance(command, str) else None
    result = row.get("result")
    if not isinstance(result, dict):
        return None
    auto_turn = result.get("auto_turn")
    if not isinstance(auto_turn, dict):
        return None
    selected = auto_turn.get("selected_step")
    return selected if isinstance(selected, str) else None


def _latest_index(
    commands: list[dict[str, object]],
    command: str,
    *,
    successful_only: bool = True,
) -> int:
    for fallback_index, row in reversed(tuple(enumerate(commands, start=1))):
        if _effective_command(row) != command:
            continue
        if successful_only and row.get("ok") is not True:
            continue
        raw_index = row.get("index")
        return raw_index if isinstance(raw_index, int) else fallback_index
    return 0


def _latest_life_advance_index(
    commands: list[dict[str, object]], *, successful_only: bool = True
) -> int:
    for fallback_index, row in reversed(tuple(enumerate(commands, start=1))):
        if not is_life_advance_step(_effective_command(row)):
            continue
        if successful_only and row.get("ok") is not True:
            continue
        raw_index = row.get("index")
        return raw_index if isinstance(raw_index, int) else fallback_index
    return 0


def _latest_effective_result(
    commands: list[dict[str, object]], command: str
) -> dict[str, object] | None:
    for row in reversed(commands):
        if _effective_command(row) != command or row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def _latest_prefix_index(
    rows: list[dict[str, object]], prefix: str, *, successful_only: bool = True
) -> int:
    for fallback_index, row in reversed(tuple(enumerate(rows, start=1))):
        command = _effective_command(row)
        if (
            isinstance(command, str)
            and command.startswith(prefix)
            and (not successful_only or row.get("ok") is True)
        ):
            raw_index = row.get("index")
            return raw_index if isinstance(raw_index, int) else fallback_index
    return 0


def _preferred_native_declaration(
    declarations: object,
    *,
    war_entry_assessments: dict[int, dict[str, object]] | None = None,
) -> dict[str, object] | None:
    if not isinstance(declarations, list):
        return None
    rows = [row for row in declarations if isinstance(row, dict)]
    if not rows:
        return None

    def preference(row: dict[str, object]) -> tuple[object, ...]:
        def stable_integer(name: str) -> int:
            value = row.get(name)
            return value if isinstance(value, int) and not isinstance(value, bool) else 2**31 - 1

        key = str(row.get("casus_belli_key") or "").casefold()
        if "holy_war" in key and "county" in key:
            key_rank = 0
        elif "county" in key:
            key_rank = 1
        elif "claim" in key:
            key_rank = 2
        else:
            key_rank = 3
        titles = row.get("target_title_ids")
        title_count = len(titles) if isinstance(titles, list) else 1_000_000
        assessment = (
            war_entry_assessments.get(stable_integer("target_character_id"))
            if isinstance(war_entry_assessments, dict)
            else None
        )
        # This is a target-level native strategic-power ordering, not a win
        # probability.  Prefer a target that the actor's own adjusted base can
        # cover even after retaining the target's full native relationship
        # network.  The native total ratio is the next ordering lane; positive
        # actor-network reliance and target-network support remain explicit
        # uncertainty tie-breakers rather than being silently netted away.
        if isinstance(assessment, dict):
            actor_base = int(assessment["actor_power_base_raw"])
            actor_network = int(assessment["actor_network_contribution_raw"])
            target_network = int(assessment["target_network_contribution_raw"])
            target_total = int(assessment["target_power_total_raw"])
            native_power_risk = (
                max(target_total - actor_base, 0),
                int(assessment["actual_power_ratio_raw"]),
                max(actor_network, 0),
                max(target_network, 0),
                target_total,
                int(assessment["distance_raw"]),
            )
            evidence_rank = 0
        else:
            native_power_risk = (2**63 - 1,) * 6
            evidence_rank = 1
        return (
            evidence_rank,
            *native_power_risk,
            key_rank,
            title_count,
            stable_integer("target_character_id"),
            stable_integer("casus_belli_index"),
            stable_integer("configuration_index"),
        )

    return min(rows, key=preference)


def _same_frame_war_entry_assessments(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
) -> dict[int, dict[str, object]]:
    """Recover complete target rows that belong to the current paused frame.

    A production request is deliberately bounded to one target.  Keeping
    prior successful query results from the same paused frame allows a caller
    to compare targets without broadening that native request or treating a
    stale assessment as current evidence.
    """

    if not isinstance(snapshot, dict):
        return {}
    played_character = snapshot.get("played_character")
    actor_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    payloads: list[object] = [snapshot.get("war_entry_assessments")]
    for command_row in rows:
        command = _effective_command(command_row)
        if not (
            isinstance(command, str)
            and command.startswith("query-war-entry-assessments-v1-")
            and command_row.get("ok") is True
        ):
            continue
        result = command_row.get("result")
        # Native command history stores the primitive result directly.  An
        # auto-turn envelope stores it one level deeper.
        if isinstance(result, dict) and isinstance(result.get("result"), dict):
            result = result["result"]
        payloads.append(
            result.get("war_entry_assessments")
            if isinstance(result, dict)
            else None
        )

    recovered: dict[int, dict[str, object]] = {}
    for payload in payloads:
        try:
            normalized = normalize_war_entry_assessments(
                payload,
                expected_actor_character_id=(
                    actor_id
                    if isinstance(actor_id, int)
                    and not isinstance(actor_id, bool)
                    else None
                ),
                expected_snapshot_revision=(
                    native_revision
                    if isinstance(native_revision, int)
                    and not isinstance(native_revision, bool)
                    else None
                ),
            )
        except ValueError:
            continue
        if (
            isinstance(date_raw, int)
            and not isinstance(date_raw, bool)
            and normalized["date_raw"] != date_raw
        ):
            continue
        for assessment in normalized["assessments"]:
            recovered[int(assessment["target_character_id"])] = assessment
    return recovered


def _same_frame_pending_interaction_context(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
) -> dict[str, object] | None:
    """Recover the latest typed interaction observation for this exact frame."""

    if not isinstance(snapshot, dict):
        return None
    pending = snapshot.get("pending_character_interaction")
    if not isinstance(pending, dict):
        return None
    pending_id = pending.get("instance_id")
    revision = snapshot.get("revision")
    snapshot_id = snapshot.get("snapshot_id")
    if (
        not _valid_pending_interaction_id(pending_id)
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or not isinstance(snapshot_id, str)
        or not snapshot_id
    ):
        return None

    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    for row in reversed(rows):
        if (
            _effective_command(row)
            != QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
            or row.get("ok") is not True
        ):
            continue
        result = _effective_command_result(row)
        context = (
            result.get("pending_character_interaction_context")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(result, dict)
            and isinstance(context, dict)
            and result.get("step")
            == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
            and result.get("accepted") is True
            and result.get("status") == context.get("status")
            and result.get("queried_snapshot_id") == snapshot_id
            and result.get("queried_revision") == revision
            and context.get("pending_interaction_id") == pending_id
        ):
            continue
        if (
            isinstance(native_revision, int)
            and not isinstance(native_revision, bool)
            and (
                result.get("queried_native_revision") != native_revision
                or result.get("snapshot_revision") != native_revision
                or context.get("snapshot_revision") != native_revision
            )
        ):
            continue
        if (
            isinstance(date_raw, int)
            and not isinstance(date_raw, bool)
            and context.get("date_raw") != date_raw
        ):
            continue
        return context
    return None


def _valid_pending_interaction_id(value: object) -> bool:
    try:
        normalize_pending_interaction_id(value)
    except ValueError:
        return False
    return True


def _pending_interaction_missing_semantics(
    context: dict[str, object],
) -> list[str]:
    """Describe semantic debt without upgrading any readiness flag."""

    missing: list[str] = []

    def add(value: object) -> None:
        if isinstance(value, str) and value and value not in missing:
            missing.append(value)

    readiness = context.get("readiness")
    if isinstance(readiness, dict):
        reasons = readiness.get("not_ready_reasons")
        if isinstance(reasons, list):
            for reason in reasons:
                add(reason)

    target = context.get("target")
    if (
        isinstance(target, dict)
        and target.get("present") is True
        and target.get("typed_identity_status") != "available"
    ):
        reason = target.get("typed_identity_reason")
        add(
            "target_typed_identity:"
            + (reason if isinstance(reason, str) and reason else "unavailable")
        )

    terms = context.get("terms")
    if isinstance(terms, dict):
        for key in (
            "structured_exchanges",
            "structured_effect_preview",
            "recipient_ai_acceptance_score",
            "recipient_ai_final_decision",
        ):
            item = terms.get(key)
            if isinstance(item, dict) and item.get("status") != "available":
                reason = item.get("reason")
                add(
                    f"terms.{key}:"
                    + (
                        reason
                        if isinstance(reason, str) and reason
                        else "unavailable"
                    )
                )
    return missing


def _pending_interaction_summary(
    pending: dict[str, object],
    context: dict[str, object] | None,
    snapshot: dict[str, object] | None,
) -> dict[str, object]:
    """Keep every decision-bearing pending field in the turn artifact."""

    summary: dict[str, object] = {
        "instance_id": pending.get("instance_id"),
        "sender_character_id": pending.get("sender_character_id"),
        "auto_accept_notification": pending.get("auto_accept_notification"),
    }
    if not isinstance(context, dict):
        return summary

    definition = context.get("definition")
    roles = context.get("roles")
    routing = context.get("routing")
    deadline = context.get("deadline")
    legality = context.get("legality")
    terms = context.get("terms")
    readiness = context.get("readiness")
    special_war_binding = (
        terms.get("special_war_binding") if isinstance(terms, dict) else None
    )
    summary.update(
        {
            "context_status": context.get("status"),
            "context_reason": context.get("reason"),
            "frame_binding": {
                "snapshot_id": (
                    snapshot.get("snapshot_id")
                    if isinstance(snapshot, dict)
                    else None
                ),
                "public_revision": (
                    snapshot.get("revision")
                    if isinstance(snapshot, dict)
                    else None
                ),
                "native_revision": context.get("snapshot_revision"),
                "date_raw": context.get("date_raw"),
                "pending_interaction_id": context.get(
                    "pending_interaction_id"
                ),
            },
            "definition": dict(definition) if isinstance(definition, dict) else None,
            "interaction_key": (
                definition.get("canonical_key")
                if isinstance(definition, dict)
                else None
            ),
            "roles": dict(roles) if isinstance(roles, dict) else None,
            "routing": dict(routing) if isinstance(routing, dict) else None,
            "current_responder_role": (
                routing.get("current_responder_role")
                if isinstance(routing, dict)
                else None
            ),
            "deadline": dict(deadline) if isinstance(deadline, dict) else None,
            "reply_legality": (
                {
                    key: dict(value) if isinstance(value, dict) else value
                    for key, value in legality.items()
                }
                if isinstance(legality, dict)
                else None
            ),
            "special_data_present": (
                terms.get("special_data_present")
                if isinstance(terms, dict)
                else None
            ),
            "special_war_binding": (
                {
                    **special_war_binding,
                    "value": (
                        dict(special_war_binding["value"])
                        if isinstance(special_war_binding.get("value"), dict)
                        else special_war_binding.get("value")
                    ),
                }
                if isinstance(special_war_binding, dict)
                else None
            ),
            "send_options": (
                context.get("send_options")
                if isinstance(context.get("send_options"), dict)
                else None
            ),
            "context_semantic_decision_ready": (
                readiness.get("interaction_semantic_decision_ready")
                if isinstance(readiness, dict)
                else None
            ),
            "not_ready_reasons": (
                list(readiness.get("not_ready_reasons", []))
                if isinstance(readiness, dict)
                and isinstance(readiness.get("not_ready_reasons"), list)
                else []
            ),
            "missing_semantics": _pending_interaction_missing_semantics(context),
        }
    )
    return summary


def _pending_interaction_evidence_gaps(
    pending: dict[str, object],
    context: dict[str, object],
    snapshot: dict[str, object],
) -> list[str]:
    """Reject incomplete or cross-identity observations before policy use."""

    gaps: list[str] = []
    if not (
        snapshot.get("paused") is True
        and isinstance(snapshot.get("snapshot_id"), str)
        and bool(snapshot.get("snapshot_id"))
        and isinstance(snapshot.get("revision"), int)
        and not isinstance(snapshot.get("revision"), bool)
        and isinstance(snapshot.get("native_revision"), int)
        and not isinstance(snapshot.get("native_revision"), bool)
        and snapshot.get("native_revision") == context.get("snapshot_revision")
        and isinstance(snapshot.get("date_raw"), int)
        and not isinstance(snapshot.get("date_raw"), bool)
        and snapshot.get("date_raw") == context.get("date_raw")
    ):
        gaps.append("same_paused_frame_binding_unavailable")
    if context.get("status") != "available":
        gaps.append("context_not_available")
    pending_id = pending.get("instance_id")
    if (
        not _valid_pending_interaction_id(pending_id)
        or context.get("pending_interaction_id") != pending_id
    ):
        gaps.append("pending_full_identity_mismatch")

    definition = context.get("definition")
    key = definition.get("canonical_key") if isinstance(definition, dict) else None
    if not isinstance(key, str) or not key:
        gaps.append("stable_definition_key_unavailable")

    roles = context.get("roles")
    role_fields = (
        "actor_character_id",
        "recipient_character_id",
        "secondary_actor_character_id",
        "secondary_recipient_character_id",
        "intermediary_character_id",
    )
    if not (
        isinstance(roles, dict)
        and all(
            isinstance(roles.get(field), int)
            and not isinstance(roles.get(field), bool)
            for field in role_fields
        )
        and isinstance(roles.get("actor_character_id"), int)
        and int(roles["actor_character_id"]) > 0
        and isinstance(roles.get("recipient_character_id"), int)
        and int(roles["recipient_character_id"]) > 0
    ):
        gaps.append("complete_roles_unavailable")
    elif pending.get("sender_character_id") != roles.get("actor_character_id"):
        gaps.append("snapshot_sender_actor_mismatch")

    routing = context.get("routing")
    if not isinstance(routing, dict):
        gaps.append("routing_unavailable")
    else:
        responder_role = routing.get("current_responder_role")
        responder_id = (
            roles.get(f"{responder_role}_character_id")
            if isinstance(roles, dict)
            and responder_role in {"recipient", "intermediary"}
            else None
        )
        if not (
            routing.get("local_route") is True
            and routing.get("auto_accept_notification") is False
            and responder_id == routing.get("played_character_id")
        ):
            gaps.append("local_responder_identity_mismatch")

    deadline = context.get("deadline")
    if not (
        isinstance(deadline, dict)
        and all(
            isinstance(deadline.get(field), int)
            and not isinstance(deadline.get(field), bool)
            for field in ("age_days", "expiration_days", "remaining_days")
        )
        and isinstance(deadline.get("expiry_boundary_status"), str)
    ):
        gaps.append("deadline_unavailable")

    legality = context.get("legality")
    if not isinstance(legality, dict):
        gaps.append("reply_legality_unavailable")
    else:
        for action in ("accept", "reject", "block", "acknowledge"):
            item = legality.get(action)
            if not (
                isinstance(item, dict)
                and item.get("status") == "available"
                and isinstance(item.get("allowed"), bool)
            ):
                gaps.append(f"{action}_legality_unavailable")

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    if not (
        isinstance(terms, dict)
        and isinstance(terms.get("special_data_present"), bool)
        and isinstance(special, dict)
        and special.get("status") in {"available", "unavailable"}
    ):
        gaps.append("special_war_classification_unavailable")
    return gaps


def _arrange_marriage_reject_contract_gaps(
    context: dict[str, object],
) -> list[str]:
    """Match only the exact direct, zero-option marriage blocker shape."""

    gaps: list[str] = []
    roles = context.get("roles")
    if not isinstance(roles, dict):
        return ["marriage_roles_unavailable"]
    for field in (
        "actor_character_id",
        "recipient_character_id",
        "secondary_actor_character_id",
        "secondary_recipient_character_id",
    ):
        value = roles.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            gaps.append(f"marriage_{field}_unavailable")
    if roles.get("intermediary_character_id") != -1:
        gaps.append("marriage_direct_recipient_route_required")

    routing = context.get("routing")
    if not (
        isinstance(routing, dict)
        and routing.get("kind") == 0
        and routing.get("current_responder_role") == "recipient"
        and routing.get("reply_execution_channel") == "recipient"
        and routing.get("local_route") is True
        and routing.get("auto_accept_notification") is False
        and routing.get("played_character_id")
        == roles.get("recipient_character_id")
    ):
        gaps.append("marriage_direct_local_recipient_route_mismatch")

    deadline = context.get("deadline")
    if not (
        isinstance(deadline, dict)
        and deadline.get("age_days") == 0
        and deadline.get("expiration_days") == 60
        and deadline.get("remaining_days") == 60
        and deadline.get("expiry_boundary_status") == "not_reached"
    ):
        gaps.append("marriage_same_day_deadline_shape_mismatch")

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    if not (
        isinstance(terms, dict)
        and terms.get("special_data_present") is True
        and isinstance(special, dict)
        and special.get("status") == "unavailable"
        and special.get("value") is None
        and special.get("reason") == "special_interaction_subtype_opaque"
    ):
        gaps.append("marriage_special_payload_shape_mismatch")

    send_options = context.get("send_options")
    rows = send_options.get("rows") if isinstance(send_options, dict) else None
    if not (
        isinstance(send_options, dict)
        and send_options.get("exclusive") is False
        and send_options.get("definition_count") == 6
        and send_options.get("context_count") == 6
        and isinstance(rows, list)
        and len(rows) == 6
        and all(
            isinstance(row, dict)
            and row.get("native_index") == index
            and row.get("selected") is False
            for index, row in enumerate(rows)
        )
    ):
        gaps.append("marriage_zero_option_vector_mismatch")

    legality = context.get("legality")
    acknowledge = legality.get("acknowledge") if isinstance(legality, dict) else None
    if not (
        isinstance(acknowledge, dict)
        and acknowledge.get("status") == "available"
        and acknowledge.get("allowed") is False
        and acknowledge.get("reason") == "normal_reply_channel"
    ):
        gaps.append("marriage_normal_reply_channel_mismatch")
    return gaps


def _special_war_snapshot_binding(
    context: dict[str, object],
    active_wars: list[dict[str, object]],
) -> dict[str, object]:
    """Audit the typed special binding against this same snapshot's war row."""

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    binding = special.get("value") if isinstance(special, dict) else None
    roles = context.get("roles")
    routing = context.get("routing")
    war_id = binding.get("war_id") if isinstance(binding, dict) else None
    matching_wars = [war for war in active_wars if war.get("war_id") == war_id]
    responder_role = (
        routing.get("current_responder_role")
        if isinstance(routing, dict)
        else None
    )
    responder_war_role = (
        binding.get(f"{responder_role}_war_role")
        if isinstance(binding, dict) and responder_role in {"actor", "recipient"}
        else None
    )
    expected_player_side = {
        "primary_attacker": "attacker",
        "primary_defender": "defender",
    }.get(responder_war_role)
    other_role = "actor" if responder_role == "recipient" else "recipient"
    expected_opponent_id = (
        roles.get(f"{other_role}_character_id")
        if isinstance(roles, dict) and responder_role in {"actor", "recipient"}
        else None
    )
    role_matched = any(
        war.get("player_side") == expected_player_side
        and war.get("player_is_primary_war_leader") is True
        and war.get("primary_opponent_character_id") == expected_opponent_id
        for war in matching_wars
    )
    return {
        "snapshot_revision": context.get("snapshot_revision"),
        "date_raw": context.get("date_raw"),
        "war_id": war_id,
        "special_interaction_kind": (
            binding.get("special_interaction_kind")
            if isinstance(binding, dict)
            else None
        ),
        "absolute_outcome": (
            binding.get("absolute_outcome")
            if isinstance(binding, dict)
            else None
        ),
        "actor_war_role": (
            binding.get("actor_war_role")
            if isinstance(binding, dict)
            else None
        ),
        "recipient_war_role": (
            binding.get("recipient_war_role")
            if isinstance(binding, dict)
            else None
        ),
        "current_responder_role": responder_role,
        "snapshot_active_war_ids": [war.get("war_id") for war in active_wars],
        "active_war_id_match": bool(matching_wars),
        "active_war_roles_match": role_matched,
        "same_frame_bound": True,
    }


def _degraded_pending_interaction_decision(
    pending: dict[str, object],
    context: dict[str, object],
    *,
    snapshot: dict[str, object],
    active_wars: list[dict[str, object]],
    available_steps: set[str],
) -> dict[str, object]:
    """Choose only the narrow, auditable reply needed to unblock a run.

    Native AI inputs remain an opponent-model reference.  This fallback is a
    player policy: reject ordinary requests when that exact reply is legal;
    accept only when native legality proves every other reply illegal.
    """

    summary = _pending_interaction_summary(pending, context, snapshot)
    legality = context.get("legality")
    candidates: list[dict[str, object]] = []
    for action in ("accept", "reject", "block", "acknowledge"):
        item = legality.get(action) if isinstance(legality, dict) else None
        step = _PENDING_REPLY_STEPS[action]
        candidates.append(
            {
                "action": action,
                "step": step,
                "legality_status": (
                    item.get("status") if isinstance(item, dict) else None
                ),
                "allowed": (
                    item.get("allowed") if isinstance(item, dict) else None
                ),
                "legality_reason": (
                    item.get("reason") if isinstance(item, dict) else None
                ),
                "native_legal": bool(
                    isinstance(item, dict)
                    and item.get("status") == "available"
                    and item.get("allowed") is True
                ),
                "action_reachable": step in available_steps,
            }
        )

    by_action = {str(row["action"]): row for row in candidates}
    evidence_gaps = _pending_interaction_evidence_gaps(
        pending, context, snapshot
    )
    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    special_status = special.get("status") if isinstance(special, dict) else None
    special_reason = special.get("reason") if isinstance(special, dict) else None
    definition = context.get("definition")
    definition_key = (
        definition.get("canonical_key")
        if isinstance(definition, dict)
        else None
    )
    special_present = (
        terms.get("special_data_present") if isinstance(terms, dict) else None
    )
    definition_allowlist_evidence = (
        _DEGRADED_ORDINARY_INTERACTION_ALLOWLIST.get(definition_key)
        if isinstance(definition_key, str)
        else None
    )
    marriage_allowlist_evidence = (
        _DEGRADED_MARRIAGE_REJECT_ONLY_ALLOWLIST.get(definition_key)
        if isinstance(definition_key, str)
        else None
    )
    marriage_contract_gaps = (
        _arrange_marriage_reject_contract_gaps(context)
        if isinstance(marriage_allowlist_evidence, dict)
        else []
    )
    if evidence_gaps:
        classification = "evidence_invalid"
    elif special_status == "available":
        classification = "known_war_exit"
    elif isinstance(marriage_allowlist_evidence, dict):
        classification = "known_marriage_special"
    elif (
        special_status == "unavailable"
        and special_reason == "special_war_binding_not_applicable"
        and special_present is False
        and definition_key not in _KNOWN_WAR_EXIT_INTERACTION_KEYS
        and isinstance(definition_allowlist_evidence, dict)
    ):
        classification = "ordinary_non_war"
    elif (
        special_status == "unavailable"
        and special_reason == "special_war_binding_not_applicable"
        and special_present is False
    ):
        classification = "definition_unclassified"
    else:
        classification = "unclassified_or_special"

    special_binding_audit = (
        _special_war_snapshot_binding(context, active_wars)
        if classification == "known_war_exit"
        else None
    )
    classification_evidence = (
        marriage_allowlist_evidence
        if classification == "known_marriage_special"
        else definition_allowlist_evidence
    )
    decision: dict[str, object] = {
        "rule_id": (
            "arrange-marriage-reject-only-v1"
            if classification == "known_marriage_special"
            else "ordinary-reject-unique-accept-v1"
        ),
        "mode": "degraded_blocker_removal",
        "native_ai_reference": (
            "CK3-1.19.0.6 inbound reply tree: intermediary then recipient "
            "ai_accept; human responder uses exact native reply legality"
        ),
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "semantic_decision_ready": False,
        "context_semantic_decision_ready": summary.get(
            "context_semantic_decision_ready"
        ),
        "classification": classification,
        "frame_binding": summary.get("frame_binding"),
        "pending_interaction_id": summary.get("instance_id"),
        "interaction_key": summary.get("interaction_key"),
        "roles": summary.get("roles"),
        "deadline": summary.get("deadline"),
        "reply_legality": summary.get("reply_legality"),
        "special_war_binding": summary.get("special_war_binding"),
        "special_war_snapshot_binding": special_binding_audit,
        "definition_classification": {
            "policy": (
                "ck3-1.19.0.6-explicit-marriage-special-reject-only-v1"
                if classification == "known_marriage_special"
                else "ck3-1.19.0.6-explicit-ordinary-nonreligious-v1"
            ),
            "definition_key": definition_key,
            "allowlisted": isinstance(classification_evidence, dict),
            "evidence": (
                dict(classification_evidence)
                if isinstance(classification_evidence, dict)
                else None
            ),
        },
        "marriage_contract_gaps": marriage_contract_gaps,
        "missing_semantics": summary.get("missing_semantics"),
        "evidence_gaps": evidence_gaps,
        "candidate_replies": candidates,
        "recommended_action": None,
        "selected_action": None,
        "selected_step": None,
        "blocked_reasons": [],
        "deterministic_rule": (
            (
                "for an exact same-frame arrange_marriage_interaction with a "
                "direct local recipient, complete marriage roles, same-day "
                "deadline, opaque marriage special payload, and six unselected "
                "send options, reject only when native reject is legal and "
                "executable; never fall through to unique accept"
            )
            if classification == "known_marriage_special"
            else (
                "for an exact same-frame request whose definition is explicitly "
                "allowlisted as ordinary non-war and nonreligious, reject when "
                "native reject is legal and executable; accept only when reject, "
                "block, and acknowledge are each natively illegal and accept is "
                "the sole legal executable reply; otherwise submit nothing"
            )
        ),
    }
    blocked_reasons = decision["blocked_reasons"]
    assert isinstance(blocked_reasons, list)

    if classification == "evidence_invalid":
        blocked_reasons.extend(evidence_gaps)
        return {"summary": summary, "decision": decision}
    if classification == "known_war_exit":
        if not (
            isinstance(special_binding_audit, dict)
            and special_binding_audit.get("active_war_id_match") is True
            and special_binding_audit.get("active_war_roles_match") is True
        ):
            blocked_reasons.append("special_war_snapshot_binding_mismatch")
        blocked_reasons.append("special_outcome_terms_unavailable")
        return {"summary": summary, "decision": decision}
    if classification == "known_marriage_special":
        if marriage_contract_gaps:
            blocked_reasons.extend(marriage_contract_gaps)
            return {"summary": summary, "decision": decision}
        reject = by_action["reject"]
        if reject["native_legal"] is not True:
            blocked_reasons.append("marriage_reject_not_native_legal")
            return {"summary": summary, "decision": decision}
        decision["recommended_action"] = "reject"
        if reject["action_reachable"] is True:
            decision["selected_action"] = "reject"
            decision["selected_step"] = reject["step"]
        else:
            blocked_reasons.append("legal_marriage_reject_command_unavailable")
        return {"summary": summary, "decision": decision}
    if classification == "definition_unclassified":
        blocked_reasons.append(
            "interaction_definition_not_explicitly_classified_"
            "nonwar_nonreligious"
        )
        return {"summary": summary, "decision": decision}
    if classification != "ordinary_non_war":
        blocked_reasons.append("interaction_war_or_special_semantics_unclassified")
        return {"summary": summary, "decision": decision}

    reject = by_action["reject"]
    if reject["native_legal"] is True:
        decision["recommended_action"] = "reject"
        if reject["action_reachable"] is True:
            decision["selected_action"] = "reject"
            decision["selected_step"] = reject["step"]
        else:
            blocked_reasons.append("legal_reject_command_unavailable")
        return {"summary": summary, "decision": decision}

    reject_proven_illegal = (
        reject["legality_status"] == "available" and reject["allowed"] is False
    )
    accept = by_action["accept"]
    other_replies_proven_illegal = all(
        by_action[action]["legality_status"] == "available"
        and by_action[action]["allowed"] is False
        for action in ("block", "acknowledge")
    )
    if (
        reject_proven_illegal
        and accept["native_legal"] is True
        and other_replies_proven_illegal
    ):
        decision["recommended_action"] = "accept"
        if accept["action_reachable"] is True:
            decision["selected_action"] = "accept"
            decision["selected_step"] = accept["step"]
        else:
            blocked_reasons.append("unique_legal_accept_command_unavailable")
        return {"summary": summary, "decision": decision}

    if not reject_proven_illegal:
        blocked_reasons.append("reject_not_proven_illegal")
    if accept["native_legal"] is not True:
        blocked_reasons.append("accept_not_legal")
    if not other_replies_proven_illegal:
        blocked_reasons.append("accept_not_unique_legal_reply")
    return {"summary": summary, "decision": decision}


def _degraded_pending_interaction_plan(
    result: dict[str, object],
) -> dict[str, object]:
    summary = result["summary"]
    decision = result["decision"]
    assert isinstance(summary, dict)
    assert isinstance(decision, dict)
    selected_step = decision.get("selected_step")
    selected_action = decision.get("selected_action")
    if selected_action == "reject":
        if decision.get("classification") == "known_marriage_special":
            phase = "pending_arrange_marriage_reject_only"
            reason = (
                "reject this exact direct zero-option marriage proposal: "
                "native reject is same-frame legal and executable, while "
                "accept lacks a secondary-pair semantic postcondition"
            )
        else:
            phase = "pending_character_interaction_degraded_reject"
            reason = (
                "reject this exact ordinary non-war request: native reject is "
                "same-frame legal and the reject command is executable"
            )
    elif selected_action == "accept":
        phase = "pending_character_interaction_degraded_unique_accept"
        reason = (
            "accept this exact ordinary non-war request only because native "
            "legality proves reject, block, and acknowledge illegal, leaving "
            "accept as the sole executable legal reply"
        )
    else:
        phase = (
            "pending_war_interaction_evidence_required"
            if decision.get("classification") == "known_war_exit"
            else "pending_character_interaction_degraded_blocked"
        )
        reasons = decision.get("blocked_reasons")
        reason = (
            "pending interaction degraded policy submitted no reply: "
            + ", ".join(str(item) for item in reasons)
            if isinstance(reasons, list) and reasons
            else "pending interaction has no proven executable degraded reply"
        )
    plan: dict[str, object] = {
        "policy": "one-life-turn-v1",
        "phase": phase,
        "selected_step": selected_step,
        "reason": reason,
        "pending_character_interaction": summary,
        "decision": decision,
    }
    if selected_step is None:
        recommended_action = decision.get("recommended_action")
        recommended = (
            _PENDING_REPLY_STEPS.get(str(recommended_action))
            if isinstance(recommended_action, str)
            else None
        )
        if isinstance(recommended, str):
            plan["required_step"] = recommended
        if decision.get("classification") == "known_war_exit":
            plan["required_capabilities"] = [
                "game.state.pending-character-interaction-special-outcome-terms",
                "game.policy.pending-character-interaction-war-outcome-decision",
            ]
        elif decision.get("classification") != "ordinary_non_war":
            plan["required_capabilities"] = [
                "game.state.pending-character-interaction-structured-terms",
                "game.policy.pending-character-interaction-semantic-decision",
            ]
    return plan


def _same_frame_event_window_context(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
) -> dict[str, object] | None:
    """Recover a typed window only when every public/native frame key matches."""

    if not isinstance(snapshot, dict):
        return None
    active_event = snapshot.get("active_event", snapshot.get("current_event"))
    event_id = (
        active_event.get("instance_id")
        if isinstance(active_event, dict)
        else None
    )
    revision = snapshot.get("revision")
    native_revision = snapshot.get("native_revision")
    snapshot_id = snapshot.get("snapshot_id")
    date_raw = snapshot.get("date_raw")
    if (
        isinstance(event_id, bool)
        or not isinstance(event_id, int)
        or not 1 <= event_id <= 2**31 - 1
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or isinstance(native_revision, bool)
        or not isinstance(native_revision, int)
        or not 1 <= native_revision <= 2**64 - 1
        or not isinstance(snapshot_id, str)
        or not snapshot_id
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not -(2**31) <= date_raw <= 2**31 - 1
    ):
        return None

    for row in reversed(rows):
        if (
            _effective_command(row)
            != QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
            or row.get("ok") is not True
        ):
            continue
        result = _effective_command_result(row)
        context = (
            result.get("current_event_window_context")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(result, dict)
            and isinstance(context, dict)
            and result.get("step")
            == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
            and result.get("accepted") is True
            and result.get("status") == context.get("status")
            and result.get("queried_snapshot_id") == snapshot_id
            and result.get("queried_revision") == revision
            and result.get("queried_native_revision") == native_revision
            and result.get("snapshot_revision") == native_revision
            and result.get("current_event_instance_id") == event_id
            and result.get("date_raw") == date_raw
            and context.get("snapshot_revision") == native_revision
            and context.get("current_event_instance_id") == event_id
            and context.get("date_raw") == date_raw
        ):
            continue
        try:
            return normalize_current_event_window_context_v1(
                context,
                expected_event_instance_id=event_id,
                expected_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError:
            continue
    return None


def _has_explicit_played_character_death_indicator(
    option: dict[str, object],
) -> bool:
    """Return true only for the narrow death signal the live wire exposes."""

    indicators = option.get("effect_indicators")
    rows = indicators.get("rows") if isinstance(indicators, dict) else None
    return bool(
        isinstance(rows, list)
        and any(
            isinstance(row, dict)
            and row.get("kind") == "death"
            and row.get("subject") == "played_character"
            for row in rows
        )
    )


def _degraded_event_option_decision(
    eligible_options: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    """Choose a bounded event fallback and return its complete audit record.

    The caller supplies only same-frame, materialized ``shown && enabled``
    rows.  Missing lossy indicators are never interpreted as proof of safety.
    """

    if not eligible_options:
        raise ValueError("degraded event choice requires an eligible option")
    ordered = sorted(
        eligible_options, key=lambda option: int(option["native_option_index"])
    )
    explicit_death = [
        option
        for option in ordered
        if _has_explicit_played_character_death_indicator(option)
    ]
    without_explicit_death = [
        option
        for option in ordered
        if not _has_explicit_played_character_death_indicator(option)
    ]
    death_avoidance_applied = bool(explicit_death and without_explicit_death)
    after_death_filter = (
        without_explicit_death if death_avoidance_applied else ordered
    )
    non_cancel = [
        option
        for option in after_death_filter
        if option.get("cancel") is not True
    ]
    cancel_deprioritization_applied = bool(
        non_cancel and len(non_cancel) != len(after_death_filter)
    )
    final_candidates = non_cancel if non_cancel else after_death_filter
    selected = final_candidates[0]
    native_index = int(selected["native_option_index"])
    decision = {
        "policy": "shown-enabled-death-cancel-native-order-v1",
        "mode": (
            "forced_presentation"
            if len(ordered) == 1
            else "degraded_blocker_removal"
        ),
        "native_ai_reference": "CK3-1.19.0.6 selector RVA 0x33E71B0",
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "semantic_decision_ready": False,
        "eligible_native_option_indices": [
            int(option["native_option_index"]) for option in ordered
        ],
        "explicit_player_death_native_option_indices": [
            int(option["native_option_index"]) for option in explicit_death
        ],
        "cancel_native_option_indices": [
            int(option["native_option_index"])
            for option in ordered
            if option.get("cancel") is True
        ],
        "death_avoidance_applied": death_avoidance_applied,
        "cancel_deprioritization_applied": cancel_deprioritization_applied,
        "final_candidate_native_option_indices": [
            int(option["native_option_index"])
            for option in final_candidates
        ],
        "selected_native_option_index": native_index,
        "selected_rendered_index": selected.get("rendered_index"),
        "missing_semantic_inputs": [
            "complete_effect_preview",
            "resource_deltas",
            "relationship_deltas",
            "native_ai_option_weights",
            "campaign_utility_score",
        ],
        "deterministic_rule": (
            "avoid an explicitly indicated played-character death when an "
            "alternative exists; then prefer a non-cancel option when one "
            "exists; then choose the lowest authored native index"
        ),
    }
    return selected, decision


def _battle_control_query_records(
    rows: list[dict[str, object]],
    *,
    position_offset: int = 0,
) -> list[dict[str, object]]:
    """Recover strict battle frames and their factual history bindings."""
    records: list[dict[str, object]] = []
    for position, row in enumerate(rows, start=position_offset + 1):
        subject = parse_query_battle_control_snapshot_v1_step(
            _effective_command(row)
        )
        if subject is None or row.get("ok") is not True:
            continue
        result = _effective_command_result(row)
        if not isinstance(result, dict):
            continue
        queried_revision = _native_int(result.get("queried_revision"))
        queried_native_revision = _native_int(
            result.get("queried_native_revision")
        )
        queried_snapshot_id = result.get("queried_snapshot_id")
        query_sequence = result.get("query_sequence")
        frame = result.get("battle_control_snapshot")
        if not (
            result.get("step") == _effective_command(row)
            and result.get("accepted") is True
            and result.get("status") == "available"
            and queried_revision is not None
            and queried_revision >= 0
            and queried_native_revision is not None
            and queried_native_revision > 0
            and isinstance(queried_snapshot_id, str)
            and bool(queried_snapshot_id)
            and isinstance(query_sequence, int)
            and not isinstance(query_sequence, bool)
            and query_sequence > 0
            and isinstance(frame, dict)
            and result.get("snapshot_revision")
            == queried_native_revision
        ):
            continue
        observed_date_raw = frame.get("observed_date_raw")
        if (
            isinstance(observed_date_raw, bool)
            or not isinstance(observed_date_raw, int)
        ):
            continue
        try:
            normalized = normalize_battle_control_snapshot_v1(
                frame,
                expected_subject_public_cunit_id=subject,
                expected_observed_date_raw=observed_date_raw,
                expected_snapshot_revision=queried_native_revision,
            )
        except ValueError:
            continue
        records.append(
            {
                "position": position,
                "subject_army_id": subject,
                "queried_snapshot_id": queried_snapshot_id,
                "queried_revision": queried_revision,
                "queried_native_revision": queried_native_revision,
                "query_sequence": query_sequence,
                "frame": normalized,
            }
        )
    return records


def _current_battle_control_frames(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
    *,
    position_offset: int = 0,
) -> tuple[dict[int, dict[str, object]], list[dict[str, object]]]:
    """Return only available frames bound to the current paused revision."""
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return {}, _battle_control_query_records(
            rows, position_offset=position_offset
        )
    snapshot_id = snapshot.get("snapshot_id")
    revision = _native_int(snapshot.get("revision"))
    native_revision = _native_int(snapshot.get("native_revision"))
    date_raw = snapshot.get("date_raw")
    if not (
        isinstance(snapshot_id, str)
        and bool(snapshot_id)
        and revision is not None
        and revision >= 0
        and native_revision is not None
        and native_revision > 0
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
    ):
        return {}, _battle_control_query_records(
            rows, position_offset=position_offset
        )

    records = _battle_control_query_records(
        rows, position_offset=position_offset
    )
    current: dict[int, dict[str, object]] = {}
    for record in records:
        frame = record["frame"]
        if (
            record.get("queried_snapshot_id") == snapshot_id
            and record.get("queried_revision") == revision
            and record.get("queried_native_revision") == native_revision
            and isinstance(frame, dict)
            and frame.get("observed_date_raw") == date_raw
        ):
            current[int(record["subject_army_id"])] = record

    direct_frame = snapshot.get("battle_control_snapshot_v1")
    direct_subject = _native_int(
        snapshot.get("battle_control_snapshot_v1_subject_army_id")
    )
    direct_sequence = snapshot.get(
        "battle_control_snapshot_v1_query_sequence"
    )
    if (
        snapshot.get("battle_control_snapshot_v1_status") == "available"
        and direct_subject is not None
        and direct_subject > 0
        and snapshot.get("battle_control_snapshot_v1_queried_snapshot_id")
        == snapshot_id
        and snapshot.get("battle_control_snapshot_v1_queried_revision")
        == revision
        and isinstance(direct_sequence, int)
        and not isinstance(direct_sequence, bool)
        and direct_sequence > 0
        and isinstance(direct_frame, dict)
    ):
        try:
            normalized = normalize_battle_control_snapshot_v1(
                direct_frame,
                expected_subject_public_cunit_id=direct_subject,
                expected_observed_date_raw=date_raw,
                expected_snapshot_revision=native_revision,
            )
        except ValueError:
            pass
        else:
            matching_positions = [
                int(record["position"])
                for record in records
                if record.get("subject_army_id") == direct_subject
                and record.get("queried_snapshot_id") == snapshot_id
                and record.get("queried_revision") == revision
                and record.get("queried_native_revision") == native_revision
                and record.get("query_sequence") == direct_sequence
            ]
            current[direct_subject] = {
                "position": max(matching_positions, default=0),
                "subject_army_id": direct_subject,
                "queried_snapshot_id": snapshot_id,
                "queried_revision": revision,
                "queried_native_revision": native_revision,
                "query_sequence": direct_sequence,
                "frame": normalized,
            }
    return current, records


def _battle_terminal_transition_query_records(
    rows: list[dict[str, object]],
    *,
    position_offset: int = 0,
) -> list[dict[str, object]]:
    """Recover strict journal queries with their paused-frame bindings."""

    records: list[dict[str, object]] = []
    for position, row in enumerate(rows, start=position_offset + 1):
        request = parse_query_battle_terminal_transition_v1_step(
            _effective_command(row)
        )
        if request is None or row.get("ok") is not True:
            continue
        result = _effective_command_result(row)
        if not isinstance(result, dict):
            continue
        queried_revision = _native_int(result.get("queried_revision"))
        queried_native_revision = _native_int(
            result.get("queried_native_revision")
        )
        queried_snapshot_id = result.get("queried_snapshot_id")
        query_sequence = _native_int(result.get("query_sequence"))
        frame = result.get("battle_terminal_transition")
        if not (
            result.get("step") == _effective_command(row)
            and result.get("accepted") is True
            and result.get("status") in {"available", "unavailable"}
            and queried_revision is not None
            and queried_revision >= 0
            and queried_native_revision is not None
            and queried_native_revision > 0
            and isinstance(queried_snapshot_id, str)
            and bool(queried_snapshot_id)
            and query_sequence is not None
            and query_sequence > 0
            and isinstance(frame, dict)
            and result.get("snapshot_revision")
            == queried_native_revision
        ):
            continue
        observed_date_raw = _native_int(frame.get("observed_date_raw"))
        if observed_date_raw is None:
            continue
        combat_id, subject, cursor = request
        try:
            normalized = normalize_battle_terminal_transition_v1(
                frame,
                expected_prior_combat_id=combat_id,
                expected_subject_public_cunit_id=subject,
                expected_after_terminal_sequence=cursor,
                expected_observed_date_raw=observed_date_raw,
                expected_snapshot_revision=queried_native_revision,
            )
        except ValueError:
            continue
        if normalized.get("status") != result.get("status"):
            continue
        records.append(
            {
                "position": position,
                "combat_id": combat_id,
                "subject_army_id": subject,
                "after_terminal_sequence": cursor,
                "queried_snapshot_id": queried_snapshot_id,
                "queried_revision": queried_revision,
                "queried_native_revision": queried_native_revision,
                "query_sequence": query_sequence,
                "frame": normalized,
            }
        )
    return records


def _current_battle_terminal_cursor(
    records: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    combat_id: int,
    subject_army_id: int,
) -> dict[str, object] | None:
    """Return a positive pre-arm journal cursor from this exact frame."""

    snapshot_id = snapshot.get("snapshot_id")
    revision = _native_int(snapshot.get("revision"))
    native_revision = _native_int(snapshot.get("native_revision"))
    date_raw = _native_int(snapshot.get("date_raw"))
    candidates: list[dict[str, object]] = []
    for record in records:
        frame = record.get("frame")
        journal = frame.get("terminal_journal") if isinstance(frame, dict) else None
        prior = frame.get("prior") if isinstance(frame, dict) else None
        latest_sequence = (
            _native_int(journal.get("latest_sequence"))
            if isinstance(journal, dict)
            else None
        )
        if (
            record.get("combat_id") == combat_id
            and record.get("subject_army_id") == subject_army_id
            and record.get("after_terminal_sequence") is None
            and record.get("queried_snapshot_id") == snapshot_id
            and record.get("queried_revision") == revision
            and record.get("queried_native_revision") == native_revision
            and isinstance(frame, dict)
            and frame.get("status") == "available"
            and frame.get("battle_terminal_transition_ready") is True
            and frame.get("observed_date_raw") == date_raw
            and isinstance(journal, dict)
            and journal.get("requested_after_sequence") is None
            and journal.get("event_status") == "not_observed"
            and journal.get("event_sequence") is None
            and latest_sequence is not None
            and latest_sequence > 0
            and isinstance(prior, dict)
            and prior.get("combat_id") == combat_id
            and prior.get("terminal_kind") == "active_not_terminal"
        ):
            candidates.append(
                {
                    "position": record.get("position"),
                    "combat_id": combat_id,
                    "subject_army_id": subject_army_id,
                    "after_terminal_sequence": latest_sequence,
                }
            )
    return candidates[-1] if candidates else None


def _is_battle_timeline_advance_step(step: object) -> bool:
    return is_life_advance_step(step)


def _battle_sentinel_advance_validation(
    advance_result: dict[str, object] | None,
) -> dict[str, object] | None:
    """Validate the complete native-stop envelope for a composite advance."""

    if not isinstance(advance_result, dict):
        return None
    step = advance_result.get("step")
    decision_target = parse_battle_decision_epoch_advance_step(step)
    expected = (
        (3, "decision_epoch")
        if decision_target is not None
        or step == _BATTLE_DECISION_EPOCH_ADVANCE_STEP
        else (5, "terminal_or_sentinel")
        if step == _BATTLE_TERMINAL_CRUISE_STEP
        else None
    )
    if expected is None:
        return None
    expected_speed, expected_mode = expected
    sentinel = advance_result.get("tactical_daily_sentinel")
    start = _native_int(advance_result.get("starting_date_raw"))
    target = _native_int(advance_result.get("target_date_raw"))
    end = _native_int(advance_result.get("ending_date_raw"))
    elapsed = _native_int(advance_result.get("elapsed_days"))
    watch = advance_result.get("watch_army_ids")
    armed = advance_result.get("armed_tactical_daily_sentinel")
    reasons = sentinel.get("trigger_reasons") if isinstance(sentinel, dict) else None
    ticks = (
        _native_int(sentinel.get("completed_daily_ticks"))
        if isinstance(sentinel, dict)
        else None
    )
    generation = (
        _native_int(sentinel.get("generation"))
        if isinstance(sentinel, dict)
        else None
    )
    trigger_flags = (
        _native_int(sentinel.get("trigger_flags"))
        if isinstance(sentinel, dict)
        else None
    )
    combat_count = (
        _native_int(sentinel.get("combat_count"))
        if isinstance(sentinel, dict)
        else None
    )
    errors: list[str] = []
    if not (
        isinstance(watch, list)
        and 0 < len(watch) <= _BATTLE_SENTINEL_MAX_WATCH_ARMIES
        and all(
            _native_int(item) is not None
            and 0 < int(item) <= 2**31 - 1
            for item in watch
        )
        and len(set(watch)) == len(watch)
    ):
        errors.append("watch_set_invalid")
    if not (
        start is not None
        and target is not None
        and end is not None
        and elapsed is not None
        and ticks is not None
        and elapsed > 0
        and 1
        <= (target - start) // 24
        <= _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS
        and (target - start) % 24 == 0
        and (
            target == decision_target
            if decision_target is not None
            else target
            == start + _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS * 24
        )
        and start + elapsed * 24 == end
        and start + ticks * 24 == end
        and elapsed == ticks
        and end <= target
    ):
        errors.append("date_tick_reconciliation_failed")
    if not (
        isinstance(sentinel, dict)
        and sentinel.get("state") == "triggered"
        and generation is not None
        and generation > 0
        and sentinel.get("starting_date_raw") == start
        and sentinel.get("target_date_raw") == target
        and sentinel.get("last_observed_date_raw") == end
        and sentinel.get("trigger_date_raw") == end
        and sentinel.get("speed") == expected_speed
        and sentinel.get("mode") == expected_mode
        and sentinel.get("army_count") == len(watch or [])
        and combat_count is not None
        and combat_count > 0
        and trigger_flags is not None
        and trigger_flags > 0
        and isinstance(reasons, list)
        and bool(reasons)
        and all(isinstance(reason, str) and reason for reason in reasons)
        and sentinel.get("signed_date_delta_from_target_raw")
        == (end - target if end is not None and target is not None else None)
        and sentinel.get("overshoot_days") == 0
        and sentinel.get("intermediate_pause_count")
        == (1 if "native_pause" in (reasons or []) else 0)
        and sentinel.get("pause_observed") is True
        and sentinel.get("abnormal") is False
        and advance_result.get("timeline_speed") == expected_speed
        and advance_result.get("paused") is True
    ):
        errors.append("sentinel_completion_invalid")
    if not (
        isinstance(armed, dict)
        and armed.get("state") == "armed"
        and armed.get("generation") == generation
        and armed.get("starting_date_raw") == start
        and armed.get("target_date_raw") == target
        and armed.get("last_observed_date_raw") == start
        and armed.get("trigger_date_raw") == 0
        and armed.get("speed") == expected_speed
        and armed.get("mode") == expected_mode
        and armed.get("army_count") == len(watch or [])
        and armed.get("combat_count") == combat_count
        and armed.get("completed_daily_ticks") == 0
        and armed.get("intermediate_pause_count") == 0
        and armed.get("trigger_flags") == 0
        and armed.get("trigger_reasons") == []
        and armed.get("signed_date_delta_from_target_raw") == 0
        and armed.get("overshoot_days") == -1
        and armed.get("pause_wrapper_called") is False
        and armed.get("pause_observed") is False
        and armed.get("terminal_observed") is False
        and armed.get("abnormal") is False
    ):
        errors.append("sentinel_arm_invalid")
    terminal_flag = (
        sentinel.get("terminal_observed")
        if isinstance(sentinel, dict)
        else None
    )
    if not isinstance(terminal_flag, bool) or (
        terminal_flag != ("combat_terminal" in (reasons or []))
    ):
        errors.append("terminal_flag_disagrees")
    cleanup = advance_result.get("managed_failure_cleanup")
    if not (
        advance_result.get("progress_status") == "postcondition"
        and advance_result.get("requested_horizon_days")
        == (
            (target - start) // 24
            if target is not None and start is not None
            else None
        )
        and advance_result.get("timeline_policy") == expected_mode
        and advance_result.get("sentinel_mode") == expected_mode
        and advance_result.get("stop_kind")
        == ("terminal" if terminal_flag is True else "decision_epoch")
        and advance_result.get("terminal_reached") is terminal_flag
        and advance_result.get("trigger_reasons") == reasons
        and isinstance(sentinel, dict)
        and advance_result.get("sentinel_generation")
        == sentinel.get("generation")
        and advance_result.get("completed_daily_ticks") == ticks
        and advance_result.get("intermediate_pause_count")
        == (1 if "native_pause" in (reasons or []) else 0)
        and advance_result.get("overshoot_days") == 0
        and advance_result.get("zero_intermediate_pause")
        is ("native_pause" not in (reasons or []))
        and advance_result.get("external_pause_count") == 0
        and advance_result.get("external_rich_query_count") == 0
        and isinstance(cleanup, dict)
        and cleanup.get("attempted") is False
        and cleanup.get("error") is None
    ):
        errors.append("composite_completion_invalid")
    if isinstance(reasons, list) and (
        ("date_deadline" in reasons) is not (end == target)
    ):
        errors.append("deadline_reason_disagrees")
    if isinstance(reasons, list) and isinstance(sentinel, dict) and (
        sentinel.get("pause_wrapper_called")
        is not ("native_pause" not in reasons)
    ):
        errors.append("pause_wrapper_not_called")
    return {
        "valid": not errors,
        "errors": errors,
        "step": step,
        "actual_elapsed_days": elapsed,
        "terminal_observed": terminal_flag,
        "watch_army_ids": list(watch) if isinstance(watch, list) else None,
    }


def _cursor_bound_terminal_transition(
    rows: list[dict[str, object]],
    *,
    previous_advance_position: int,
    advance_position: int,
    before_record: dict[str, object],
    snapshot: dict[str, object],
    advance_result: dict[str, object] | None,
) -> dict[str, object]:
    """Require a pre-arm cursor and its exact post-stop terminal event."""

    before = before_record.get("frame")
    if not isinstance(before, dict):
        return {
            "status": "invalid",
            "reason": "the terminal cruise lacks a normalized pre-arm frame",
        }
    combat_id = int(before["combat_id"])
    transition_subject = int(before["subject_public_cunit_id"])
    sentinel_validation = _battle_sentinel_advance_validation(advance_result)
    if not (
        isinstance(sentinel_validation, dict)
        and sentinel_validation.get("valid") is True
        and sentinel_validation.get("step") == _BATTLE_TERMINAL_CRUISE_STEP
        and sentinel_validation.get("terminal_observed") is True
    ):
        return {
            "status": "invalid",
            "reason": (
                "the subject left combat after a terminal cruise without a "
                "complete native terminal sentinel result"
            ),
            "sentinel_validation": sentinel_validation,
        }

    records = _battle_terminal_transition_query_records(rows)
    pre_cursor_records: list[dict[str, object]] = []
    for record in records:
        frame = record.get("frame")
        journal = frame.get("terminal_journal") if isinstance(frame, dict) else None
        prior = frame.get("prior") if isinstance(frame, dict) else None
        latest = (
            _native_int(journal.get("latest_sequence"))
            if isinstance(journal, dict)
            else None
        )
        if (
            previous_advance_position < int(record["position"])
            < advance_position
            and record.get("combat_id") == combat_id
            and record.get("after_terminal_sequence") is None
            and record.get("queried_snapshot_id")
            == before_record.get("queried_snapshot_id")
            and record.get("queried_revision")
            == before_record.get("queried_revision")
            and record.get("queried_native_revision")
            == before_record.get("queried_native_revision")
            and isinstance(frame, dict)
            and frame.get("status") == "available"
            and frame.get("observed_date_raw")
            == before.get("observed_date_raw")
            and isinstance(journal, dict)
            and journal.get("requested_after_sequence") is None
            and journal.get("event_status") == "not_observed"
            and journal.get("event_sequence") is None
            and latest is not None
            and latest > 0
            and isinstance(prior, dict)
            and prior.get("combat_id") == combat_id
            and prior.get("terminal_kind") == "active_not_terminal"
        ):
            pre_cursor_records.append(
                {**record, "frozen_after_terminal_sequence": latest}
            )
    if not pre_cursor_records:
        return {
            "status": "invalid",
            "reason": (
                "the terminal cruise was not bound to a positive pre-arm "
                "terminal journal cursor"
            ),
        }
    cursor_record = min(
        pre_cursor_records,
        key=lambda record: (
            int(record["subject_army_id"]),
            -int(record["position"]),
        ),
    )
    cursor = int(cursor_record["frozen_after_terminal_sequence"])
    journal_subject = int(cursor_record["subject_army_id"])
    query_step = query_battle_terminal_transition_v1_step(
        combat_id, journal_subject, cursor
    )
    current_snapshot_id = snapshot.get("snapshot_id")
    current_revision = _native_int(snapshot.get("revision"))
    current_native_revision = _native_int(snapshot.get("native_revision"))
    current_date = _native_int(snapshot.get("date_raw"))
    matching = [
        record
        for record in records
        if int(record["position"]) > advance_position
        and record.get("combat_id") == combat_id
        and record.get("subject_army_id") == journal_subject
        and record.get("after_terminal_sequence") == cursor
        and record.get("queried_snapshot_id") == current_snapshot_id
        and record.get("queried_revision") == current_revision
        and record.get("queried_native_revision") == current_native_revision
        and isinstance(record.get("frame"), dict)
        and record["frame"].get("observed_date_raw") == current_date
    ]
    if not matching:
        attempted = any(
            int(position) > advance_position
            and _effective_command(row) == query_step
            for position, row in enumerate(rows, start=1)
        )
        return {
            "status": "invalid" if attempted else "query_required",
            "reason": (
                "the cursor-bound terminal query was attempted but did not "
                "produce a valid current-frame result"
                if attempted
                else "query the terminal journal after the native stop"
            ),
            "step": query_step,
            "combat_id": combat_id,
            "subject_army_id": journal_subject,
            "transition_subject_army_id": transition_subject,
            "after_terminal_sequence": cursor,
        }

    terminal = matching[-1]["frame"]
    journal = terminal.get("terminal_journal")
    prior = terminal.get("prior")
    event_sequence = (
        _native_int(journal.get("event_sequence"))
        if isinstance(journal, dict)
        else None
    )
    winner_raw = (
        _native_int(prior.get("winner_raw"))
        if isinstance(prior, dict)
        else None
    )
    terminal_date = (
        _native_int(prior.get("terminal_date_raw"))
        if isinstance(prior, dict)
        else None
    )
    expected_terminal_date = (
        _native_int(advance_result.get("ending_date_raw"))
        if isinstance(advance_result, dict)
        else None
    )
    if not (
        terminal.get("status") == "available"
        and terminal.get("battle_terminal_transition_ready") is True
        and terminal.get("prior_combat_id") == combat_id
        and terminal.get("subject_public_cunit_id") == journal_subject
        and isinstance(journal, dict)
        and journal.get("requested_after_sequence") == cursor
        and journal.get("event_status") == "observed"
        and event_sequence is not None
        and event_sequence > cursor
        and isinstance(prior, dict)
        and prior.get("combat_id") == combat_id
        and prior.get("terminal_kind")
        in {"normal_result", "no_normal_result"}
        and terminal_date == expected_terminal_date
        and winner_raw in {0, 1}
    ):
        return {
            "status": "invalid",
            "reason": (
                "the post-stop journal does not prove the same CombatID, "
                "cursor, terminal date, and native winner outcome"
            ),
            "step": query_step,
        }
    return {
        "status": "terminal_journal_observed",
        "subject_army_id": transition_subject,
        "journal_subject_army_id": journal_subject,
        "before_combat_id": combat_id,
        "terminal_date_raw": terminal_date,
        "terminal_journal_sequence": event_sequence,
        "after_terminal_sequence": cursor,
        "outcome": {
            "terminal_kind": prior.get("terminal_kind"),
            "winner_side": "attacker" if winner_raw == 0 else "defender",
            "winner_raw": winner_raw,
            "battle_result_id": prior.get("battle_result_id"),
            "wipe": prior.get("wipe_raw"),
        },
        "successor": terminal.get("successor"),
        "removal": terminal.get("removal"),
        "reason": (
            "a cursor-bound terminal journal event proves the same CombatID "
            "and native outcome at the sentinel stop date"
        ),
    }


def _battle_control_ledger_fingerprint(
    frame: dict[str, object],
) -> tuple[object, ...]:
    """Project the exact retained-entry and participant-hard ledgers."""
    sides: list[object] = []
    for role in ("attacker", "defender"):
        side = frame.get(role)
        if not isinstance(side, dict):
            return ()
        ordered_armies = side.get("ordered_armies")
        army_rows = tuple(
            (
                row.get("native_carmy_id"),
                row.get("public_cunit_id"),
                row.get("owner_character_id"),
                row.get("combat_backlink_id"),
            )
            for row in (
                ordered_armies if isinstance(ordered_armies, list) else []
            )
            if isinstance(row, dict)
        )
        entries: list[object] = []
        for bucket in ("levy_entries", "men_at_arms_entries"):
            raw_entries = side.get(bucket)
            entries.extend(
                (
                    row.get("bucket"),
                    row.get("bucket_index"),
                    row.get("regiment_id"),
                    row.get("native_carmy_id"),
                    row.get("public_cunit_id"),
                    row.get("owner_character_id"),
                    row.get("starting_raw"),
                    row.get("current_fighting_raw"),
                    row.get("soft_casualties_raw"),
                    row.get("fights_in_main_phase"),
                    row.get("hard_casualties_status"),
                    row.get("hard_casualties_raw"),
                )
                for row in (
                    raw_entries if isinstance(raw_entries, list) else []
                )
                if isinstance(row, dict)
            )
        raw_participants = side.get("participant_hard_ledger")
        participants = tuple(
            (
                row.get("row_index"),
                row.get("participant_character_id"),
                row.get("hard_casualties_raw"),
            )
            for row in (
                raw_participants
                if isinstance(raw_participants, list)
                else []
            )
            if isinstance(row, dict)
        )
        sides.append(
            (
                role,
                army_rows,
                tuple(entries),
                participants,
                side.get("derived_current_fighting_raw"),
                side.get("derived_soft_casualties_raw"),
                side.get(
                    "derived_main_fighting_entry_hard_casualties_raw"
                ),
                side.get("non_main_start_minus_current_minus_soft_raw"),
                side.get("participant_hard_total_raw"),
            )
        )
    return tuple(sides)


def _battle_control_transition(
    before: dict[str, object],
    after: dict[str, object],
    advance_result: dict[str, object] | None,
) -> dict[str, object]:
    """Classify one bounded post-advance battle observation."""
    subject = int(after["subject_public_cunit_id"])
    before_combat_id = int(before["combat_id"])
    after_combat_id = int(after["combat_id"])
    before_date = int(before["observed_date_raw"])
    after_date = int(after["observed_date_raw"])
    advance_start = (
        _native_int(advance_result.get("starting_date_raw"))
        if isinstance(advance_result, dict)
        else None
    )
    advance_end = (
        _native_int(advance_result.get("ending_date_raw"))
        if isinstance(advance_result, dict)
        else None
    )
    advance_elapsed = (
        _native_int(advance_result.get("elapsed_days"))
        if isinstance(advance_result, dict)
        else None
    )
    sentinel_validation = _battle_sentinel_advance_validation(advance_result)
    observed_date_delta = after_date - before_date
    common = {
        "subject_army_id": subject,
        "before_combat_id": before_combat_id,
        "after_combat_id": after_combat_id,
        "before_snapshot_revision": int(before["snapshot_revision"]),
        "after_snapshot_revision": int(after["snapshot_revision"]),
        "before_date_raw": before_date,
        "after_date_raw": after_date,
        "observed_date_delta_raw": observed_date_delta,
        "advance_starting_date_raw": advance_start,
        "advance_ending_date_raw": advance_end,
        "advance_elapsed_days": advance_elapsed,
        "before_phase": before["phase"],
        "before_phase_day": int(before["phase_day"]),
        "after_phase": after["phase"],
        "after_phase_day": int(after["phase_day"]),
    }
    if before_combat_id != after_combat_id:
        return {
            **common,
            "status": "combat_replaced",
            "reason": (
                "the prior CombatID left the subject and a different active "
                "CombatID is now bound to it"
            ),
        }
    if (
        before.get("subject_native_carmy_id")
        != after.get("subject_native_carmy_id")
        or before.get("province_id") != after.get("province_id")
    ):
        return {
            **common,
            "status": "invalid",
            "reason": "same-CombatID subject identity or province changed",
        }

    before_revision = int(before["snapshot_revision"])
    after_revision = int(after["snapshot_revision"])
    if after_revision <= before_revision:
        return {
            **common,
            "status": "invalid",
            "reason": "the post-advance native revision did not increase",
        }
    if not isinstance(advance_result, dict) or (
        advance_result.get("step") != "life-advance"
        and sentinel_validation is None
    ) or advance_start is None or advance_end is None or advance_elapsed is None:
        return {
            **common,
            "status": "invalid",
            "reason": (
                "the bounded battle advance did not report an exact "
                "life-advance or native-sentinel start/end/elapsed result"
            ),
        }
    if (
        isinstance(sentinel_validation, dict)
        and sentinel_validation.get("valid") is not True
    ):
        return {
            **common,
            "status": "invalid",
            "reason": (
                "the native battle sentinel result is incomplete, overshot, "
                "or failed exact date/tick reconciliation"
            ),
            "sentinel_validation": sentinel_validation,
        }
    if advance_start != before_date or advance_end != after_date:
        return {
            **common,
            "status": "invalid",
            "reason": (
                "the bounded battle advance result does not match the "
                "observed battle dates"
            ),
        }
    if observed_date_delta <= 0 or observed_date_delta % 24 != 0:
        return {
            **common,
            "status": "invalid",
            "reason": (
                "the observed battle date delta is not a positive whole "
                "game day"
            ),
        }
    actual_elapsed_days = observed_date_delta // 24
    common["actual_elapsed_days"] = actual_elapsed_days
    if advance_elapsed != actual_elapsed_days:
        return {
            **common,
            "status": "invalid",
            "reason": (
                "the bounded battle advance elapsed_days does not match "
                "its exact date delta"
            ),
        }
    if sentinel_validation is None and actual_elapsed_days not in (1, 2):
        return {
            **common,
            "status": "invalid",
            "reason": (
                "the battle observation exceeded the proven two-day "
                "pause-settle envelope"
            ),
        }

    before_phase = int(before["phase_raw"])
    after_phase = int(after["phase_raw"])
    before_day = int(before["phase_day"])
    after_day = int(after["phase_day"])
    phase_path_legal = False
    pursuit_reopened_to_main = False
    if after_phase == before_phase:
        phase_path_legal = (
            before_day <= after_day <= before_day + actual_elapsed_days
        )
    elif after_phase == before_phase + 1:
        phase_path_legal = 0 <= after_day <= actual_elapsed_days
    elif (
        before_phase == 2
        and after_phase == 1
        and after.get("winner_side") == "none"
        and after.get("forced_winner_side") == "none"
    ):
        # CK3 can reopen the same CombatID from pursuit into main when a new
        # participant joins.  The live/native tree proves the winner reset;
        # treating this as an ordinary phase regression would freeze a real
        # ongoing battle.
        phase_path_legal = (
            0 <= after_day <= before_day + actual_elapsed_days
        )
        pursuit_reopened_to_main = True
    if not phase_path_legal:
        return {
            **common,
            "status": "invalid",
            "reason": "the phase/day path regressed or skipped a phase/day",
        }

    phase_day_changed = (before_phase, before_day) != (
        after_phase,
        after_day,
    )
    ledger_changed = _battle_control_ledger_fingerprint(
        before
    ) != _battle_control_ledger_fingerprint(after)
    if not (phase_day_changed or ledger_changed):
        return {
            **common,
            "status": "invalid",
            "reason": (
                "ACK/date/revision changed without a phase/day or exact "
                "casualty-ledger transition"
            ),
            "phase_day_changed": False,
            "ledger_changed": False,
        }
    return {
        **common,
        "status": (
            "same_combat_reopened"
            if pursuit_reopened_to_main
            else "same_combat_advanced"
        ),
        "reason": (
            "the same CombatID legally reopened from pursuit into main with "
            "its winner reset"
            if pursuit_reopened_to_main
            else "the same CombatID has a legal bounded phase/day or exact "
            "casualty-ledger transition"
        ),
        "phase_day_changed": phase_day_changed,
        "ledger_changed": ledger_changed,
    }


def _battle_control_frame_summary(
    frame: dict[str, object],
) -> dict[str, object]:
    return {
        "subject_army_id": frame.get("subject_public_cunit_id"),
        "combat_id": frame.get("combat_id"),
        "snapshot_revision": frame.get("snapshot_revision"),
        "observed_date_raw": frame.get("observed_date_raw"),
        "phase": frame.get("phase"),
        "phase_day": frame.get("phase_day"),
        "winner_side": frame.get("winner_side"),
        "finalized": frame.get("finalized"),
        "attacker_current_raw": (
            frame["attacker"].get("derived_current_fighting_raw")
            if isinstance(frame.get("attacker"), dict)
            else None
        ),
        "attacker_soft_raw": (
            frame["attacker"].get("derived_soft_casualties_raw")
            if isinstance(frame.get("attacker"), dict)
            else None
        ),
        "attacker_hard_raw": (
            frame["attacker"].get("participant_hard_total_raw")
            if isinstance(frame.get("attacker"), dict)
            else None
        ),
        "defender_current_raw": (
            frame["defender"].get("derived_current_fighting_raw")
            if isinstance(frame.get("defender"), dict)
            else None
        ),
        "defender_soft_raw": (
            frame["defender"].get("derived_soft_casualties_raw")
            if isinstance(frame.get("defender"), dict)
            else None
        ),
        "defender_hard_raw": (
            frame["defender"].get("participant_hard_total_raw")
            if isinstance(frame.get("defender"), dict)
            else None
        ),
    }


def _battle_control_turn_state(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
    controlled_armies: list[dict[str, object]],
) -> dict[str, object]:
    """Gate combat time advancement on exact pre/post battle frames."""
    scoped = _history_after_latest_restore(rows)
    advance_positions = [
        position
        for position, row in enumerate(scoped, start=1)
        if row.get("ok") is True
        and _is_battle_timeline_advance_step(_effective_command(row))
    ]
    latest_advance = advance_positions[-1] if advance_positions else 0
    previous_advance = advance_positions[-2] if len(advance_positions) > 1 else 0
    latest_advance_result = (
        _effective_command_result(scoped[latest_advance - 1])
        if latest_advance
        else None
    )
    latest_sentinel_validation = _battle_sentinel_advance_validation(
        latest_advance_result
    )
    if (
        isinstance(latest_sentinel_validation, dict)
        and latest_sentinel_validation.get("valid") is not True
    ):
        return {
            "status": "transition_invalid",
            "transition": {
                "status": "invalid",
                "reason": (
                    "the native battle sentinel result is incomplete, "
                    "overshot, or failed exact date/tick reconciliation"
                ),
                "sentinel_validation": latest_sentinel_validation,
            },
            "frame": None,
        }
    relevant_rows = scoped[previous_advance:]
    current_frames, records = _current_battle_control_frames(
        relevant_rows,
        snapshot,
        position_offset=previous_advance,
    )
    pre_advance: dict[int, dict[str, object]] = {}
    if latest_advance:
        for record in records:
            position = int(record["position"])
            subject = int(record["subject_army_id"])
            if previous_advance < position < latest_advance:
                pre_advance[subject] = record

    army_by_id = {
        army_id: army
        for army in controlled_armies
        if (army_id := _native_int(army.get("army_id"))) is not None
    }
    all_armies = (
        snapshot.get("player_armies")
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("player_armies"), list)
        else []
    )
    all_army_by_id = {
        army_id: army
        for army in all_armies
        if isinstance(army, dict)
        and (army_id := _native_int(army.get("army_id"))) is not None
    }
    active_subjects = sorted(
        army_id
        for army_id, army in army_by_id.items()
        if _army_tactical_state(army) == "combat"
    )

    recognized: list[dict[str, object]] = []
    recognized_subjects: set[int] = set()
    for subject, record in sorted(pre_advance.items()):
        if subject in active_subjects:
            continue
        observed_army = all_army_by_id.get(subject)
        observed_state = (
            _army_tactical_state(observed_army)
            if isinstance(observed_army, dict)
            else None
        )
        before = record["frame"]
        if (
            isinstance(latest_advance_result, dict)
            and latest_advance_result.get("step")
            == _BATTLE_TERMINAL_CRUISE_STEP
        ):
            terminal = _cursor_bound_terminal_transition(
                scoped,
                previous_advance_position=previous_advance,
                advance_position=latest_advance,
                before_record=record,
                snapshot=snapshot,
                advance_result=latest_advance_result,
            )
            if terminal.get("status") == "query_required":
                return {
                    **terminal,
                    "status": "terminal_query_required",
                }
            if terminal.get("status") == "invalid":
                return {
                    "status": "transition_invalid",
                    "transition": terminal,
                    "frame": _battle_control_frame_summary(before),
                }
            recognized.append(terminal)
        else:
            recognized.append(
                {
                    "status": "left_combat",
                    "subject_army_id": subject,
                    "before_combat_id": before.get("combat_id"),
                    "before_snapshot_revision": before.get(
                        "snapshot_revision"
                    ),
                    "before_phase": before.get("phase"),
                    "before_phase_day": before.get("phase_day"),
                    "observed_army_state": observed_state or "absent",
                    "reason": (
                        "the post-advance semantic army state explicitly "
                        "shows that the queried subject left active combat; "
                        "this is a terminal/removal discriminant and does "
                        "not infer a winner"
                    ),
                }
            )
        recognized_subjects.add(subject)
    if recognized:
        remove_positions = {
            position
            for position, row in enumerate(scoped, start=1)
            if previous_advance < position < latest_advance
            and parse_query_battle_control_snapshot_v1_step(
                _effective_command(row)
            )
            in recognized_subjects
        }
        return {
            "status": "transition_recognized",
            "transitions": recognized,
            "remaining_rows": [
                row
                for position, row in enumerate(scoped, start=1)
                if position not in remove_positions
            ],
        }

    if not active_subjects:
        return {"status": "not_in_combat", "evidence": []}
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return {
            "status": "wait_for_pause",
            "subject_army_ids": active_subjects,
        }

    for subject in active_subjects:
        if subject not in current_frames:
            try:
                step = query_battle_control_snapshot_v1_step(subject)
            except ValueError:
                return {
                    "status": "invalid_subject",
                    "subject_army_id": subject,
                }
            return {
                "status": "query_required",
                "subject_army_id": subject,
                "step": step,
            }

    transitions: list[dict[str, object]] = []
    replaced_subjects: set[int] = set()
    for subject in active_subjects:
        frame = current_frames[subject]["frame"]
        if (
            frame.get("finalized") is True
            or frame.get("phase") == "done"
        ):
            before_record = pre_advance.get(subject)
            if (
                isinstance(latest_advance_result, dict)
                and latest_advance_result.get("step")
                == _BATTLE_TERMINAL_CRUISE_STEP
            ):
                if not isinstance(before_record, dict):
                    return {
                        "status": "transition_invalid",
                        "transition": {
                            "status": "invalid",
                            "reason": (
                                "the finalized terminal-cruise frame lacks "
                                "its pre-arm CombatID observation"
                            ),
                        },
                        "frame": _battle_control_frame_summary(frame),
                    }
                terminal = _cursor_bound_terminal_transition(
                    scoped,
                    previous_advance_position=previous_advance,
                    advance_position=latest_advance,
                    before_record=before_record,
                    snapshot=snapshot,
                    advance_result=latest_advance_result,
                )
                if terminal.get("status") == "query_required":
                    return {
                        **terminal,
                        "status": "terminal_query_required",
                    }
                if terminal.get("status") == "invalid":
                    return {
                        "status": "transition_invalid",
                        "transition": terminal,
                        "frame": _battle_control_frame_summary(frame),
                    }
                return {
                    "status": "terminal_observed",
                    "subject_army_id": subject,
                    "transition": terminal,
                    "frame": _battle_control_frame_summary(frame),
                }
            return {
                "status": "terminal_observed",
                "subject_army_id": subject,
                "frame": _battle_control_frame_summary(frame),
            }
        before_record = pre_advance.get(subject)
        if not isinstance(before_record, dict):
            continue
        transition = _battle_control_transition(
            before_record["frame"], frame, latest_advance_result
        )
        if transition.get("status") == "invalid":
            return {
                "status": "transition_invalid",
                "transition": transition,
                "frame": _battle_control_frame_summary(frame),
            }
        if transition.get("status") == "combat_replaced":
            if (
                isinstance(latest_sentinel_validation, dict)
                and latest_sentinel_validation.get("step")
                == _BATTLE_TERMINAL_CRUISE_STEP
            ):
                terminal = _cursor_bound_terminal_transition(
                    scoped,
                    previous_advance_position=previous_advance,
                    advance_position=latest_advance,
                    before_record=pre_advance[subject],
                    snapshot=snapshot,
                    advance_result=latest_advance_result,
                )
                if terminal.get("status") == "query_required":
                    return {
                        **terminal,
                        "status": "terminal_query_required",
                    }
                if terminal.get("status") == "invalid":
                    return {
                        "status": "transition_invalid",
                        "transition": terminal,
                        "frame": _battle_control_frame_summary(frame),
                    }
                recognized.append(terminal)
            else:
                recognized.append(transition)
            replaced_subjects.add(subject)
        else:
            transitions.append(transition)

    if recognized:
        remove_positions = {
            position
            for position, row in enumerate(scoped, start=1)
            if previous_advance < position < latest_advance
            and parse_query_battle_control_snapshot_v1_step(
                _effective_command(row)
            )
            in replaced_subjects
        }
        return {
            "status": "transition_recognized",
            "transitions": recognized,
            "remaining_rows": [
                row
                for position, row in enumerate(scoped, start=1)
                if position not in remove_positions
            ],
        }

    return {
        "status": "ready",
        "evidence": [
            _battle_control_frame_summary(current_frames[subject]["frame"])
            for subject in active_subjects
        ],
        "full_frames": [
            current_frames[subject]["frame"] for subject in active_subjects
        ],
        "transitions": transitions,
    }


def _war_entry_power_eu_projection(
    assessment: dict[str, object] | None,
) -> dict[str, object]:
    """Project exact native power into the incomplete war-entry EU ledger.

    The raw margin is a real consumed input, but it remains in CK3's strategic
    power domain.  It is not assigned an invented gold/title utility
    coefficient and therefore cannot unlock declaration by itself.
    """

    missing = [
        "participant_arrival_bounds",
        "combat_forecast",
        "campaign_cost",
        "exit_assessment",
        "calibrated_utility_policy",
    ]
    if not isinstance(assessment, dict):
        return {
            "status": "power_assessment_required",
            "native_power_component_ready": False,
            "eu_lower_raw": None,
            "missing_components": ["native_power_assessment", *missing],
            "automatic_declaration_enabled": False,
        }
    actor_base = int(assessment["actor_power_base_raw"])
    actor_total = int(assessment["actor_power_total_raw"])
    actor_network = int(assessment["actor_network_contribution_raw"])
    target_total = int(assessment["target_power_total_raw"])
    target_network = int(assessment["target_network_contribution_raw"])
    conservative_margin = actor_base - target_total
    total_margin = actor_total - target_total
    return {
        "status": "native_power_component_ready",
        "native_power_component_ready": True,
        "native_power_component": {
            "scale": WAR_ENTRY_FIXED_POINT_SCALE,
            "actual_power_ratio_raw": int(
                assessment["actual_power_ratio_raw"]
            ),
            "actor_power_base_raw": actor_base,
            "actor_power_total_raw": actor_total,
            "target_power_total_raw": target_total,
            "native_total_power_margin_raw": total_margin,
            "conservative_self_power_margin_raw": conservative_margin,
            "actor_network_dependency_raw": max(actor_network, 0),
            "target_network_support_raw": max(target_network, 0),
            "distance_raw": int(assessment["distance_raw"]),
            "risk_order_key": [
                max(-conservative_margin, 0),
                int(assessment["actual_power_ratio_raw"]),
                max(actor_network, 0),
                max(target_network, 0),
                target_total,
                int(assessment["distance_raw"]),
            ],
        },
        "eu_lower_raw": None,
        "missing_components": missing,
        "automatic_declaration_enabled": False,
    }


def _cross_run_focus(plan: dict[str, object] | None) -> str | None:
    """Map the highest cross-run priority to one opening strategy family."""
    priorities = plan.get("priorities") if isinstance(plan, dict) else None
    if not isinstance(priorities, list):
        return None
    ranked = sorted(
        (row for row in priorities if isinstance(row, dict)),
        key=lambda row: (
            -int(row.get("priority", 0))
            if isinstance(row.get("priority"), int)
            and not isinstance(row.get("priority"), bool)
            else 0,
            str(row.get("action") or ""),
        ),
    )
    for row in ranked:
        action = str(row.get("action") or "").casefold()
        if any(token in action for token in ("war", "expansion", "palermo")):
            return "war"
        if any(token in action for token in ("marriage", "alliance", "betrothal")):
            return "marriage"
        if any(token in action for token in ("succession", "partition")):
            return "succession"
    return None


def _native_marriage_attempt_state(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
) -> dict[str, object] | None:
    """Recover the latest outbound proposal intent from persistent history."""
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        choice_id = parse_arrange_marriage_step(_effective_command(row))
        if choice_id is None:
            continue
        parsed_played, parsed_candidate = (
            int(value) for value in choice_id.split("-", maxsplit=1)
        )
        row_index = (
            row.get("index")
            if isinstance(row.get("index"), int)
            else position + 1
        )
        if row.get("ok") is not True:
            return {
                "status": "retry",
                "reason": "submission_failed",
                "played_character_id": parsed_played,
                "candidate_character_id": parsed_candidate,
                "attempt_index": row_index,
                "retry_index": row_index,
            }
        result = row.get("result")
        action = (
            result.get("marriage_action")
            if isinstance(result, dict)
            else None
        )
        if not isinstance(action, dict):
            return {
                "status": "retry",
                "reason": "submission_result_missing",
                "played_character_id": parsed_played,
                "candidate_character_id": parsed_candidate,
                "attempt_index": row_index,
                "retry_index": row_index,
            }
        played_character_id = action.get("played_character_id")
        candidate_character_id = action.get("candidate_character_id")
        if isinstance(played_character_id, bool) or not isinstance(
            played_character_id, int
        ):
            played_character_id = parsed_played
        if isinstance(candidate_character_id, bool) or not isinstance(
            candidate_character_id, int
        ):
            candidate_character_id = parsed_candidate
        if action.get("status") != "proposal_submitted":
            return {
                "status": "retry",
                "reason": "submission_rejected",
                "played_character_id": played_character_id,
                "candidate_character_id": candidate_character_id,
                "attempt_index": row_index,
                "retry_index": row_index,
            }

        relationship_status = observed_marriage_status(
            snapshot.get("played_character"),
            played_character_id=played_character_id,
            candidate_character_id=candidate_character_id,
        )
        recorded_outcome = result.get("marriage_result")
        if relationship_status is not None or (
            isinstance(recorded_outcome, dict)
            and recorded_outcome.get("source")
            == "native_relationship_snapshot"
            and recorded_outcome.get("candidate_character_id")
            == candidate_character_id
            and recorded_outcome.get("status")
            in {"accepted_betrothal", "accepted_marriage"}
        ):
            return {
                "status": "completed",
                "relationship_status": (
                    relationship_status
                    if relationship_status is not None
                    else recorded_outcome.get("status")
                ),
                "played_character_id": played_character_id,
                "candidate_character_id": candidate_character_id,
                "attempt_index": row_index,
            }

        submitted_date_raw = action.get("submitted_date_raw")
        current_date_raw = snapshot.get("date_raw")
        elapsed_days: int | None = None
        if (
            isinstance(submitted_date_raw, int)
            and not isinstance(submitted_date_raw, bool)
            and isinstance(current_date_raw, int)
            and not isinstance(current_date_raw, bool)
            and current_date_raw >= submitted_date_raw
        ):
            elapsed_days = (current_date_raw - submitted_date_raw) // 24
        advances = sum(
            1
            for later in commands[position + 1 :]
            if is_life_advance_step(_effective_command(later))
            and later.get("ok") is True
        )
        timed_out = (
            advances >= _MARRIAGE_PROPOSAL_MAX_ADVANCES
            or (
                elapsed_days is not None
                and elapsed_days >= _MARRIAGE_PROPOSAL_MAX_GAME_DAYS
            )
        )
        return {
            "status": "retry" if timed_out else "pending",
            "reason": "proposal_timeout" if timed_out else "awaiting_relationship",
            "played_character_id": played_character_id,
            "candidate_character_id": candidate_character_id,
            "submitted_date_raw": (
                submitted_date_raw
                if isinstance(submitted_date_raw, int)
                and not isinstance(submitted_date_raw, bool)
                else None
            ),
            "elapsed_days": elapsed_days,
            "life_advances": advances,
            "timeout_days": _MARRIAGE_PROPOSAL_MAX_GAME_DAYS,
            "max_life_advances": _MARRIAGE_PROPOSAL_MAX_ADVANCES,
            "attempt_index": row_index,
            "retry_index": row_index,
        }
    return None


def _same_frame_termination_row(
    snapshot: dict[str, object], row: object, war_id: int
) -> bool:
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    return bool(
        isinstance(row, dict)
        and row.get("war_id") == war_id
        and row.get("queried_snapshot_id") == snapshot.get("snapshot_id")
        and row.get("queried_revision") == snapshot.get("revision")
        and row.get("queried_native_revision")
        == snapshot.get("native_revision")
        and row.get("queried_connection_generation")
        == connection_generation
        and row.get("episode_run_id") == snapshot.get("episode_run_id")
    )


def _claim_cb_white_peace_base_ready(
    snapshot: dict[str, object],
    war: dict[str, object],
    options: object,
) -> bool:
    war_id = war.get("war_id")
    if not isinstance(war_id, int) or isinstance(war_id, bool):
        return False
    if not _same_frame_termination_row(snapshot, options, war_id):
        return False
    assert isinstance(options, dict)
    score = war.get("player_relative_war_score")
    duration = options.get("war_duration_days")
    casus_belli = options.get("active_casus_belli_identity")
    option_rows = options.get("options")
    white_peace = (
        option_rows.get("white_peace")
        if isinstance(option_rows, dict)
        else None
    )
    response = (
        white_peace.get("recipient_response")
        if isinstance(white_peace, dict)
        else None
    )
    return bool(
        snapshot.get("paused") is True
        and war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score") == score
        and isinstance(score, int)
        and not isinstance(score, bool)
        and 0 <= score < 100
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration >= 365
        and options.get("active_casus_belli_present") is True
        and isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key") == "claim_cb"
        and options.get("cb_allows_white_peace") is True
        and isinstance(white_peace, dict)
        and white_peace.get("outcome") == "white_peace"
        and white_peace.get("hostage_variant") == "none"
        and white_peace.get("context_constructed") is True
        and white_peace.get("native_validator_passed") is True
        and white_peace.get("available") is True
        and isinstance(response, dict)
        and response.get("status") == "available"
        and response.get("would_accept_now") is True
    )


def _claim_cb_white_peace_terms_ready(
    snapshot: dict[str, object],
    war: dict[str, object],
    options: dict[str, object],
    terms: object,
) -> bool:
    war_id = war.get("war_id")
    if (
        not isinstance(war_id, int)
        or isinstance(war_id, bool)
        or not _same_frame_termination_row(snapshot, terms, war_id)
    ):
        return False
    assert isinstance(terms, dict)
    option_cb = options.get("active_casus_belli_identity")
    terms_cb = terms.get("casus_belli")
    readiness = terms.get("readiness")
    played_character = snapshot.get("played_character")
    target_title_ids = war.get("targeted_title_ids")
    claims = terms.get("claims")
    return bool(
        terms.get("status") == "available"
        and isinstance(option_cb, dict)
        and isinstance(terms_cb, dict)
        and terms_cb.get("canonical_key") == "claim_cb"
        and terms_cb.get("database_index")
        == option_cb.get("database_index")
        and isinstance(readiness, dict)
        and readiness.get("ready") is True
        and isinstance(played_character, dict)
        and terms.get("claimant_character_id")
        == played_character.get("character_id")
        and isinstance(target_title_ids, list)
        and bool(target_title_ids)
        and terms.get("target_title_ids") == target_title_ids
        and isinstance(claims, list)
        and len(claims) == len(target_title_ids)
        and all(
            isinstance(claim, dict)
            and claim.get("title_id") == title_id
            and claim.get("present") is True
            for claim, title_id in zip(claims, target_title_ids, strict=True)
        )
    )


def _white_peace_submission_cooldown(
    commands: list[dict[str, object]],
    *,
    war_id: int,
    date_raw: object,
    episode_run_id: object,
) -> dict[str, object] | None:
    if isinstance(date_raw, bool) or not isinstance(date_raw, int):
        return {"status": "invalid_current_date"}
    expected_step = offer_white_peace_step(war_id)
    for row in reversed(commands):
        if row.get("command") != expected_step or row.get("ok") is not True:
            continue
        result = row.get("result")
        action = (
            result.get("war_termination_result")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(action, dict)
            and action.get("war_id") == war_id
            and action.get("outcome") == "white_peace"
            and action.get("episode_run_id") == episode_run_id
            and action.get("status") in {"submitted_pending", "applied"}
        ):
            continue
        submitted_date_raw = action.get("submitted_date_raw")
        if isinstance(submitted_date_raw, bool) or not isinstance(
            submitted_date_raw, int
        ):
            return {"status": "malformed_submission_history"}
        elapsed_raw = date_raw - submitted_date_raw
        if elapsed_raw < _WHITE_PEACE_PROPOSAL_COOLDOWN_RAW:
            return {
                "status": "cooldown",
                "submitted_date_raw": submitted_date_raw,
                "elapsed_raw": elapsed_raw,
                "remaining_raw": (
                    _WHITE_PEACE_PROPOSAL_COOLDOWN_RAW - elapsed_raw
                ),
                "same_day_pending": (
                    elapsed_raw == 0
                    and action.get("status") == "submitted_pending"
                ),
                "history_index": row.get("index"),
            }
        return None
    return None


def choose_one_life_turn(
    commands: list[dict[str, object]],
    *,
    snapshot: dict[str, object] | None = None,
    action_steps: Iterable[str] | None = None,
    bridge_capabilities: Iterable[str] | None = None,
    next_run_plan: dict[str, object] | None = None,
    battle_speed_readiness: dict[str, object] | None = None,
) -> dict[str, object]:
    """Choose one useful, inspectable action for the current life.

    This is deliberately a one-step planner.  The caller records the result,
    then invokes it again; failures and newly visible events therefore change
    the next choice instead of being hidden inside a long macro.
    """
    rows = _expanded_command_rows(commands)
    available_steps = {
        step for step in (action_steps or ()) if isinstance(step, str) and step
    }
    available_capabilities = {
        capability
        for capability in (bridge_capabilities or ())
        if isinstance(capability, str) and capability
    }
    battle_speed_gates = {
        name: bool(
            isinstance(battle_speed_readiness, dict)
            and battle_speed_readiness.get(name) is True
        )
        for name in (
            "decision_sentinel_live_ready",
            "terminal_sentinel_live_ready",
            "overwhelming_matrix_live_ready",
        )
    }
    cross_run_focus = _cross_run_focus(next_run_plan)
    played_character = (
        snapshot.get("played_character")
        if isinstance(snapshot, dict)
        else None
    )
    terminal_reason = (
        snapshot.get("one_life_terminal_reason")
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("one_life_terminal_reason"), str)
        else (
            "played_character_dead"
            if isinstance(played_character, dict)
            and played_character.get("alive") is False
            else None
        )
    )
    if terminal_reason is not None:
        episode_character_id = (
            snapshot.get("episode_character_id")
            if isinstance(snapshot, dict)
            else None
        )
        completed_terminal = _latest_effective_result(rows, "death-terminal")
        if (
            isinstance(completed_terminal, dict)
            and completed_terminal.get("terminal") is True
            and completed_terminal.get("score") is not None
            and completed_terminal.get("settlement_status")
            in {None, "complete"}
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_complete",
                "selected_step": (
                    "start-next-episode"
                    if "start-next-episode" in available_steps
                    else None
                ),
                "reason": "this one-life episode is already settled",
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "score": completed_terminal.get("score"),
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
            }
        if (
            isinstance(completed_terminal, dict)
            and completed_terminal.get("settlement_status")
            == "settlement_unavailable"
            and isinstance(snapshot, dict)
            and snapshot.get("one_life_settlement_status")
            == "settlement_unavailable"
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_settlement_unavailable",
                "selected_step": None,
                "required_capability": (
                    ONE_LIFE_SETTLEMENT_CAPABILITY
                ),
                "reason": (
                    "the episode is terminal but this bridge cannot publish "
                    "its score; wait for a settlement-capable backend"
                ),
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
            }
        reason = (
            "CK3 changed the played CharacterID after the episode character; "
            "end this one-life episode instead of continuing as the heir"
            if terminal_reason == "played_character_changed"
            else "the native played character is dead; end this one-life episode"
        )
        if "death-terminal" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_native",
                "selected_step": "death-terminal",
                "reason": reason,
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "played_character": (
                    dict(played_character)
                    if isinstance(played_character, dict)
                    else None
                ),
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "terminal_native_unsupported",
            "selected_step": None,
            "required_step": "death-terminal",
            "reason": "the backend cannot finalize the detected player death",
            "terminal_reason": terminal_reason,
            "episode_character_id": episode_character_id,
            "played_character": (
                dict(played_character)
                if isinstance(played_character, dict)
                else None
            ),
        }
    raw_active_event = (
        snapshot.get("active_event", snapshot.get("current_event"))
        if isinstance(snapshot, dict)
        else None
    )
    active_event = normalize_active_event(
        raw_active_event,
        default_source=(
            str(snapshot.get("source"))
            if isinstance(snapshot, dict) and snapshot.get("source")
            else "planner"
        ),
    )
    if active_event is not None:
        typed_event_window_supported = (
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            in available_capabilities
            or QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP in available_steps
        )
        if typed_event_window_supported:
            event_summary: dict[str, object] = {
                "instance_id": active_event.get("instance_id"),
                "option_count": active_event.get("option_count"),
                "selected_option_number": None,
                "selected_option_index": None,
            }
            if (
                not isinstance(snapshot, dict)
                or snapshot.get("paused") is not True
            ):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_window_pause_required",
                    "selected_step": (
                        "pause-map" if "pause-map" in available_steps else None
                    ),
                    "required_step": "pause-map",
                    "reason": (
                        "pause the map before querying the exact current "
                        "event window"
                    ),
                    "active_event": event_summary,
                }
            if (
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
                not in available_steps
            ):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_window_query_unavailable",
                    "selected_step": None,
                    "required_step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                    "reason": (
                        "the backend advertises typed event-window observation "
                        "but cannot query this paused active event"
                    ),
                    "active_event": event_summary,
                }
            event_context = _same_frame_event_window_context(rows, snapshot)
            if event_context is None:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_window_query",
                    "selected_step": (
                        QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
                    ),
                    "reason": (
                        "query the exact current event window before choosing "
                        "from its materialized options"
                    ),
                    "active_event": event_summary,
                }

            event_summary.update(
                {
                    "window_context_status": event_context.get("status"),
                    "window_match_count": event_context.get(
                        "window_match_count"
                    ),
                    "readiness": event_context.get("readiness"),
                }
            )
            if event_context.get("status") == "unavailable":
                event_summary["materialized_options"] = None
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_window_unavailable",
                    "selected_step": None,
                    "required_capability": (
                        "game.state.current-event-window-materialization"
                    ),
                    "reason": (
                        "the same-frame exact event-window query is "
                        "unavailable: "
                        f"{event_context.get('unavailable_reason')}"
                    ),
                    "active_event": event_summary,
                }

            materialized_options = event_context.get("options")
            assert isinstance(materialized_options, list)
            eligible_options = [
                option
                for option in materialized_options
                if isinstance(option, dict)
                and option.get("shown") is True
                and option.get("enabled") is True
            ]
            readiness = event_context.get("readiness")
            semantic_ready = bool(
                isinstance(readiness, dict)
                and readiness.get("semantic_decision_ready") is True
            )
            event_summary.update(
                {
                    "materialized_options": materialized_options,
                    "materialized_option_count": len(materialized_options),
                    "enabled_materialized_option_count": len(
                        eligible_options
                    ),
                    "semantic_decision_ready": semantic_ready,
                }
            )

            if not semantic_ready and eligible_options:
                option, event_decision = _degraded_event_option_decision(
                    eligible_options
                )
                native_index = option["native_option_index"]
                assert isinstance(native_index, int)
                option_number = native_index + 1
                exact_step = event_option_step(option_number)
                event_summary.update(
                    {
                        "selected_option_number": option_number,
                        "selected_option_index": native_index,
                        "selected_native_option_index": native_index,
                        "selected_rendered_index": option.get(
                            "rendered_index"
                        ),
                        "semantic_optimal": False,
                        "degraded_decision": event_decision,
                    }
                )
                if exact_step in available_steps:
                    if len(eligible_options) == 1:
                        phase = "active_event_forced_presentation_choice"
                        reason = (
                            "forced presentation choice: exactly one "
                            "materialized option is shown and enabled; this "
                            "is not a semantic optimum"
                        )
                    else:
                        phase = "active_event_degraded_minimal_choice"
                        reason = (
                            "semantic inputs are incomplete; choose a "
                            "same-frame shown+enabled option with the "
                            "audited death/cancel/native-order fallback so "
                            "the campaign can continue; this is not the "
                            "native selector or a semantic optimum"
                        )
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": phase,
                        "selected_step": exact_step,
                        "reason": reason,
                        "active_event": event_summary,
                        "event_decision": event_decision,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": (
                        "active_event_forced_choice_unsupported"
                        if len(eligible_options) == 1
                        else "active_event_degraded_choice_unsupported"
                    ),
                    "selected_step": None,
                    "required_step": exact_step,
                    "reason": (
                        "the selected same-frame shown and enabled native "
                        f"event option is authored index {native_index}, but "
                        f"the backend did not advertise {exact_step}"
                    ),
                    "active_event": event_summary,
                    "event_decision": event_decision,
                }

            if semantic_ready:
                reason = (
                    "the event window reports semantic inputs ready, but no "
                    "event semantic policy is implemented"
                )
            elif not eligible_options:
                reason = (
                    "no materialized event option is both shown and enabled; "
                    "effect preview or a semantic policy is required"
                )
            else:
                reason = "event semantic choice could not produce a candidate"
            return {
                "policy": "one-life-turn-v1",
                "phase": "active_event_semantic_evidence_required",
                "selected_step": None,
                "required_capabilities": [
                    "game.state.current-event-window-effect-preview",
                    "game.policy.current-event-semantic-decision",
                ],
                "reason": reason,
                "active_event": event_summary,
            }

        # Compatibility path for backends predating the typed event-window
        # query.  Their snapshot-native or visual event behavior is unchanged.
        option_number = choose_event_option_number(active_event)
        exact_step = (
            event_option_step(option_number)
            if option_number is not None
            else None
        )
        event_summary = {
            "instance_id": active_event.get("instance_id"),
            "option_count": active_event.get("option_count"),
            "selected_option_number": option_number,
            "selected_option_index": (
                option_number - 1 if option_number is not None else None
            ),
        }
        if exact_step is not None and exact_step in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "active_event",
                "selected_step": exact_step,
                "reason": "select the best enabled option on the active CK3 event",
                "active_event": event_summary,
            }
        if "resolve-current-event" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "active_event_visual_fallback",
                "selected_step": "resolve-current-event",
                "reason": (
                    "the active event is delegated explicitly to the visual "
                    "event resolver"
                ),
                "active_event": event_summary,
            }
        required_step = exact_step or "resolve-current-event"
        return {
            "policy": "one-life-turn-v1",
            "phase": "active_event_unsupported",
            "selected_step": None,
            "required_step": required_step,
            "reason": (
                "the selected backend reported an active event but did not "
                f"advertise {required_step}"
            ),
            "active_event": event_summary,
        }

    active_wars = (
        [war for war in snapshot.get("active_wars", []) if isinstance(war, dict)]
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("active_wars"), list)
        else []
    )
    war_summary = [
        {
            "war_id": war.get("war_id"),
            "player_side": war.get("player_side"),
            "primary_opponent_character_id": war.get(
                "primary_opponent_character_id"
            ),
            "player_is_primary_war_leader": war.get(
                "player_is_primary_war_leader"
            ),
            "enemy_primary_default_raise_province_id": war.get(
                "enemy_primary_default_raise_province_id"
            ),
            "player_relative_war_score": war.get(
                "player_relative_war_score"
            ),
        }
        for war in active_wars
    ]
    enforceable = next(
        (
            war
            for war in active_wars
            if isinstance(war.get("war_id"), int)
            and isinstance(war.get("player_relative_war_score"), int)
            and int(war["player_relative_war_score"]) >= 100
            and (
                war.get("player_is_primary_war_leader") is True
                or (
                    war.get("player_is_primary_war_leader") is None
                    and enforce_demands_step(int(war["war_id"]))
                    in available_steps
                )
            )
        ),
        None,
    )
    if isinstance(enforceable, dict):
        step = enforce_demands_step(int(enforceable["war_id"]))
        if step in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_enforce_demands",
                "selected_step": step,
                "reason": "the native war reached 100%; enforce demands before issuing more army orders",
                "active_wars": war_summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_enforce_demands_unsupported",
            "selected_step": None,
            "required_step": step,
            "reason": "the war reached 100% but this backend cannot enforce demands",
            "active_wars": war_summary,
        }
    pending_interaction = (
        snapshot.get("pending_character_interaction")
        if isinstance(snapshot, dict)
        else None
    )
    if (
        isinstance(pending_interaction, dict)
        and pending_interaction.get("auto_accept_notification") is True
    ):
        notification_summary = {
            "instance_id": pending_interaction.get("instance_id"),
            "sender_character_id": pending_interaction.get(
                "sender_character_id"
            ),
            "auto_accept_notification": True,
        }
        if ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "pending_character_interaction_acknowledge",
                "selected_step": (
                    ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP
                ),
                "reason": (
                    "acknowledge the already resolved native interaction "
                    "notification so the pending queue can advance"
                ),
                "pending_character_interaction": notification_summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "pending_character_interaction_acknowledge_unsupported",
            "selected_step": None,
            "required_step": ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
            "reason": (
                "the current pending item is an auto-accept notification, "
                "but the backend cannot acknowledge its exact full ID"
            ),
            "pending_character_interaction": notification_summary,
        }
    pending_war_interaction_plan: dict[str, object] | None = None
    if (
        isinstance(pending_interaction, dict)
        and pending_interaction.get("auto_accept_notification") is False
    ):
        typed_context = _same_frame_pending_interaction_context(
            rows,
            snapshot if isinstance(snapshot, dict) else None,
        )
        summary = _pending_interaction_summary(
            pending_interaction,
            typed_context,
            snapshot if isinstance(snapshot, dict) else None,
        )
        if typed_context is None and (
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
            in available_steps
        ):
            query_plan = {
                "policy": "one-life-turn-v1",
                "phase": (
                    "pending_war_interaction_query"
                    if active_wars
                    else "pending_character_interaction_query"
                ),
                "selected_step": (
                    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
                ),
                "reason": (
                    "observe the pending interaction's exact type, roles, "
                    "routing, deadline and reply legality before deciding"
                    if not active_wars
                    else (
                        "observe the pending interaction after the enforce-"
                        "demands priority check and before any war reply"
                    )
                ),
                "pending_character_interaction": summary,
            }
            if active_wars:
                pending_war_interaction_plan = query_plan
            else:
                return query_plan
        elif typed_context is None:
            blocked_plan = {
                "policy": "one-life-turn-v1",
                "phase": (
                    "pending_war_interaction_evidence_required"
                    if active_wars
                    else "pending_character_interaction_evidence_required"
                ),
                "selected_step": None,
                "required_step": (
                    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
                ),
                "required_capabilities": [
                    "game.state.pending-character-interaction-structured-terms",
                    "game.policy.pending-character-interaction-semantic-decision",
                    *(
                        ["game.command.query-war-termination-options-N"]
                        if active_wars
                        else []
                    ),
                ],
                "reason": "the pending interaction has no same-frame typed context",
                "pending_character_interaction": summary,
            }
            if active_wars:
                pending_war_interaction_plan = blocked_plan
            else:
                return blocked_plan
        else:
            assert isinstance(snapshot, dict)
            degraded = _degraded_pending_interaction_decision(
                pending_interaction,
                typed_context,
                snapshot=snapshot,
                active_wars=active_wars,
                available_steps=available_steps,
            )
            degraded_plan = _degraded_pending_interaction_plan(degraded)
            if active_wars:
                # Every pending reply waits behind the active-war 100%
                # enforce-demands check.  Definition classification cannot
                # pre-empt a terminal war action merely because the request
                # itself is independently non-war.
                pending_war_interaction_plan = degraded_plan
            else:
                return degraded_plan
    player_armies = (
        [army for army in snapshot.get("player_armies", []) if isinstance(army, dict)]
        if isinstance(snapshot, dict)
        and isinstance(snapshot.get("player_armies"), list)
        else []
    )
    controlled_armies = controllable_armies(player_armies)
    battle_control_state = _battle_control_turn_state(
        rows,
        snapshot if isinstance(snapshot, dict) else None,
        controlled_armies,
    )
    battle_control_status = battle_control_state.get("status")
    if battle_control_status == "transition_recognized":
        remaining_rows = battle_control_state.get("remaining_rows")
        if not isinstance(remaining_rows, list) or len(remaining_rows) >= len(
            rows
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_battle_transition_invalid",
                "selected_step": None,
                "required_step": "fresh-paused-battle-control-frame",
                "reason": (
                    "the recognized battle transition could not be separated "
                    "from its pre-advance evidence epoch"
                ),
                "battle_transitions": battle_control_state.get(
                    "transitions", []
                ),
            }
        continued = choose_one_life_turn(
            [row for row in remaining_rows if isinstance(row, dict)],
            snapshot=snapshot,
            action_steps=available_steps,
            bridge_capabilities=available_capabilities,
            next_run_plan=next_run_plan,
            battle_speed_readiness=battle_speed_gates,
        )
        nested_transitions = continued.get("battle_transitions")
        return {
            **continued,
            "battle_transitions": [
                *(
                    battle_control_state.get("transitions", [])
                    if isinstance(
                        battle_control_state.get("transitions"), list
                    )
                    else []
                ),
                *(
                    nested_transitions
                    if isinstance(nested_transitions, list)
                    else []
                ),
            ],
        }
    if battle_control_status == "wait_for_pause":
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_wait_for_pause",
            "selected_step": (
                "pause-map" if "pause-map" in available_steps else None
            ),
            "required_step": "pause-map",
            "reason": (
                "pause the map before reading any active subject's exact "
                "battle-control frame"
            ),
            "battle_subject_army_ids": battle_control_state.get(
                "subject_army_ids", []
            ),
        }
    if battle_control_status == "query_required":
        battle_query_step = battle_control_state.get("step")
        if (
            isinstance(battle_query_step, str)
            and battle_query_step in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_battle_control_query",
                "selected_step": battle_query_step,
                "reason": (
                    "read an available exact battle-control frame bound to "
                    "the current paused revision before any combat time slice"
                ),
                "battle_subject_army_id": battle_control_state.get(
                    "subject_army_id"
                ),
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_control_query_unsupported",
            "selected_step": None,
            "required_step": battle_query_step,
            "reason": (
                "the active combat cannot advance without a current-revision "
                "available battle-control frame"
            ),
            "battle_subject_army_id": battle_control_state.get(
                "subject_army_id"
            ),
        }
    if battle_control_status == "invalid_subject":
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_control_query_unsupported",
            "selected_step": None,
            "required_capability": (
                "game.command.query-battle-control-snapshot-v1-N"
            ),
            "reason": (
                "the active controllable combat subject lacks a queryable "
                "positive public CUnitID"
            ),
            "battle_subject_army_id": battle_control_state.get(
                "subject_army_id"
            ),
        }
    if battle_control_status == "terminal_query_required":
        terminal_step = battle_control_state.get("step")
        if (
            isinstance(terminal_step, str)
            and QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
            in available_capabilities
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_battle_terminal_journal_query",
                "selected_step": terminal_step,
                "reason": (
                    "read the cursor-bound terminal journal after the native "
                    "terminal stop before accepting the CombatID outcome"
                ),
                "battle_subject_army_id": battle_control_state.get(
                    "subject_army_id"
                ),
                "battle_combat_id": battle_control_state.get("combat_id"),
                "after_terminal_sequence": battle_control_state.get(
                    "after_terminal_sequence"
                ),
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_terminal_journal_query_unsupported",
            "selected_step": None,
            "required_step": terminal_step,
            "required_capability": (
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
            ),
            "reason": (
                "the terminal cruise stopped, but its cursor-bound CombatID "
                "outcome cannot be queried"
            ),
        }
    if battle_control_status == "transition_invalid":
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_transition_invalid",
            "selected_step": None,
            "required_step": "fresh-paused-battle-control-frame",
            "reason": (
                "the post-advance exact frame did not prove a legal same-"
                "CombatID phase/day or casualty-ledger transition"
            ),
            "battle_transition": battle_control_state.get("transition"),
            "battle_control_frame": battle_control_state.get("frame"),
        }
    if battle_control_status == "terminal_observed":
        terminal_transition = battle_control_state.get("transition")
        if not isinstance(terminal_transition, dict):
            terminal_transition = {
                "status": "terminal_observed",
                "subject_army_id": battle_control_state.get(
                    "subject_army_id"
                ),
                "outcome": None,
            }
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_battle_terminal_cleanup",
                "selected_step": "life-advance",
                "reason": (
                    "the exact frame explicitly reached finalized/done while "
                    "the semantic subject remains in combat; advance at most "
                    "one day so CK3 can remove the completed combat, then "
                    "observe the subject again"
                ),
                "battle_transition": terminal_transition,
                "battle_transitions": [terminal_transition],
                "battle_control_frame": battle_control_state.get("frame"),
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_terminal_cleanup_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": (
                "the exact frame explicitly reached finalized/done while the "
                "semantic subject remains in combat, but the backend cannot "
                "perform the bounded cleanup slice"
            ),
            "battle_transition": {
                "status": "terminal_observed",
                "subject_army_id": battle_control_state.get(
                    "subject_army_id"
                ),
                "outcome": None,
            },
            "battle_control_frame": battle_control_state.get("frame"),
        }
    if active_wars:
        raw_termination_options = (
            snapshot.get("war_termination_options")
            if isinstance(snapshot, dict)
            else None
        )
        termination_by_war_id = {
            row["war_id"]: row
            for row in (
                raw_termination_options
                if isinstance(raw_termination_options, list)
                else []
            )
            if isinstance(row, dict)
            and isinstance(row.get("war_id"), int)
            and not isinstance(row.get("war_id"), bool)
        }
        raw_termination_terms = (
            snapshot.get("war_termination_terms")
            if isinstance(snapshot, dict)
            else None
        )
        termination_terms_by_war_id = {
            row["war_id"]: row
            for row in (
                raw_termination_terms
                if isinstance(raw_termination_terms, list)
                else []
            )
            if isinstance(row, dict)
            and isinstance(row.get("war_id"), int)
            and not isinstance(row.get("war_id"), bool)
        }
        raw_exit_terms = (
            snapshot.get("war_termination_exit_terms")
            if isinstance(snapshot, dict)
            else None
        )
        exit_terms_by_war_id = {
            row["war_id"]: row
            for row in (
                raw_exit_terms if isinstance(raw_exit_terms, list) else []
            )
            if isinstance(row, dict)
            and isinstance(row.get("war_id"), int)
            and not isinstance(row.get("war_id"), bool)
            and row.get("status") == "available"
            and isinstance(row.get("readiness"), dict)
            and row["readiness"].get("exit_terms_ready") is True
        }
        for summary in war_summary:
            termination = termination_by_war_id.get(summary.get("war_id"))
            termination_terms = termination_terms_by_war_id.get(
                summary.get("war_id")
            )
            exit_terms = exit_terms_by_war_id.get(summary.get("war_id"))
            if isinstance(termination, dict):
                options = termination.get("options")
                legal_options = {
                    name: option.get("available")
                    for name, option in (
                        options.items() if isinstance(options, dict) else []
                    )
                    if isinstance(name, str) and isinstance(option, dict)
                }
                option_evidence = {
                    name: {
                        "outcome": option.get("outcome"),
                        "available": option.get("available"),
                        "terms_observable": option.get("terms_observable"),
                        "terms": option.get("terms"),
                        "ai_acceptance_observable": option.get(
                            "ai_acceptance_observable"
                        ),
                        "ai_acceptance": option.get("ai_acceptance"),
                        "auto_accept_observable": option.get(
                            "auto_accept_observable"
                        ),
                        "auto_accept": option.get("auto_accept"),
                        "recipient_response": option.get(
                            "recipient_response"
                        ),
                    }
                    for name, option in (
                        options.items() if isinstance(options, dict) else []
                    )
                    if isinstance(name, str) and isinstance(option, dict)
                }
                constructed_options = [
                    option
                    for option in (
                        options.values() if isinstance(options, dict) else []
                    )
                    if isinstance(option, dict)
                    and option.get("context_constructed") is True
                ]
                terms_complete = isinstance(exit_terms, dict) or (
                    bool(constructed_options)
                    and all(
                        option.get("terms_observable") is True
                        for option in constructed_options
                    )
                )
                acceptance_complete = bool(constructed_options) and all(
                    option.get("ai_acceptance_observable") is True
                    and option.get("auto_accept_observable") is True
                    for option in constructed_options
                )
                unknown_fields = ["campaign_outcome_forecast"]
                if not (
                    isinstance(exit_terms, dict)
                    and isinstance(
                        exit_terms.get("primary_resource_balances"), dict
                    )
                ):
                    unknown_fields.append("primary_resource_balances")
                if not terms_complete:
                    unknown_fields.append("termination_terms")
                if not acceptance_complete:
                    unknown_fields.append("opponent_acceptance")
                summary["war_termination_options"] = dict(termination)
                if isinstance(termination_terms, dict):
                    summary["war_termination_terms"] = dict(
                        termination_terms
                    )
                if isinstance(exit_terms, dict):
                    summary["war_termination_exit_terms"] = dict(exit_terms)
                summary["war_exit_assessment"] = {
                    "status": "evidence_partial",
                    "reason": (
                        (
                            "native legality, acceptance, and structured exit "
                            "terms including current primary resource balances "
                            "are complete, but automatic termination remains "
                            "disabled until campaign outcomes are observable"
                        )
                        if isinstance(exit_terms, dict)
                        else (
                            "native termination legality, score, and per-option "
                            "acceptance evidence are projected for expected-"
                            "utility evaluation, but automatic termination "
                            "remains disabled while CB-specific terms and "
                            "campaign outcomes are unknown"
                        )
                    ),
                    "eu_inputs": {
                        "war_duration_days": termination.get(
                            "war_duration_days"
                        ),
                        "attacker_war_score": termination.get(
                            "attacker_war_score"
                        ),
                        "defender_war_score": termination.get(
                            "defender_war_score"
                        ),
                        "war_score_breakdown": termination.get(
                            "war_score_breakdown"
                        ),
                        "active_casus_belli_identity": termination.get(
                            "active_casus_belli_identity"
                        ),
                        "structured_exit_terms": (
                            dict(exit_terms)
                            if isinstance(exit_terms, dict)
                            else None
                        ),
                        "legal_options": legal_options,
                        "option_evidence": option_evidence,
                    },
                    "unknown_fields": unknown_fields,
                    "automatic_termination_enabled": False,
                }
            elif summary.get("player_side") == "defender":
                summary["war_exit_assessment"] = {
                    "status": "unavailable",
                    "reason": (
                        "the bridge does not yet publish complete termination "
                        "terms, opponent acceptance, or a campaign outcome "
                        "forecast; do not infer surrender value from war score"
                    ),
                    "required_capabilities": [
                        "game.command.query-war-termination-options-N",
                        "game.forecast.campaign-outcomes-v1",
                    ],
                }
        if isinstance(snapshot, dict) and snapshot.get("paused") is True:
            latched_unobservable_assaults = _unobservable_started_assaults(
                snapshot,
                active_wars=active_wars,
                commands=rows,
            )
            if latched_unobservable_assaults:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_assault_lifecycle_blocked",
                    "selected_step": None,
                    "required_step": "observable-exact-assault-state",
                    "reason": "a proven assault_started lifecycle has no exact completed, stopped, restored, or currently observable same-SiegeID state; do not advance time",
                    "assault_lifecycles": latched_unobservable_assaults,
                    "active_wars": war_summary,
                }
        if pending_war_interaction_plan is not None:
            return {
                **pending_war_interaction_plan,
                "active_wars": war_summary,
            }
        for war in active_wars:
            if not isinstance(war, dict):
                continue
            war_id = war.get("war_id")
            if (
                isinstance(war_id, bool)
                or not isinstance(war_id, int)
                or war_id <= 0
            ):
                continue
            cooldown = _white_peace_submission_cooldown(
                rows,
                war_id=war_id,
                date_raw=(
                    snapshot.get("date_raw")
                    if isinstance(snapshot, dict)
                    else None
                ),
                episode_run_id=(
                    snapshot.get("episode_run_id")
                    if isinstance(snapshot, dict)
                    else None
                ),
            )
            if isinstance(cooldown, dict) and cooldown.get(
                "same_day_pending"
            ) is True:
                if "life-advance" in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_white_peace_response_advance",
                        "selected_step": "life-advance",
                        "war_id": war_id,
                        "decision": {
                            "policy": "claim-cb-minimal-white-peace-v1",
                            "outcome": "white_peace",
                            "status": "submitted_pending",
                            "cooldown": cooldown,
                            "native_ai_equivalent": False,
                            "semantic_optimal": False,
                        },
                        "reason": (
                            "the same-WarID white-peace proposal was queued "
                            "on this game date; advance once so the recipient "
                            "AI can process it, without treating ACK as an "
                            "applied war result"
                        ),
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_white_peace_response_advance_unsupported",
                    "selected_step": None,
                    "required_step": "life-advance",
                    "war_id": war_id,
                    "reason": (
                        "a queued white-peace proposal needs one same-day "
                        "advance before any repeat proposal"
                    ),
                    "active_wars": war_summary,
                }
            if (
                isinstance(cooldown, dict)
                and cooldown.get("status") == "cooldown"
            ):
                # The outbound proposal remains inside CK3's asynchronous
                # response window.  Do not spend every game day rebuilding
                # same-WarID termination contexts which the duplicate gate
                # will reject anyway; continue ordinary military OODA until
                # the WarID disappears or the exact 30-day retry boundary.
                continue
            options = termination_by_war_id.get(war_id)
            if not isinstance(options, dict):
                query_step = query_war_termination_options_step(war_id)
                if query_step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_termination_query",
                        "selected_step": query_step,
                        "war_id": war_id,
                        "reason": (
                            "read the exact native termination contexts, "
                            "final recipient response, and score evidence "
                            "before any claim_cb white-peace decision"
                        ),
                        "active_wars": war_summary,
                    }
                continue
            if not (
                isinstance(snapshot, dict)
                and _claim_cb_white_peace_base_ready(
                    snapshot, war, options
                )
            ):
                continue
            terms = termination_terms_by_war_id.get(war_id)
            if not isinstance(terms, dict):
                terms_step = query_war_termination_terms_step(war_id)
                if terms_step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_termination_terms_v1_query",
                        "selected_step": terms_step,
                        "war_id": war_id,
                        "decision": {
                            "policy": "claim-cb-minimal-white-peace-v1",
                            "outcome": "white_peace",
                            "status": "terms_required",
                            "native_ai_equivalent": False,
                            "semantic_optimal": False,
                        },
                        "reason": (
                            "the exact recipient would accept white peace; "
                            "read same-frame claim-disposition v1 before "
                            "offering it"
                        ),
                        "active_wars": war_summary,
                    }
                continue
            if not (
                isinstance(snapshot, dict)
                and _claim_cb_white_peace_terms_ready(
                    snapshot, war, options, terms
                )
            ):
                continue
            step = offer_white_peace_step(war_id)
            if cooldown is None and step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_claim_cb_minimal_white_peace",
                    "selected_step": step,
                    "war_id": war_id,
                    "decision": {
                        "policy": "claim-cb-minimal-white-peace-v1",
                        "outcome": "white_peace",
                        "recipient_response": dict(
                            options["options"]["white_peace"][
                                "recipient_response"
                            ]
                        ),
                        "claimant_character_id": terms.get(
                            "claimant_character_id"
                        ),
                        "target_title_ids": list(
                            terms.get("target_title_ids", [])
                        ),
                        "all_declared_target_claims_present": True,
                        "weak_claims_allowed": True,
                        "native_ai_equivalent": False,
                        "semantic_optimal": False,
                        "campaign_forecast_used": False,
                    },
                    "reason": (
                        "owner-authorized blocker removal: this primary "
                        "attacker claim_cb is at least one year old, below "
                        "100%, the exact recipient accepts, and same-frame "
                        "v1 proves every declared target claim is retained; "
                        "this minimal rule is not native-equivalent or the "
                        "full v2 campaign policy"
                    ),
                    "active_wars": war_summary,
                }
            if cooldown is None:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_claim_cb_minimal_white_peace_unsupported",
                    "selected_step": None,
                    "required_step": step,
                    "war_id": war_id,
                    "reason": (
                        "same-frame minimal white-peace evidence is ready, "
                        "but the exact native literal is not reachable"
                    ),
                    "active_wars": war_summary,
                }
        if not controlled_armies:
            if RAISE_TROOPS_STEP in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_raise",
                    "selected_step": RAISE_TROOPS_STEP,
                    "reason": "an active war has no controllable army; raise troops at the native default rally point",
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_raise_unsupported",
                "selected_step": None,
                "required_step": RAISE_TROOPS_STEP,
                "reason": "the active war cannot continue until this backend can raise troops",
                "active_wars": war_summary,
            }
        primary_defensive_wars = [
            summary
            for summary in war_summary
            if summary.get("player_side") == "defender"
            and summary.get("player_is_primary_war_leader") is not False
        ]
        if primary_defensive_wars:
            return {
                "policy": "one-life-turn-v1",
                "phase": "defensive_war_exit_evidence_required",
                "selected_step": None,
                "required_capabilities": [
                    "game.command.query-war-termination-options-N",
                    "game.forecast.campaign-outcomes-v1",
                ],
                "reason": (
                    "a primary defensive war requires complete victory, white-"
                    "peace, and surrender terms plus opponent acceptance and a "
                    "campaign forecast before more time or army orders are issued"
                ),
                "defensive_wars": primary_defensive_wars,
                "active_wars": war_summary,
            }

        army_routes_supported = bool(
            isinstance(snapshot, dict)
            and snapshot.get("army_routes_supported") is True
        )
        move_route_preview_supported = bool(
            isinstance(snapshot, dict)
            and snapshot.get("move_route_preview_supported") is True
        )
        route_contact_horizon_supported = bool(
            isinstance(snapshot, dict)
            and snapshot.get("route_contact_horizon_supported") is True
        )
        paused_objective_state_supported = bool(
            isinstance(snapshot, dict)
            and (
                snapshot.get("war_objective_garrison_supported") is True
                or snapshot.get("war_objective_siege_progress_supported")
                is True
                or snapshot.get("war_objective_assault_supported") is True
            )
        )
        if (
            (
                army_routes_supported
                or move_route_preview_supported
                or route_contact_horizon_supported
                or paused_objective_state_supported
            )
            and isinstance(snapshot, dict)
            and snapshot.get("paused") is not True
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_route_wait_for_pause",
                "selected_step": (
                    "pause-map" if "pause-map" in available_steps else None
                ),
                "required_step": "pause-map",
                "reason": "pause the map before reading deep native route or objective state",
                "active_wars": war_summary,
            }
        if (
            move_route_preview_supported
            and not army_routes_supported
            and war_objective_province_ids(active_wars)
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_route_monitoring_unsupported",
                "selected_step": None,
                "required_step": "game.state.army-routes",
                "reason": "route preview without passive army routes cannot safely monitor a submitted march as enemy positions change",
                "active_wars": war_summary,
            }

        route_threat_enemies = [
            army
            for army in enemy_armies_from_wars(active_wars)
            if _army_tactical_state(army) != "retreating"
        ]
        route_threat_enemy_ids = tuple(
            sorted(
                {
                    enemy_id
                    for enemy in route_threat_enemies
                    if (enemy_id := _native_int(enemy.get("army_id")))
                    is not None
                    and enemy_id > 0
                }
            )
        )
        route_contact_scope_supported = bool(
            route_contact_horizon_supported
            and 0 < len(route_threat_enemy_ids)
            <= MAX_ROUTE_CONTACT_HOSTILE_IDS
        )
        enemy_endpoint_epochs = _enemy_endpoint_epochs(
            rows,
            snapshot if isinstance(snapshot, dict) else {},
        )
        for summary in war_summary:
            summary_war_id = _native_int(summary.get("war_id"))
            summary["enemy_endpoint_epochs"] = [
                epoch
                for epoch in enemy_endpoint_epochs
                if epoch.get("war_id") == summary_war_id
            ]
        route_evidence_issues = _route_evidence_issues(
            active_wars, controlled_armies
        )
        if route_evidence_issues:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_route_evidence_blocked",
                "selected_step": None,
                "required_step": "observable-complete-army-routes",
                "reason": "at least one controllable or non-retreating hostile active route lacks an exact target and complete matching endpoint; keep the map paused",
                "route_evidence_issues": route_evidence_issues,
                "active_wars": war_summary,
            }
        combat_armies = [
            army
            for army in controlled_armies
            if _army_tactical_state(army) == "combat"
        ]
        retreating_armies = [
            army
            for army in controlled_armies
            if _army_tactical_state(army) == "retreating"
        ]
        combat_retreat_armies = [
            army
            for army in controlled_armies
            if _army_tactical_state(army) in {"combat", "retreating"}
        ]
        stationary_threats_by_army_id: dict[
            int, list[dict[str, object]]
        ] = {}
        for controlled_army in controlled_armies:
            controlled_army_id = _native_int(
                controlled_army.get("army_id")
            )
            if (
                controlled_army_id is None
                or _native_int(
                    controlled_army.get("move_target_province_id")
                )
                is not None
                or _army_tactical_state(controlled_army)
                not in {"regular", "sieging"}
            ):
                continue
            threats = _stationary_province_threats(
                controlled_army.get("current_province_id"),
                route_threat_enemies,
            )
            if threats:
                stationary_threats_by_army_id[controlled_army_id] = threats
        threatened_stationary_armies = [
            army
            for army in controlled_armies
            if _native_int(army.get("army_id"))
            in stationary_threats_by_army_id
        ]
        start_blocking_route_armies = [
            army
            for army in controlled_armies
            if (
                (
                    (target := _native_int(army.get("move_target_province_id")))
                    is not None
                    and target > 0
                )
                or (
                    isinstance(army.get("route_province_ids"), list)
                    and bool(army["route_province_ids"])
                )
                or _army_tactical_state(army) == "moving"
                or _native_int(army.get("army_state_code")) == 7
            )
        ]
        global_route_audits: list[dict[str, object]] = []
        if army_routes_supported:
            for controlled_army in controlled_armies:
                controlled_army_id = _native_int(controlled_army.get("army_id"))
                controlled_state = _army_tactical_state(controlled_army)
                controlled_state_code = _native_int(
                    controlled_army.get("army_state_code")
                )
                controlled_target = _native_int(
                    controlled_army.get("move_target_province_id")
                )
                if (
                    controlled_army_id is None
                    or controlled_state in {"combat", "retreating", "gathering"}
                ):
                    continue
                controlled_route = controlled_army.get("route_province_ids")
                if controlled_target is None:
                    if (
                        controlled_state == "moving"
                        or controlled_state_code == 7
                        or (
                            isinstance(controlled_route, list)
                            and bool(controlled_route)
                        )
                    ):
                        global_route_audits.append(
                            {
                                "army_id": controlled_army_id,
                                "army_state": controlled_state,
                                "status": "unavailable",
                                "reason": "active controlled movement lacks an observable exact move target",
                                "conflicts": [],
                            }
                        )
                    continue
                route_audit = _audit_war_route(
                    controlled_army.get("route_province_ids"),
                    origin_province_id=_native_int(
                        controlled_army.get("current_province_id")
                    ),
                    target_province_id=controlled_target,
                    enemies=route_threat_enemies,
                )
                global_route_audits.append(
                    {
                        "army_id": controlled_army_id,
                        "army_state": controlled_state,
                        **route_audit,
                    }
                )
        unsafe_army_ids = {
            int(audit["army_id"])
            for audit in global_route_audits
            if audit.get("status") == "unsafe"
            and isinstance(audit.get("army_id"), int)
        }
        unsafe_armies = [
            army
            for army in controlled_armies
            if army.get("army_id") in unsafe_army_ids
        ]
        pursuit_army = (
            _stable_strongest_army(unsafe_armies)
            if unsafe_armies
            else _stable_strongest_army(threatened_stationary_armies)
            if threatened_stationary_armies
            else _stable_strongest_army(controlled_armies)
        )
        unavailable_routes = [
            audit
            for audit in global_route_audits
            if audit.get("status") == "unavailable"
        ]
        if unavailable_routes:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_route_audit_pending",
                "selected_step": None,
                "required_step": "game.state.army-routes",
                "reason": "at least one controllable active route is incomplete; do not advance or mutate any army until every route is auditable",
                "route_audits": global_route_audits,
                "active_wars": war_summary,
            }

        split_recovery = _split_merge_recovery(
            rows,
            snapshot if isinstance(snapshot, dict) else {},
            controlled_armies=controlled_armies,
            active_wars=active_wars,
        )
        if isinstance(split_recovery, dict) and split_recovery.get("status") in {
            "split_identity_pending",
            "split_army_set_inconsistent",
            "merge_pending",
            "merge_failed",
            "merge_postcondition_inconsistent",
        }:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_merge_recovery_blocked",
                "selected_step": None,
                "required_step": "fresh-paused-merge-postcondition",
                "reason": "the latest exact split/merge lifecycle is pending, failed, or inconsistent; keep the map paused and do not resubmit or advance time",
                "merge_recovery": split_recovery,
                "active_wars": war_summary,
            }

        tactical_war = _stable_tactical_war(active_wars)
        tactical_war_id = (
            tactical_war.get("war_id")
            if isinstance(tactical_war, dict)
            else None
        )
        tactical_enemies = [
            army
            for army in enemy_armies_from_wars(
                [tactical_war] if isinstance(tactical_war, dict) else []
            )
            if _army_tactical_state(army) != "retreating"
        ]
        visible_enemies = [
            army
            for army in tactical_enemies
            if isinstance(army.get("current_province_id"), int)
        ]
        enemy = _stable_strongest_army(visible_enemies)
        army_id = (
            pursuit_army.get("army_id")
            if isinstance(pursuit_army, dict)
            else None
        )
        tactical = _recent_war_tactics(
            rows,
            snapshot if isinstance(snapshot, dict) else {},
            army_id=army_id if isinstance(army_id, int) else None,
            war_id=(
                tactical_war_id
                if isinstance(tactical_war_id, int)
                else None
            ),
        )
        blocked_enemy_ids = set(tactical["blocked_enemy_ids"])
        blocked_province_ids = set(tactical["blocked_province_ids"])
        siege_objective_province_ids = _attacker_siege_objective_province_ids(
            [tactical_war] if isinstance(tactical_war, dict) else []
        )
        exact_objective_province_ids = war_objective_province_ids(
            [tactical_war] if isinstance(tactical_war, dict) else []
        )
        exact_objective_state_by_id = _objective_province_state_by_id(
            tactical_war if isinstance(tactical_war, dict) else None
        )
        assault_reviews = _review_all_player_assaults(
            snapshot if isinstance(snapshot, dict) else {},
            active_wars=active_wars,
            enemies=route_threat_enemies,
            commands=rows,
        )
        unobservable_assaults = [
            review
            for review in assault_reviews
            if review.get("status") == "unavailable"
        ]
        if unobservable_assaults:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_assault_observation_blocked",
                "selected_step": None,
                "required_step": "observable-exact-assault-state",
                "reason": "at least one player siege has an unavailable exact assault subdomain; do not advance a potentially active assault",
                "assault_states": unobservable_assaults,
                "active_wars": war_summary,
            }
        active_assaults = [
            review
            for review in assault_reviews
            if review.get("status") == "active"
        ]
        unsafe_assaults = [
            review
            for review in active_assaults
            if review.get("one_day_safe") is not True
        ]
        if unsafe_assaults:
            unsafe_assault = min(
                unsafe_assaults,
                key=lambda review: _native_int(review.get("siege_id"))
                or 2**31,
            )
            unsafe_siege_id = _native_int(unsafe_assault.get("siege_id"))
            stop_step = (
                stop_assault_step(unsafe_siege_id)
                if unsafe_siege_id is not None
                else None
            )
            if (
                stop_step is not None
                and unsafe_assault.get("can_stop_assault") is True
                and stop_step in available_steps
            ):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_assault_stop",
                    "selected_step": stop_step,
                    "reason": "an active exact assault failed its daily progress, casualty, or threat review; stop it before any time advance",
                    "assault_state": unsafe_assault,
                    "assault_states": active_assaults,
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_assault_stop_blocked",
                "selected_step": None,
                "required_step": stop_step or "exact-stop-assault",
                "reason": "an active assault failed its one-day safety review but no exact Stop Assault action is eligible",
                "assault_state": unsafe_assault,
                "assault_states": active_assaults,
                "active_wars": war_summary,
            }
        if combat_armies and not unsafe_armies and not threatened_stationary_armies:
            tactical_states = [
                {
                    "army_id": _native_int(army.get("army_id")),
                    "army_state": _army_tactical_state(army),
                }
                for army in combat_armies
            ]
            watch_army_ids = sorted(
                army_id
                for army in controlled_armies
                if (army_id := _native_int(army.get("army_id"))) is not None
                and army_id > 0
            )
            sentinel_watch_ready = bool(
                watch_army_ids
                and len(watch_army_ids)
                <= _BATTLE_SENTINEL_MAX_WATCH_ARMIES
                and len(watch_army_ids) == len(set(watch_army_ids))
            )
            start_date_raw = (
                _native_int(snapshot.get("date_raw"))
                if isinstance(snapshot, dict)
                else None
            )
            fallback_target_date_raw = (
                start_date_raw
                + _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS * 24
                if start_date_raw is not None
                else None
            )
            full_frames = battle_control_state.get("full_frames")
            decision_gate_dates: list[int] = []
            if start_date_raw is not None:
                for frame in (
                    full_frames if isinstance(full_frames, list) else []
                ):
                    legality = (
                        frame.get("legality")
                        if isinstance(frame, dict)
                        else None
                    )
                    gate_date_raw = (
                        _native_int(
                            legality.get("earliest_day_gate_date_raw")
                        )
                        if isinstance(legality, dict)
                        else None
                    )
                    if (
                        isinstance(frame, dict)
                        and frame.get("observed_date_raw") == start_date_raw
                        and isinstance(legality, dict)
                        and legality.get("status") == "available"
                        and legality.get("legal_now") is False
                        and legality.get("reason_codes_in_native_order")
                        == ["too_early"]
                        and gate_date_raw is not None
                        and start_date_raw < gate_date_raw
                        <= start_date_raw
                        + _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS * 24
                        and (gate_date_raw - start_date_raw) % 24 == 0
                    ):
                        decision_gate_dates.append(gate_date_raw)
            decision_target_date_raw = (
                min(decision_gate_dates)
                if decision_gate_dates
                else fallback_target_date_raw
            )
            distinct_frames: dict[int, dict[str, object]] = {}
            for frame in full_frames if isinstance(full_frames, list) else []:
                combat_id = (
                    _native_int(frame.get("combat_id"))
                    if isinstance(frame, dict)
                    else None
                )
                subject = (
                    _native_int(frame.get("subject_public_cunit_id"))
                    if isinstance(frame, dict)
                    else None
                )
                if combat_id is None or combat_id <= 0 or subject is None:
                    continue
                incumbent = distinct_frames.get(combat_id)
                incumbent_subject = (
                    _native_int(incumbent.get("subject_public_cunit_id"))
                    if isinstance(incumbent, dict)
                    else None
                )
                if incumbent_subject is None or subject < incumbent_subject:
                    distinct_frames[combat_id] = frame

            terminal_assessments = [
                assess_battle_terminal_cruise(
                    frame,
                    paused=(
                        snapshot.get("paused")
                        if isinstance(snapshot, dict)
                        else None
                    ),
                    map_ready=(
                        snapshot.get("map_ready")
                        if isinstance(snapshot, dict)
                        else None
                    ),
                    active_event_present=raw_active_event is not None,
                    pending_interaction_present=(
                        pending_interaction is not None
                    ),
                    all_controllable_army_ids=watch_army_ids,
                    watched_army_ids=watch_army_ids,
                    absolute_target_date_raw=fallback_target_date_raw,
                    speed_5_available=(
                        _BATTLE_TERMINAL_CRUISE_STEP in available_steps
                    ),
                    terminal_sentinel_implemented=(
                        sentinel_watch_ready
                        and _BATTLE_TERMINAL_CRUISE_STEP in available_steps
                    ),
                    terminal_sentinel_live_ready=battle_speed_gates[
                        "terminal_sentinel_live_ready"
                    ],
                    overwhelming_matrix_live_ready=battle_speed_gates[
                        "overwhelming_matrix_live_ready"
                    ],
                )
                for _, frame in sorted(distinct_frames.items())
            ]
            terminal_all_of_ready = bool(
                distinct_frames
                and len(terminal_assessments) == len(distinct_frames)
                and all(
                    assessment.get("production_ready") is True
                    for assessment in terminal_assessments
                )
            )
            terminal_cursor_rows = _battle_terminal_transition_query_records(
                _history_after_latest_restore(rows)
            )
            terminal_cursors: list[dict[str, object]] = []
            if terminal_all_of_ready and isinstance(snapshot, dict):
                for combat_id, frame in sorted(distinct_frames.items()):
                    subject = int(frame["subject_public_cunit_id"])
                    cursor = _current_battle_terminal_cursor(
                        terminal_cursor_rows,
                        snapshot,
                        combat_id=combat_id,
                        subject_army_id=subject,
                    )
                    if cursor is not None:
                        terminal_cursors.append(cursor)
                        continue
                    current_query_attempted = any(
                        record.get("combat_id") == combat_id
                        and record.get("subject_army_id") == subject
                        and record.get("after_terminal_sequence") is None
                        and record.get("queried_snapshot_id")
                        == snapshot.get("snapshot_id")
                        and record.get("queried_revision")
                        == snapshot.get("revision")
                        and record.get("queried_native_revision")
                        == snapshot.get("native_revision")
                        for record in terminal_cursor_rows
                    )
                    if (
                        not current_query_attempted
                        and QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
                        in available_capabilities
                    ):
                        cursor_step = query_battle_terminal_transition_v1_step(
                            combat_id, subject
                        )
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_battle_terminal_cursor_query",
                            "selected_step": cursor_step,
                            "reason": (
                                "freeze the current terminal-journal sequence "
                                "for every qualifying CombatID before the "
                                "zero-intermediate-pause terminal cruise"
                            ),
                            "battle_combat_id": combat_id,
                            "battle_subject_army_id": subject,
                            "watch_army_ids": watch_army_ids,
                            "battle_terminal_cruise_assessments": (
                                terminal_assessments
                            ),
                        }
                    terminal_all_of_ready = False
                    break
            if (
                terminal_all_of_ready
                and len(terminal_cursors) == len(distinct_frames)
            ):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_global_battle_terminal_cruise",
                    "selected_step": _BATTLE_TERMINAL_CRUISE_STEP,
                    "reason": (
                        "every distinct active CombatID passed the production "
                        "terminal-cruise policy; run at speed 5 until the "
                        "native terminal or semantic sentinel stops once"
                    ),
                    "timeline_policy": "battle_terminal_cruise_speed_5",
                    "timeline_speed": 5,
                    "sentinel_mode": "terminal_or_sentinel",
                    "absolute_target_date_raw": fallback_target_date_raw,
                    "watch_army_ids": watch_army_ids,
                    "terminal_journal_cursors": terminal_cursors,
                    "combat_retreat_armies": tactical_states,
                    "battle_control_frames": battle_control_state.get(
                        "evidence", []
                    ),
                    "battle_transitions": battle_control_state.get(
                        "transitions", []
                    ),
                    "battle_terminal_cruise_assessments": (
                        terminal_assessments
                    ),
                    "active_wars": war_summary,
                }
            if (
                battle_speed_gates["decision_sentinel_live_ready"]
                and sentinel_watch_ready
                and _BATTLE_DECISION_EPOCH_ADVANCE_STEP in available_steps
                and start_date_raw is not None
                and decision_target_date_raw is not None
            ):
                decision_step = battle_decision_epoch_advance_step(
                    decision_target_date_raw
                )
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_global_battle_decision_epoch",
                    "selected_step": decision_step,
                    "reason": (
                        "the global tactical audit passed; run at speed 3 "
                        "until the native decision-epoch sentinel observes a "
                        "phase, winner, roster, route, contact, retreat, "
                        "terminal, native-pause, or absolute-bound change"
                    ),
                    "timeline_policy": "battle_decision_epoch_speed_3",
                    "timeline_speed": 3,
                    "sentinel_mode": "decision_epoch",
                    "absolute_target_date_raw": decision_target_date_raw,
                    "watch_army_ids": watch_army_ids,
                    "combat_retreat_armies": tactical_states,
                    "battle_control_frames": battle_control_state.get(
                        "evidence", []
                    ),
                    "battle_transitions": battle_control_state.get(
                        "transitions", []
                    ),
                    "active_wars": war_summary,
                }
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_global_battle_control_progress",
                    "selected_step": "life-advance",
                    "reason": "every active subject has an available exact battle-control frame bound to this paused revision; all other routes and stationary positions passed the global audit, so advance at most one day and query every continuing battle again",
                    "combat_retreat_armies": tactical_states,
                    "battle_control_frames": battle_control_state.get(
                        "evidence", []
                    ),
                    "battle_transitions": battle_control_state.get(
                        "transitions", []
                    ),
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_global_battle_control_progress_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "the current exact battle-control frames are available, but the backend cannot perform their required one-day observation slice",
                "combat_retreat_armies": tactical_states,
                "battle_control_frames": battle_control_state.get(
                    "evidence", []
                ),
                "battle_transitions": battle_control_state.get(
                    "transitions", []
                ),
                "active_wars": war_summary,
            }
        if (
            retreating_armies
            and not unsafe_armies
            and not threatened_stationary_armies
        ):
            tactical_states = [
                {
                    "army_id": _native_int(army.get("army_id")),
                    "army_state": _army_tactical_state(army),
                }
                for army in retreating_armies
            ]
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_global_combat_retreat_progress",
                    "selected_step": "life-advance",
                    "reason": "at least one controllable army is retreating; all other routes and stationary positions passed the global audit, so advance at most one day and re-observe every army",
                    "combat_retreat_armies": tactical_states,
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_global_combat_retreat_progress_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "a controllable army is retreating, but the backend cannot perform its required one-day observation slice",
                "combat_retreat_armies": tactical_states,
                "active_wars": war_summary,
            }
        if (
            isinstance(split_recovery, dict)
            and (
                split_recovery.get("status") == "merge_requires_rendezvous"
                or (
                    split_recovery.get("status") == "merge_waiting_for_idle"
                    and not unsafe_armies
                    and not threatened_stationary_armies
                )
            )
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_merge_rendezvous_blocked",
                "selected_step": None,
                "required_step": "safe-exact-rendezvous",
                "reason": "the exact split pair is separated or not merge-idle, and this first counter-policy stage has no proven safe rendezvous intent; keep both armies paused instead of issuing independent orders",
                "merge_recovery": split_recovery,
                "active_wars": war_summary,
            }
        if (
            isinstance(split_recovery, dict)
            and split_recovery.get("status") == "ready_to_merge"
        ):
            pair_ids = {
                _native_int(split_recovery.get("original_army_id")),
                _native_int(split_recovery.get("sibling_army_id")),
            }
            other_unsafe = [
                army
                for army in unsafe_armies
                if _native_int(army.get("army_id")) not in pair_ids
            ]
            other_threatened = [
                army
                for army in threatened_stationary_armies
                if _native_int(army.get("army_id")) not in pair_ids
            ]
            if not other_unsafe and not other_threatened:
                merge_step = split_recovery.get("merge_step")
                if isinstance(merge_step, str) and merge_step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_merge_recovery",
                        "selected_step": merge_step,
                        "reason": "the exact latest split pair is still co-located, but no exact combat prediction proves both halves independently safe; merge the sibling back into the original army without advancing time",
                        "merge_recovery": split_recovery,
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_merge_recovery_unsupported",
                    "selected_step": None,
                    "required_step": merge_step,
                    "reason": "the exact co-located split pair requires recovery, but the generation-bound Merge action is not currently eligible; keep the map paused",
                    "merge_recovery": split_recovery,
                    "active_wars": war_summary,
                }
        if (
            isinstance(split_recovery, dict)
            and split_recovery.get("status") == "merge_completed"
            and not unsafe_armies
            and not threatened_stationary_armies
        ):
            merged_army_id = _native_int(
                split_recovery.get("original_army_id")
            )
            merged_army = next(
                (
                    army
                    for army in controlled_armies
                    if _native_int(army.get("army_id")) == merged_army_id
                ),
                None,
            )
            merged_target = (
                _native_int(merged_army.get("move_target_province_id"))
                if isinstance(merged_army, dict)
                else None
            )
            merged_origin = (
                _native_int(merged_army.get("current_province_id"))
                if isinstance(merged_army, dict)
                else None
            )
            if (
                merged_army_id is not None
                and merged_target is not None
                and merged_origin is not None
            ):
                fresh_after_merge = _fresh_move_route_preview(
                    rows,
                    army_id=merged_army_id,
                    origin_province_id=merged_origin,
                    target_province_id=merged_target,
                    date_raw=_native_int(snapshot.get("date_raw")),
                )
                preview_step = preview_move_army_step(
                    merged_army_id, merged_target
                )
                if fresh_after_merge is None:
                    if preview_step in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_merge_route_preview",
                            "selected_step": preview_step,
                            "reason": "the confirmed Merge invalidated every older same-date move intent and preview; preview the destination army's current target again before advancing",
                            "merge_recovery": split_recovery,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_merge_route_preview_unsupported",
                        "selected_step": None,
                        "required_step": preview_step,
                        "reason": "the confirmed Merge invalidated the old route, but a fresh same-origin preview is not currently advertised; keep the map paused",
                        "merge_recovery": split_recovery,
                        "active_wars": war_summary,
                    }
                refreshed_audit = _audit_war_route(
                    fresh_after_merge.get("route_province_ids"),
                    origin_province_id=merged_origin,
                    target_province_id=merged_target,
                    enemies=route_threat_enemies,
                )
                if refreshed_audit.get("status") != "safe":
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_merge_route_preview_unsafe",
                        "selected_step": None,
                        "required_step": "safe-exact-war-route",
                        "reason": "the first post-Merge preview is not safe against the current hostile route matrix; do not advance the retained pre-Merge route",
                        "route_audit": refreshed_audit,
                        "merge_recovery": split_recovery,
                        "active_wars": war_summary,
                    }
                observed_after_merge = _normalized_remaining_route(
                    merged_army
                )
                previewed_after_merge = refreshed_audit.get(
                    "route_province_ids"
                )
                if observed_after_merge != previewed_after_merge:
                    refreshed_move_step = move_army_step(
                        merged_army_id, merged_target
                    )
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_merge_route_refresh_blocked",
                        "selected_step": None,
                        "required_step": refreshed_move_step,
                        "reason": "the first safe post-Merge preview does not match the retained route; the current action surface intentionally does not resubmit a same-target move, so keep the map paused for a future exact replace-route primitive",
                        "route_audit": refreshed_audit,
                        "observed_route_province_ids": observed_after_merge,
                        "merge_recovery": split_recovery,
                        "active_wars": war_summary,
                    }
                if "life-advance" in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_merge_route_progress",
                        "selected_step": "life-advance",
                        "reason": "the first post-Merge preview is safe and exactly matches the observed remaining route; advance one bounded slice from this fresh intent epoch",
                        "route_audit": refreshed_audit,
                        "merge_recovery": split_recovery,
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_merge_route_progress_unsupported",
                    "selected_step": None,
                    "required_step": "life-advance",
                    "reason": "the post-Merge route is freshly revalidated but the backend cannot advance its bounded slice",
                    "route_audit": refreshed_audit,
                    "merge_recovery": split_recovery,
                    "active_wars": war_summary,
                }
        if (
            active_assaults
            and not unsafe_armies
            and not threatened_stationary_armies
        ):
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_assault_daily_progress",
                    "selected_step": "life-advance",
                    "reason": "every active exact assault and every controlled route passed the current one-day review; advance exactly one day and re-observe all armies",
                    "assault_state": active_assaults[0],
                    "assault_states": active_assaults,
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_assault_daily_progress_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "active assaults may only advance through one-day paused-to-paused slices",
                "assault_state": active_assaults[0],
                "assault_states": active_assaults,
                "active_wars": war_summary,
            }
        exact_occupation_rows_complete = bool(
            exact_objective_province_ids
            and isinstance(snapshot, dict)
            and snapshot.get("war_objective_occupation_supported") is True
            and list(exact_objective_state_by_id)
            == exact_objective_province_ids
        )
        exact_occupation_fully_observable = bool(
            exact_occupation_rows_complete
            and all(
                exact_objective_state_by_id[province_id].get(
                    "occupation_observable"
                )
                is True
                for province_id in exact_objective_province_ids
            )
        )
        completed_objectives = set(
            tactical.get("completed_objective_province_ids", [])
        )
        if exact_occupation_rows_complete:
            player_occupied_objectives = _player_occupied_objective_ids(
                snapshot if isinstance(snapshot, dict) else {},
                tactical_war if isinstance(tactical_war, dict) else None,
                exact_objective_state_by_id,
            )
            for province_id in exact_objective_province_ids:
                if (
                    exact_objective_state_by_id[province_id].get(
                        "occupation_observable"
                    )
                    is not True
                ):
                    continue
                completed_objectives.discard(province_id)
                if province_id in player_occupied_objectives:
                    completed_objectives.add(province_id)
        exact_objective_province_ids = _rank_exact_objectives(
            exact_objective_province_ids,
            exact_objective_state_by_id,
            fort_supported=(
                isinstance(snapshot, dict)
                and snapshot.get("war_objective_fort_level_supported") is True
            ),
            garrison_supported=(
                isinstance(snapshot, dict)
                and snapshot.get("war_objective_garrison_supported") is True
            ),
        )
        if exact_occupation_fully_observable:
            # Only a fully observable exact set can retire the legacy rally
            # fallback. Unknown provinces retain their prior completion state.
            siege_objective_province_ids = list(
                exact_objective_province_ids
            )
        all_siege_objectives_completed = bool(siege_objective_province_ids)
        siege_objective_province_ids = [
            province_id
            for province_id in siege_objective_province_ids
            if province_id not in completed_objectives
        ]
        exact_objective_province_ids = [
            province_id
            for province_id in exact_objective_province_ids
            if province_id not in completed_objectives
        ]
        all_siege_objectives_completed &= not siege_objective_province_ids
        army_state = (
            _army_tactical_state(pursuit_army)
            if isinstance(pursuit_army, dict)
            else None
        )
        current_province_id = (
            pursuit_army.get("current_province_id")
            if isinstance(pursuit_army, dict)
            else None
        )
        enemy_threat_province_ids = {
            province_id
            for row in route_threat_enemies
            for province_id in (
                row.get("current_province_id"),
                row.get("move_target_province_id"),
            )
            if isinstance(province_id, int)
            and not isinstance(province_id, bool)
        }
        observed_route_target = (
            _native_int(pursuit_army.get("move_target_province_id"))
            if isinstance(pursuit_army, dict)
            else None
        )
        stationary_threats = (
            list(stationary_threats_by_army_id.get(int(army_id), []))
            if isinstance(army_id, int)
            else []
        )
        exact_siege_status = _current_exact_siege_status(
            snapshot if isinstance(snapshot, dict) else {},
            tactical_war_id=(
                tactical_war_id
                if isinstance(tactical_war_id, int)
                else None
            ),
            province_id=(
                current_province_id
                if isinstance(current_province_id, int)
                else None
            ),
            objective_state_by_id=exact_objective_state_by_id,
            commands=rows,
        )
        exact_assault_state = _current_exact_assault_state(
            snapshot if isinstance(snapshot, dict) else {},
            province_id=(
                current_province_id
                if isinstance(current_province_id, int)
                else None
            ),
            objective_state_by_id=exact_objective_state_by_id,
            stationary_threats=stationary_threats,
            siege_status=exact_siege_status,
            commands=rows,
            tactical_war_id=(
                tactical_war_id
                if isinstance(tactical_war_id, int)
                else None
            ),
        )
        exact_siege_rejection = (
            exact_siege_status
            if current_province_id in siege_objective_province_ids
            and isinstance(exact_siege_status, dict)
            and (
                exact_siege_status.get("status") in {
                    "not_player_besieging",
                    "insufficient_strength",
                    "stalled",
                }
                or (
                    exact_siege_status.get("status") == "not_active"
                    and army_state == "sieging"
                )
            )
            else None
        )
        if (
            isinstance(exact_siege_rejection, dict)
            and isinstance(current_province_id, int)
        ):
            blocked_province_ids.add(current_province_id)
        if army_state == "gathering":
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_gathering_progress",
                    "selected_step": "life-advance",
                    "reason": "the raised army is still gathering; advance before previewing or issuing movement",
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_gathering_progress_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "the raised army must finish gathering before route preview",
                "active_wars": war_summary,
            }
        if isinstance(exact_assault_state, dict):
            assault_status = exact_assault_state.get("status")
            siege_id = _native_int(exact_assault_state.get("siege_id"))
            if assault_status == "unavailable":
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_assault_observation_blocked",
                    "selected_step": None,
                    "required_step": "observable-exact-assault-state",
                    "reason": "the exact adapter advertises assault state but the current SiegeID is not atomically observable; do not advance an unknown potentially active assault",
                    "assault_state": exact_assault_state,
                    "active_wars": war_summary,
                }
            if assault_status == "active" and siege_id is not None:
                if exact_assault_state.get("one_day_safe") is True:
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_assault_daily_progress",
                            "selected_step": "life-advance",
                            "reason": "the same exact SiegeID remains assaulting and its current one-day progress, casualties, and enemy convergence projection are safe; advance exactly one day and re-observe",
                            "assault_state": exact_assault_state,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_assault_daily_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "an active assault may only advance through one-day paused-to-paused slices",
                        "assault_state": exact_assault_state,
                        "active_wars": war_summary,
                    }
                stop_step = stop_assault_step(siege_id)
                if (
                    exact_assault_state.get("can_stop_assault") is True
                    and stop_step in available_steps
                ):
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_assault_stop",
                        "selected_step": stop_step,
                        "reason": "the next assault day no longer satisfies the exact progress, casualty, or threat budget; stop it before advancing time",
                        "assault_state": exact_assault_state,
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_assault_stop_blocked",
                    "selected_step": None,
                    "required_step": stop_step,
                    "reason": "the active assault failed its one-day safety review but no exact Stop Assault action is currently eligible",
                    "assault_state": exact_assault_state,
                    "active_wars": war_summary,
                }
            if (
                assault_status == "inactive"
                and siege_id is not None
                and exact_assault_state.get("walls_breached") is True
                and exact_assault_state.get("can_start_assault") is True
                and exact_assault_state.get("one_day_safe") is True
                and not start_blocking_route_armies
                and not unsafe_armies
            ):
                start_step = start_assault_step(siege_id)
                if start_step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_assault_start",
                        "selected_step": start_step,
                        "reason": "the walls are breached, CK3's exact validator accepts Start Assault, and the projected next day stays inside the progress, casualty, and threat budget",
                        "assault_state": exact_assault_state,
                        "active_wars": war_summary,
                    }
        if (
            isinstance(exact_siege_status, dict)
            and exact_siege_status.get("status") == "progressing"
            and observed_route_target is None
            and not stationary_threats
            and current_province_id in siege_objective_province_ids
            and "life-advance" in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_siege_progress",
                "selected_step": "life-advance",
                "reason": "the exact paused state confirms a player siege; advance one seven-day progress slice",
                "siege_state": exact_siege_status,
                "active_wars": war_summary,
            }
        if (
            army_state == "sieging"
            and observed_route_target is None
            and not stationary_threats
            and exact_siege_status is None
            and (
                current_province_id in siege_objective_province_ids
                or (
                    not siege_objective_province_ids
                    and not exact_occupation_fully_observable
                )
            )
            and "life-advance" in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_siege_progress",
                "selected_step": "life-advance",
                "reason": "the native army is sieging; advance the occupation",
                "active_wars": war_summary,
            }
        if army_state == "retreating":
            retreat_days = int(tactical.get("retreat_days", 0))
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": (
                        "native_war_retreat_progress"
                        if retreat_days < _NATIVE_RETREAT_MAX_GAME_DAYS
                        else "native_war_recovery_wait"
                    ),
                    "selected_step": "life-advance",
                    "reason": (
                        "the native army is retreating; wait within the 30-day deadline"
                        if retreat_days < _NATIVE_RETREAT_MAX_GAME_DAYS
                        else "the retreat exceeded its normal deadline; keep advancing bounded intervals until CK3 releases the army"
                    ),
                    "retreat_days": retreat_days,
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_no_safe_target",
                "selected_step": None,
                "required_step": "query-safe-war-objectives",
                "reason": "the native retreat exceeded its bounded deadline",
                "active_wars": war_summary,
            }
        if army_state == "combat":
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_battle_control_progress",
                    "selected_step": "life-advance",
                    "reason": "the active subject has an available exact battle-control frame bound to this paused revision; advance at most one day, then query and verify the same CombatID again",
                    "battle_control_frames": battle_control_state.get(
                        "evidence", []
                    ),
                    "battle_transitions": battle_control_state.get(
                        "transitions", []
                    ),
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_battle_control_progress_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "the exact battle-control frame is current, but this backend cannot advance its required bounded time slice",
                "battle_control_frames": battle_control_state.get(
                    "evidence", []
                ),
                "battle_transitions": battle_control_state.get(
                    "transitions", []
                ),
                "active_wars": war_summary,
            }

        passive_route_audit: dict[str, object] | None = None
        if (
            isinstance(army_id, int)
            and isinstance(pursuit_army, dict)
            and isinstance(observed_route_target, int)
        ):
            observed_intent = _active_native_move_intent(
                rows,
                snapshot if isinstance(snapshot, dict) else {},
                army_id=army_id,
                target_province_id=observed_route_target,
            )
            if army_routes_supported:
                passive_route_audit = next(
                    (
                        audit
                        for audit in global_route_audits
                        if audit.get("army_id") == army_id
                        and audit.get("target_province_id")
                        == observed_route_target
                    ),
                    _audit_war_route(
                        pursuit_army.get("route_province_ids"),
                        origin_province_id=current_province_id,
                        target_province_id=observed_route_target,
                        enemies=route_threat_enemies,
                    ),
                )
                if passive_route_audit["status"] == "unavailable":
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_route_audit_pending",
                        "selected_step": None,
                        "required_step": "game.state.army-routes",
                        "reason": "the accepted move has no complete passive route yet; do not advance into an unaudited path",
                        "route_audit": passive_route_audit,
                        "active_wars": war_summary,
                    }
                if passive_route_audit["status"] == "unsafe":
                    contact_horizon = (
                        _fresh_route_contact_horizon(
                            rows,
                            snapshot,
                            army_id=army_id,
                            origin_province_id=current_province_id,
                            target_province_id=observed_route_target,
                            hostile_army_ids=route_threat_enemy_ids,
                            route_province_ids=pursuit_army.get(
                                "route_province_ids"
                            ),
                        )
                        if route_contact_scope_supported
                        else None
                    )
                    if (
                        route_contact_scope_supported
                        and contact_horizon is None
                    ):
                        horizon_step = query_route_contact_horizon_step(
                            army_id,
                            observed_route_target,
                            route_threat_enemy_ids,
                        )
                        if horizon_step in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_route_contact_horizon",
                                "selected_step": horizon_step,
                                "reason": "read the exact one-day native arrival/contact horizon before advancing an intersecting active route",
                                "route_audit": passive_route_audit,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_route_contact_horizon_unsupported",
                            "selected_step": None,
                            "required_step": horizon_step,
                            "reason": "the intersecting active route requires a fresh exact one-day contact horizon",
                            "route_audit": passive_route_audit,
                            "active_wars": war_summary,
                        }
                    if (
                        isinstance(contact_horizon, dict)
                        and contact_horizon.get("one_day_contact_free") is True
                    ):
                        passive_route_audit = {
                            **passive_route_audit,
                            "status": "safe_one_day_contact_horizon",
                            "contact_horizon": contact_horizon,
                        }
                        moving_conjunction = (
                            _moving_route_contact_horizon_conjunction(
                                rows,
                                snapshot,
                                controlled_armies=controlled_armies,
                                subject_army_id=army_id,
                                subject_contact_horizon=contact_horizon,
                                hostile_army_ids=route_threat_enemy_ids,
                                enemies=route_threat_enemies,
                            )
                        )
                        missing_moving = moving_conjunction["missing"]
                        if missing_moving:
                            missing = missing_moving[0]
                            sibling_query_step = missing.get("query_step")
                            if (
                                isinstance(sibling_query_step, str)
                                and sibling_query_step in available_steps
                            ):
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": "native_war_sibling_route_contact_horizon",
                                    "selected_step": sibling_query_step,
                                    "reason": "the main route proof cannot cover another moving army's closed current-Province occupancy; query that sibling's own exact one-day timeline before advancing global time",
                                    "route_audit": passive_route_audit,
                                    "moving_contact_horizons": moving_conjunction,
                                    "active_wars": war_summary,
                                }
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_sibling_route_contact_horizon_unsupported",
                                "selected_step": None,
                                "required_step": sibling_query_step,
                                "reason": "another moving army requires its own exact one-day contact horizon, but the current backend does not advertise that query",
                                "route_audit": passive_route_audit,
                                "moving_contact_horizons": moving_conjunction,
                                "active_wars": war_summary,
                            }
                        if moving_conjunction["unavailable"]:
                            unavailable = moving_conjunction["unavailable"][0]
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_sibling_route_contact_horizon_unavailable",
                                "selected_step": None,
                                "required_step": unavailable.get("query_step"),
                                "reason": "the sibling's own route-contact query was already attempted in this unchanged frame but did not yield a usable exact proof; keep time paused without resubmitting it",
                                "route_audit": passive_route_audit,
                                "moving_contact_horizons": moving_conjunction,
                                "active_wars": war_summary,
                            }
                        if moving_conjunction["conflicting"]:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_sibling_route_contact_horizon_conflict",
                                "selected_step": None,
                                "required_step": "safe-exact-war-route",
                                "reason": "a sibling moving army has a malformed route or a fresh timed conflict that is not the narrow unavoidable current-Province transition",
                                "route_audit": passive_route_audit,
                                "moving_contact_horizons": moving_conjunction,
                                "active_wars": war_summary,
                            }
                        proven_moving_ids = {
                            _native_int(candidate.get("army_id"))
                            for candidate in (
                                moving_conjunction["covered"]
                                + moving_conjunction["unavoidable"]
                            )
                        }
                        other_unsafe_armies = [
                            candidate
                            for candidate in unsafe_armies
                            if candidate.get("army_id") != army_id
                            and _native_int(candidate.get("army_id"))
                            not in proven_moving_ids
                        ]
                        stationary_contact_horizons: list[
                            dict[str, object]
                        ] = []
                        uncovered_stationary_armies: list[
                            dict[str, object]
                        ] = []
                        for candidate in sorted(
                            threatened_stationary_armies,
                            key=lambda row: _native_int(row.get("army_id"))
                            or 2**31,
                        ):
                            candidate_id = _native_int(
                                candidate.get("army_id")
                            )
                            candidate_province_id = _native_int(
                                candidate.get("current_province_id")
                            )
                            if (
                                candidate_id is None
                                or candidate_province_id is None
                            ):
                                uncovered_stationary_armies.append(candidate)
                                continue
                            try:
                                stationary_contact_free = (
                                    stationary_province_contact_free_in_horizon(
                                        contact_horizon,
                                        candidate_province_id,
                                    )
                                )
                            except ValueError:
                                stationary_contact_free = False
                            if stationary_contact_free:
                                stationary_contact_horizons.append(
                                    {
                                        "army_id": candidate_id,
                                        "current_province_id": (
                                            candidate_province_id
                                        ),
                                        "proof_subject_army_id": army_id,
                                        "horizon_start_date_raw": (
                                            contact_horizon.get(
                                                "horizon_start_date_raw"
                                            )
                                        ),
                                        "horizon_end_date_raw": (
                                            contact_horizon.get(
                                                "horizon_end_date_raw"
                                            )
                                        ),
                                        "one_day_contact_free": True,
                                    }
                                )
                            else:
                                uncovered_stationary_armies.append(candidate)
                        if (
                            other_unsafe_armies
                            or uncovered_stationary_armies
                            or [
                                candidate
                                for candidate in combat_retreat_armies
                                if candidate.get("army_id") != army_id
                            ]
                        ):
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_route_contact_horizon_global_blocked",
                                "selected_step": None,
                                "required_step": "complete-global-route-contact-horizon",
                                "reason": "one army's contact-free horizon cannot authorize time while another controllable army remains unsafe or threatened",
                                "route_audit": passive_route_audit,
                                "other_unsafe_armies": other_unsafe_armies,
                                "threatened_stationary_armies": uncovered_stationary_armies,
                                "stationary_contact_horizons": stationary_contact_horizons,
                                "active_wars": war_summary,
                            }
                        unavoidable_siblings = moving_conjunction[
                            "unavoidable"
                        ]
                        if unavoidable_siblings:
                            if len(unavoidable_siblings) != 1:
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": "native_war_sibling_unavoidable_contact_global_blocked",
                                    "selected_step": None,
                                    "required_step": "single-proof-bound-unavoidable-contact-transition",
                                    "reason": "more than one moving sibling has an unavoidable current-Province contact in the same day; one subject proof cannot verify all resulting transitions",
                                    "route_audit": passive_route_audit,
                                    "moving_contact_horizons": moving_conjunction,
                                    "active_wars": war_summary,
                                }
                            unavoidable_sibling = unavoidable_siblings[0]
                            sibling_advance_step = unavoidable_sibling.get(
                                "advance_step"
                            )
                            sibling_audit = {
                                "army_id": unavoidable_sibling.get("army_id"),
                                "status": "unavoidable_current_province_contact",
                                "target_province_id": unavoidable_sibling.get(
                                    "target_province_id"
                                ),
                                "contact_horizon": unavoidable_sibling.get(
                                    "contact_horizon"
                                ),
                            }
                            if (
                                isinstance(sibling_advance_step, str)
                                and sibling_advance_step in available_steps
                            ):
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": "native_war_unavoidable_contact_transition",
                                    "selected_step": sibling_advance_step,
                                    "reason": "the sibling's own fresh timeline proves an unavoidable closed-end current-Province contact while every other moving route is contact-free; use that subject's strict one-day contact transition",
                                    "route_audit": sibling_audit,
                                    "stationary_contact_horizons": stationary_contact_horizons,
                                    "moving_contact_horizons": moving_conjunction,
                                    "active_wars": war_summary,
                                }
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_unavoidable_contact_transition_unsupported",
                                "selected_step": None,
                                "required_step": sibling_advance_step,
                                "reason": "the sibling has its own unavoidable current-Province proof, but the multi-proof capability conjunction does not advertise that strict transition",
                                "route_audit": sibling_audit,
                                "moving_contact_horizons": moving_conjunction,
                                "active_wars": war_summary,
                            }
                        advance_step = advance_route_contact_horizon_step(
                            army_id,
                            observed_route_target,
                            route_threat_enemy_ids,
                        )
                        if advance_step in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_route_contact_horizon_progress",
                                "selected_step": advance_step,
                                "reason": "the exact native timeline proves the intersecting active route contact-free for the next day",
                                "route_audit": passive_route_audit,
                                "stationary_contact_horizons": stationary_contact_horizons,
                                "moving_contact_horizons": moving_conjunction,
                                "move_intent": observed_intent,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_route_contact_horizon_progress_unsupported",
                            "selected_step": None,
                            "required_step": advance_step,
                            "reason": "the exact route is contact-free for one day but this backend cannot advance it",
                            "route_audit": passive_route_audit,
                        }
                    if (
                        isinstance(contact_horizon, dict)
                        and unavoidable_current_province_contact_in_horizon(
                            contact_horizon
                        )
                    ):
                        unavoidable_audit = {
                            **passive_route_audit,
                            "status": "unavoidable_current_province_contact",
                            "contact_horizon": contact_horizon,
                        }
                        other_unsafe_armies = [
                            candidate
                            for candidate in unsafe_armies
                            if candidate.get("army_id") != army_id
                        ]
                        stationary_contact_horizons: list[
                            dict[str, object]
                        ] = []
                        uncovered_stationary_armies: list[
                            dict[str, object]
                        ] = []
                        for candidate in sorted(
                            threatened_stationary_armies,
                            key=lambda row: _native_int(row.get("army_id"))
                            or 2**31,
                        ):
                            candidate_id = _native_int(
                                candidate.get("army_id")
                            )
                            candidate_province_id = _native_int(
                                candidate.get("current_province_id")
                            )
                            if (
                                candidate_id is None
                                or candidate_province_id is None
                            ):
                                uncovered_stationary_armies.append(candidate)
                                continue
                            try:
                                stationary_contact_free = (
                                    stationary_province_contact_free_in_horizon(
                                        contact_horizon,
                                        candidate_province_id,
                                    )
                                )
                            except ValueError:
                                stationary_contact_free = False
                            if stationary_contact_free:
                                stationary_contact_horizons.append(
                                    {
                                        "army_id": candidate_id,
                                        "current_province_id": (
                                            candidate_province_id
                                        ),
                                        "proof_subject_army_id": army_id,
                                        "horizon_start_date_raw": (
                                            contact_horizon.get(
                                                "horizon_start_date_raw"
                                            )
                                        ),
                                        "horizon_end_date_raw": (
                                            contact_horizon.get(
                                                "horizon_end_date_raw"
                                            )
                                        ),
                                        "one_day_contact_free": True,
                                    }
                                )
                            else:
                                uncovered_stationary_armies.append(candidate)
                        other_combat_retreat_armies = [
                            candidate
                            for candidate in combat_retreat_armies
                            if candidate.get("army_id") != army_id
                        ]
                        if (
                            other_unsafe_armies
                            or uncovered_stationary_armies
                            or other_combat_retreat_armies
                        ):
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_route_contact_horizon_global_blocked",
                                "selected_step": None,
                                "required_step": "complete-global-route-contact-horizon",
                                "reason": "the unavoidable subject contact cannot authorize time while another controllable army remains unsafe or threatened",
                                "route_audit": unavoidable_audit,
                                "other_unsafe_armies": other_unsafe_armies,
                                "threatened_stationary_armies": uncovered_stationary_armies,
                                "stationary_contact_horizons": stationary_contact_horizons,
                                "combat_retreat_armies": other_combat_retreat_armies,
                                "active_wars": war_summary,
                            }
                        advance_step = advance_route_contact_horizon_step(
                            army_id,
                            observed_route_target,
                            route_threat_enemy_ids,
                        )
                        if advance_step in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_unavoidable_contact_transition",
                                "selected_step": advance_step,
                                "reason": "the fresh exact timeline proves every next-day conflict is at the subject's current Province and its committed edge cannot complete before contact; advance exactly one day, then re-observe combat or changed hostile intent",
                                "route_audit": unavoidable_audit,
                                "stationary_contact_horizons": stationary_contact_horizons,
                                "move_intent": observed_intent,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_unavoidable_contact_transition_unsupported",
                            "selected_step": None,
                            "required_step": advance_step,
                            "reason": "the exact next-day current-Province contact is unavoidable, but no proof-bound one-day transition is available",
                            "route_audit": unavoidable_audit,
                            "active_wars": war_summary,
                        }
                    blocked_province_ids.add(observed_route_target)
                elif "life-advance" in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_route_progress",
                        "selected_step": "life-advance",
                        "reason": "the remaining native route is still clear of observable enemy convergence",
                        "route_audit": passive_route_audit,
                        "move_intent": observed_intent,
                        "active_wars": war_summary,
                    }
                else:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_route_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the remaining native route is safe but this backend cannot advance it",
                        "route_audit": passive_route_audit,
                        "move_intent": observed_intent,
                        "active_wars": war_summary,
                    }
            elif (
                observed_intent is not None
                and observed_route_target not in enemy_threat_province_ids
            ):
                if "life-advance" in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress",
                        "selected_step": "life-advance",
                        "reason": "the accepted native route is still observable and safe; finish it before reconsidering siege priority",
                        "pursuit": {
                            "war_id": tactical_war_id,
                            "army_id": army_id,
                            "target_army_id": None,
                            "target_province_id": observed_route_target,
                            "target_soldiers": None,
                            "target_source": (
                                "war_objective_province"
                                if observed_route_target
                                in set(
                                    war_objective_province_ids(
                                        [tactical_war]
                                        if isinstance(tactical_war, dict)
                                        else []
                                    )
                                )
                                else "enemy_primary_default_raise_province"
                            ),
                            "objective_kind": "siege",
                        },
                        "move_intent": observed_intent,
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_pursuit_progress_unsupported",
                    "selected_step": None,
                    "required_step": "life-advance",
                    "reason": "the accepted native siege route is active but this backend cannot advance it",
                    "move_intent": observed_intent,
                    "active_wars": war_summary,
                }

        active_route_unsafe = bool(
            isinstance(passive_route_audit, dict)
            and passive_route_audit.get("status") == "unsafe"
        )
        objective_kind = "pursuit"
        preview_selected_target: int | None = None
        selected_route_audit: dict[str, object] | None = None
        route_preview_required = bool(
            move_route_preview_supported
        )
        route_exact_candidates = [
            province_id
            for province_id in exact_objective_province_ids
            if province_id in siege_objective_province_ids
        ]
        if (
            route_preview_required
            and isinstance(army_id, int)
            and isinstance(current_province_id, int)
            and route_exact_candidates
        ):
            route_rejections: list[dict[str, object]] = []
            # The exact set is already ranked by observable siege quality.
            # Stop at its first fully safe route instead of globally scanning
            # every objective for the shortest path.  This is not a fixed cap:
            # rejected candidates still fall through to the rest of the set.
            for objective_rank, province_id in enumerate(route_exact_candidates):
                if province_id in blocked_province_ids:
                    route_rejections.append(
                        {"target_province_id": province_id, "status": "blocked"}
                    )
                    continue
                if province_id == current_province_id:
                    if active_route_unsafe:
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": "cannot_replace_unsafe_active_route",
                            }
                        )
                        continue
                    if stationary_threats:
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": "unsafe",
                                "conflicts": stationary_threats,
                            }
                        )
                        continue
                    preview_selected_target = province_id
                    selected_route_audit = {
                        "status": "arrived",
                        "target_province_id": province_id,
                    }
                    break
                preview = _fresh_move_route_preview(
                    rows,
                    army_id=army_id,
                    origin_province_id=current_province_id,
                    target_province_id=province_id,
                    date_raw=_native_int(
                        snapshot.get("date_raw")
                        if isinstance(snapshot, dict)
                        else None
                    ),
                )
                if (
                    isinstance(preview, dict)
                    and preview.get("status") == "deferred"
                ):
                    if stationary_threats:
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": (
                                    "deferred_while_stationary_province_threatened"
                                ),
                            }
                        )
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": (
                                "native_war_move_readiness_observation_required"
                            ),
                            "selected_step": None,
                            "required_step": (
                                "query-native-army-move-readiness"
                            ),
                            "reason": (
                                "the same-frame native preview rejected this "
                                "canonical threatened CUnit before route "
                                "construction; target enumeration cannot "
                                "change the subject's move readiness"
                            ),
                            "route_preview": preview,
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    if (
                        active_route_unsafe
                        or isinstance(exact_siege_rejection, dict)
                    ):
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": (
                                    "deferred_while_active_route_unsafe"
                                    if active_route_unsafe
                                    else "deferred_while_exact_siege_rejected"
                                ),
                            }
                        )
                        continue
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_route_preview_deferred",
                            "selected_step": "life-advance",
                            "reason": "the army was not route-preview-ready at this date and origin; advance once before retrying",
                            "route_preview": preview,
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_route_preview_deferred_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the deferred route preview requires time to advance",
                        "route_preview": preview,
                        "route_rejections": route_rejections,
                        "active_wars": war_summary,
                    }
                if preview is None:
                    preview_step = preview_move_army_step(army_id, province_id)
                    if preview_step in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_route_preview",
                            "selected_step": preview_step,
                            "reason": "preview the exact objective route at the current date and origin before moving",
                            "route_preview": {
                                "status": "required",
                                "army_id": army_id,
                                "origin_province_id": current_province_id,
                                "target_province_id": province_id,
                            },
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_route_preview_unsupported",
                        "selected_step": None,
                        "required_step": preview_step,
                        "reason": "the exact objective requires a fresh route preview before movement",
                        "route_rejections": route_rejections,
                        "active_wars": war_summary,
                    }
                audit = _audit_war_route(
                    preview.get("route_province_ids"),
                    origin_province_id=current_province_id,
                    target_province_id=province_id,
                    enemies=route_threat_enemies,
                )
                if (
                    audit["status"] == "unsafe"
                    and route_contact_scope_supported
                ):
                    contact_horizon = _fresh_route_contact_horizon(
                        rows,
                        snapshot,
                        army_id=army_id,
                        origin_province_id=current_province_id,
                        target_province_id=province_id,
                        hostile_army_ids=route_threat_enemy_ids,
                        route_province_ids=preview.get("route_province_ids"),
                    )
                    if contact_horizon is None:
                        horizon_step = query_route_contact_horizon_step(
                            army_id, province_id, route_threat_enemy_ids
                        )
                        if horizon_step in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_candidate_contact_horizon",
                                "selected_step": horizon_step,
                                "reason": "resolve a geometric route intersection with the exact one-day native arrival/contact timeline",
                                "route_preview": preview,
                                "route_audit": audit,
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_candidate_contact_horizon_unsupported",
                            "selected_step": None,
                            "required_step": horizon_step,
                            "reason": "the intersecting candidate route requires a fresh exact one-day contact horizon",
                            "route_preview": preview,
                            "route_audit": audit,
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    if contact_horizon.get("one_day_contact_free") is True:
                        audit = {
                            **audit,
                            "status": "safe_one_day_contact_horizon",
                            "contact_horizon": contact_horizon,
                        }
                if audit["status"] not in {
                    "safe",
                    "safe_one_day_contact_horizon",
                }:
                    route_rejections.append(audit)
                    blocked_province_ids.add(province_id)
                    continue
                rollback_failure = _matching_rollback_war_failure(
                    snapshot if isinstance(snapshot, dict) else {},
                    war_id=(
                        tactical_war_id
                        if isinstance(tactical_war_id, int)
                        else None
                    ),
                    army_id=army_id,
                    origin_province_id=current_province_id,
                    target_province_id=province_id,
                    route_province_ids=audit.get("route_province_ids"),
                )
                if rollback_failure is not None:
                    route_rejections.append(
                        {
                            "status": "rolled_back_route_failure",
                            "target_province_id": province_id,
                            "route_province_ids": list(
                                audit.get("route_province_ids", [])
                            ),
                            "failure": rollback_failure,
                        }
                    )
                    blocked_province_ids.add(province_id)
                    continue
                preview_selected_target = province_id
                selected_route_audit = {
                    **audit,
                    "selection": {
                        "policy": "first_safe_ranked_exact_objective",
                        "route_hops": len(
                            audit.get("route_province_ids", [])
                        ),
                        "objective_rank": objective_rank,
                        "evaluated_candidate_count": objective_rank + 1,
                        "unevaluated_candidate_count": max(
                            0,
                            len(route_exact_candidates) - objective_rank - 1,
                        ),
                    },
                }
                break
            if preview_selected_target is None:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_no_safe_exact_route",
                    "selected_step": None,
                    "required_step": "safe-exact-war-route",
                    "reason": "every remaining exact objective route is blocked or observably intersects a non-retreating enemy",
                    "route_rejections": route_rejections,
                    "active_wars": war_summary,
                }
        if (
            active_route_unsafe
            and preview_selected_target is None
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_no_safe_exact_route",
                "selected_step": None,
                "required_step": "safe-exact-war-route",
                "reason": "the active route became unsafe and no remaining exact objective has a safe preview",
                "route_rejections": [passive_route_audit],
                "active_wars": war_summary,
            }
        if preview_selected_target is not None:
            target_province_id = preview_selected_target
            enemy = None
            target_source = "war_objective_province"
            objective_kind = "siege"
        elif exact_objective_province_ids:
            safe = [
                province_id
                for province_id in exact_objective_province_ids
                if province_id not in blocked_province_ids
                and province_id not in enemy_threat_province_ids
                and not (
                    province_id == current_province_id
                    and stationary_threats
                )
                and not (
                    blocked_enemy_ids
                    and any(
                        row.get("current_province_id") == province_id
                        for row in visible_enemies
                    )
                )
            ]
            target_province_id = safe[0] if safe else None
            enemy = None
            target_source = "war_objective_province"
            objective_kind = "siege"
        else:
            enemy = None
            target_province_id = None
            target_source = "exact_objective_unavailable"
        if target_province_id is None:
            if (
                exact_occupation_fully_observable
                and all_siege_objectives_completed
                and not stationary_threats
                and not unsafe_armies
            ):
                if "life-advance" in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_objective_settlement_progress",
                        "selected_step": "life-advance",
                        "reason": "every authoritative exact occupation objective is complete and the global route matrix is safe; advance one bounded settlement slice without selecting an enemy target",
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_objective_settlement_progress_unsupported",
                    "selected_step": None,
                    "required_step": "life-advance",
                    "reason": "all authoritative exact objectives are complete, but the backend cannot advance the bounded war-settlement slice",
                    "active_wars": war_summary,
                }
            if isinstance(exact_siege_rejection, dict):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_siege_stalled",
                    "selected_step": None,
                    "required_step": "progress-capable-exact-war-objective",
                    "reason": "the current exact siege is not progressing and no alternate exact objective is available",
                    "siege_state": exact_siege_rejection,
                    "active_wars": war_summary,
                }
            if stationary_threats:
                exact = current_province_id in exact_objective_province_ids
                return {
                    "policy": "one-life-turn-v1",
                    "phase": (
                        "native_war_no_safe_exact_route"
                        if exact
                        else "native_war_no_safe_target"
                    ),
                    "selected_step": None,
                    "required_step": (
                        "safe-exact-war-route"
                        if exact
                        else "query-safe-war-objectives"
                    ),
                    "reason": "the stationary province is under observable enemy convergence and no alternate target is available",
                    "route_rejections": stationary_threats,
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_counterpolicy_hold",
                "selected_step": None,
                "required_step": "safe-exact-war-objective-or-exact-combat-prediction",
                "reason": "no safe exact objective is available and the adapter publishes no exact combat prediction; do not infer native power from soldiers or chase a visible enemy province",
                "tactical_state": tactical,
                "active_wars": war_summary,
            }
        if isinstance(pursuit_army, dict) and isinstance(target_province_id, int):
            army_id = pursuit_army.get("army_id")
            if isinstance(army_id, int):
                step = move_army_step(army_id, target_province_id)
                pursuit = {
                    "war_id": tactical_war_id,
                    "army_id": army_id,
                    "target_army_id": (
                        enemy.get("army_id")
                        if isinstance(enemy, dict)
                        else None
                    ),
                    "target_province_id": target_province_id,
                    "target_soldiers": (
                        enemy.get("soldiers")
                        if isinstance(enemy, dict)
                        else None
                    ),
                    "target_source": target_source,
                    "objective_kind": objective_kind,
                }
                if selected_route_audit is not None:
                    pursuit["route_audit"] = selected_route_audit
                active_move_intent = _active_native_move_intent(
                    rows,
                    snapshot if isinstance(snapshot, dict) else {},
                    army_id=army_id,
                    target_province_id=target_province_id,
                )
                move_backoff = _deferred_move_backoff(
                    rows,
                    snapshot if isinstance(snapshot, dict) else {},
                    step,
                )
                if stationary_threats and (
                    active_move_intent is not None
                    or (
                        move_backoff is not None
                        and move_backoff.get("retry_due") is not True
                    )
                    or target_province_id
                    in {
                        pursuit_army.get("current_province_id"),
                        pursuit_army.get("move_target_province_id"),
                    }
                ):
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_stationary_threat_blocked",
                        "selected_step": None,
                        "required_step": "replace-threatened-stationary-position",
                        "reason": "enemy convergence threatens the stationary army; deferred, pending, or same-province alternatives cannot justify advancing time",
                        "pursuit": pursuit,
                        "route_rejections": stationary_threats,
                        "move_intent": active_move_intent,
                        "move_backoff": move_backoff,
                        "active_wars": war_summary,
                    }
                if active_route_unsafe:
                    if (
                        active_move_intent is None
                        and (
                            move_backoff is None
                            or move_backoff.get("retry_due") is True
                        )
                        and target_province_id
                        not in {
                            pursuit_army.get("current_province_id"),
                            pursuit_army.get("move_target_province_id"),
                        }
                        and step in available_steps
                    ):
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_unsafe_route_reroute",
                            "selected_step": step,
                            "reason": "replace the observably unsafe active route before any game-time advance",
                            "pursuit": pursuit,
                            "route_audit": passive_route_audit,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_unsafe_route_blocked",
                        "selected_step": None,
                        "required_step": "replace-unsafe-native-route",
                        "reason": "an unsafe route is still active; deferred, pending, or same-province alternatives cannot justify advancing it",
                        "pursuit": pursuit,
                        "route_audit": passive_route_audit,
                        "move_intent": active_move_intent,
                        "move_backoff": move_backoff,
                        "active_wars": war_summary,
                    }
                if isinstance(exact_siege_rejection, dict) and (
                    active_move_intent is not None
                    or (
                        move_backoff is not None
                        and move_backoff.get("retry_due") is not True
                    )
                    or target_province_id
                    in {
                        pursuit_army.get("current_province_id"),
                        pursuit_army.get("move_target_province_id"),
                    }
                ):
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_siege_exit_blocked",
                        "selected_step": None,
                        "required_step": "replace-rejected-siege-position",
                        "reason": "the exact siege was rejected; deferred, pending, or same-province movement cannot justify advancing time",
                        "siege_state": exact_siege_rejection,
                        "pursuit": pursuit,
                        "move_intent": active_move_intent,
                        "move_backoff": move_backoff,
                        "active_wars": war_summary,
                    }
                if active_move_intent is not None:
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": "the accepted native move intent is still active; advance the war without submitting the same move again",
                            "pursuit": pursuit,
                            "move_intent": active_move_intent,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the native move intent is still active but this backend cannot advance the march",
                        "pursuit": pursuit,
                        "move_intent": active_move_intent,
                        "active_wars": war_summary,
                    }
                if move_backoff is not None and not move_backoff["retry_due"]:
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": "the army was not move-ready; use the 7/14/30-day retry backoff",
                            "pursuit": pursuit,
                            "move_backoff": move_backoff,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the deferred native move needs time to advance but this backend cannot do so",
                        "pursuit": pursuit,
                        "move_backoff": move_backoff,
                        "active_wars": war_summary,
                    }
                if target_province_id in {
                    pursuit_army.get("current_province_id"),
                    pursuit_army.get("move_target_province_id"),
                }:
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_pursuit_progress",
                            "selected_step": "life-advance",
                            "reason": (
                                "the native army is already at or moving toward the stable siege objective; advance the occupation"
                                if objective_kind == "siege"
                                else "the native army is already at or moving toward the strongest visible enemy; advance the battle"
                            ),
                            "pursuit": pursuit,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the army is already pursuing the enemy but this backend cannot advance time",
                        "pursuit": pursuit,
                        "active_wars": war_summary,
                    }
                if step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_pursuit",
                        "selected_step": step,
                        "reason": (
                            "move the strongest controllable army to the strongest visible enemy army"
                            if target_source == "enemy_army"
                            else "move the army along a previewed safe route to the next exact war objective"
                            if target_source == "war_objective_province"
                            else "move toward the primary opponent's default rally province fallback"
                        ),
                        "pursuit": pursuit,
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_pursuit_unsupported",
                    "selected_step": None,
                    "required_step": step,
                    "reason": "the backend cannot issue the required native army move",
                    "pursuit": pursuit,
                    "active_wars": war_summary,
                }
        if stationary_threats:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_stationary_threat_blocked",
                "selected_step": None,
                "required_step": "replace-threatened-stationary-position",
                "reason": "enemy convergence threatens the stationary army and no immediate reroute is available",
                "route_rejections": stationary_threats,
                "active_wars": war_summary,
            }
        if isinstance(exact_siege_rejection, dict):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_siege_exit_blocked",
                "selected_step": None,
                "required_step": "replace-rejected-siege-position",
                "reason": "the exact siege was rejected and no safe replacement route is active; do not advance time",
                "siege_state": exact_siege_rejection,
                "active_wars": war_summary,
            }
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_reconnaissance",
                "selected_step": "life-advance",
                "reason": "no enemy province is currently published; advance one bounded native interval and inspect again",
                "active_wars": war_summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_reconnaissance_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": "the active war has no published enemy province and time cannot advance",
            "active_wars": war_summary,
        }

    if controlled_armies:
        army = _stable_strongest_army(controlled_armies)
        army_id = army.get("army_id") if isinstance(army, dict) else None
        if isinstance(army_id, int):
            step = disband_army_step(army_id)
            if step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_postwar_disband",
                    "selected_step": step,
                    "reason": "no active war remains; disband the strongest residual player army",
                    "army_id": army_id,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_postwar_disband_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "a player army remains after the war but this backend cannot disband it",
                "army_id": army_id,
            }

    last = rows[-1] if rows else None
    last_error = str(last.get("error", "")) if last is not None else ""
    if "one-life death terminal visible:" in last_error:
        return {
            "policy": "one-life-turn-v1",
            "phase": "terminal_visible",
            "selected_step": "death-terminal",
            "reason": "player death is visibly stable; settle and end this episode",
        }
    if "ordinary event interrupted" in last_error:
        return {
            "policy": "one-life-turn-v1",
            "phase": "visible_interruption",
            "selected_step": "resolve-current-event",
            "reason": "the previous timeline step stopped on a visible CK3 event",
        }

    if _latest_index(rows, "death-terminal"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "terminal",
            "selected_step": "strategy-review",
            "reason": "player death already ended this one-life episode",
        }

    if not _latest_index(rows, "save-checkpoint"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "baseline",
            "selected_step": "save-checkpoint",
            "reason": "create a native CK3 recovery point before strategic mutations",
        }

    latest_checkpoint_index = _latest_index(rows, "save-checkpoint")
    latest_postwar_disband_index = _latest_prefix_index(
        rows, "disband-army-"
    )
    if (
        latest_postwar_disband_index > latest_checkpoint_index
        and not player_armies
    ):
        if "save-checkpoint" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_postwar_checkpoint",
                "selected_step": "save-checkpoint",
                "reason": (
                    "the last active war is gone and every residual player "
                    "army has been disbanded; persist this verified peaceful "
                    "state before starting long-term governance"
                ),
                "postwar_disband_history_index": (
                    latest_postwar_disband_index
                ),
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_postwar_checkpoint_unsupported",
            "selected_step": None,
            "required_step": "save-checkpoint",
            "reason": (
                "the verified postwar cleanup is newer than the durable "
                "checkpoint, but this backend cannot save it"
            ),
            "postwar_disband_history_index": latest_postwar_disband_index,
        }

    if (
        cross_run_focus == "succession"
        and not _latest_index(rows, "succession-review")
        and "succession-review" in available_steps
    ):
        return {
            "policy": "one-life-turn-v1",
            "phase": "cross_run_succession_first",
            "selected_step": "succession-review",
            "reason": "the previous episode promoted succession review to the first strategic action",
        }

    native_relationship_known = (
        isinstance(played_character, dict)
        and {
            "betrothed_id",
            "primary_spouse_id",
            "spouse_ids",
        }
        <= played_character.keys()
    )
    native_relationship_present = (
        native_relationship_known
        and (
            played_character.get("betrothed_id") is not None
            or played_character.get("primary_spouse_id") is not None
            or bool(played_character.get("spouse_ids"))
        )
    )
    marriage_attempt = _native_marriage_attempt_state(
        rows, snapshot if isinstance(snapshot, dict) else {}
    )
    war_attempted = bool(
        _latest_index(rows, QUERY_DECLARABLE_WARS_STEP)
        or _latest_prefix_index(rows, "declare-war-", successful_only=False)
        or _latest_prefix_index(rows, "enforce-demands-", successful_only=False)
    )
    defer_marriage_for_war = cross_run_focus == "war" and not war_attempted
    if (
        not native_relationship_present
        and (marriage_attempt is not None or not defer_marriage_for_war)
    ):
        if (
            isinstance(marriage_attempt, dict)
            and marriage_attempt.get("status") == "pending"
        ):
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_arrange_marriage_response_wait",
                    "selected_step": "life-advance",
                    "reason": "advance one bounded interval while waiting for the exact spouse or betrothal relationship",
                    "marriage_intent": marriage_attempt,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_response_wait_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "the native proposal is unresolved but this backend cannot advance time",
                "marriage_intent": marriage_attempt,
            }

        retry_candidate_id = (
            marriage_attempt.get("candidate_character_id")
            if isinstance(marriage_attempt, dict)
            and marriage_attempt.get("status") == "retry"
            else None
        )
        raw_marriage_choices = (
            snapshot.get("arrange_marriage_choices")
            if isinstance(snapshot, dict)
            else None
        )
        marriage_choices = sorted(
            (
                choice
                for choice in raw_marriage_choices
                if isinstance(choice, dict)
                and isinstance(choice.get("choice_id"), str)
                and isinstance(choice.get("candidate_character_id"), int)
            ),
            key=lambda choice: (
                choice.get("candidate_character_id") == retry_candidate_id,
                int(choice["candidate_character_id"]),
                str(choice["choice_id"]),
            ),
        ) if isinstance(raw_marriage_choices, list) else []
        if marriage_choices:
            choice = marriage_choices[0]
            step = arrange_marriage_step(str(choice["choice_id"]))
            if step in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_arrange_marriage",
                    "selected_step": step,
                    "reason": (
                        "submit a fresh valid candidate after the previous proposal failed or timed out"
                        if retry_candidate_id is not None
                        else "submit the first currently valid native marriage choice for this one-life ruler"
                    ),
                    "marriage_choice": choice,
                    "previous_marriage_intent": marriage_attempt,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_unsupported",
                "selected_step": None,
                "required_step": step,
                "reason": "the selected native marriage choice is not executable",
                "marriage_choice": choice,
            }
        query_anchor = (
            int(marriage_attempt.get("retry_index", 0))
            if isinstance(marriage_attempt, dict)
            and marriage_attempt.get("status") == "retry"
            else 0
        )
        marriage_query_index = _latest_index(
            rows,
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
            successful_only=False,
        )
        successful_marriage_query_index = _latest_index(
            rows, QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
        )
        life_advance_index = _latest_life_advance_index(rows)
        marriage_query_attempts = sum(
            1
            for fallback_index, row in enumerate(rows, start=1)
            if _effective_command(row) == QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
            and (
                row.get("index")
                if isinstance(row.get("index"), int)
                else fallback_index
            )
            > query_anchor
        )
        marriage_query_limit = (
            _MARRIAGE_RETRY_QUERY_LIMIT
            if query_anchor
            else _EMPTY_MARRIAGE_QUERY_LIMIT
        )
        latest_query_result = _latest_effective_result(
            rows, QUERY_ARRANGE_MARRIAGE_CHOICES_STEP
        )
        lost_nonempty_query_cache = (
            successful_marriage_query_index > query_anchor
            and successful_marriage_query_index == marriage_query_index
            and isinstance(latest_query_result, dict)
            and isinstance(
                latest_query_result.get("arrange_marriage_choices"), list
            )
            and bool(latest_query_result["arrange_marriage_choices"])
        )
        if (
            marriage_query_attempts < marriage_query_limit
            and QUERY_ARRANGE_MARRIAGE_CHOICES_STEP in available_steps
            and (
                marriage_query_index <= query_anchor
                or successful_marriage_query_index != marriage_query_index
                or life_advance_index > marriage_query_index
                or lost_nonempty_query_cache
            )
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_discovery",
                "selected_step": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "reason": (
                    "rebuild the native choice cache after reconnecting or refresh candidates after a failed proposal"
                    if lost_nonempty_query_cache or query_anchor
                    else "refresh native marriage choices after the world changed"
                    if marriage_query_index
                    else "enumerate valid native marriage choices before starting the first war"
                ),
                "previous_marriage_intent": marriage_attempt,
            }
        if (
            marriage_query_attempts < marriage_query_limit
            and marriage_query_index > life_advance_index
            and "life-advance" in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_arrange_marriage_refresh",
                "selected_step": "life-advance",
                "reason": "the latest native marriage query was empty; advance time once before refreshing it",
                "previous_marriage_intent": marriage_attempt,
            }

    declaration_index = _latest_prefix_index(rows, "declare-war-")
    life_advance_index = _latest_life_advance_index(rows)
    if declaration_index > life_advance_index:
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_declaration_progress",
                "selected_step": "life-advance",
                "reason": "the native declaration was submitted; advance once for the war state to materialize",
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_declaration_progress_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": "the native declaration was submitted but this backend cannot advance the map",
        }

    war_entry_assessment_rows = _same_frame_war_entry_assessments(
        rows, snapshot if isinstance(snapshot, dict) else None
    )
    declaration = _preferred_native_declaration(
        snapshot.get("declarable_wars") if isinstance(snapshot, dict) else None,
        war_entry_assessments=war_entry_assessment_rows,
    )
    if isinstance(declaration, dict):
        declaration_target = declaration.get("target_character_id")
        assessment_step = (
            query_war_entry_assessments_step([declaration_target])
            if isinstance(declaration_target, int)
            and not isinstance(declaration_target, bool)
            and 0 < declaration_target <= 2**31 - 1
            else None
        )
        assessment_row = (
            war_entry_assessment_rows.get(declaration_target)
            if isinstance(declaration_target, int)
            and not isinstance(declaration_target, bool)
            else None
        )
        fresh_assessment = isinstance(assessment_row, dict)
        if (
            not fresh_assessment
            and isinstance(assessment_step, str)
            and assessment_step in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_entry_assessment",
                "selected_step": assessment_step,
                "reason": (
                    "read CK3's exact strategic power lane for the current "
                    "declaration target before considering time advance or war"
                ),
                "declaration": declaration,
            }
        power_eu = _war_entry_power_eu_projection(assessment_row)
        power_component = power_eu.get("native_power_component")
        conservative_margin = (
            power_component.get("conservative_self_power_margin_raw")
            if isinstance(power_component, dict)
            else None
        )
        if (
            isinstance(conservative_margin, int)
            and not isinstance(conservative_margin, bool)
            and conservative_margin < 0
            and isinstance(snapshot, dict)
        ):
            raw_declarations = snapshot.get("declarable_wars")
            unassessed = [
                row
                for row in (
                    raw_declarations
                    if isinstance(raw_declarations, list)
                    else []
                )
                if isinstance(row, dict)
                and isinstance(row.get("target_character_id"), int)
                and not isinstance(row.get("target_character_id"), bool)
                and row["target_character_id"]
                not in war_entry_assessment_rows
            ]
            alternative = _preferred_native_declaration(unassessed)
            alternative_target = (
                alternative.get("target_character_id")
                if isinstance(alternative, dict)
                else None
            )
            alternative_step = (
                query_war_entry_assessments_step([alternative_target])
                if isinstance(alternative_target, int)
                and not isinstance(alternative_target, bool)
                and 0 < alternative_target <= 2**31 - 1
                else None
            )
            if (
                isinstance(alternative_step, str)
                and alternative_step in available_steps
            ):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_entry_assessment_alternative",
                    "selected_step": alternative_step,
                    "reason": (
                        "the current target depends on more strategic power "
                        "than the actor's own adjusted base; inspect the next "
                        "legal target on the same paused frame before choosing "
                        "a diagnostic war-entry candidate"
                    ),
                    "declaration": alternative,
                    "rejected_power_declaration": declaration,
                    "rejected_war_entry_assessment": dict(assessment_row),
                    "rejected_war_entry_expected_utility": power_eu,
                }
        # The declaration row proves legality and the war-entry query now
        # contributes exact native power/network risk to candidate ordering
        # and the EU ledger.  It is still not a battle forecast, campaign-cost
        # model, exit assessment, or calibrated utility policy, so this partial
        # EU record cannot authorize an automatic declaration.  Missing entry
        # evidence is a NO_DECLARE decision, not a reason to stop an otherwise
        # playable lifetime: advance one bounded interval when that primitive
        # is available and re-observe the world on the next turn.
        required_capabilities = [
            QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
            "game.forecast.combat-monte-carlo-v1",
            "game.command.query-war-entry-assessments-v1-N",
        ]
        shared_evidence = {
            "required_capabilities": required_capabilities,
            "declaration": declaration,
            "war_entry_assessment": (
                dict(assessment_row) if fresh_assessment else None
            ),
            "war_entry_expected_utility": power_eu,
        }
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_entry_no_declare",
                "selected_step": "life-advance",
                "reason": (
                    "the native declaration is legally available and exact "
                    "strategic power is consumed when present, but participant "
                    "bounds, combat forecast, campaign costs, exit outcomes, "
                    "and calibrated utility are incomplete; choose "
                    "NO_DECLARE and advance one bounded interval"
                ),
                "decision": {
                    "policy": "war-entry-minimal-defer-v1",
                    "outcome": "NO_DECLARE",
                    "declaration_id": declaration.get("declaration_id"),
                    "target_character_id": declaration.get(
                        "target_character_id"
                    ),
                    "casus_belli_key": declaration.get("casus_belli_key"),
                    "native_power_assessment_consumed": fresh_assessment,
                    "eu_lower_raw": power_eu.get("eu_lower_raw"),
                    "advance_contract": "native_life_advance",
                    "automatic_declaration_enabled": False,
                    "native_ai_equivalent": False,
                    "semantic_optimal": False,
                    "missing_components": list(
                        power_eu.get("missing_components", [])
                    ),
                },
                **shared_evidence,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_entry_evidence_required",
            "selected_step": None,
            "reason": (
                "the native declaration is legally available and exact "
                "strategic power is consumed when present, but automatic war "
                "entry still requires participant bounds, a combat forecast, "
                "campaign costs, exit outcomes, and a calibrated utility policy"
            ),
            **shared_evidence,
        }

    if QUERY_DECLARABLE_WARS_STEP in available_steps:
        query_index = _latest_index(rows, QUERY_DECLARABLE_WARS_STEP)
        if query_index > life_advance_index and "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_discovery_progress",
                "selected_step": "life-advance",
                "reason": "no war was currently declarable; advance once before the next native query",
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_discovery",
            "selected_step": QUERY_DECLARABLE_WARS_STEP,
            "reason": "enumerate current native war declarations before using visual diplomacy",
        }

    if not _latest_index(rows, "dynasty-review"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "current_life_family",
            "selected_step": "dynasty-review",
            "reason": "read the current ruler's spouse, children and available family",
        }
    if not _latest_index(rows, "succession-review"):
        return {
            "policy": "one-life-turn-v1",
            "phase": "current_life_domain",
            "selected_step": "succession-review",
            "reason": "measure title loss that matters while the current ruler is alive",
        }

    if not _latest_index(rows, "marriage-confirm-response"):
        marriage_review_index = _latest_index(rows, "marriage-review")
        marriage_alliance_index = _latest_index(rows, "marriage-alliance")
        if not marriage_review_index:
            step = "marriage-review"
            reason = "compare visible child marriage candidates for a current-life alliance"
        elif not marriage_alliance_index:
            step = "marriage-alliance"
            reason = "send the best visible current-life alliance proposal"
        else:
            confirmation_attempt = _latest_index(
                rows, "marriage-confirm-response", successful_only=False
            )
            elapsed_after_attempt = max(
                _latest_index(rows, "war-advance-week"),
                _latest_index(rows, "resolve-current-event"),
                _latest_life_advance_index(rows),
                _latest_index(rows, "economic-event-cycle"),
            )
            if not confirmation_attempt or elapsed_after_attempt > confirmation_attempt:
                step = "marriage-confirm-response"
                reason = "check and accept the pending visible betrothal response"
            else:
                step = "war-advance-week"
                reason = "advance one bounded week so the pending proposal can resolve"
        return {
            "policy": "one-life-turn-v1",
            "phase": "current_life_marriage",
            "selected_step": step,
            "reason": reason,
        }

    victory_index = _latest_index(rows, "war-enforce-demands")
    if not victory_index:
        if not _latest_index(rows, "war-declare-palermo"):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_entry_evidence_required",
                "selected_step": None,
                "reason": (
                    "the legacy Palermo declaration has no same-epoch power "
                    "assessment, combat forecast, campaign-cost model, or "
                    "exit assessment; do not declare through the visual fallback"
                ),
                "required_capabilities": [
                    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
                    "game.forecast.combat-monte-carlo-v1",
                    "game.command.query-war-entry-assessments-v1-N",
                ],
                "declaration": {
                    "source": "legacy-visual-palermo",
                    "step": "war-declare-palermo",
                },
            }
        elif not _latest_index(rows, "war-raise-all"):
            step = "war-raise-all"
            reason = "raise the army for the active Palermo war"
        elif not _latest_index(rows, "war-siege-palermo"):
            step = "war-siege-palermo"
            reason = "move the selected army to the visibly confirmed Palermo fort"
        else:
            latest_status_index = _latest_index(rows, "war-status")
            latest_advance_index = max(
                _latest_index(rows, "war-advance-week"),
                _latest_index(rows, "war-advance-month"),
            )
            status = _latest_effective_result(rows, "war-status")
            war_status = status.get("war_status") if isinstance(status, dict) else None
            score = (
                war_status.get("war_score_percent")
                if isinstance(war_status, dict)
                else None
            )
            if latest_status_index <= latest_advance_index:
                step = "war-status"
                reason = "re-read visible war score after the latest campaign advance"
            elif isinstance(score, int) and score >= 100:
                step = "war-enforce-demands"
                reason = "visible war score reached 100 percent"
            else:
                step = "war-advance-week"
                reason = "continue the active siege for one bounded week"
        return {
            "policy": "one-life-turn-v1",
            "phase": "palermo_war",
            "selected_step": step,
            "reason": reason,
        }

    disband_index = _latest_index(rows, "war-disband-armies")
    if not disband_index or disband_index < victory_index:
        return {
            "policy": "one-life-turn-v1",
            "phase": "postwar",
            "selected_step": "war-disband-armies",
            "reason": "remove raised-army costs after the confirmed victory",
        }

    checkpoint_index = _latest_index(rows, "save-checkpoint")
    strategic_change_index = max(
        victory_index,
        disband_index,
        _latest_index(rows, "marriage-confirm-response"),
    )
    if checkpoint_index < strategic_change_index:
        return {
            "policy": "one-life-turn-v1",
            "phase": "post_milestone_checkpoint",
            "selected_step": "save-checkpoint",
            "reason": "persist the completed war and alliance milestones in a native save",
        }

    cycles_since_checkpoint = sum(
        1
        for row in rows
        if row.get("ok") is True
        and (
            is_life_advance_step(_effective_command(row))
            or _effective_command(row) == "economic-event-cycle"
        )
        and (
            not isinstance(row.get("index"), int)
            or int(row["index"]) > checkpoint_index
        )
    )
    if cycles_since_checkpoint >= 3:
        step = "save-checkpoint"
        reason = "three completed event cycles have elapsed since the last native save"
        phase = "periodic_checkpoint"
    else:
        step = "life-advance"
        reason = "advance the current life to the next visible event and reassess the realm"
        phase = "current_life_loop"
    return {
        "policy": "one-life-turn-v1",
        "phase": phase,
        "selected_step": step,
        "reason": reason,
    }


def _stable_strongest_army(
    armies: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    rows = [army for army in armies if isinstance(army.get("army_id"), int)]
    if not rows:
        return None
    return max(
        rows,
        key=lambda army: (
            army.get("soldiers")
            if isinstance(army.get("soldiers"), int)
            else -1,
            -int(army["army_id"]),
        ),
    )


def _stable_tactical_war(
    wars: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    rows = [war for war in wars if isinstance(war.get("war_id"), int)]
    if not rows:
        return None

    def priority(war: dict[str, object]) -> tuple[int, int]:
        exact_attacker = (
            war.get("player_side") == "attacker"
            and war.get("player_is_primary_war_leader") is True
            and bool(war_objective_province_ids([war]))
        )
        rank = (
            0
            if exact_attacker
            else 1
            if war.get("player_is_primary_war_leader") is True
            else 2
        )
        return rank, int(war["war_id"])

    return min(rows, key=priority)


def _attacker_siege_objective_province_ids(
    wars: Iterable[dict[str, object]],
) -> list[int]:
    """Order exact target-title capitals before the legacy rally fallback."""
    exact_qualifying: list[dict[str, object]] = []
    fallback_qualifying: list[dict[str, object]] = []
    for war in wars:
        score = war.get("player_relative_war_score")
        if (
            war.get("player_side") == "attacker"
            and war.get("player_is_primary_war_leader") is True
            and isinstance(score, int)
            and not isinstance(score, bool)
        ):
            exact_qualifying.append(war)
            if score > 0:
                fallback_qualifying.append(war)
    exact = war_objective_province_ids(exact_qualifying)
    fallback = enemy_primary_default_raise_province_ids(fallback_qualifying)
    return exact + [
        province_id for province_id in fallback if province_id not in exact
    ]


def _progress_siege_objectives(war: dict[str, object]) -> list[int]:
    exact = war.get("war_objective_province_ids")
    result = [
        province_id
        for province_id in (exact if isinstance(exact, list) else [])
        if _native_int(province_id) is not None
    ]
    fallback = _native_int(war.get("enemy_primary_default_raise_province_id"))
    if fallback is not None and fallback not in result:
        result.append(fallback)
    return result


def _objective_province_state_by_id(
    war: dict[str, object] | None,
) -> dict[int, dict[str, object]]:
    states = war.get("objective_province_states") if isinstance(war, dict) else None
    result: dict[int, dict[str, object]] = {}
    for state in states if isinstance(states, list) else []:
        if not isinstance(state, dict):
            continue
        province_id = _native_int(state.get("province_id"))
        if province_id is not None and province_id not in result:
            result[province_id] = state
    return result


def _player_occupied_objective_ids(
    snapshot: dict[str, object],
    war: dict[str, object] | None,
    state_by_id: dict[int, dict[str, object]],
) -> set[int]:
    known_player_side: set[int] = set()
    played_character = snapshot.get("played_character")
    if isinstance(played_character, dict):
        character_id = _native_int(played_character.get("character_id"))
        if character_id is not None:
            known_player_side.add(character_id)
    armies = war.get("allied_armies") if isinstance(war, dict) else None
    for army in armies if isinstance(armies, list) else []:
        if not isinstance(army, dict):
            continue
        owner_id = _native_int(army.get("owner_character_id"))
        if owner_id is not None:
            known_player_side.add(owner_id)
    return {
        province_id
        for province_id, state in state_by_id.items()
        if state.get("occupation_observable") is True
        and state.get("is_occupied") is True
        and state.get("occupying_character_id") in known_player_side
    }


def _rank_exact_objectives(
    province_ids: list[int],
    state_by_id: dict[int, dict[str, object]],
    *,
    fort_supported: bool,
    garrison_supported: bool,
) -> list[int]:
    if not fort_supported and not garrison_supported:
        return list(province_ids)
    native_order = {
        province_id: index for index, province_id in enumerate(province_ids)
    }

    def rank(province_id: int) -> tuple[int, int, int]:
        state = state_by_id.get(province_id, {})
        fort = _native_int(state.get("fort_level"))
        garrison = _native_int(state.get("garrison_size"))
        return (
            fort if fort_supported and fort is not None else 2**31 - 1,
            (
                garrison
                if garrison_supported and garrison is not None
                else 2**31 - 1
            ),
            native_order[province_id],
        )

    return sorted(province_ids, key=rank)


def _open_assault_lifecycles(
    commands: list[dict[str, object]],
) -> list[dict[str, int]]:
    """Return exact Start lifecycles not closed by a proven Stop.

    A submitted ACK is deliberately insufficient: only the driver's
    ``assault_started``/``assault_stopped`` paused postconditions participate.
    Successful restore starts a new factual branch and isolates older rows.
    """
    opened: dict[tuple[int, int, int], dict[str, int]] = {}
    for fallback_index, row in enumerate(
        _history_after_latest_restore(commands), start=1
    ):
        if row.get("ok") is not True:
            continue
        command = _effective_command(row)
        result = _effective_command_result(row)
        if not isinstance(result, dict):
            continue
        action = result.get("assault_action")
        if not isinstance(action, dict):
            candidate = result.get("war_action")
            action = candidate if isinstance(candidate, dict) else None
        if not isinstance(action, dict):
            continue
        siege_id = _native_int(action.get("siege_id"))
        war_id = _native_int(action.get("war_id"))
        province_id = _native_int(action.get("province_id"))
        if (
            siege_id is None
            or siege_id <= 0
            or war_id is None
            or war_id <= 0
            or province_id is None
            or province_id <= 0
        ):
            continue
        key = (war_id, province_id, siege_id)
        status = action.get("status")
        if (
            status == "assault_started"
            and parse_start_assault_step(command) == siege_id
        ):
            raw_index = row.get("index")
            opened[key] = {
                "war_id": war_id,
                "province_id": province_id,
                "siege_id": siege_id,
                "started_index": (
                    raw_index
                    if isinstance(raw_index, int)
                    and not isinstance(raw_index, bool)
                    else fallback_index
                ),
            }
        elif (
            status == "assault_stopped"
            and parse_stop_assault_step(command) == siege_id
        ):
            opened.pop(key, None)
    return sorted(
        opened.values(),
        key=lambda row: (
            row["started_index"],
            row["war_id"],
            row["province_id"],
            row["siege_id"],
        ),
    )


def _unobservable_started_assaults(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    commands: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Latch proven Starts until the same assault is observable or closed."""
    pending: list[dict[str, object]] = []
    wars_by_id = {
        war_id: war
        for war in active_wars
        if (war_id := _native_int(war.get("war_id"))) is not None
    }
    for lifecycle in _open_assault_lifecycles(commands):
        war_id = lifecycle["war_id"]
        province_id = lifecycle["province_id"]
        siege_id = lifecycle["siege_id"]
        war = wars_by_id.get(war_id)
        if not isinstance(war, dict):
            # The exact active-war set no longer contains this generation.
            continue
        state_by_id = _objective_province_state_by_id(war)
        state = state_by_id.get(province_id)
        if isinstance(state, dict) and province_id in (
            _player_occupied_objective_ids(snapshot, war, state_by_id)
        ):
            # Exact occupation is the completion postcondition for the old
            # siege, even when active_siege has already disappeared.
            continue

        reason: str | None = None
        if snapshot.get("war_objective_assault_supported") is not True:
            reason = "assault_capability_unavailable_after_start"
        elif not isinstance(state, dict):
            reason = "objective_row_unavailable_after_start"
        elif state.get("siege_observable") is not True:
            reason = "siege_unobservable_after_start"
        else:
            active_siege = state.get("active_siege")
            if "active_siege" in state and active_siege is None:
                # siege_observable=true plus explicit null is the exact
                # completed/no-active-siege fact for the old lifecycle.
                continue
            if not isinstance(active_siege, dict):
                reason = "active_siege_unavailable_after_start"
            else:
                observed_siege_id = _native_int(active_siege.get("siege_id"))
                if observed_siege_id != siege_id:
                    # A different full-generation SiegeID proves that this
                    # lifecycle cannot still govern the replacement siege.
                    if observed_siege_id is not None and observed_siege_id > 0:
                        continue
                    reason = "siege_generation_unavailable_after_start"
                elif active_siege.get("assault_observable") is not True:
                    reason = "assault_subdomain_unobservable_after_start"
                elif active_siege.get("assault_in_progress") is False:
                    # Same-SiegeID inactive is an exact completed/stopped fact.
                    continue
                elif active_siege.get("assault_in_progress") is True:
                    if active_siege.get("player_army_besieging") is True:
                        # The ordinary active-assault review owns this row.
                        continue
                    reason = "player_besieger_unavailable_after_start"
                else:
                    reason = "assault_flag_unavailable_after_start"

        pending.append(
            {
                **lifecycle,
                "status": "unavailable",
                "reason": reason or "assault_state_unavailable_after_start",
            }
        )
    return pending


def _current_exact_siege_status(
    snapshot: dict[str, object],
    *,
    tactical_war_id: int | None,
    province_id: int | None,
    objective_state_by_id: dict[int, dict[str, object]],
    commands: list[dict[str, object]],
) -> dict[str, object] | None:
    if (
        province_id is None
        or snapshot.get("war_objective_siege_progress_supported") is not True
    ):
        return None
    state = objective_state_by_id.get(province_id)
    if not isinstance(state, dict) or state.get("siege_observable") is not True:
        return None
    active_siege = state.get("active_siege")
    if not isinstance(active_siege, dict):
        return {
            "status": "not_active",
            "province_id": province_id,
        }
    siege_id = _native_int(active_siege.get("siege_id"))
    result: dict[str, object] = {
        "status": "progressing",
        "province_id": province_id,
        "siege_id": siege_id,
        "besieging_army_id": active_siege.get("besieging_army_id"),
        "player_army_besieging": active_siege.get(
            "player_army_besieging"
        ),
        "garrison_size": state.get("garrison_size"),
        "besieging_strength": state.get("besieging_strength"),
        "progress_fraction": active_siege.get("progress_fraction"),
        "current_work": active_siege.get("current_work"),
        "total_work": active_siege.get("total_work"),
        "remaining_work": active_siege.get("remaining_work"),
        "days_left": active_siege.get("days_left"),
    }
    if active_siege.get("player_army_besieging") is not True:
        result["status"] = "not_player_besieging"
        return result
    garrison = _native_int(state.get("garrison_size"))
    strength = _native_int(state.get("besieging_strength"))
    if (
        snapshot.get("war_objective_garrison_supported") is True
        and garrison is not None
        and strength is not None
        and strength < garrison
    ):
        result["status"] = "insufficient_strength"
        return result
    stall_days = (
        _recent_exact_siege_stall_days(
            commands,
            war_id=tactical_war_id,
            province_id=province_id,
            siege_id=siege_id,
        )
        if tactical_war_id is not None and siege_id is not None
        else 0
    )
    result["stall_days"] = stall_days
    if stall_days >= _NATIVE_SIEGE_STALL_GAME_DAYS:
        result["status"] = "stalled"
    return result


def _current_exact_assault_state(
    snapshot: dict[str, object],
    *,
    province_id: int | None,
    objective_state_by_id: dict[int, dict[str, object]],
    stationary_threats: list[dict[str, object]],
    siege_status: dict[str, object] | None,
    commands: list[dict[str, object]],
    tactical_war_id: int | None,
) -> dict[str, object] | None:
    """Project only the next assault day; never invent a multi-day ETA."""
    if (
        province_id is None
        or snapshot.get("war_objective_assault_supported") is not True
    ):
        return None
    state = objective_state_by_id.get(province_id)
    active_siege = (
        state.get("active_siege")
        if isinstance(state, dict)
        and state.get("siege_observable") is True
        else None
    )
    if not isinstance(active_siege, dict):
        return None
    siege_id = _native_int(active_siege.get("siege_id"))
    base: dict[str, object] = {
        "province_id": province_id,
        "siege_id": siege_id,
        "assault_observable": active_siege.get("assault_observable") is True,
    }
    if active_siege.get("assault_observable") is not True:
        return {
            **base,
            "status": "unavailable",
            "one_day_safe": False,
            "one_day_rejection_reasons": ["assault_subdomain_unobservable"],
        }

    breach_level = _native_int(active_siege.get("breach_level"))
    walls_breached = breach_level in {1, 2}
    assault_in_progress = active_siege.get("assault_in_progress") is True
    daily_progress = active_siege.get("assault_daily_progress")
    daily_progress_raw = _fixed_raw(daily_progress)
    daily_casualties = _native_int(
        active_siege.get("assault_daily_casualties")
    )
    besieging_strength = _native_int(state.get("besieging_strength"))
    garrison_size = _native_int(state.get("garrison_size"))
    projected_strength = (
        besieging_strength - daily_casualties
        if besieging_strength is not None and daily_casualties is not None
        else None
    )
    previous_day = (
        _latest_assault_day_observation(
            commands,
            war_id=tactical_war_id,
            province_id=province_id,
            siege_id=siege_id,
        )
        if tactical_war_id is not None and siege_id is not None
        else None
    )
    rejection_reasons: list[str] = []
    if siege_id is None:
        rejection_reasons.append("siege_id_unavailable")
    if active_siege.get("player_army_besieging") is not True:
        rejection_reasons.append("player_not_primary_besieger")
    if not walls_breached:
        rejection_reasons.append("walls_not_breached")
    if daily_progress_raw is None or daily_progress_raw <= 0:
        rejection_reasons.append("daily_progress_not_positive")
    if daily_casualties is None:
        rejection_reasons.append("daily_casualties_unavailable")
    if besieging_strength is None or garrison_size is None:
        rejection_reasons.append("one_day_strength_budget_unavailable")
    elif (
        projected_strength is None
        or projected_strength <= 0
        or projected_strength < garrison_size
    ):
        rejection_reasons.append("projected_strength_below_garrison")
    if stationary_threats:
        rejection_reasons.append("enemy_convergence_observed")
    if (
        isinstance(siege_status, dict)
        and siege_status.get("status") != "progressing"
    ):
        rejection_reasons.append(
            f"siege_{siege_status.get('status') or 'unavailable'}"
        )
    if isinstance(previous_day, dict):
        previous_day_reason = previous_day.get("reason")
        if (
            previous_day.get("status") == "unknown"
            and isinstance(previous_day_reason, str)
        ):
            rejection_reasons.append(previous_day_reason)
        if previous_day.get("elapsed_days") != 1:
            rejection_reasons.append("previous_assault_slice_not_one_day")
        previous_work_delta = _native_int(
            previous_day.get("work_delta_raw")
        )
        if previous_work_delta is None or previous_work_delta <= 0:
            rejection_reasons.append("previous_assault_day_no_work_progress")
        if previous_day.get("strength_loss") is None:
            rejection_reasons.append(
                "previous_assault_day_strength_change_unavailable"
            )
    return {
        **base,
        "status": "active" if assault_in_progress else "inactive",
        "breach_level": breach_level,
        "walls_breached": walls_breached,
        "assault_in_progress": assault_in_progress,
        "can_start_assault": active_siege.get("can_start_assault") is True,
        "can_stop_assault": active_siege.get("can_stop_assault") is True,
        "assault_daily_progress": daily_progress,
        "assault_daily_casualties": daily_casualties,
        "besieging_strength": besieging_strength,
        "garrison_size": garrison_size,
        "projected_strength_after_one_day": projected_strength,
        "threats": list(stationary_threats),
        "one_day_safe": not rejection_reasons,
        "one_day_rejection_reasons": rejection_reasons,
        "projection_horizon_days": 1,
        "previous_assault_day": previous_day,
    }


def _review_all_player_assaults(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    enemies: list[dict[str, object]],
    commands: list[dict[str, object]],
) -> list[dict[str, object]]:
    if snapshot.get("war_objective_assault_supported") is not True:
        return []
    reviews: list[dict[str, object]] = []
    for war in active_wars:
        tactical_war_id = _native_int(war.get("war_id"))
        if tactical_war_id is None:
            continue
        objective_state_by_id = _objective_province_state_by_id(war)
        for province_id, state in objective_state_by_id.items():
            active_siege = (
                state.get("active_siege")
                if state.get("siege_observable") is True
                else None
            )
            if not (
                isinstance(active_siege, dict)
                and active_siege.get("player_army_besieging") is True
            ):
                continue
            siege_status = _current_exact_siege_status(
                snapshot,
                tactical_war_id=tactical_war_id,
                province_id=province_id,
                objective_state_by_id=objective_state_by_id,
                commands=commands,
            )
            review = _current_exact_assault_state(
                snapshot,
                province_id=province_id,
                objective_state_by_id=objective_state_by_id,
                stationary_threats=_stationary_province_threats(
                    province_id, enemies
                ),
                siege_status=siege_status,
                commands=commands,
                tactical_war_id=tactical_war_id,
            )
            if isinstance(review, dict):
                reviews.append({**review, "war_id": tactical_war_id})
    return sorted(
        reviews,
        key=lambda review: (
            _native_int(review.get("siege_id")) or 2**31,
            _native_int(review.get("province_id")) or 2**31,
        ),
    )


def _native_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _army_tactical_state(army: dict[str, object]) -> str | None:
    named = army.get("army_state")
    if isinstance(named, str):
        return named.casefold()
    code = _native_int(army.get("army_state_code"))
    if code is not None:
        return {2: "combat", 3: "sieging", 6: "retreating", 7: "moving"}.get(code)
    if army.get("retreating") is True:
        return "retreating"
    if army.get("in_combat") is True:
        return "combat"
    return None


def _stationary_province_threats(
    province_id: object,
    enemies: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Return observable enemies converging on one stationary province."""
    guarded_province_id = _native_int(province_id)
    if guarded_province_id is None:
        return []
    conflicts: list[dict[str, object]] = []
    for enemy in enemies:
        if _army_tactical_state(enemy) == "retreating":
            continue
        enemy_id = _native_int(enemy.get("army_id"))
        enemy_current = _native_int(enemy.get("current_province_id"))
        enemy_target = _native_int(enemy.get("move_target_province_id"))
        route = enemy.get("route_province_ids")
        if enemy_current == guarded_province_id:
            kind = "enemy_at_stationary_province"
        elif enemy_target == guarded_province_id:
            kind = "enemy_targeting_stationary_province"
        elif isinstance(route, list) and guarded_province_id in route:
            kind = "enemy_route_to_stationary_province"
        else:
            continue
        conflicts.append(
            {
                "kind": kind,
                "enemy_army_id": enemy_id,
                "province_id": guarded_province_id,
            }
        )
    return conflicts


def _progress_slice(
    result: object, name: str, war_id: int
) -> tuple[int | None, dict[str, object] | None]:
    summary = result.get(name) if isinstance(result, dict) else None
    wars = summary.get("wars") if isinstance(summary, dict) else None
    war = next(
        (
            row
            for row in wars
            if isinstance(row, dict) and row.get("war_id") == war_id
        ),
        None,
    ) if isinstance(wars, list) else None
    return (
        _native_int(summary.get("date_raw")) if isinstance(summary, dict) else None,
        war,
    )


def _progress_army(
    war: dict[str, object] | None, role: str, army_id: int
) -> dict[str, object] | None:
    armies = war.get(role) if isinstance(war, dict) else None
    if not isinstance(armies, list):
        return None
    return next(
        (
            row
            for row in armies
            if isinstance(row, dict) and row.get("army_id") == army_id
        ),
        None,
    )


def _progress_objective_state(
    war: dict[str, object] | None, province_id: int
) -> dict[str, object] | None:
    states = war.get("objective_province_states") if isinstance(war, dict) else None
    if not isinstance(states, list):
        return None
    return next(
        (
            state
            for state in states
            if isinstance(state, dict)
            and state.get("province_id") == province_id
        ),
        None,
    )


def _progress_active_siege(
    state: dict[str, object] | None,
    siege_id: int,
) -> dict[str, object] | None:
    active_siege = state.get("active_siege") if isinstance(state, dict) else None
    if (
        isinstance(active_siege, dict)
        and active_siege.get("siege_id") == siege_id
        and active_siege.get("player_army_besieging") is True
    ):
        return active_siege
    return None


def _fixed_raw(value: object) -> int | None:
    raw = value.get("raw") if isinstance(value, dict) else None
    return _native_int(raw)


def _latest_assault_day_observation(
    commands: list[dict[str, object]],
    *,
    war_id: int,
    province_id: int,
    siege_id: int,
) -> dict[str, object] | None:
    """Read the latest completed assault slice without extrapolating an ETA."""
    scoped_history = _history_after_latest_restore(commands)
    opened = next(
        (
            lifecycle
            for lifecycle in reversed(_open_assault_lifecycles(commands))
            if lifecycle["war_id"] == war_id
            and lifecycle["province_id"] == province_id
            and lifecycle["siege_id"] == siege_id
        ),
        None,
    )
    started_index = opened.get("started_index") if isinstance(opened, dict) else None

    def unknown(reason: str) -> dict[str, object]:
        return {
            "status": "unknown",
            "reason": reason,
            "elapsed_days": None,
            "work_delta_raw": None,
            "strength_loss": None,
            "starting_besieging_strength": None,
            "ending_besieging_strength": None,
            "soldier_loss": None,
            "starting_soldiers": None,
            "ending_soldiers": None,
        }

    indexed_history = list(enumerate(scoped_history, start=1))
    for fallback_index, row in reversed(indexed_history):
        raw_index = row.get("index")
        row_index = (
            raw_index
            if isinstance(raw_index, int) and not isinstance(raw_index, bool)
            else fallback_index
        )
        if isinstance(started_index, int) and row_index <= started_index:
            break
        if not is_life_advance_step(_effective_command(row)):
            continue
        if row.get("ok") is not True:
            if isinstance(started_index, int):
                return unknown("previous_assault_slice_failed_unknown")
            continue
        result = row.get("result")
        before_date, before_war = _progress_slice(
            result, "war_progress_before", war_id
        )
        after_date, after_war = _progress_slice(
            result, "war_progress_after", war_id
        )
        before_state = _progress_objective_state(before_war, province_id)
        before_siege = _progress_active_siege(before_state, siege_id)
        if not (
            isinstance(before_siege, dict)
            and before_siege.get("assault_observable") is True
            and before_siege.get("assault_in_progress") is True
        ):
            if isinstance(started_index, int):
                return unknown("previous_assault_slice_state_unavailable")
            continue
        after_state = _progress_objective_state(after_war, province_id)
        after_siege = _progress_active_siege(after_state, siege_id)
        before_work = _fixed_raw(before_siege.get("current_work"))
        after_work = (
            _fixed_raw(after_siege.get("current_work"))
            if isinstance(after_siege, dict)
            else None
        )
        before_strength = (
            _native_int(before_state.get("besieging_strength"))
            if isinstance(before_state, dict)
            else None
        )
        after_strength = (
            _native_int(after_state.get("besieging_strength"))
            if isinstance(after_state, dict)
            else None
        )
        if before_strength is not None and before_strength < 0:
            before_strength = None
        if after_strength is not None and after_strength < 0:
            after_strength = None
        army_id = _native_int(before_siege.get("besieging_army_id"))
        before_army = (
            _progress_army(before_war, "player_armies", army_id)
            if army_id is not None
            else None
        )
        after_army = (
            _progress_army(after_war, "player_armies", army_id)
            if army_id is not None
            else None
        )
        before_soldiers = (
            _native_int(before_army.get("soldiers"))
            if isinstance(before_army, dict)
            else None
        )
        after_soldiers = (
            _native_int(after_army.get("soldiers"))
            if isinstance(after_army, dict)
            else None
        )
        elapsed_days = (
            max(0, (after_date - before_date) // 24)
            if before_date is not None and after_date is not None
            else None
        )
        return {
            "elapsed_days": elapsed_days,
            "work_delta_raw": (
                after_work - before_work
                if before_work is not None and after_work is not None
                else None
            ),
            # This is the authoritative realized safety input.  It measures
            # the eligible besieging-strength change published on the same
            # objective, rather than requiring army soldiers (which exact
            # progress frames may legitimately omit).
            "strength_loss": (
                max(0, before_strength - after_strength)
                if before_strength is not None and after_strength is not None
                else None
            ),
            "starting_besieging_strength": before_strength,
            "ending_besieging_strength": after_strength,
            # Army soldiers remain useful diagnostics when a producer happens
            # to publish them, but never gate the next one-day assault slice.
            "soldier_loss": (
                max(0, before_soldiers - after_soldiers)
                if before_soldiers is not None and after_soldiers is not None
                else None
            ),
            "starting_soldiers": before_soldiers,
            "ending_soldiers": after_soldiers,
        }
    return None


def _recent_exact_siege_stall_days(
    commands: list[dict[str, object]],
    *,
    war_id: int,
    province_id: int,
    siege_id: int,
) -> int:
    """Count consecutive paused-to-paused days with no exact siege work."""
    stalled_days = 0
    for row in _history_after_latest_restore(commands):
        if (
            not is_life_advance_step(_effective_command(row))
            or row.get("ok") is not True
        ):
            continue
        result = row.get("result")
        before_date, before_war = _progress_slice(
            result, "war_progress_before", war_id
        )
        after_date, after_war = _progress_slice(
            result, "war_progress_after", war_id
        )
        if (
            before_date is None
            or after_date is None
            or after_date < before_date
            or before_war is None
            or after_war is None
        ):
            stalled_days = 0
            continue
        before = _progress_active_siege(
            _progress_objective_state(before_war, province_id), siege_id
        )
        after = _progress_active_siege(
            _progress_objective_state(after_war, province_id), siege_id
        )
        if before is None or after is None:
            stalled_days = 0
            continue
        elapsed = max(0, (after_date - before_date) // 24)
        before_work = _fixed_raw(before.get("current_work"))
        after_work = _fixed_raw(after.get("current_work"))
        before_fraction = _fixed_raw(before.get("progress_fraction"))
        after_fraction = _fixed_raw(after.get("progress_fraction"))
        advanced = bool(
            before_work is not None
            and after_work is not None
            and after_work > before_work
        ) or bool(
            before_fraction is not None
            and after_fraction is not None
            and after_fraction > before_fraction
        )
        stalled_days = 0 if advanced else stalled_days + elapsed
    return stalled_days


def _history_after_latest_restore(
    commands: list[dict[str, object]],
) -> list[dict[str, object]]:
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        if (
            _effective_command(row) == "restore-checkpoint"
            and row.get("ok") is True
        ):
            return commands[position + 1 :]
    return commands


def _effective_command_result(row: dict[str, object]) -> dict[str, object] | None:
    result = row.get("result")
    if row.get("command") != "auto-turn":
        return result if isinstance(result, dict) else None
    if isinstance(result, dict):
        # gameplay_runner decorates the actual executor result at the root and
        # stores the plan under auto_turn.  Prefer factual root postconditions
        # over any nested/planner-shaped payload.
        if any(
            isinstance(result.get(name), dict)
            for name in (
                "assault_action",
                "route_preview",
                "war_action",
                "war_progress_before",
                "war_progress_after",
            )
        ):
            return result
    auto_turn = result.get("auto_turn") if isinstance(result, dict) else None
    nested = auto_turn.get("result") if isinstance(auto_turn, dict) else None
    if isinstance(nested, dict):
        return nested
    return result if isinstance(result, dict) else None


def _normalized_remaining_route(
    army: dict[str, object],
) -> list[int] | None:
    route = army.get("route_province_ids")
    if not isinstance(route, list) or any(
        isinstance(province_id, bool)
        or not isinstance(province_id, int)
        or province_id <= 0
        for province_id in route
    ):
        return None
    remaining = [int(province_id) for province_id in route]
    current = _native_int(army.get("current_province_id"))
    if remaining and remaining[0] == current:
        remaining = remaining[1:]
    return remaining


def _active_route_evidence_issue(
    army: dict[str, object], *, role: str, war_id: int | None = None
) -> dict[str, object] | None:
    target = _native_int(army.get("move_target_province_id"))
    route = army.get("route_province_ids")
    state = _army_tactical_state(army)
    state_code = _native_int(army.get("army_state_code"))
    route_present = isinstance(route, list) and bool(route)
    active = bool(
        state == "moving"
        or state_code == 7
        or route_present
        or role == "player"
        and target is not None
    )
    if not active:
        return None
    reason: str | None = None
    remaining = _normalized_remaining_route(army)
    if target is None or target <= 0:
        reason = "active_route_target_unavailable"
    elif remaining is None:
        reason = "active_route_unavailable"
    elif not remaining:
        reason = "active_route_empty"
    elif remaining[-1] != target:
        reason = "active_route_endpoint_mismatch"
    if reason is None:
        return None
    return {
        "role": role,
        "war_id": war_id,
        "army_id": _native_int(army.get("army_id")),
        "army_state": state,
        "current_province_id": _native_int(army.get("current_province_id")),
        "move_target_province_id": target,
        "route_province_ids": (
            list(route) if isinstance(route, list) else None
        ),
        "reason": reason,
    }


def _route_evidence_issues(
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
) -> list[dict[str, object]]:
    issues = [
        issue
        for army in controlled_armies
        if (
            issue := _active_route_evidence_issue(
                army, role="player", war_id=None
            )
        )
        is not None
    ]
    for war in active_wars:
        war_id = _native_int(war.get("war_id"))
        enemies = war.get("enemy_armies")
        for enemy in enemies if isinstance(enemies, list) else []:
            if not isinstance(enemy, dict) or _army_tactical_state(enemy) == "retreating":
                continue
            issue = _active_route_evidence_issue(
                enemy, role="enemy", war_id=war_id
            )
            if issue is not None:
                issues.append(issue)
    return issues


def _enemy_endpoint_observation(
    army: dict[str, object], *, war_id: int, date_raw: int
) -> dict[str, object] | None:
    army_id = _native_int(army.get("army_id"))
    target = _native_int(army.get("move_target_province_id"))
    remaining = _normalized_remaining_route(army)
    state = _army_tactical_state(army)
    if (
        army_id is None
        or army_id <= 0
        or state in {"combat", "retreating"}
        or target is None
        or target <= 0
        or remaining is None
        or not remaining
        or remaining[-1] != target
    ):
        return None
    return {
        "war_id": war_id,
        "enemy_army_id": army_id,
        "date_raw": date_raw,
        "current_province_id": _native_int(army.get("current_province_id")),
        "move_target_province_id": target,
        "next_hop_province_id": remaining[0],
        "endpoint_province_id": remaining[-1],
        "route_province_ids": remaining,
        # An observable active route is one intent state even if an adapter
        # transiently names it regular while CK3 consumes the leading hop.
        "intent_state": "moving",
    }


def _route_is_natural_suffix(
    previous: list[int],
    current: list[int],
    *,
    previous_current_province_id: object,
    current_province_id: object,
) -> bool:
    if (
        not current
        or len(current) > len(previous)
        or previous[len(previous) - len(current) :] != current
    ):
        return False
    consumed = previous[: len(previous) - len(current)]
    if not consumed:
        return current_province_id == previous_current_province_id
    return current_province_id == consumed[-1]


def _enemy_endpoint_epochs(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
) -> list[dict[str, object]]:
    """Derive contiguous observed endpoint epochs without native timer guesses."""
    frames_by_date: dict[int, list[dict[str, object]]] = {}
    for row in _history_after_latest_restore(commands):
        if (
            not is_life_advance_step(_effective_command(row))
            or row.get("ok") is not True
        ):
            continue
        result = _effective_command_result(row)
        for name in ("war_progress_before", "war_progress_after"):
            summary = result.get(name) if isinstance(result, dict) else None
            date_raw = (
                _native_int(summary.get("date_raw"))
                if isinstance(summary, dict)
                else None
            )
            wars = summary.get("wars") if isinstance(summary, dict) else None
            if date_raw is not None and isinstance(wars, list):
                frames_by_date[date_raw] = [
                    war for war in wars if isinstance(war, dict)
                ]
    current_date = _native_int(snapshot.get("date_raw"))
    current_wars = snapshot.get("active_wars")
    if current_date is not None and isinstance(current_wars, list):
        frames_by_date[current_date] = [
            war for war in current_wars if isinstance(war, dict)
        ]

    epochs: list[dict[str, object]] = []
    opened: dict[tuple[int, int], dict[str, object]] = {}
    sequence_by_key: dict[tuple[int, int], int] = {}

    def close(key: tuple[int, int], date_raw: int, reason: str) -> None:
        epoch = opened.pop(key, None)
        if epoch is None:
            return
        epoch["active"] = False
        epoch["closed_date_raw"] = date_raw
        epoch["closed_reason"] = reason

    for date_raw in sorted(frames_by_date):
        observations: dict[tuple[int, int], dict[str, object]] = {}
        for war in frames_by_date[date_raw]:
            war_id = _native_int(war.get("war_id"))
            enemies = war.get("enemy_armies")
            if war_id is None or war_id <= 0 or not isinstance(enemies, list):
                continue
            for enemy in enemies:
                if not isinstance(enemy, dict):
                    continue
                observation = _enemy_endpoint_observation(
                    enemy, war_id=war_id, date_raw=date_raw
                )
                if observation is None:
                    continue
                key = (war_id, int(observation["enemy_army_id"]))
                observations[key] = observation

        for key in tuple(opened):
            if key not in observations:
                close(key, date_raw, "observation_gap_or_intent_closed")

        for key, observation in observations.items():
            current_epoch = opened.get(key)
            same_intent = bool(
                isinstance(current_epoch, dict)
                and current_epoch.get("move_target_province_id")
                == observation["move_target_province_id"]
                and current_epoch.get("endpoint_province_id")
                == observation["endpoint_province_id"]
                and current_epoch.get("intent_state")
                == observation["intent_state"]
                and _route_is_natural_suffix(
                    list(current_epoch.get("route_province_ids", [])),
                    list(observation["route_province_ids"]),
                    previous_current_province_id=current_epoch.get(
                        "current_province_id"
                    ),
                    current_province_id=observation.get(
                        "current_province_id"
                    ),
                )
            )
            if not same_intent:
                close(key, date_raw, "intent_changed")
                sequence = sequence_by_key.get(key, 0) + 1
                sequence_by_key[key] = sequence
                current_epoch = {
                    **observation,
                    "epoch_sequence": sequence,
                    "first_observed_date_raw": date_raw,
                    "last_observed_date_raw": date_raw,
                    "observed_span_days": 0,
                    "sample_count": 1,
                    "milestones_crossed_days": [],
                    "active": True,
                    "closed_date_raw": None,
                    "closed_reason": None,
                }
                epochs.append(current_epoch)
                opened[key] = current_epoch
                continue
            first_date = int(current_epoch["first_observed_date_raw"])
            span_days = max(0, (date_raw - first_date) // 24)
            current_epoch.update(
                {
                    **observation,
                    "last_observed_date_raw": date_raw,
                    "observed_span_days": span_days,
                    "sample_count": int(current_epoch["sample_count"]) + 1,
                    "milestones_crossed_days": [
                        milestone
                        for milestone in _NATIVE_ENEMY_TARGET_MILESTONES_DAYS
                        if span_days >= milestone
                    ],
                }
            )
    return sorted(
        epochs,
        key=lambda epoch: (
            int(epoch["war_id"]),
            int(epoch["enemy_army_id"]),
            int(epoch["epoch_sequence"]),
        ),
    )


def _split_merge_recovery(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    controlled_armies: list[dict[str, object]],
    active_wars: list[dict[str, object]],
) -> dict[str, object] | None:
    """Recover only an exact recent split pair; never rank IDs or soldiers."""
    scoped = _history_after_latest_restore(commands)
    current_by_id = {
        int(army["army_id"]): army
        for army in controlled_armies
        if _native_int(army.get("army_id")) is not None
        and int(army["army_id"]) > 0
    }
    current_ids = set(current_by_id)
    for split_position in range(len(scoped) - 1, -1, -1):
        split_row = scoped[split_position]
        original_army_id = parse_split_army_half_step(
            _effective_command(split_row)
        )
        if original_army_id is None or split_row.get("ok") is not True:
            continue
        result = _effective_command_result(split_row)
        action = result.get("war_action") if isinstance(result, dict) else None
        if not isinstance(action, dict) or action.get("status") not in {
            "split_submitted",
            "split_applied",
        }:
            continue
        action_source = _native_int(action.get("source_army_id"))
        before_raw = action.get("player_army_ids_before")
        if action_source not in {None, original_army_id} or not isinstance(
            before_raw, list
        ):
            continue
        before_ids = [
            int(army_id)
            for army_id in before_raw
            if _native_int(army_id) is not None and int(army_id) > 0
        ]
        before_set = set(before_ids)
        if (
            len(before_ids) != len(before_raw)
            or len(before_set) != len(before_ids)
            or original_army_id not in before_set
        ):
            continue

        later_rows = scoped[split_position + 1 :]
        sibling_candidates: set[int] = set()
        action_sibling = _native_int(action.get("sibling_army_id"))
        if action_sibling is not None and action_sibling not in before_set:
            sibling_candidates.add(action_sibling)
        current_delta = current_ids - before_set
        if len(current_delta) == 1:
            sibling_candidates.update(current_delta)
        exact_merge_rows: list[dict[str, object]] = []
        for later_row in later_rows:
            parsed_merge = parse_merge_armies_step(
                _effective_command(later_row)
            )
            if parsed_merge is None or parsed_merge[0] != original_army_id:
                continue
            if parsed_merge[1] not in before_set:
                sibling_candidates.add(parsed_merge[1])
                exact_merge_rows.append(later_row)
        if len(sibling_candidates) != 1:
            return {
                "status": "split_identity_pending",
                "original_army_id": original_army_id,
                "split_history_position": split_position,
                "reason": "the exact split receipt and current army-set delta do not identify one sibling",
            }
        sibling_army_id = next(iter(sibling_candidates))
        expected_split_ids = before_set | {sibling_army_id}
        if current_ids != before_set and current_ids != expected_split_ids:
            return {
                "status": "split_army_set_inconsistent",
                "original_army_id": original_army_id,
                "sibling_army_id": sibling_army_id,
                "player_army_ids_before": sorted(before_set),
                "current_player_army_ids": sorted(current_ids),
            }

        merge_step = merge_armies_step(original_army_id, sibling_army_id)
        latest_merge = exact_merge_rows[-1] if exact_merge_rows else None
        if latest_merge is not None:
            merge_result = _effective_command_result(latest_merge)
            merge_action = (
                merge_result.get("war_action")
                if isinstance(merge_result, dict)
                else None
            )
            if latest_merge.get("ok") is not True:
                return {
                    "status": "merge_failed",
                    "original_army_id": original_army_id,
                    "sibling_army_id": sibling_army_id,
                    "merge_step": merge_step,
                    "error": latest_merge.get("error"),
                    "war_action": merge_action,
                }
            if current_ids == before_set and original_army_id in current_ids:
                return {
                    "status": "merge_completed",
                    "original_army_id": original_army_id,
                    "sibling_army_id": sibling_army_id,
                    "merge_step": merge_step,
                    "war_action": merge_action,
                }
            if (
                isinstance(merge_action, dict)
                and merge_action.get("status") == "merge_applied"
            ):
                return {
                    "status": "merge_postcondition_inconsistent",
                    "original_army_id": original_army_id,
                    "sibling_army_id": sibling_army_id,
                    "merge_step": merge_step,
                    "current_player_army_ids": sorted(current_ids),
                    "war_action": merge_action,
                }
            return {
                "status": "merge_pending",
                "original_army_id": original_army_id,
                "sibling_army_id": sibling_army_id,
                "merge_step": merge_step,
                "war_action": merge_action,
            }

        if current_ids == before_set:
            return {
                "status": "split_identity_pending",
                "original_army_id": original_army_id,
                "sibling_army_id": sibling_army_id,
                "reason": "the submitted split has no observable sibling yet",
            }
        original = current_by_id.get(original_army_id)
        sibling = current_by_id.get(sibling_army_id)
        if not isinstance(original, dict) or not isinstance(sibling, dict):
            return None
        province_id = _native_int(original.get("current_province_id"))
        if province_id is None or province_id <= 0 or _native_int(
            sibling.get("current_province_id")
        ) != province_id:
            return {
                "status": "merge_requires_rendezvous",
                "original_army_id": original_army_id,
                "sibling_army_id": sibling_army_id,
                "merge_step": merge_step,
            }
        if any(
            _army_tactical_state(army) in {"combat", "retreating"}
            for army in (original, sibling)
        ):
            return {
                "status": "merge_waiting_for_idle",
                "original_army_id": original_army_id,
                "sibling_army_id": sibling_army_id,
                "merge_step": merge_step,
            }
        exact_objectives = set(war_objective_province_ids(active_wars))
        durable_goal_army_ids = sorted(
            army_id
            for army_id, army in (
                (original_army_id, original),
                (sibling_army_id, sibling),
            )
            if _native_int(army.get("move_target_province_id"))
            in exact_objectives
        )
        return {
            "status": "ready_to_merge",
            "original_army_id": original_army_id,
            "sibling_army_id": sibling_army_id,
            "province_id": province_id,
            "merge_step": merge_step,
            "durable_goal_army_ids": durable_goal_army_ids,
            "missing_proofs": ["exact_combat_prediction_unavailable"],
            "submitted_date_raw": _native_int(action.get("submitted_date_raw")),
            "player_army_ids_before": sorted(before_set),
        }
    return None


def _successful_merge_barrier(
    row: dict[str, object], army_id: int
) -> bool:
    parsed = parse_merge_armies_step(_effective_command(row))
    return bool(
        row.get("ok") is True
        and parsed is not None
        and army_id in parsed
    )


def _fresh_move_route_preview(
    commands: list[dict[str, object]],
    *,
    army_id: int,
    origin_province_id: int,
    target_province_id: int,
    date_raw: int | None,
) -> dict[str, object] | None:
    if date_raw is None:
        return None
    expected_step = (army_id, target_province_id)
    for row in reversed(_history_after_latest_restore(commands)):
        if _successful_merge_barrier(row, army_id):
            return None
        if parse_preview_move_army_step(_effective_command(row)) != expected_step:
            continue
        if row.get("ok") is not True:
            continue
        result = _effective_command_result(row)
        preview = result.get("route_preview") if isinstance(result, dict) else None
        if (
            not isinstance(preview, dict)
            or preview.get("status") not in {"available", "deferred"}
            or preview.get("army_id") != army_id
            or preview.get("origin_province_id") != origin_province_id
            or preview.get("target_province_id") != target_province_id
            or preview.get("previewed_date_raw") != date_raw
        ):
            continue
        if preview.get("status") == "deferred":
            return {**preview, "route_province_ids": []}
        route = preview.get("route_province_ids")
        if not isinstance(route, list) or any(
            isinstance(item, bool) or not isinstance(item, int) or item <= 0
            for item in route
        ):
            continue
        return {**preview, "route_province_ids": list(route)}
    return None


def _fresh_route_contact_horizon(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    army_id: int,
    origin_province_id: int,
    target_province_id: int,
    hostile_army_ids: tuple[int, ...],
    route_province_ids: object,
) -> dict[str, object] | None:
    if not hostile_army_ids or not isinstance(route_province_ids, list):
        return None
    expected_step = (army_id, target_province_id, hostile_army_ids)
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    expected_route = list(route_province_ids)
    if expected_route and expected_route[0] == origin_province_id:
        expected_route = expected_route[1:]
    for row in reversed(_history_after_latest_restore(commands)):
        if _successful_merge_barrier(row, army_id):
            return None
        if (
            parse_query_route_contact_horizon_step(_effective_command(row))
            != expected_step
            or row.get("ok") is not True
        ):
            continue
        result = _effective_command_result(row)
        horizon = (
            result.get("route_contact_horizon")
            if isinstance(result, dict)
            else None
        )
        subject_route = (
            horizon.get("subject_route")
            if isinstance(horizon, dict)
            else None
        )
        observed_route = (
            subject_route.get("route_province_ids")
            if isinstance(subject_route, dict)
            else None
        )
        normalized_observed = (
            list(observed_route) if isinstance(observed_route, list) else None
        )
        if (
            isinstance(normalized_observed, list)
            and normalized_observed
            and normalized_observed[0] == origin_province_id
        ):
            normalized_observed = normalized_observed[1:]
        if not (
            isinstance(horizon, dict)
            and horizon.get("status") == "available"
            and horizon.get("subject_army_id") == army_id
            and horizon.get("target_province_id") == target_province_id
            and tuple(horizon.get("hostile_army_ids", ()))
            == hostile_army_ids
            and horizon.get("date_raw") == snapshot.get("date_raw")
            and horizon.get("snapshot_revision")
            == snapshot.get("native_revision")
            and result.get("queried_snapshot_id")
            == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision")
            == snapshot.get("native_revision")
            and result.get("queried_connection_generation")
            == connection_generation
            and result.get("queried_episode_run_id")
            == snapshot.get("episode_run_id")
            and isinstance(subject_route, dict)
            and subject_route.get("army_id") == army_id
            and subject_route.get("current_province_id")
            == origin_province_id
            and normalized_observed == expected_route
            and isinstance(horizon.get("one_day_contact_free"), bool)
        ):
            continue
        return dict(horizon)
    return None


def _moving_route_contact_horizon_conjunction(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    controlled_armies: list[dict[str, object]],
    subject_army_id: int,
    subject_contact_horizon: dict[str, object],
    hostile_army_ids: tuple[int, ...],
    enemies: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """Classify every non-subject active route for one global native day."""
    result: dict[str, list[dict[str, object]]] = {
        "covered": [],
        "missing": [],
        "unavailable": [],
        "unavoidable": [],
        "conflicting": [],
    }
    for army in sorted(
        controlled_armies,
        key=lambda row: _native_int(row.get("army_id")) or 2**31,
    ):
        army_id = _native_int(army.get("army_id"))
        if army_id is None or army_id == subject_army_id:
            continue
        target_province_id = _native_int(
            army.get("move_target_province_id")
        )
        current_province_id = _native_int(army.get("current_province_id"))
        route = _normalized_remaining_route(army)
        if target_province_id is None and route == []:
            continue
        if not (
            target_province_id is not None
            and target_province_id > 0
            and current_province_id is not None
            and current_province_id > 0
            and route
            and route[-1] == target_province_id
            and _army_tactical_state(army)
            not in {"combat", "retreating", "gathering"}
        ):
            result["conflicting"].append(
                {
                    "army_id": army_id,
                    "status": "active_route_shape_unavailable",
                }
            )
            continue
        try:
            current_contact_free = (
                stationary_province_contact_free_in_horizon(
                    subject_contact_horizon, current_province_id
                )
            )
        except ValueError:
            current_contact_free = False
        geometric_audit = _audit_war_route(
            army.get("route_province_ids"),
            origin_province_id=current_province_id,
            target_province_id=target_province_id,
            enemies=enemies,
        )
        if current_contact_free and geometric_audit.get("status") == "safe":
            result["covered"].append(
                {
                    "army_id": army_id,
                    "target_province_id": target_province_id,
                    "status": "derived_current_and_route_safe",
                    "proof_subject_army_id": subject_army_id,
                }
            )
            continue

        query_step = query_route_contact_horizon_step(
            army_id, target_province_id, hostile_army_ids
        )
        own_horizon = _fresh_route_contact_horizon(
            commands,
            snapshot,
            army_id=army_id,
            origin_province_id=current_province_id,
            target_province_id=target_province_id,
            hostile_army_ids=hostile_army_ids,
            route_province_ids=army.get("route_province_ids"),
        )
        evidence = {
            "army_id": army_id,
            "current_province_id": current_province_id,
            "target_province_id": target_province_id,
            "query_step": query_step,
            "geometric_audit": geometric_audit,
            "derived_current_contact_free": current_contact_free,
        }
        if own_horizon is None:
            attempted = _current_frame_route_contact_query_failure(
                commands, snapshot, query_step
            )
            result["unavailable" if attempted else "missing"].append(
                {
                    **evidence,
                    "status": (
                        "fresh_subject_query_unavailable"
                        if attempted
                        else "fresh_subject_query_required"
                    ),
                    **({"attempt": attempted} if attempted else {}),
                }
            )
            continue
        if own_horizon.get("one_day_contact_free") is True:
            result["covered"].append(
                {
                    **evidence,
                    "status": "fresh_subject_contact_free",
                    "contact_horizon": own_horizon,
                }
            )
            continue
        if unavoidable_current_province_contact_in_horizon(own_horizon):
            result["unavoidable"].append(
                {
                    **evidence,
                    "status": "unavoidable_current_province_contact",
                    "advance_step": advance_route_contact_horizon_step(
                        army_id, target_province_id, hostile_army_ids
                    ),
                    "contact_horizon": own_horizon,
                }
            )
            continue
        result["conflicting"].append(
            {
                **evidence,
                "status": "fresh_subject_timed_conflict",
                "contact_horizon": own_horizon,
            }
        )
    return result


def _current_frame_route_contact_query_failure(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    query_step: str,
) -> dict[str, object] | None:
    """Return a surviving failed/unusable query without creating a loop."""
    for row in reversed(_history_after_latest_restore(commands)):
        command = _effective_command(row)
        if command == query_step:
            result = _effective_command_result(row)
            exact_frame = bool(
                isinstance(result, dict)
                and result.get("queried_snapshot_id")
                == snapshot.get("snapshot_id")
                and result.get("queried_revision")
                == snapshot.get("revision")
                and result.get("queried_native_revision")
                == snapshot.get("native_revision")
            )
            if row.get("ok") is False or exact_frame:
                return {
                    "history_index": row.get("index"),
                    "ok": row.get("ok"),
                    "error": row.get("error"),
                    "status": (
                        result.get("status")
                        if isinstance(result, dict)
                        else None
                    ),
                }
            return None
        if (
            is_life_advance_step(command)
            or parse_move_army_step(command) is not None
            or parse_merge_armies_step(command) is not None
            or parse_split_army_half_step(command) is not None
        ):
            return None
    return None


def _matching_rollback_war_failure(
    snapshot: dict[str, object],
    *,
    war_id: int | None,
    army_id: int,
    origin_province_id: int,
    target_province_id: int,
    route_province_ids: object,
) -> dict[str, object] | None:
    """Return advisory rollback memory without treating it as game history."""
    plural = snapshot.get("native_rollback_war_failures")
    failures = (
        [failure for failure in plural if isinstance(failure, dict)]
        if isinstance(plural, list)
        else [snapshot.get("native_rollback_war_failure")]
    )
    for failure in failures:
        if not isinstance(failure, dict) or (
            failure.get("status") != "rolled_back_active_route"
            or (war_id is not None and failure.get("war_id") != war_id)
            or failure.get("army_id") != army_id
            or failure.get("restored_origin_province_id")
            != origin_province_id
            or failure.get("route_origin_province_id")
            != origin_province_id
            or failure.get("target_province_id") != target_province_id
        ):
            continue
        failed_route = failure.get("route_province_ids")
        if not isinstance(failed_route, list) or not isinstance(
            route_province_ids, list
        ):
            continue
        normalized_failed_route = list(failed_route)
        if (
            normalized_failed_route
            and normalized_failed_route[0] == origin_province_id
        ):
            normalized_failed_route = normalized_failed_route[1:]
        if normalized_failed_route != route_province_ids:
            continue
        run_id = snapshot.get("episode_run_id")
        failure_run_id = failure.get("episode_run_id")
        if (
            isinstance(run_id, str)
            and isinstance(failure_run_id, str)
            and run_id != failure_run_id
        ):
            continue
        return dict(failure)
    return None


def _audit_war_route(
    route_value: object,
    *,
    origin_province_id: int | None,
    target_province_id: int,
    enemies: Iterable[dict[str, object]],
) -> dict[str, object]:
    if not isinstance(route_value, list) or any(
        isinstance(item, bool) or not isinstance(item, int) or item <= 0
        for item in route_value
    ):
        return {
            "status": "unavailable",
            "target_province_id": target_province_id,
            "reason": "route_not_observable",
        }
    remaining_route = [int(province_id) for province_id in route_value]
    if remaining_route and remaining_route[0] == origin_province_id:
        remaining_route = remaining_route[1:]
    if not remaining_route or remaining_route[-1] != target_province_id:
        return {
            "status": "unavailable",
            "target_province_id": target_province_id,
            "route_province_ids": remaining_route,
            "reason": "route_does_not_reach_target",
        }

    route_provinces = set(remaining_route)
    conflicts: list[dict[str, object]] = []
    for enemy in enemies:
        if _army_tactical_state(enemy) == "retreating":
            continue
        enemy_id = _native_int(enemy.get("army_id"))
        enemy_current = _native_int(enemy.get("current_province_id"))
        enemy_target = _native_int(enemy.get("move_target_province_id"))
        if enemy_current in route_provinces:
            conflicts.append(
                {
                    "kind": "enemy_current_on_route",
                    "enemy_army_id": enemy_id,
                    "province_id": enemy_current,
                }
            )
        if enemy_target in route_provinces:
            conflicts.append(
                {
                    "kind": "enemy_target_on_route",
                    "enemy_army_id": enemy_id,
                    "province_id": enemy_target,
                }
            )
        enemy_route = enemy.get("route_province_ids")
        enemy_remaining = (
            [
                int(province_id)
                for province_id in enemy_route
                if isinstance(province_id, int)
                and not isinstance(province_id, bool)
                and province_id > 0
            ]
            if isinstance(enemy_route, list)
            else []
        )
        if enemy_remaining and enemy_remaining[0] == enemy_current:
            enemy_remaining = enemy_remaining[1:]
        if enemy_remaining and enemy_remaining[0] == remaining_route[0]:
            conflicts.append(
                {
                    "kind": "shared_next_hop",
                    "enemy_army_id": enemy_id,
                    "province_id": remaining_route[0],
                }
            )
        enemy_hops: dict[int, int] = {}
        for enemy_hop, province_id in enumerate(enemy_remaining, start=1):
            enemy_hops.setdefault(province_id, enemy_hop)
        for player_hop, province_id in enumerate(remaining_route, start=1):
            enemy_hop = enemy_hops.get(province_id)
            if enemy_hop is None:
                continue
            conflicts.append(
                {
                    "kind": "enemy_route_intersection",
                    "enemy_army_id": enemy_id,
                    "province_id": province_id,
                    "player_hop": player_hop,
                    "enemy_hop": enemy_hop,
                }
            )
        reverse_enemy_edges = {
            (destination, origin): enemy_hop
            for enemy_hop, (origin, destination) in enumerate(
                zip(enemy_remaining, enemy_remaining[1:]),
                start=1,
            )
        }
        for player_hop, edge in enumerate(
            zip(remaining_route, remaining_route[1:]),
            start=1,
        ):
            enemy_hop = reverse_enemy_edges.get(edge)
            if enemy_hop is None:
                continue
            conflicts.append(
                {
                    "kind": "opposite_edge_intersection",
                    "enemy_army_id": enemy_id,
                    "from_province_id": edge[0],
                    "to_province_id": edge[1],
                    "player_hop": player_hop,
                    "enemy_hop": enemy_hop,
                }
            )
    return {
        "status": "unsafe" if conflicts else "safe",
        "target_province_id": target_province_id,
        "route_province_ids": remaining_route,
        "conflicts": conflicts,
    }


def _recent_war_tactics(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    army_id: int | None,
    war_id: int | None,
) -> dict[str, object]:
    """Bound legacy same-province contact using compact advance summaries."""
    if army_id is None or war_id is None:
        return {
            "blocked_enemy_ids": [],
            "blocked_province_ids": [],
            "retreat_days": 0,
            "completed_objective_province_ids": [],
        }
    current_date = _native_int(snapshot.get("date_raw"))
    blocked_enemies: dict[int, int] = {}
    blocked_provinces: dict[int, int] = {}
    completed_objectives: set[int] = set()
    contact_days = contact_probes = retreat_days = 0

    def block(
        enemy_ids: set[int], province_id: int | None, date_raw: int | None
    ) -> None:
        if date_raw is None:
            return
        until = date_raw + _NATIVE_COLLISION_COOLDOWN_GAME_DAYS * 24
        blocked_enemies.update({enemy_id: until for enemy_id in enemy_ids})
        if province_id is not None:
            blocked_provinces[province_id] = until

    for row in _history_after_latest_restore(commands):
        if (
            not is_life_advance_step(_effective_command(row))
            or row.get("ok") is not True
        ):
            continue
        result = row.get("result")
        before_date, before_war = _progress_slice(
            result, "war_progress_before", war_id
        )
        after_date, after_war = _progress_slice(
            result, "war_progress_after", war_id
        )
        if before_war is None:
            continue
        before_player = _progress_army(before_war, "player_armies", army_id)
        after_player = _progress_army(after_war, "player_armies", army_id)
        elapsed = (
            max(0, (after_date - before_date) // 24)
            if before_date is not None and after_date is not None
            else 0
        )
        retreat_days = (
            retreat_days + elapsed
            if isinstance(after_player, dict)
            and _army_tactical_state(after_player) == "retreating"
            else 0
        )
        province = (
            _native_int(before_player.get("current_province_id"))
            if isinstance(before_player, dict)
            else None
        )
        enemies = before_war.get("enemy_armies")
        local_enemy_ids = {
            int(enemy["army_id"])
            for enemy in (enemies if isinstance(enemies, list) else [])
            if isinstance(enemy, dict)
            and _native_int(enemy.get("army_id")) is not None
            and enemy.get("current_province_id") == province
        }
        after_enemies = after_war.get("enemy_armies") if after_war else None
        after_enemy_ids = {
            int(enemy["army_id"])
            for enemy in (
                after_enemies if isinstance(after_enemies, list) else []
            )
            if isinstance(enemy, dict)
            and _native_int(enemy.get("army_id")) is not None
        }
        before_score = _native_int(
            before_war.get("player_relative_war_score")
        )
        after_score = _native_int(
            after_war.get("player_relative_war_score") if after_war else None
        )
        objective = (
            _native_int(before_player.get("current_province_id"))
            if isinstance(before_player, dict)
            and _army_tactical_state(before_player) == "sieging"
            else None
        )
        if (
            objective in _progress_siege_objectives(before_war)
            and _army_tactical_state(after_player or {}) != "sieging"
            and (
                after_war is None
                or (
                    before_score is not None
                    and after_score is not None
                    and after_score > before_score
                )
            )
        ):
            completed_objectives.add(int(objective))
        improved = (
            before_score is not None
            and after_score is not None
            and after_score > before_score
        )
        if improved or local_enemy_ids - after_enemy_ids:
            contact_days = contact_probes = 0
            for enemy_id in local_enemy_ids:
                blocked_enemies.pop(enemy_id, None)
            if province is not None:
                blocked_provinces.pop(province, None)
        elif local_enemy_ids:
            contact_days += elapsed
            contact_probes += 1
            if (
                contact_days >= _NATIVE_CONTACT_STALE_GAME_DAYS
                or contact_probes >= _NATIVE_CONTACT_MAX_PROBES
            ):
                block(local_enemy_ids, province, after_date)
        if (
            before_score is not None
            and after_score is not None
            and before_score - after_score >= _NATIVE_DEFEAT_SCORE_DROP
        ):
            block(local_enemy_ids, province, after_date)

    active_enemy = sorted(
        key
        for key, until in blocked_enemies.items()
        if current_date is None or current_date < until
    )
    active_province = sorted(
        key
        for key, until in blocked_provinces.items()
        if current_date is None or current_date < until
    )
    return {
        "blocked_enemy_ids": active_enemy,
        "blocked_province_ids": active_province,
        "contact_stale": bool(active_enemy or active_province),
        "retreat_days": retreat_days,
        "completed_objective_province_ids": sorted(completed_objectives),
    }


def _deferred_move_backoff(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    step: str,
) -> dict[str, object] | None:
    deferred_dates: list[int | None] = []
    current = _native_int(snapshot.get("date_raw"))
    scoped = _history_after_latest_restore(commands)
    parsed_step = parse_move_army_step(step)
    if parsed_step is not None:
        army_id = parsed_step[0]
        for position in range(len(scoped) - 1, -1, -1):
            if _successful_merge_barrier(scoped[position], army_id):
                scoped = scoped[position + 1 :]
                break
    for row in scoped:
        if _effective_command(row) != step or row.get("ok") is not True:
            continue
        result = row.get("result")
        action = result.get("war_action") if isinstance(result, dict) else None
        status = action.get("status") if isinstance(action, dict) else None
        if status in {"move_submitted", "moving", "arrived"}:
            deferred_dates.clear()
        elif status == "move_deferred":
            submitted = _native_int(action.get("submitted_date_raw"))
            if submitted is not None:
                deferred_dates.append(submitted)
    if not deferred_dates:
        return None
    attempt = len(deferred_dates)
    required = _NATIVE_MOVE_RETRY_BACKOFF_DAYS[min(attempt - 1, 2)]
    latest = deferred_dates[-1]
    elapsed = (
        max(0, (current - latest) // 24)
        if current is not None and latest is not None
        else 0
    )
    return {
        "attempt": attempt,
        "elapsed_days": elapsed,
        "required_days": required,
        "retry_due": elapsed >= required,
    }


def _active_native_move_intent(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    army_id: int,
    target_province_id: int,
) -> dict[str, object] | None:
    latest_position = -1
    latest_row: dict[str, object] | None = None
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        if _successful_merge_barrier(row, army_id):
            return None
        command = _effective_command(row)
        if command == "restore-checkpoint" and row.get("ok") is True:
            return None
        parsed = parse_move_army_step(command)
        if parsed is None or parsed[0] != army_id:
            continue
        latest_position = position
        latest_row = row
        break
    if latest_row is None or latest_row.get("ok") is not True:
        return None
    parsed = parse_move_army_step(_effective_command(latest_row))
    if parsed != (army_id, target_province_id):
        return None
    result = latest_row.get("result")
    action = result.get("war_action") if isinstance(result, dict) else None
    if (
        not isinstance(action, dict)
        or action.get("status") not in {"move_submitted", "moving"}
        or result.get("accepted") is False
    ):
        return None
    action_army_id = action.get("army_id")
    action_target_province_id = action.get("target_province_id")
    if (
        action_army_id is not None
        and action_army_id != army_id
    ) or (
        action_target_province_id is not None
        and action_target_province_id != target_province_id
    ):
        return None

    player_armies = snapshot.get("player_armies")
    army = (
        next(
            (
                row
                for row in player_armies
                if isinstance(row, dict) and row.get("army_id") == army_id
            ),
            None,
        )
        if isinstance(player_armies, list)
        else None
    )
    if not isinstance(army, dict):
        return None
    if army.get("current_province_id") == target_province_id:
        return None
    observed_target = army.get("move_target_province_id")
    if (
        observed_target is None
        and (
            army.get("move_target_observable") is True
            or (
                army.get("move_target_observable") is False
                and _army_tactical_state(army)
                in {"regular", "sieging", "gathering", "raiding", "bartering"}
            )
        )
    ):
        return None
    if isinstance(observed_target, int) and observed_target != target_province_id:
        return None

    elapsed_days = _move_intent_elapsed_days(
        commands,
        latest_position=latest_position,
        action=action,
        snapshot=snapshot,
    )
    if elapsed_days >= _NATIVE_MOVE_INTENT_MAX_GAME_DAYS:
        return None
    return {
        "status": "active",
        "army_id": army_id,
        "target_province_id": target_province_id,
        "elapsed_days": elapsed_days,
        "timeout_days": _NATIVE_MOVE_INTENT_MAX_GAME_DAYS,
    }


def _move_intent_elapsed_days(
    commands: list[dict[str, object]],
    *,
    latest_position: int,
    action: dict[str, object],
    snapshot: dict[str, object],
) -> int:
    submitted_date_raw = action.get("submitted_date_raw")
    current_date_raw = snapshot.get("date_raw")
    if (
        isinstance(submitted_date_raw, int)
        and not isinstance(submitted_date_raw, bool)
        and isinstance(current_date_raw, int)
        and not isinstance(current_date_raw, bool)
        and current_date_raw >= submitted_date_raw
    ):
        return (current_date_raw - submitted_date_raw) // 24

    elapsed_days = 0
    for row in commands[latest_position + 1 :]:
        if (
            not is_life_advance_step(_effective_command(row))
            or row.get("ok") is not True
        ):
            continue
        result = row.get("result")
        if not isinstance(result, dict):
            continue
        elapsed = result.get("elapsed_days")
        if (
            isinstance(elapsed, int)
            and not isinstance(elapsed, bool)
            and elapsed >= 0
        ):
            elapsed_days += elapsed
            continue
        starting_date_raw = result.get("starting_date_raw")
        ending_date_raw = result.get("ending_date_raw")
        if (
            isinstance(starting_date_raw, int)
            and not isinstance(starting_date_raw, bool)
            and isinstance(ending_date_raw, int)
            and not isinstance(ending_date_raw, bool)
            and ending_date_raw >= starting_date_raw
        ):
            elapsed_days += (ending_date_raw - starting_date_raw) // 24
    return elapsed_days


def _successful_result(
    commands: Iterable[dict[str, object]], command: str
) -> dict[str, object] | None:
    for row in reversed(_expanded_command_rows(commands)):
        if _effective_command(row) != command or row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def _successful_result_for_steps(
    commands: Iterable[dict[str, object]],
    *,
    exact: tuple[str, ...] = (),
    prefixes: tuple[str, ...] = (),
) -> dict[str, object] | None:
    for row in reversed(_expanded_command_rows(commands)):
        command = _effective_command(row)
        if not isinstance(command, str) or (
            command not in exact
            and not any(command.startswith(prefix) for prefix in prefixes)
        ):
            continue
        if row.get("ok") is not True:
            continue
        result = row.get("result")
        if isinstance(result, dict):
            return result
    return None


def _accepted_marriage_result(
    commands: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    for row in reversed(_expanded_command_rows(commands)):
        command = _effective_command(row)
        if row.get("ok") is not True or not isinstance(command, str):
            continue
        result = row.get("result")
        outcome = (
            result.get("marriage_result")
            if isinstance(result, dict)
            else None
        )
        if (
            not isinstance(result, dict)
            or not isinstance(outcome, dict)
            or outcome.get("status")
            not in {"accepted_betrothal", "accepted_marriage"}
        ):
            continue
        if command == "marriage-confirm-response":
            return result
        if (
            parse_arrange_marriage_step(command) is not None
            and outcome.get("source") == "native_relationship_snapshot"
            and isinstance(outcome.get("candidate_character_id"), int)
            and not isinstance(outcome.get("candidate_character_id"), bool)
        ):
            return result
    return None


def _next_run_plan(achievements: dict[str, bool]) -> dict[str, object]:
    priorities: list[dict[str, object]] = []
    if achievements["palermo_holy_war_won"]:
        priorities.append(
            {
                "priority": 100,
                "action": "repeat_palermo_opening_war_when_visible_conditions_match",
                "reason": "the previous life converted the Palermo holy war into a confirmed win",
            }
        )
    else:
        priorities.append(
            {
                "priority": 70,
                "action": "reassess_first_low_cost_expansion",
                "reason": "the previous life did not prove a completed Palermo victory",
            }
        )
    if achievements["danish_betrothal_accepted"]:
        priorities.append(
            {
                "priority": 80,
                "action": "repeat_high_value_child_alliance_review",
                "reason": "the previous life secured the visible Danish betrothal",
            }
        )
    else:
        priorities.append(
            {
                "priority": 100,
                "action": "seek_current_life_marriage_alliance",
                "reason": "the previous life has no confirmed alliance marriage",
            }
        )
    if achievements["partition_risk_visible"]:
        priorities.append(
            {
                "priority": 60,
                "action": "reduce_current_ruler_partition_loss",
                "reason": "succession review exposed title loss during the current life",
            }
        )
    priorities.append(
        {
            "priority": 10,
            "action": "finish_on_player_death_and_record_score",
            "reason": "this is a one-generation roguelike; death ends the episode",
        }
    )
    return {
        "policy": "one-life-visible-outcomes-v1",
        "continue_as_heir_after_death": False,
        "priorities": priorities,
    }


def read_one_life_strategy(state_dir: Path) -> dict[str, object]:
    """Read the cross-run strategy without consulting CK3's protected store."""
    path = state_dir / ONE_LIFE_STRATEGY_RELATIVE_PATH
    if not path.exists():
        empty_achievements = {
            "palermo_holy_war_won": False,
            "armies_disbanded": False,
            "danish_betrothal_accepted": False,
            "partition_risk_visible": False,
        }
        return {
            "format_version": 1,
            "mode": "one_life_roguelike",
            "continue_as_heir_after_death": False,
            "episodes": [],
            "next_run_plan": _next_run_plan(empty_achievements),
            "path": str(path),
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AgentError(f"one-life strategy history is unreadable: {error}") from error
    if (
        not isinstance(payload, dict)
        or payload.get("format_version") != 1
        or payload.get("mode") != "one_life_roguelike"
        or payload.get("continue_as_heir_after_death") is not False
        or not isinstance(payload.get("episodes"), list)
        or not isinstance(payload.get("next_run_plan"), dict)
    ):
        raise AgentError("one-life strategy history has an unsupported contract")
    result = dict(payload)
    result["path"] = str(path)
    return result


def record_one_life_episode(
    state_dir: Path,
    *,
    run_id: str,
    commands: list[dict[str, object]],
    terminal: dict[str, object],
) -> dict[str, object]:
    """Record one finished life and derive the priorities for the next one."""
    if not run_id or terminal.get("terminal") is not True:
        raise AgentError("one-life episode requires a terminal death result")
    succession = _successful_result(commands, "succession-review")
    marriage = _accepted_marriage_result(commands)
    war = _successful_result_for_steps(
        commands,
        exact=("war-enforce-demands",),
        prefixes=("enforce-demands-",),
    )
    disband = _successful_result_for_steps(
        commands,
        exact=("war-disband-armies",),
        prefixes=("disband-army-",),
    )
    checkpoint_result = _successful_result(commands, "save-checkpoint")
    achievements = {
        "palermo_holy_war_won": bool(
            isinstance(war, dict)
            and isinstance(war.get("war_victory"), dict)
            and war["war_victory"].get("status") == "victory_enforced"
        ),
        "armies_disbanded": bool(
            isinstance(disband, dict)
            and (
                (
                    isinstance(disband.get("army_disband"), dict)
                    and disband["army_disband"].get("status") == "disbanded"
                )
                or (
                    isinstance(disband.get("war_action"), dict)
                    and disband["war_action"].get("status") == "disbanded"
                )
            )
        ),
        "danish_betrothal_accepted": bool(
            isinstance(marriage, dict)
            and isinstance(marriage.get("marriage_result"), dict)
            and marriage["marriage_result"].get("status")
            in {"accepted_betrothal", "accepted_marriage"}
        ),
        "partition_risk_visible": bool(
            isinstance(succession, dict)
            and isinstance(succession.get("succession_state"), dict)
            and succession["succession_state"].get("partition_risk_visible")
            is True
        ),
    }
    checkpoint = None
    if isinstance(checkpoint_result, dict) and isinstance(
        checkpoint_result.get("checkpoint"), dict
    ):
        raw = checkpoint_result["checkpoint"]
        checkpoint = {
            key: raw.get(key) for key in ("name", "size", "sha256")
        }
    episode = {
        "run_id": run_id,
        "finished_at": utc_now(),
        "terminal_reason": (
            terminal.get("terminal_reason")
            if isinstance(terminal.get("terminal_reason"), str)
            else "player_death"
        ),
        "continue_as_heir_after_death": False,
        "technical_settlement_handoff": bool(
            terminal.get("technical_settlement_handoff")
        ),
        "heir_gameplay_actions": 0,
        "score": terminal.get("score"),
        "achievements": achievements,
        "latest_checkpoint": checkpoint,
        "successful_steps": [
            row.get("command")
            for row in commands
            if row.get("ok") is True and isinstance(row.get("command"), str)
        ],
    }
    history = read_one_life_strategy(state_dir)
    episodes = [
        row
        for row in history["episodes"]
        if isinstance(row, dict) and row.get("run_id") != run_id
    ]
    episodes.append(episode)
    payload = {
        "format_version": 1,
        "mode": "one_life_roguelike",
        "continue_as_heir_after_death": False,
        "updated_at": utc_now(),
        "episodes": episodes,
        "next_run_plan": _next_run_plan(achievements),
    }
    path = state_dir / ONE_LIFE_STRATEGY_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(path, payload)
    result = dict(payload)
    result["path"] = str(path)
    result["recorded_episode"] = episode
    return result
