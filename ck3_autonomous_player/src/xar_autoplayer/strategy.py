"""Persistent one-life episode summaries used by the gameplay policy."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Iterable

from .bridge.event_contract import (
    choose_event_option_number,
    event_option_step,
    normalize_active_event,
    parse_event_option_step,
)
from .bridge.declaration_contract import (
    QUERY_DECLARABLE_WARS_STEP,
    declare_war_step,
)
from .bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    parse_query_combat_simulation_inputs_v3_step,
    query_combat_simulation_inputs_v3_step,
)
from .bridge.battle_control_contract import (
    BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC,
    BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
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
    RAIKTOR_BOOKMARK_EVENT_SCOPE_CAPABILITY,
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
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_BACKEND_ID,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
    normalize_pending_interaction_id,
)
from .bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from .bridge.council_composition_candidates_contract import (
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
    STEWARD_POSITION_KEY,
    normalize_council_composition_candidates_v1,
)
from .bridge.council_assign_councillor_action_contract import (
    ASSIGN_COUNCILLOR_V1_CAPABILITY,
    ASSIGN_COUNCILLOR_V1_STEP,
)
from .bridge.settlement_contract import ONE_LIFE_SETTLEMENT_CAPABILITY
from .bridge.succession_transition_contract import (
    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
    ORDINARY_CAMPAIGN_SUCCESSION,
    ROGUE_ONE_LIFE,
    UNKNOWN_SUCCESSION_LIFECYCLE,
    legacy_rogue_one_life_binding_v1,
    normalize_succession_lifecycle_binding_v1,
    unknown_succession_lifecycle_binding_v1,
)
from .bridge.war_contract import (
    MAX_ROUTE_CONTACT_HOSTILE_IDS,
    QUERY_ARMY_STRENGTHS_STEP,
    RAISE_TROOPS_STEP,
    advance_route_contact_horizon_step,
    battle_decision_epoch_advance_step,
    war_objective_hold_sentinel_advance_step,
    controllable_armies,
    disband_army_step,
    enemy_primary_default_raise_province_ids,
    enforce_demands_step,
    enemy_armies_from_wars,
    is_life_advance_step,
    merge_armies_step,
    observe_merge_armies_postcondition_v1,
    move_army_step,
    offer_white_peace_step,
    surrender_war_step,
    parse_merge_armies_step,
    parse_battle_decision_epoch_advance_step,
    parse_committed_route_sentinel_advance_speed,
    parse_committed_route_sentinel_advance_step,
    parse_war_objective_hold_sentinel_advance_speed,
    parse_war_objective_hold_sentinel_advance_step,
    parse_move_army_step,
    parse_preview_move_army_step,
    parse_query_war_termination_options_step,
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
    war_termination_active_war_signature,
    war_termination_negative_query_signature,
)
from .environment import write_json_atomic
from .errors import AgentError
from .runtime import utc_now
from .raiktor_formal_exit import plan_raiktor_formal_exit
from .lifestyle_formal_consumer import consume_lifestyle_private_query
from .simulation.battle_terminal_cruise_policy import (
    assess_battle_terminal_cruise,
)
from .simulation import combat_decision_contract as combat_entry_eu
from .simulation.general_battle_forecast import contact_admission, forecast_fixed_contact
from .simulation.prewar_battle_proxy import (
    forecast_prewar_power_battle,
    prewar_declaration_admission,
)
from .vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)
from .vanilla_events.bookmark_raiktor_policy import (
    recommend_robert_raiktor_option_v1,
)
from .vanilla_events.outcome import (
    plan_registered_event_material_postcondition_v1,
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
_NATIVE_CAPITAL_REGROUP_MIN_GAME_DAYS = 1
_NATIVE_MOVE_RETRY_BACKOFF_DAYS = (7, 14, 30)
_WHITE_PEACE_PROPOSAL_COOLDOWN_RAW = 30 * 24
_WHITE_PEACE_NATIVE_RESPONSE_OBSERVATION_RAW = 10 * 24
_NEGATIVE_WAR_TERMINATION_REUSE_RAW = 7 * 24
_DE_JURE_NO_SAFE_ROUTE_SURRENDER_CB = "individual_county_de_jure_cb"
_DE_JURE_NO_SAFE_ROUTE_CB_DATABASE_INDEX = 17
# R851 proved that a long-running negative-score war can reach a deterministic
# dead end before the older R767 -25 score sample. Keep zero/positive frames
# out, but do not require another lost battle after every route is exhausted.
_DE_JURE_NO_SAFE_ROUTE_SURRENDER_MAX_SCORE = -1
_DE_JURE_NO_SAFE_ROUTE_SURRENDER_MIN_DAYS = 180
_TERMINAL_SCORE_SURRENDER_SCORE = -100
_BATTLE_DECISION_EPOCH_ADVANCE_STEP = "battle-decision-epoch-advance"
_PROVISIONAL_DEFENSE_TRIALS = 512
_PROVISIONAL_DEFENSE_HORIZON_DAYS = 120
_PROVISIONAL_DEFENSE_MAX_P90_HARD_LOSS_PERCENT = 20
_WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP = (
    "war-objective-hold-sentinel-advance"
)
_CONSERVATIVE_FEUDAL_DE_JURE_WAR_ENTRY = {
    "rule_id": "feudal-single-county-de-jure-forecast-candidate-v1",
    "casus_belli_key": "individual_county_de_jure_cb",
    "source": "common/casus_belli_types/00_dejure_war.txt",
    "source_sha256": (
        "D8737A2205116118A5ECD6EFA576D316B3155730A3824DC4BD109A68B9D5B6EE"
    ),
}
_CONSERVATIVE_FEUDAL_PLAYER_CLAIM_WAR_ENTRY = {
    "rule_id": "feudal-adjacent-independent-county-player-claim-forecast-candidate-v1",
    "casus_belli_key": "claim_cb",
    "source": "common/casus_belli_types/00_claim.txt",
    "source_sha256": (
        "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
    ),
}
_BATTLE_TERMINAL_CRUISE_STEP = "battle-terminal-cruise"
_BATTLE_CONTROL_IDENTITY_PENDING_QUERY_ATTEMPTS = 3
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
_RAIKTOR_INBOUND_WHITE_PEACE_POLICY = {
    "rule_id": "raiktor-inbound-white-peace-v1",
    "definition_key": "end_war_attacker_white_peace_interaction",
    "special_interaction_kind": "end_war_white_peace_interaction",
    "absolute_outcome": "white_peace",
    "casus_belli_key": "raiktor_claim_cb",
    "source": "common/casus_belli_types/00_event_war.txt",
    "source_sha256": (
        "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707"
    ),
}
_DEGRADED_ORDINARY_INTERACTION_ALLOWLIST = {
    "demand_hostage_interaction": {
        "classification": "ordinary_non_war_nonreligious",
        "domain": "hostage_demand",
        "war_sensitive": True,
        "source": "common/character_interactions/05_bp2_interactions.txt",
        "source_sha256": (
            "78526C7BBC520B4F8D8713DC80BF8C089655A3000B661FC104FA1AF139AD7E94"
        ),
        "known_decline_effects": [
            "secondary_recipient:remove_under_offer_as_hostage_flag",
            "actor:char_interaction.0301",
            "conditional_actor_tyranny_and_opinion_if_player_vassal",
        ],
    },
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
    "ransom_interaction": {
        "classification": "ordinary_non_war_nonreligious",
        "domain": "prison_ransom",
        "war_sensitive": True,
        "authored_special_interaction": "ransom_interaction",
        "source": "common/character_interactions/00_prison_interactions.txt",
        "source_sha256": (
            "3E05C94CDCE4D42CCE8256D2D79CD78FEB1C9D5B79DAA64AA8243AA0C658F22B"
        ),
        "known_decline_effects": [
            "secondary_recipient:character_ransom_refused_by_player:10y",
            "actor:char_interaction.0131",
        ],
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
_GRANT_VASSAL_REJECT_ONLY_POLICY = {
    "rule_id": "grant-vassal-reject-only-v1",
    "definition_key": "grant_vassal_interaction",
    "deterministic_key_hash": 1_006_648_858,
    "runtime_ordinal": 277,
    "domain": "vassal_transfer",
    "supported_scope": "frozen_standard_feudal_profile_not_frame_attested",
    "source": "common/character_interactions/00_vassal_interactions.txt",
    "source_sha256": (
        "1249CAC40138D48210A07245746C4A6683C5F58F3141C04A20DB2C00B6375BF8"
    ),
    "decline_event_source": (
        "events/interaction_events/character_interaction_events.txt"
    ),
    "decline_event_source_sha256": (
        "D238E0A3442F41C35AF35157D47A754CB200B72AB2A0184BAEFC86E63347A150"
    ),
    "known_decline_effects": [
        "actor:char_interaction.0211:letter_only",
        "conditional_clan_unity_loss",
    ],
}
_NEGOTIATE_ALLIANCE_INBOUND_POLICY = {
    "rule_id": "negotiate-alliance-inbound-accept-v1",
    "definition_key": "negotiate_alliance_interaction",
    "domain": "marriage_alliance",
    "source": "common/character_interactions/00_alliance.txt",
    "source_sha256": (
        "919ED408EC735F64ED972E23A376CD618A2E207A0EA273F973C5B1F89440E39D"
    ),
    "required_send_option_count": 2,
    "known_selected_option_costs": ["actor_hook", "actor_influence"],
    "known_decline_effects": [
        "actor:refused_alliance_opinion:toward_recipient",
        "minor_clan_unity_loss",
    ],
}
_PERK_ALLIANCE_INBOUND_POLICY = {
    "rule_id": "perk-alliance-inbound-accept-v1",
    "definition_key": "perk_alliance_interaction",
    "deterministic_key_hash": 328_040_944,
    "runtime_ordinal": 4,
    "domain": "alliance",
    "source": "common/character_interactions/00_alliance.txt",
    "source_sha256": (
        "919ED408EC735F64ED972E23A376CD618A2E207A0EA273F973C5B1F89440E39D"
    ),
    "required_send_option_count": 2,
    "known_selected_option_costs": ["actor_hook", "actor_influence"],
    "known_decline_effects": [
        "actor:refused_alliance_opinion:toward_recipient",
        "minor_clan_unity_loss",
    ],
}
_CALL_ALLY_BUSY_REJECT_POLICY = {
    "rule_id": "call-ally-busy-reject-v1",
    "definition_key": "call_ally_interaction",
    "deterministic_key_hash": 936_306_703,
    "domain": "war_call",
    "source": "common/character_interactions/00_alliance.txt",
    "source_sha256": (
        "919ED408EC735F64ED972E23A376CD618A2E207A0EA273F973C5B1F89440E39D"
    ),
    "known_decline_effects": [
        "actor:rejected_call_to_offensive_war_opinion:-20",
        "actor:rejected_call_to_defensive_war_opinion:-50",
        "recipient:prestige_experience_or_mandala_penalty",
        "target_war:set_called_to",
        "conditional_contract_house_blood_brother_penalties",
    ],
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


def _same_frame_campaign_root_context(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
) -> dict[str, object] | None:
    """Recover a complete campaign-root row bound to this paused frame."""

    if not isinstance(snapshot, dict):
        return None
    played_character = snapshot.get("played_character")
    actor_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    if not (
        isinstance(actor_id, int)
        and not isinstance(actor_id, bool)
        and isinstance(native_revision, int)
        and not isinstance(native_revision, bool)
        and isinstance(date_raw, int)
        and not isinstance(date_raw, bool)
    ):
        return None
    payloads: list[object] = [snapshot.get("campaign_root_context")]
    for row in rows:
        if (
            _effective_command(row) != "query-campaign-root-context-v1"
            or row.get("ok") is not True
        ):
            continue
        result = _effective_command_result(row)
        payloads.append(
            result.get("campaign_root_context")
            if isinstance(result, dict)
            else None
        )
    for payload in reversed(payloads):
        if not isinstance(payload, dict):
            continue
        readiness = payload.get("readiness")
        if (
            payload.get("status") == "available"
            and payload.get("snapshot_revision") == native_revision
            and payload.get("date_raw") == date_raw
            and payload.get("player_character_id") == actor_id
            and isinstance(readiness, dict)
            and readiness.get("ready") is True
        ):
            return payload
    return None


def _complete_player_held_county_capital_province_ids(
    campaign_root: dict[str, object],
) -> list[int] | None:
    """Return the complete directly-held county-capital set, or unknown.

    Historical v1 campaign-root rows did not carry the additive county
    capital field.  They remain readable for restore compatibility, but must
    never be mistaken for a complete empty defensive-objective set.
    """

    readiness = campaign_root.get("readiness")
    partition = campaign_root.get("held_title_partition")
    if not (
        isinstance(readiness, dict)
        and readiness.get("held_title_partition_ready") is True
        and isinstance(partition, list)
    ):
        return None
    candidates: list[tuple[int, int]] = []
    for row in partition:
        if not isinstance(row, dict):
            return None
        title = row.get("title")
        if not isinstance(title, dict):
            return None
        title_id = _native_int(title.get("title_id"))
        tier_raw = _native_int(title.get("tier_raw"))
        if title_id is None or tier_raw is None:
            return None
        if tier_raw != 2:
            continue
        province_id = _native_int(row.get("capital_province_id"))
        if province_id is None:
            return None
        candidates.append((title_id, province_id))
    if not candidates:
        return None
    candidates.sort()
    province_ids = [province_id for _, province_id in candidates]
    if len(province_ids) != len(set(province_ids)):
        return None
    return province_ids


def _conservative_feudal_de_jure_war_entry(
    declaration: dict[str, object],
    assessment: dict[str, object] | None,
    campaign_root: dict[str, object] | None,
    available_steps: set[str],
    *,
    at_peace: bool,
) -> dict[str, object]:
    """Keep one exact-build single-county candidate for a future forecast."""

    rule = _CONSERVATIVE_FEUDAL_DE_JURE_WAR_ENTRY
    declaration_id = declaration.get("declaration_id")
    try:
        declaration_step = (
            declare_war_step(declaration_id)
            if isinstance(declaration_id, str)
            else None
        )
    except ValueError:
        declaration_step = None
    titles = declaration.get("target_title_ids")
    government = (
        campaign_root.get("government")
        if isinstance(campaign_root, dict)
        else None
    )
    government_flags = (
        government.get("flags") if isinstance(government, dict) else None
    )
    monthly_income = (
        campaign_root.get("player_monthly_gold_income")
        if isinstance(campaign_root, dict)
        else None
    )
    blockers: list[str] = []
    if not at_peace:
        blockers.append("active_war_blocks_conservative_entry")
    if not (
        declaration.get("source") == "native"
        and declaration.get("casus_belli_key") == rule["casus_belli_key"]
        and declaration.get("configuration_index") == -1
        and declaration.get("claimant_character_id") == -1
        and isinstance(titles, list)
        and len(titles) == 1
        and isinstance(titles[0], int)
        and not isinstance(titles[0], bool)
        and titles[0] > 0
    ):
        blockers.append("declaration_outside_single_county_de_jure_slice")
    if not (
        isinstance(government, dict)
        and government.get("key") == "feudal_government"
        and isinstance(government_flags, list)
        and "government_is_feudal" in government_flags
    ):
        blockers.append("same_frame_standard_feudal_scope_unavailable")
    if not (
        isinstance(campaign_root, dict)
        and campaign_root.get("player_targeting_faction_count") == 0
        and isinstance(campaign_root.get("player_domain_size"), int)
        and not isinstance(campaign_root.get("player_domain_size"), bool)
        and isinstance(campaign_root.get("player_domain_limit"), int)
        and not isinstance(campaign_root.get("player_domain_limit"), bool)
        and int(campaign_root["player_domain_size"])
        <= int(campaign_root["player_domain_limit"])
        and isinstance(monthly_income, dict)
        and monthly_income.get("scale") == WAR_ENTRY_FIXED_POINT_SCALE
        and isinstance(monthly_income.get("raw"), int)
        and not isinstance(monthly_income.get("raw"), bool)
        and int(monthly_income["raw"]) > 0
    ):
        blockers.append("same_frame_peacetime_budget_scope_not_conservative")
    if not isinstance(assessment, dict):
        blockers.append("same_frame_native_power_assessment_unavailable")
    else:
        actor_base = int(assessment["actor_power_base_raw"])
        actor_total = int(assessment["actor_power_total_raw"])
        target_base = int(assessment["target_power_base_raw"])
        target_pre_adjustment = int(
            assessment["target_pre_adjustment_total_raw"]
        )
        target_total = int(assessment["target_power_total_raw"])
        ratio = int(assessment["actual_power_ratio_raw"])
        if not (
            assessment.get("target_character_id")
            == declaration.get("target_character_id")
            and assessment.get("effective_target_character_id")
            == declaration.get("target_character_id")
            and actor_base > 0
            and target_total > 0
            and assessment.get("actor_network_contribution_raw") == 0
            and actor_total == actor_base
            and assessment.get("target_network_contribution_raw") == 0
            and target_pre_adjustment == target_base
            and assessment.get("target_adjustment_delta_raw") == 0
            and target_total == target_pre_adjustment
            and assessment.get("distance_raw") == 0
            and ratio > 0
        ):
            blockers.append("native_de_jure_candidate_scope_not_met")
    return {
        "status": "forecast_required" if not blockers else "blocked",
        "rule_id": rule["rule_id"],
        "selected_step": None,
        "typed_declaration_step": declaration_step,
        "typed_declaration_available": (
            isinstance(declaration_step, str)
            and declaration_step in available_steps
        ),
        "blockers": blockers,
        "source": rule["source"],
        "source_sha256": rule["source_sha256"],
        "native_actual_power_ratio_raw": (
            assessment.get("actual_power_ratio_raw")
            if isinstance(assessment, dict)
            else None
        ),
    }


def _player_claim_declarations(
    declarations: object,
    *,
    actor_character_id: object,
) -> list[dict[str, object]]:
    """Return final-legal native claim rows pressed by the current player."""

    if not (
        isinstance(declarations, list)
        and isinstance(actor_character_id, int)
        and not isinstance(actor_character_id, bool)
        and actor_character_id > 0
    ):
        return []
    rows = [
        row
        for row in declarations
        if isinstance(row, dict)
        and row.get("source") == "native"
        and row.get("casus_belli_key")
        == _CONSERVATIVE_FEUDAL_PLAYER_CLAIM_WAR_ENTRY["casus_belli_key"]
        and row.get("claimant_character_id") == actor_character_id
        and isinstance(row.get("declaration_id"), str)
        and isinstance(row.get("target_character_id"), int)
        and not isinstance(row.get("target_character_id"), bool)
        and isinstance(row.get("target_title_ids"), list)
        and len(row["target_title_ids"]) == 1
        and isinstance(row["target_title_ids"][0], int)
        and not isinstance(row["target_title_ids"][0], bool)
        and row["target_title_ids"][0] > 0
    ]
    return sorted(
        rows,
        key=lambda row: (
            int(row["target_character_id"]),
            str(row["declaration_id"]),
        ),
    )


def _adjacent_independent_county_player_claims(
    declarations: list[dict[str, object]],
    campaign_root: dict[str, object] | None,
) -> list[dict[str, object]]:
    """Keep the bounded claim slice proven by campaign-root relationships."""

    if not isinstance(campaign_root, dict):
        return []
    readiness = campaign_root.get("readiness")
    adjacent = campaign_root.get(
        "adjacent_external_province_holder_character_ids"
    )
    contexts = campaign_root.get("related_character_contexts")
    if not (
        isinstance(readiness, dict)
        and readiness.get("adjacent_external_province_holders_ready") is True
        and readiness.get("related_character_contexts_ready") is True
        and isinstance(adjacent, list)
        and isinstance(contexts, list)
    ):
        return []
    adjacent_ids = {
        value
        for value in adjacent
        if isinstance(value, int) and not isinstance(value, bool) and value > 0
    }
    county_targets: dict[int, int] = {}
    for context in contexts:
        if not isinstance(context, dict):
            continue
        target = context.get("character_id")
        title = context.get("primary_title")
        if not (
            isinstance(target, int)
            and not isinstance(target, bool)
            and target in adjacent_ids
            and context.get("relationship_role")
            == "adjacent_external_province_holder"
            and context.get("independent") is True
            and isinstance(title, dict)
            and title.get("tier_raw") == 2
            and title.get("tier_key") == "county"
            and isinstance(title.get("title_id"), int)
            and not isinstance(title.get("title_id"), bool)
            and int(title["title_id"]) > 0
        ):
            continue
        county_targets[target] = int(title["title_id"])
    return [
        declaration
        for declaration in declarations
        if county_targets.get(int(declaration["target_character_id"]))
        == declaration["target_title_ids"][0]
    ]


def _conservative_feudal_player_claim_war_entry(
    declarations: list[dict[str, object]],
    assessments: dict[int, dict[str, object]],
    campaign_root: dict[str, object] | None,
    available_steps: set[str],
    *,
    at_peace: bool,
) -> dict[str, object]:
    """Rank adjacent player claims without using power as action permission."""

    rule = _CONSERVATIVE_FEUDAL_PLAYER_CLAIM_WAR_ENTRY
    government = (
        campaign_root.get("government")
        if isinstance(campaign_root, dict)
        else None
    )
    government_flags = (
        government.get("flags") if isinstance(government, dict) else None
    )
    monthly_income = (
        campaign_root.get("player_monthly_gold_income")
        if isinstance(campaign_root, dict)
        else None
    )
    global_blockers: list[str] = []
    if not at_peace:
        global_blockers.append("active_war_blocks_player_claim_entry")
    if not (
        isinstance(campaign_root, dict)
        and campaign_root.get("independent") is True
        and isinstance(government, dict)
        and government.get("key") == "feudal_government"
        and isinstance(government_flags, list)
        and "government_is_feudal" in government_flags
    ):
        global_blockers.append("same_frame_independent_feudal_scope_unavailable")
    if not (
        isinstance(campaign_root, dict)
        and campaign_root.get("player_targeting_faction_count") == 0
        and isinstance(campaign_root.get("player_domain_size"), int)
        and not isinstance(campaign_root.get("player_domain_size"), bool)
        and isinstance(campaign_root.get("player_domain_limit"), int)
        and not isinstance(campaign_root.get("player_domain_limit"), bool)
        and int(campaign_root["player_domain_size"])
        <= int(campaign_root["player_domain_limit"])
        and isinstance(monthly_income, dict)
        and monthly_income.get("scale") == WAR_ENTRY_FIXED_POINT_SCALE
        and isinstance(monthly_income.get("raw"), int)
        and not isinstance(monthly_income.get("raw"), bool)
        and int(monthly_income["raw"]) > 0
    ):
        global_blockers.append("same_frame_peacetime_budget_scope_not_conservative")

    admitted: list[
        tuple[int, int, int, int, str, dict[str, object], dict[str, object], str]
    ] = []
    candidate_blockers: list[dict[str, object]] = []
    for declaration in declarations:
        target = int(declaration["target_character_id"])
        assessment = assessments.get(target)
        blockers = list(global_blockers)
        if not isinstance(assessment, dict):
            blockers.append("same_frame_native_power_assessment_unavailable")
            candidate_blockers.append(
                {
                    "declaration_id": declaration["declaration_id"],
                    "target_character_id": target,
                    "blockers": blockers,
                }
            )
            continue
        integer_fields = (
            "effective_target_character_id",
            "actor_power_base_raw",
            "actor_network_contribution_raw",
            "actor_power_total_raw",
            "target_power_base_raw",
            "target_network_contribution_raw",
            "target_pre_adjustment_total_raw",
            "target_adjustment_delta_raw",
            "target_power_total_raw",
            "actual_power_ratio_raw",
            "distance_raw",
        )
        if not all(
            isinstance(assessment.get(field), int)
            and not isinstance(assessment.get(field), bool)
            for field in integer_fields
        ):
            blockers.append("native_power_assessment_shape_invalid")
        else:
            actor_base = int(assessment["actor_power_base_raw"])
            actor_network = int(
                assessment["actor_network_contribution_raw"]
            )
            actor_total = int(assessment["actor_power_total_raw"])
            target_base = int(assessment["target_power_base_raw"])
            target_network = int(
                assessment["target_network_contribution_raw"]
            )
            target_pre_adjustment = int(
                assessment["target_pre_adjustment_total_raw"]
            )
            target_adjustment = int(
                assessment["target_adjustment_delta_raw"]
            )
            target_total = int(assessment["target_power_total_raw"])
            ratio = int(assessment["actual_power_ratio_raw"])
            if not (
                assessment.get("target_character_id") == target
                and assessment["effective_target_character_id"] == target
                and actor_total > 0
                and actor_total == actor_base + actor_network
                and target_total > 0
                and target_pre_adjustment == target_base + target_network
                and target_total == target_pre_adjustment + target_adjustment
                and ratio > 0
            ):
                blockers.append("native_complete_power_assessment_invalid")
        try:
            declaration_step = declare_war_step(
                str(declaration["declaration_id"])
            )
        except ValueError:
            declaration_step = ""
        if blockers:
            candidate_blockers.append(
                {
                    "declaration_id": declaration["declaration_id"],
                    "target_character_id": target,
                    "blockers": blockers,
                }
            )
            continue
        admitted.append(
            (
                int(assessment["actual_power_ratio_raw"]),
                int(assessment["target_power_total_raw"]),
                int(assessment["distance_raw"]),
                target,
                str(declaration["declaration_id"]),
                declaration,
                assessment,
                declaration_step,
            )
        )

    if not admitted:
        return {
            "status": "blocked",
            "rule_id": rule["rule_id"],
            "selected_step": None,
            "candidate_blockers": candidate_blockers,
            "source": rule["source"],
            "source_sha256": rule["source_sha256"],
        }
    selected = min(admitted)
    return {
        "status": "forecast_required",
        "rule_id": rule["rule_id"],
        "selected_step": None,
        "typed_declaration_step": selected[7],
        "typed_declaration_available": selected[7] in available_steps,
        "declaration": selected[5],
        "assessment": selected[6],
        "candidate_blockers": candidate_blockers,
        "source": rule["source"],
        "source_sha256": rule["source_sha256"],
        "native_actual_power_ratio_raw": selected[0],
        "eligible_candidate_count": len(admitted),
    }


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
    """Match only the exact direct, unexpired zero-option marriage shape."""

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
    age_days = deadline.get("age_days") if isinstance(deadline, dict) else None
    expiration_days = (
        deadline.get("expiration_days") if isinstance(deadline, dict) else None
    )
    remaining_days = (
        deadline.get("remaining_days") if isinstance(deadline, dict) else None
    )
    if not (
        isinstance(deadline, dict)
        and isinstance(age_days, int)
        and not isinstance(age_days, bool)
        and isinstance(expiration_days, int)
        and not isinstance(expiration_days, bool)
        and expiration_days == 60
        and isinstance(remaining_days, int)
        and not isinstance(remaining_days, bool)
        and 0 <= age_days < expiration_days
        and remaining_days == expiration_days - age_days
        and remaining_days > 0
        and deadline.get("expiry_boundary_status") == "not_reached"
    ):
        gaps.append("marriage_unexpired_deadline_shape_mismatch")

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


def _grant_vassal_reject_contract_gaps(
    context: dict[str, object],
    *,
    snapshot: dict[str, object],
    active_wars: list[dict[str, object]],
) -> list[str]:
    """Admit only the observed direct, zero-option feudal-preview decline."""

    gaps: list[str] = []
    definition = context.get("definition")
    if not (
        isinstance(definition, dict)
        and definition.get("canonical_key")
        == _GRANT_VASSAL_REJECT_ONLY_POLICY["definition_key"]
        and definition.get("deterministic_key_hash")
        == _GRANT_VASSAL_REJECT_ONLY_POLICY["deterministic_key_hash"]
        and definition.get("runtime_ordinal")
        == _GRANT_VASSAL_REJECT_ONLY_POLICY["runtime_ordinal"]
    ):
        gaps.append("grant_vassal_exact_definition_mismatch")

    roles = context.get("roles")
    played = snapshot.get("played_character")
    actor = roles.get("actor_character_id") if isinstance(roles, dict) else None
    recipient = (
        roles.get("recipient_character_id") if isinstance(roles, dict) else None
    )
    transferred = (
        roles.get("secondary_actor_character_id")
        if isinstance(roles, dict)
        else None
    )
    if not (
        all(
            isinstance(value, int) and not isinstance(value, bool) and value > 0
            for value in (actor, recipient, transferred)
        )
        and len({actor, recipient, transferred}) == 3
        and roles.get("secondary_recipient_character_id") == -1
        and roles.get("intermediary_character_id") == -1
        and isinstance(played, dict)
        and played.get("character_id") == recipient
    ):
        gaps.append("grant_vassal_direct_three_role_binding_mismatch")

    routing = context.get("routing")
    if not (
        isinstance(routing, dict)
        and routing.get("kind") == 0
        and routing.get("current_responder_role") == "recipient"
        and routing.get("reply_execution_channel") == "recipient"
        and routing.get("local_route") is True
        and routing.get("played_character_id") == recipient
        and routing.get("auto_accept_notification") is False
    ):
        gaps.append("grant_vassal_direct_local_reply_mismatch")

    deadline = context.get("deadline")
    age = deadline.get("age_days") if isinstance(deadline, dict) else None
    remaining = (
        deadline.get("remaining_days") if isinstance(deadline, dict) else None
    )
    if not (
        isinstance(deadline, dict)
        and isinstance(age, int)
        and not isinstance(age, bool)
        and isinstance(remaining, int)
        and not isinstance(remaining, bool)
        and deadline.get("expiration_days") == 60
        and 0 <= age < 60
        and remaining == 60 - age
        and deadline.get("expiry_boundary_status") == "not_reached"
    ):
        gaps.append("grant_vassal_unexpired_deadline_mismatch")

    options = context.get("send_options")
    if not (
        isinstance(options, dict)
        and options.get("exclusive") is True
        and options.get("definition_count") == 0
        and options.get("context_count") == 0
        and options.get("rows") == []
    ):
        gaps.append("grant_vassal_zero_send_options_mismatch")

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    if not (
        isinstance(terms, dict)
        and terms.get("special_data_present") is False
        and isinstance(special, dict)
        and special.get("status") == "unavailable"
        and special.get("value") is None
        and special.get("reason") == "special_war_binding_not_applicable"
    ):
        gaps.append("grant_vassal_nonwar_special_binding_mismatch")
    legality = context.get("legality")
    acknowledge = (
        legality.get("acknowledge") if isinstance(legality, dict) else None
    )
    if not (
        isinstance(acknowledge, dict)
        and acknowledge.get("status") == "available"
        and acknowledge.get("allowed") is False
        and acknowledge.get("reason") == "normal_reply_channel"
    ):
        gaps.append("grant_vassal_normal_reply_channel_mismatch")
    # A concurrent war does not change the exact-build authored decline into
    # an acceptance/transfer.  Still require an observed war list: the
    # planner's filtered view must not silently turn missing or malformed
    # native state into an empty-war claim.
    snapshot_wars = snapshot.get("active_wars")
    if not isinstance(snapshot_wars, list) or snapshot_wars != active_wars:
        gaps.append("grant_vassal_active_war_or_war_scope_unknown")
    return gaps


def _negotiate_alliance_inbound_assessment(
    context: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    available_steps: set[str],
    candidate_replies: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Admit only the exact zero-option inbound alliance production blocker."""

    policy = _NEGOTIATE_ALLIANCE_INBOUND_POLICY
    definition = context.get("definition")
    definition_key = (
        definition.get("canonical_key")
        if isinstance(definition, dict)
        else None
    )
    if definition_key != policy["definition_key"]:
        return {"status": "not_applicable", "rule_id": policy["rule_id"]}

    blocked: list[str] = []
    roles = context.get("roles")
    actor_id = (
        roles.get("actor_character_id") if isinstance(roles, dict) else None
    )
    recipient_id = (
        roles.get("recipient_character_id") if isinstance(roles, dict) else None
    )
    if not (
        isinstance(actor_id, int)
        and not isinstance(actor_id, bool)
        and actor_id > 0
        and isinstance(recipient_id, int)
        and not isinstance(recipient_id, bool)
        and recipient_id > 0
        and actor_id != recipient_id
        and isinstance(roles, dict)
        and roles.get("secondary_actor_character_id") == -1
        and roles.get("secondary_recipient_character_id") == -1
        and roles.get("intermediary_character_id") == -1
    ):
        blocked.append("negotiate_alliance_direct_roles_mismatch")

    routing = context.get("routing")
    if not (
        isinstance(routing, dict)
        and routing.get("kind") == 0
        and routing.get("played_character_id") == recipient_id
        and routing.get("current_responder_role") == "recipient"
        and routing.get("reply_execution_channel") == "recipient"
        and routing.get("local_route") is True
        and routing.get("auto_accept_notification") is False
    ):
        blocked.append("negotiate_alliance_direct_local_route_mismatch")

    deadline = context.get("deadline")
    if not (
        isinstance(deadline, dict)
        and deadline.get("age_days") == 0
        and deadline.get("expiration_days") == 60
        and deadline.get("remaining_days") == 60
        and deadline.get("expiry_boundary_status") == "not_reached"
    ):
        blocked.append("negotiate_alliance_same_day_deadline_shape_mismatch")

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    if not (
        isinstance(terms, dict)
        and terms.get("special_data_present") is False
        and isinstance(special, dict)
        and special.get("status") == "unavailable"
        and special.get("value") is None
        and special.get("reason") == "special_war_binding_not_applicable"
    ):
        blocked.append("negotiate_alliance_non_special_shape_mismatch")

    send_options = context.get("send_options")
    rows = send_options.get("rows") if isinstance(send_options, dict) else None
    if not (
        isinstance(send_options, dict)
        and send_options.get("exclusive") is False
        and send_options.get("definition_count")
        == policy["required_send_option_count"]
        and send_options.get("context_count")
        == policy["required_send_option_count"]
        and isinstance(rows, list)
        and len(rows) == policy["required_send_option_count"]
        and all(
            isinstance(row, dict)
            and row.get("native_index") == index
            and row.get("selected") is False
            for index, row in enumerate(rows)
        )
    ):
        blocked.append("negotiate_alliance_zero_option_vector_mismatch")

    defensive_wars = [
        war
        for war in active_wars
        if isinstance(war, dict)
        and war.get("player_side") == "defender"
        and war.get("player_is_primary_war_leader") is True
    ]
    if not defensive_wars:
        blocked.append("negotiate_alliance_active_defensive_war_required")
    if any(
        isinstance(war, dict)
        and war.get("primary_opponent_character_id") == actor_id
        for war in active_wars
    ):
        blocked.append("negotiate_alliance_actor_is_active_war_opponent")

    accept = candidate_replies.get("accept")
    if not isinstance(accept, dict) or accept.get("native_legal") is not True:
        blocked.append("negotiate_alliance_accept_not_native_legal")
    elif accept.get("action_reachable") is not True:
        blocked.append("negotiate_alliance_accept_command_unavailable")

    evidence = {
        "source": policy["source"],
        "source_sha256": policy["source_sha256"],
        "actor_character_id": actor_id,
        "recipient_character_id": recipient_id,
        "selected_option_count": (
            sum(
                1
                for row in rows
                if isinstance(row, dict) and row.get("selected") is True
            )
            if isinstance(rows, list)
            else None
        ),
        "active_defensive_war_ids": [
            war.get("war_id") for war in defensive_wars
        ],
        "known_selected_option_costs": list(
            policy["known_selected_option_costs"]
        ),
        "known_decline_effects": list(policy["known_decline_effects"]),
        "postcondition": "old_pending_full_id_absent_in_paused_frame",
        "alliance_semantic_postcondition_ready": False,
    }
    return {
        "status": "ready" if not blocked else "blocked",
        "rule_id": policy["rule_id"],
        "evidence": evidence,
        "blocked_reasons": blocked,
    }


def _perk_alliance_inbound_assessment(
    context: dict[str, object],
    *,
    snapshot: dict[str, object],
    active_wars: list[dict[str, object]],
    available_steps: set[str],
    candidate_replies: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Accept only the source-pinned, cost-free R0127 alliance reply shape."""

    policy = _PERK_ALLIANCE_INBOUND_POLICY
    definition = context.get("definition")
    if not (
        isinstance(definition, dict)
        and definition.get("canonical_key") == policy["definition_key"]
    ):
        return {"status": "not_applicable", "rule_id": policy["rule_id"]}

    blocked: list[str] = []
    if not (
        definition.get("deterministic_key_hash")
        == policy["deterministic_key_hash"]
        and definition.get("runtime_ordinal") == policy["runtime_ordinal"]
    ):
        blocked.append("perk_alliance_definition_identity_mismatch")

    roles = context.get("roles")
    actor_id = roles.get("actor_character_id") if isinstance(roles, dict) else None
    recipient_id = (
        roles.get("recipient_character_id") if isinstance(roles, dict) else None
    )
    if not (
        isinstance(actor_id, int)
        and not isinstance(actor_id, bool)
        and actor_id > 0
        and isinstance(recipient_id, int)
        and not isinstance(recipient_id, bool)
        and recipient_id > 0
        and actor_id != recipient_id
        and isinstance(roles, dict)
        and roles.get("secondary_actor_character_id") == -1
        and roles.get("secondary_recipient_character_id") == -1
        and roles.get("intermediary_character_id") == -1
    ):
        blocked.append("perk_alliance_direct_roles_mismatch")

    routing = context.get("routing")
    if not (
        isinstance(routing, dict)
        and routing.get("kind") == 0
        and routing.get("played_character_id") == recipient_id
        and routing.get("current_responder_role") == "recipient"
        and routing.get("reply_execution_channel") == "recipient"
        and routing.get("local_route") is True
        and routing.get("auto_accept_notification") is False
    ):
        blocked.append("perk_alliance_direct_local_route_mismatch")

    deadline = context.get("deadline")
    age = deadline.get("age_days") if isinstance(deadline, dict) else None
    remaining = (
        deadline.get("remaining_days") if isinstance(deadline, dict) else None
    )
    if not (
        isinstance(age, int)
        and not isinstance(age, bool)
        and 0 <= age < 60
        and isinstance(remaining, int)
        and not isinstance(remaining, bool)
        and remaining == 60 - age
        and deadline.get("expiration_days") == 60
        and deadline.get("expiry_boundary_status") == "not_reached"
    ):
        blocked.append("perk_alliance_unexpired_deadline_mismatch")

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    if not (
        isinstance(terms, dict)
        and terms.get("special_data_present") is False
        and isinstance(special, dict)
        and special.get("status") == "unavailable"
        and special.get("value") is None
        and special.get("reason") == "special_war_binding_not_applicable"
    ):
        blocked.append("perk_alliance_non_special_shape_mismatch")

    send_options = context.get("send_options")
    rows = send_options.get("rows") if isinstance(send_options, dict) else None
    option_count = policy["required_send_option_count"]
    if not (
        isinstance(send_options, dict)
        and send_options.get("exclusive") is False
        and send_options.get("definition_count") == option_count
        and send_options.get("context_count") == option_count
        and isinstance(rows, list)
        and len(rows) == option_count
        and all(
            isinstance(row, dict)
            and row.get("native_index") == index
            and row.get("selected") is False
            for index, row in enumerate(rows)
        )
    ):
        blocked.append("perk_alliance_zero_option_vector_mismatch")

    observed_wars = snapshot.get("active_wars")
    if not isinstance(observed_wars, list) or not all(
        isinstance(war, dict) for war in observed_wars
    ):
        blocked.append("perk_alliance_active_war_observation_unavailable")
    elif active_wars:
        blocked.append("perk_alliance_no_active_war_required")
    accept = candidate_replies.get("accept")
    if not isinstance(accept, dict) or accept.get("native_legal") is not True:
        blocked.append("perk_alliance_accept_not_native_legal")
    elif accept.get("action_reachable") is not True:
        blocked.append("perk_alliance_accept_command_unavailable")

    return {
        "status": "ready" if not blocked else "blocked",
        "rule_id": policy["rule_id"],
        "evidence": {
            "source": policy["source"],
            "source_sha256": policy["source_sha256"],
            "actor_character_id": actor_id,
            "recipient_character_id": recipient_id,
            "selected_option_count": (
                sum(
                    1 for row in rows
                    if isinstance(row, dict) and row.get("selected") is True
                )
                if isinstance(rows, list)
                else None
            ),
            "active_war_count": len(active_wars),
            "known_selected_option_costs": list(
                policy["known_selected_option_costs"]
            ),
            "known_decline_effects": list(policy["known_decline_effects"]),
            "postcondition": "old_pending_full_id_absent_in_paused_frame",
            "alliance_semantic_postcondition_ready": False,
        },
        "blocked_reasons": blocked,
    }


def _call_ally_busy_reject_assessment(
    context: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    available_steps: set[str],
    candidate_replies: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Reject only the frozen busy-player inbound call-to-war shape."""

    policy = _CALL_ALLY_BUSY_REJECT_POLICY
    definition = context.get("definition")
    definition_key = (
        definition.get("canonical_key")
        if isinstance(definition, dict)
        else None
    )
    if definition_key != policy["definition_key"]:
        return {"status": "not_applicable", "rule_id": policy["rule_id"]}

    blocked: list[str] = []
    build = context.get("build")
    provenance = context.get("provenance")
    if build != {
        "version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
        "exe_sha256": (
            PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        ),
    } or not (
        isinstance(provenance, dict)
        and provenance.get("backend_id")
        == PENDING_CHARACTER_INTERACTION_CONTEXT_V1_BACKEND_ID
    ):
        blocked.append("call_ally_frozen_exact_build_mismatch")
    if not (
        isinstance(definition, dict)
        and definition.get("deterministic_key_hash")
        == policy["deterministic_key_hash"]
    ):
        blocked.append("call_ally_definition_identity_mismatch")
    pending_id = context.get("pending_interaction_id")
    if not _valid_pending_interaction_id(pending_id):
        blocked.append("call_ally_full_pending_identity_unavailable")

    roles = context.get("roles")
    actor_id = (
        roles.get("actor_character_id") if isinstance(roles, dict) else None
    )
    recipient_id = (
        roles.get("recipient_character_id")
        if isinstance(roles, dict)
        else None
    )
    if not (
        isinstance(actor_id, int)
        and not isinstance(actor_id, bool)
        and actor_id > 0
        and isinstance(recipient_id, int)
        and not isinstance(recipient_id, bool)
        and recipient_id > 0
        and actor_id != recipient_id
        and isinstance(roles, dict)
        and roles.get("secondary_actor_character_id") == -1
        and roles.get("secondary_recipient_character_id") == -1
        and roles.get("intermediary_character_id") == -1
    ):
        blocked.append("call_ally_direct_roles_mismatch")

    routing = context.get("routing")
    if not (
        isinstance(routing, dict)
        and routing.get("kind") == 0
        and routing.get("played_character_id") == recipient_id
        and routing.get("current_responder_role") == "recipient"
        and routing.get("reply_execution_channel") == "recipient"
        and routing.get("local_route") is True
        and routing.get("auto_accept_notification") is False
    ):
        blocked.append("call_ally_direct_local_route_mismatch")

    target = context.get("target")
    if not (
        isinstance(target, dict)
        and target.get("present") is True
        and target.get("type_key_status") == "available"
        and target.get("type_key") == "war"
        and target.get("type_key_reason") is None
    ):
        blocked.append("call_ally_stable_war_target_type_mismatch")

    send_options = context.get("send_options")
    if not (
        isinstance(send_options, dict)
        and send_options.get("exclusive") is True
        and send_options.get("definition_count") == 0
        and send_options.get("context_count") == 0
        and send_options.get("rows") == []
    ):
        blocked.append("call_ally_zero_option_vector_mismatch")

    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    if not (
        isinstance(terms, dict)
        and terms.get("special_data_present") is False
        and isinstance(special, dict)
        and special.get("status") == "unavailable"
        and special.get("value") is None
        and special.get("reason") == "special_war_binding_not_applicable"
    ):
        blocked.append("call_ally_non_special_shape_mismatch")

    deadline = context.get("deadline")
    age_days = deadline.get("age_days") if isinstance(deadline, dict) else None
    expiration_days = (
        deadline.get("expiration_days") if isinstance(deadline, dict) else None
    )
    remaining_days = (
        deadline.get("remaining_days") if isinstance(deadline, dict) else None
    )
    if not (
        isinstance(age_days, int)
        and not isinstance(age_days, bool)
        and isinstance(expiration_days, int)
        and not isinstance(expiration_days, bool)
        and isinstance(remaining_days, int)
        and not isinstance(remaining_days, bool)
        and 0 <= age_days < expiration_days
        and remaining_days == expiration_days - age_days
        and remaining_days > 0
        and isinstance(deadline, dict)
        and deadline.get("expiry_boundary_status") == "not_reached"
    ):
        blocked.append("call_ally_unexpired_deadline_required")

    active_war_signature = war_termination_active_war_signature(active_wars)
    if not active_war_signature:
        blocked.append("call_ally_existing_active_war_required")
    if any(
        isinstance(war.get("player_relative_war_score"), int)
        and not isinstance(war.get("player_relative_war_score"), bool)
        and int(war["player_relative_war_score"]) >= 100
        for war in active_wars
        if isinstance(war, dict)
    ):
        blocked.append("call_ally_enforce_demands_priority_not_cleared")

    reject = candidate_replies.get("reject")
    if not isinstance(reject, dict) or reject.get("native_legal") is not True:
        blocked.append("call_ally_reject_not_native_legal")
    elif reject.get("action_reachable") is not True:
        blocked.append("call_ally_reject_command_unavailable")

    evidence = {
        "source": policy["source"],
        "source_sha256": policy["source_sha256"],
        "build": dict(build) if isinstance(build, dict) else None,
        "backend_id": (
            provenance.get("backend_id")
            if isinstance(provenance, dict)
            else None
        ),
        "definition_key": definition_key,
        "deterministic_key_hash": (
            definition.get("deterministic_key_hash")
            if isinstance(definition, dict)
            else None
        ),
        "runtime_ordinal_consumed_as_identity": False,
        "pending_interaction_id": pending_id,
        "actor_character_id": actor_id,
        "recipient_character_id": recipient_id,
        "target_type_key": (
            target.get("type_key") if isinstance(target, dict) else None
        ),
        "target_raw_token_consumed": False,
        "target_typed_identity_consumed": False,
        "target_war_id_resolved": False,
        "selected_option_count": (
            sum(
                1
                for row in send_options.get("rows", [])
                if isinstance(row, dict) and row.get("selected") is True
            )
            if isinstance(send_options, dict)
            and isinstance(send_options.get("rows"), list)
            else None
        ),
        "deadline_remaining_days": remaining_days,
        "active_war_signature_before_reply": (
            active_war_signature if active_war_signature is not None else None
        ),
        "active_war_ids_before_reply": (
            [row["war_id"] for row in active_war_signature]
            if active_war_signature is not None
            else None
        ),
        "enforce_demands_priority_cleared": not any(
            reason == "call_ally_enforce_demands_priority_not_cleared"
            for reason in blocked
        ),
        "known_decline_effects": list(policy["known_decline_effects"]),
        "postcondition": (
            "old_pending_full_id_absent_and_no_new_active_war_id_in_"
            "next_paused_frame"
        ),
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "interaction_semantic_decision_ready": False,
    }
    return {
        "status": "ready" if not blocked else "blocked",
        "rule_id": policy["rule_id"],
        "evidence": evidence,
        "blocked_reasons": blocked,
    }


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


def _raiktor_inbound_white_peace_assessment(
    context: dict[str, object],
    *,
    snapshot: dict[str, object],
    active_wars: list[dict[str, object]],
    available_steps: set[str],
    candidate_replies: dict[str, dict[str, object]],
    special_binding_audit: dict[str, object] | None,
) -> dict[str, object]:
    """Evaluate one exact inbound event-CB white-peace blocker.

    This is deliberately not a generic special-terms decoder.  It joins the
    existing pending binding to the existing same-frame termination query and
    admits only the frozen Raiktor CB whose authored white-peace branch is
    claim-like and distinct from its special victory rewards.
    """

    policy = _RAIKTOR_INBOUND_WHITE_PEACE_POLICY
    definition = context.get("definition")
    definition_key = (
        definition.get("canonical_key")
        if isinstance(definition, dict)
        else None
    )
    terms = context.get("terms")
    special = terms.get("special_war_binding") if isinstance(terms, dict) else None
    binding = special.get("value") if isinstance(special, dict) else None
    if not (
        definition_key == policy["definition_key"]
        and isinstance(binding, dict)
        and binding.get("special_interaction_kind")
        == policy["special_interaction_kind"]
        and binding.get("absolute_outcome") == policy["absolute_outcome"]
        and binding.get("actor_war_role") == "primary_defender"
        and binding.get("recipient_war_role") == "primary_attacker"
        and binding.get("binding_source") == "native_common_war_relation"
    ):
        return {"status": "not_applicable", "rule_id": policy["rule_id"]}

    blocked: list[str] = []
    war_id = binding.get("war_id")
    if (
        isinstance(war_id, bool)
        or not isinstance(war_id, int)
        or war_id <= 0
    ):
        blocked.append("raiktor_white_peace_war_id_unavailable")
    if not (
        isinstance(special_binding_audit, dict)
        and special_binding_audit.get("active_war_id_match") is True
        and special_binding_audit.get("active_war_roles_match") is True
    ):
        blocked.append("special_war_snapshot_binding_mismatch")

    roles = context.get("roles")
    if not (
        isinstance(roles, dict)
        and roles.get("secondary_actor_character_id") == -1
        and roles.get("secondary_recipient_character_id") == -1
        and roles.get("intermediary_character_id") == -1
    ):
        blocked.append("raiktor_white_peace_hostage_or_intermediary_present")

    matching_wars = [
        war
        for war in active_wars
        if isinstance(war_id, int)
        and not isinstance(war_id, bool)
        and war.get("war_id") == war_id
    ]
    war = matching_wars[0] if len(matching_wars) == 1 else None
    score = war.get("player_relative_war_score") if isinstance(war, dict) else None
    if not (
        isinstance(war, dict)
        and war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and isinstance(score, int)
        and not isinstance(score, bool)
        and 0 <= score < 100
    ):
        blocked.append("raiktor_white_peace_active_war_shape_mismatch")
    if blocked:
        return {
            "status": "blocked",
            "rule_id": policy["rule_id"],
            "war_id": war_id,
            "blocked_reasons": blocked,
        }

    raw_options = snapshot.get("war_termination_options")
    same_frame_rows = [
        row
        for row in (raw_options if isinstance(raw_options, list) else [])
        if isinstance(row, dict)
        and row.get("war_id") == war_id
        and _same_frame_termination_row(snapshot, row, int(war_id))
    ]
    query_step = query_war_termination_options_step(int(war_id))
    if len(same_frame_rows) != 1:
        return {
            "status": "query_required",
            "rule_id": policy["rule_id"],
            "war_id": war_id,
            "query_step": query_step,
            "query_reachable": query_step in available_steps,
            "blocked_reasons": (
                []
                if query_step in available_steps
                else ["raiktor_white_peace_termination_query_unavailable"]
            ),
        }

    options = same_frame_rows[0]
    casus_belli = options.get("active_casus_belli_identity")
    option_rows = options.get("options")
    white_peace = (
        option_rows.get("white_peace")
        if isinstance(option_rows, dict)
        else None
    )
    duration = options.get("war_duration_days")
    option_score = options.get("player_relative_war_score")
    if not (
        options.get("source") == "native"
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and option_score == score
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration >= 365
        and options.get("active_casus_belli_present") is True
        and isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key") == policy["casus_belli_key"]
        and options.get("cb_allows_white_peace") is True
        and isinstance(white_peace, dict)
        and white_peace.get("outcome") == "white_peace"
        and white_peace.get("hostage_variant") == "none"
    ):
        blocked.append("raiktor_white_peace_termination_terms_mismatch")

    accept = candidate_replies.get("accept")
    if not isinstance(accept, dict) or accept.get("native_legal") is not True:
        blocked.append("raiktor_white_peace_accept_not_native_legal")
    elif accept.get("action_reachable") is not True:
        blocked.append("raiktor_white_peace_accept_command_unavailable")

    evidence = {
        "source": policy["source"],
        "source_sha256": policy["source_sha256"],
        "war_id": war_id,
        "casus_belli_key": (
            casus_belli.get("canonical_key")
            if isinstance(casus_belli, dict)
            else None
        ),
        "player_side": options.get("player_side"),
        "player_is_primary_war_leader": options.get(
            "player_is_primary_war_leader"
        ),
        "player_relative_war_score": option_score,
        "war_duration_days": duration,
        "cb_allows_white_peace": options.get("cb_allows_white_peace"),
        "outbound_white_peace_available": (
            white_peace.get("available")
            if isinstance(white_peace, dict)
            else None
        ),
        "outbound_white_peace_validator_passed": (
            white_peace.get("native_validator_passed")
            if isinstance(white_peace, dict)
            else None
        ),
        "postcondition": "old_pending_full_id_and_bound_war_id_absent",
    }
    return {
        "status": "ready" if not blocked else "blocked",
        "rule_id": policy["rule_id"],
        "war_id": war_id,
        "evidence": evidence,
        "blocked_reasons": blocked,
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
    grant_vassal_evidence = (
        _GRANT_VASSAL_REJECT_ONLY_POLICY
        if definition_key == _GRANT_VASSAL_REJECT_ONLY_POLICY["definition_key"]
        else None
    )
    grant_vassal_contract_gaps = (
        _grant_vassal_reject_contract_gaps(
            context, snapshot=snapshot, active_wars=active_wars
        )
        if isinstance(grant_vassal_evidence, dict)
        else []
    )
    negotiate_alliance_evidence = (
        _NEGOTIATE_ALLIANCE_INBOUND_POLICY
        if definition_key
        == _NEGOTIATE_ALLIANCE_INBOUND_POLICY["definition_key"]
        else None
    )
    perk_alliance_evidence = (
        _PERK_ALLIANCE_INBOUND_POLICY
        if definition_key == _PERK_ALLIANCE_INBOUND_POLICY["definition_key"]
        else None
    )
    call_ally_evidence = (
        _CALL_ALLY_BUSY_REJECT_POLICY
        if definition_key == _CALL_ALLY_BUSY_REJECT_POLICY["definition_key"]
        else None
    )
    if evidence_gaps:
        classification = "evidence_invalid"
    elif special_status == "available":
        classification = "known_war_exit"
    elif isinstance(marriage_allowlist_evidence, dict):
        classification = "known_marriage_special"
    elif isinstance(grant_vassal_evidence, dict):
        classification = "known_grant_vassal_reject_only"
    elif (
        isinstance(negotiate_alliance_evidence, dict)
        and special_status == "unavailable"
        and special_reason == "special_war_binding_not_applicable"
        and special_present is False
    ):
        classification = "known_negotiate_alliance_inbound"
    elif isinstance(perk_alliance_evidence, dict):
        classification = "known_perk_alliance_inbound"
    elif isinstance(call_ally_evidence, dict):
        classification = "known_call_ally_busy_reject"
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
    raiktor_white_peace = (
        _raiktor_inbound_white_peace_assessment(
            context,
            snapshot=snapshot,
            active_wars=active_wars,
            available_steps=available_steps,
            candidate_replies=by_action,
            special_binding_audit=special_binding_audit,
        )
        if classification == "known_war_exit"
        else None
    )
    negotiate_alliance = (
        _negotiate_alliance_inbound_assessment(
            context,
            active_wars=active_wars,
            available_steps=available_steps,
            candidate_replies=by_action,
        )
        if classification == "known_negotiate_alliance_inbound"
        else None
    )
    perk_alliance = (
        _perk_alliance_inbound_assessment(
            context,
            snapshot=snapshot,
            active_wars=active_wars,
            available_steps=available_steps,
            candidate_replies=by_action,
        )
        if classification == "known_perk_alliance_inbound"
        else None
    )
    call_ally_busy_reject = (
        _call_ally_busy_reject_assessment(
            context,
            active_wars=active_wars,
            available_steps=available_steps,
            candidate_replies=by_action,
        )
        if classification == "known_call_ally_busy_reject"
        else None
    )
    classification_evidence = (
        dict(_RAIKTOR_INBOUND_WHITE_PEACE_POLICY)
        if isinstance(raiktor_white_peace, dict)
        and raiktor_white_peace.get("status") != "not_applicable"
        else (
            call_ally_evidence
            if classification == "known_call_ally_busy_reject"
            else (
                negotiate_alliance_evidence
                if classification == "known_negotiate_alliance_inbound"
                else (
                    perk_alliance_evidence
                    if classification == "known_perk_alliance_inbound"
                    else (
                        marriage_allowlist_evidence
                        if classification == "known_marriage_special"
                        else (
                            grant_vassal_evidence
                            if classification == "known_grant_vassal_reject_only"
                            else definition_allowlist_evidence
                        )
                    )
                )
            )
        )
    )
    decision: dict[str, object] = {
        "rule_id": (
            "arrange-marriage-reject-only-v1"
            if classification == "known_marriage_special"
            else (
                _GRANT_VASSAL_REJECT_ONLY_POLICY["rule_id"]
                if classification == "known_grant_vassal_reject_only"
                else "ordinary-reject-unique-accept-v1"
            )
        ),
        "mode": "degraded_blocker_removal",
        "native_ai_reference": (
            "CK3-1.19.0.6 inbound reply tree: intermediary then recipient "
            "ai_accept; human responder uses exact native reply legality"
        ),
        "native_ai_equivalent": False,
        "semantic_optimal": False,
        "semantic_decision_ready": False,
        "interaction_semantic_decision_ready": False,
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
        "raiktor_inbound_white_peace": raiktor_white_peace,
        "negotiate_alliance_inbound": negotiate_alliance,
        "perk_alliance_inbound": perk_alliance,
        "call_ally_busy_reject": call_ally_busy_reject,
        "definition_classification": {
            "policy": (
                "ck3-1.19.0.6-exact-raiktor-inbound-white-peace-v1"
                if isinstance(raiktor_white_peace, dict)
                and raiktor_white_peace.get("status") != "not_applicable"
                else (
                    "ck3-1.19.0.6-exact-call-ally-busy-reject-v1"
                    if classification == "known_call_ally_busy_reject"
                    else (
                        "ck3-1.19.0.6-exact-negotiate-alliance-inbound-v1"
                        if classification
                        == "known_negotiate_alliance_inbound"
                        else (
                            "ck3-1.19.0.6-exact-grant-vassal-reject-only-v1"
                            if classification == "known_grant_vassal_reject_only"
                            else (
                                "ck3-1.19.0.6-explicit-marriage-special-reject-"
                                "only-v1"
                                if classification == "known_marriage_special"
                                else (
                                    "ck3-1.19.0.6-explicit-ordinary-"
                                    "nonreligious-v1"
                                )
                            )
                        )
                    )
                )
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
        "grant_vassal_contract_gaps": grant_vassal_contract_gaps,
        "missing_semantics": summary.get("missing_semantics"),
        "evidence_gaps": evidence_gaps,
        "candidate_replies": candidates,
        "recommended_action": None,
        "selected_action": None,
        "selected_step": None,
        "blocked_reasons": [],
        "deterministic_rule": (
            (
                "for only the exact source-pinned, direct, zero-option "
                "grant_vassal_interaction in the frozen standard-feudal "
                "preview scope, reject when native reject is legal and "
                "executable; never accept or block as fallback"
            )
            if classification == "known_grant_vassal_reject_only"
            else (
                (
                    "for an exact same-frame arrange_marriage_interaction with a "
                    "direct local recipient, complete marriage roles, an internally "
                    "consistent unexpired stock deadline, opaque marriage special "
                    "payload, and six unselected send options, reject only when "
                    "native reject is legal and executable; never fall through to "
                    "unique accept"
                )
                if classification == "known_marriage_special"
                else (
                    "for the exact frozen call_ally_interaction shape, reject only "
                    "while the player already has a completely observed active-war "
                    "signature, the target is stably typed as war without decoding "
                    "its raw token, no enforce-demands action is pending, and native "
                    "reject is legal and executable"
                    if classification == "known_call_ally_busy_reject"
                    else (
                        "for an exact same-frame request whose definition is "
                        "explicitly allowlisted as ordinary non-war and "
                        "nonreligious, reject when native reject is legal and "
                        "executable; accept only when reject, block, and "
                        "acknowledge are each natively illegal and accept is the "
                        "sole legal executable reply; otherwise submit nothing"
                    )
                )
            )
        ),
    }
    blocked_reasons = decision["blocked_reasons"]
    assert isinstance(blocked_reasons, list)

    if classification == "evidence_invalid":
        blocked_reasons.extend(evidence_gaps)
        return {"summary": summary, "decision": decision}
    if classification == "known_war_exit":
        if (
            isinstance(raiktor_white_peace, dict)
            and raiktor_white_peace.get("status") != "not_applicable"
        ):
            decision["rule_id"] = raiktor_white_peace["rule_id"]
            decision["deterministic_rule"] = (
                "for only the exact no-hostage inbound Raiktor white-peace "
                "binding, join the active WarID to a same-frame native "
                "termination row before any reply, keep overall semantic "
                "readiness false, and require the bound WarID to disappear "
                "after an accepted reply"
            )
        if (
            isinstance(raiktor_white_peace, dict)
            and raiktor_white_peace.get("status") == "query_required"
        ):
            decision["recommended_action"] = "observe_war_termination"
            query_step = raiktor_white_peace.get("query_step")
            if (
                raiktor_white_peace.get("query_reachable") is True
                and isinstance(query_step, str)
            ):
                decision["selected_action"] = "observe_war_termination"
                decision["selected_step"] = query_step
            else:
                decision["required_step"] = query_step
                blocked_reasons.extend(
                    raiktor_white_peace.get("blocked_reasons", [])
                )
            decision["deterministic_rule"] = (
                "for the exact inbound Raiktor white-peace binding, first "
                "join the bound WarID to a same-frame native termination "
                "row; a stale or missing row may only select its read-only "
                "query"
            )
            return {"summary": summary, "decision": decision}
        if (
            isinstance(raiktor_white_peace, dict)
            and raiktor_white_peace.get("status") == "ready"
        ):
            decision["recommended_action"] = "accept"
            decision["selected_action"] = "accept"
            decision["selected_step"] = _ACCEPT_PENDING_CHARACTER_INTERACTION_STEP
            decision["deterministic_rule"] = (
                "accept only an exact same-frame, no-hostage Raiktor "
                "white-peace request sent by the primary defender to the "
                "player primary attacker after at least 365 days while "
                "the player score is 0..99 and native accept is legal; "
                "then require both the old pending ID and bound WarID to "
                "disappear"
            )
            return {"summary": summary, "decision": decision}
        if isinstance(raiktor_white_peace, dict):
            blocked_reasons.extend(
                raiktor_white_peace.get("blocked_reasons", [])
            )
        if not blocked_reasons:
            if not (
                isinstance(special_binding_audit, dict)
                and special_binding_audit.get("active_war_id_match") is True
                and special_binding_audit.get("active_war_roles_match") is True
            ):
                blocked_reasons.append("special_war_snapshot_binding_mismatch")
        if not blocked_reasons:
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
    if classification == "known_grant_vassal_reject_only":
        if grant_vassal_contract_gaps:
            blocked_reasons.extend(grant_vassal_contract_gaps)
            return {"summary": summary, "decision": decision}
        reject = by_action["reject"]
        if reject["native_legal"] is not True:
            blocked_reasons.append("grant_vassal_reject_not_native_legal")
            return {"summary": summary, "decision": decision}
        decision["recommended_action"] = "reject"
        if reject["action_reachable"] is True:
            decision["selected_action"] = "reject"
            decision["selected_step"] = reject["step"]
        else:
            blocked_reasons.append("grant_vassal_reject_command_unavailable")
        return {"summary": summary, "decision": decision}
    if classification == "known_negotiate_alliance_inbound":
        decision["rule_id"] = _NEGOTIATE_ALLIANCE_INBOUND_POLICY["rule_id"]
        decision["deterministic_rule"] = (
            "accept only the exact same-day, direct, zero-option inbound "
            "negotiate_alliance_interaction while the player leads an active "
            "defensive war and the actor is not an active-war opponent; keep "
            "semantic alliance outcome readiness false and require the old "
            "signed pending ID to disappear in a paused frame"
        )
        if not (
            isinstance(negotiate_alliance, dict)
            and negotiate_alliance.get("status") == "ready"
        ):
            if isinstance(negotiate_alliance, dict):
                blocked_reasons.extend(
                    negotiate_alliance.get("blocked_reasons", [])
                )
            else:
                blocked_reasons.append(
                    "negotiate_alliance_assessment_unavailable"
                )
            return {"summary": summary, "decision": decision}
        decision["recommended_action"] = "accept"
        decision["selected_action"] = "accept"
        decision["selected_step"] = _ACCEPT_PENDING_CHARACTER_INTERACTION_STEP
        return {"summary": summary, "decision": decision}
    if classification == "known_perk_alliance_inbound":
        decision["rule_id"] = _PERK_ALLIANCE_INBOUND_POLICY["rule_id"]
        classification_row = decision["definition_classification"]
        assert isinstance(classification_row, dict)
        classification_row["policy"] = (
            "ck3-1.19.0.6-exact-perk-alliance-inbound-v1"
        )
        decision["deterministic_rule"] = (
            "accept only the exact source-pinned perk_alliance_interaction "
            "with direct local player recipient, unexpired stock deadline, "
            "two unselected send options, no special payload or current "
            "active war, and same-frame native accept legality; then require "
            "the old signed pending ID to disappear in a paused frame"
        )
        if not (
            isinstance(perk_alliance, dict)
            and perk_alliance.get("status") == "ready"
        ):
            if isinstance(perk_alliance, dict):
                blocked_reasons.extend(perk_alliance.get("blocked_reasons", []))
            else:
                blocked_reasons.append("perk_alliance_assessment_unavailable")
            return {"summary": summary, "decision": decision}
        decision["recommended_action"] = "accept"
        decision["selected_action"] = "accept"
        decision["selected_step"] = _ACCEPT_PENDING_CHARACTER_INTERACTION_STEP
        return {"summary": summary, "decision": decision}
    if classification == "known_call_ally_busy_reject":
        decision["rule_id"] = _CALL_ALLY_BUSY_REJECT_POLICY["rule_id"]
        decision["deterministic_rule"] = (
            "reject only the frozen exact-build, direct, zero-option inbound "
            "call_ally_interaction while the player already has a complete "
            "active-war signature, no 100% enforce-demands action is pending, "
            "the unexpired same-frame target is stably typed as war without "
            "decoding its raw token, and native reject is legal and reachable; "
            "then require the old pending ID to disappear and no new active "
            "WarID to appear in the next paused snapshot"
        )
        if not (
            isinstance(call_ally_busy_reject, dict)
            and call_ally_busy_reject.get("status") == "ready"
        ):
            if isinstance(call_ally_busy_reject, dict):
                blocked_reasons.extend(
                    call_ally_busy_reject.get("blocked_reasons", [])
                )
            else:
                blocked_reasons.append("call_ally_busy_assessment_unavailable")
            return {"summary": summary, "decision": decision}
        decision["recommended_action"] = "reject"
        decision["selected_action"] = "reject"
        decision["selected_step"] = _REJECT_PENDING_CHARACTER_INTERACTION_STEP
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
    rule_id = decision.get("rule_id")
    if selected_action == "observe_war_termination":
        phase = "pending_raiktor_white_peace_termination_query"
        reason = (
            "read the bound WarID's same-frame native CB identity, duration, "
            "score, and white-peace permission before replying to the exact "
            "Raiktor request"
        )
    elif selected_action == "reject":
        if rule_id == _CALL_ALLY_BUSY_REJECT_POLICY["rule_id"]:
            phase = "pending_call_ally_busy_reject"
            reason = (
                "reject this exact inbound call to a second war while the "
                "player is still busy in at least one observed active war; "
                "the target raw token remains opaque, and the next paused "
                "frame must show no added active WarID"
            )
        elif rule_id == _GRANT_VASSAL_REJECT_ONLY_POLICY["rule_id"]:
            phase = "pending_grant_vassal_reject_only"
            reason = (
                "reject this exact inbound direct three-role vassal transfer: "
                "native reject is same-frame legal and executable, while "
                "accept would change the transferred vassal's liege"
            )
        elif decision.get("classification") == "known_marriage_special":
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
        if rule_id == _RAIKTOR_INBOUND_WHITE_PEACE_POLICY["rule_id"]:
            phase = "pending_raiktor_white_peace_accept"
            reason = (
                "accept this exact no-hostage Raiktor white peace: the "
                "same-frame native row proves the bound active CB, duration, "
                "score and permission, while the authored white-peace branch "
                "does not execute Raiktor's special victory rewards"
            )
        elif rule_id == _NEGOTIATE_ALLIANCE_INBOUND_POLICY["rule_id"]:
            phase = "pending_negotiate_alliance_accept"
            reason = (
                "accept this exact direct, zero-option alliance proposal: "
                "the player leads an active defensive war, no selected hook "
                "or influence cost exists, and stock decline has a definite "
                "opinion and clan-unity penalty"
            )
        elif rule_id == _PERK_ALLIANCE_INBOUND_POLICY["rule_id"]:
            phase = "pending_perk_alliance_accept"
            reason = (
                "accept this exact direct perk alliance proposal: the player "
                "has no active war, neither sender option is selected, native "
                "accept is legal, and stock decline has an opinion and "
                "clan-unity penalty"
            )
        else:
            phase = "pending_character_interaction_degraded_unique_accept"
            reason = (
                "accept this exact ordinary non-war request only because "
                "native legality proves reject, block, and acknowledge "
                "illegal, leaving accept as the sole executable legal reply"
            )
    else:
        phase = (
            "pending_war_interaction_evidence_required"
            if decision.get("classification") == "known_war_exit"
            else (
                "pending_call_ally_busy_reject_blocked"
                if decision.get("classification")
                == "known_call_ally_busy_reject"
                else "pending_character_interaction_degraded_blocked"
            )
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
        required_step = decision.get("required_step")
        if isinstance(required_step, str) and required_step:
            plan["required_step"] = required_step
        recommended_action = decision.get("recommended_action")
        recommended = (
            _PENDING_REPLY_STEPS.get(str(recommended_action))
            if isinstance(recommended_action, str)
            else None
        )
        if isinstance(recommended, str) and "required_step" not in plan:
            plan["required_step"] = recommended
        if decision.get("classification") == "known_war_exit":
            plan["required_capabilities"] = [
                "game.state.pending-character-interaction-special-outcome-terms",
                "game.policy.pending-character-interaction-war-outcome-decision",
            ]
        elif decision.get("classification") not in {
            "ordinary_non_war",
            "known_negotiate_alliance_inbound",
            "known_perk_alliance_inbound",
            "known_call_ally_busy_reject",
            "known_grant_vassal_reject_only",
        }:
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


def _same_frame_council_composition_candidates_v1(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
) -> dict[str, object] | None:
    """Recover only a complete Council19 observation for this paused frame."""

    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return None
    snapshot_id = snapshot.get("snapshot_id")
    public_revision = snapshot.get("revision")
    native_revision = snapshot.get("native_revision")
    date_raw = snapshot.get("date_raw")
    played_character = snapshot.get("played_character")
    owner_character_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    for row in reversed(rows):
        if (
            _effective_command(row)
            != QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP
            or row.get("ok") is not True
        ):
            continue
        result = _effective_command_result(row)
        payload = (
            result.get("council_composition_candidates")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(result, dict)
            and result.get("step")
            == QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP
            and result.get("accepted") is True
            and result.get("status") == "available"
            and result.get("queried_snapshot_id") == snapshot_id
            and result.get("queried_revision") == public_revision
            and result.get("queried_native_revision") == native_revision
            and isinstance(result.get("backend_id"), str)
            and bool(result.get("backend_id"))
        ):
            continue
        try:
            return normalize_council_composition_candidates_v1(
                payload,
                expected_snapshot_id=snapshot_id,
                expected_public_revision=public_revision,
                expected_native_revision=native_revision,
                expected_date_raw=date_raw,
                expected_owner_character_id=owner_character_id,
            )
        except ValueError:
            continue
    return None


def _plan_steward_composition_v1(
    observation: dict[str, object],
    *,
    available_capabilities: set[str],
) -> dict[str, object]:
    """Plan the narrow steward decision without inventing an assignment ACK."""

    position = observation.get("position")
    if not isinstance(position, dict):
        raise ValueError("normalized council observation lacks position")
    candidates = sorted(
        observation["candidates"],
        key=lambda row: (
            -int(row["main_skill"]["value"]),
            int(row["character_id"]),
        ),
    )
    evidence = {
        "position_key": STEWARD_POSITION_KEY,
        "incumbent_character_id": position["incumbent_character_id"],
        "incumbent_main_skill": position["incumbent_main_skill"],
        "vacant": position["vacant"],
        "candidate_count": len(candidates),
        "ordered_candidates": [dict(row) for row in candidates],
    }
    if not candidates:
        return {
            "policy": "council-composition-steward-v1",
            "outcome": "NO_CHANGE",
            "reason_code": "no_eligible_candidates",
            **evidence,
        }
    selected = candidates[0]
    if position["vacant"] is not True:
        incumbent_skill = int(position["incumbent_main_skill"]["value"])
        if int(selected["main_skill"]["value"]) <= incumbent_skill:
            return {
                "policy": "council-composition-steward-v1",
                "outcome": "NO_CHANGE",
                "reason_code": "incumbent_not_outperformed",
                "selected_candidate": dict(selected),
                **evidence,
            }
        routable = ASSIGN_COUNCILLOR_V1_CAPABILITY in available_capabilities
        return {
            "policy": "council-composition-steward-v1",
            "outcome": "REPLACE_REQUIRED",
            "reason_code": (
                "replacement_action_ready"
                if routable
                else "replacement_action_capability_unavailable"
            ),
            "required_capability": ASSIGN_COUNCILLOR_V1_CAPABILITY,
            "action_routable": routable,
            "selected_candidate": dict(selected),
            **evidence,
        }
    routable = ASSIGN_COUNCILLOR_V1_CAPABILITY in available_capabilities
    return {
        "policy": "council-composition-steward-v1",
        "outcome": "ASSIGN_REQUIRED",
        "reason_code": (
            "assignment_action_ready"
            if routable
            else "assignment_action_capability_unavailable"
        ),
        "required_capability": ASSIGN_COUNCILLOR_V1_CAPABILITY,
        "action_routable": routable,
        "selected_candidate": dict(selected),
        **evidence,
    }


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
    committed_route_request = parse_committed_route_sentinel_advance_step(
        step
    )
    committed_route_speed = parse_committed_route_sentinel_advance_speed(step)
    objective_hold_request = (
        parse_war_objective_hold_sentinel_advance_step(step)
    )
    objective_hold_speed = (
        parse_war_objective_hold_sentinel_advance_speed(step)
    )
    expected = (
        (committed_route_speed, "decision_epoch")
        if committed_route_request is not None
        else (objective_hold_speed, "decision_epoch")
        if objective_hold_request is not None
        else (3, "decision_epoch")
        if decision_target is not None
        or step == _BATTLE_DECISION_EPOCH_ADVANCE_STEP
        else (5, "terminal_or_sentinel")
        if step == _BATTLE_TERMINAL_CRUISE_STEP
        else None
    )
    if expected is None:
        return None
    expected_speed, expected_mode = expected
    requested_scope = (
        "stationary_objective_hold"
        if objective_hold_request is not None
        else "committed_route"
        if committed_route_request is not None
        else "active_battle"
    )
    if advance_result.get("player_decision_boundary") is not None:
        return _battle_sentinel_player_decision_validation(
            advance_result,
            expected_speed=expected_speed,
            expected_mode=expected_mode,
            requested_scope=requested_scope,
            decision_target=decision_target,
            committed_route_request=committed_route_request,
            objective_hold_request=objective_hold_request,
        )
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
    sentinel_scope = advance_result.get("sentinel_scope")
    combat_scope_valid = bool(
        (
            requested_scope == "active_battle"
            and sentinel_scope == "active_battle"
            and (combat_count or 0) > 0
        )
        or (
            requested_scope == "committed_route"
            and sentinel_scope == "committed_route"
            and combat_count == 0
            and expected_mode == "decision_epoch"
        )
        or (
            requested_scope == "stationary_objective_hold"
            and sentinel_scope == "stationary_objective_hold"
            and combat_count == 0
            and expected_mode == "decision_epoch"
        )
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
        <= (
            7
            if objective_hold_request is not None
            else _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS
        )
        and (target - start) % 24 == 0
        and (
            target == decision_target
            if decision_target is not None
            else target == objective_hold_request[3]
            if objective_hold_request is not None
            else target == committed_route_request[2]
            if committed_route_request is not None
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
        and combat_scope_valid
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
    if (
        sentinel_scope
        in {"committed_route", "stationary_objective_hold"}
        and terminal_flag is not False
    ):
        errors.append("noncombat_scope_claimed_combat_terminal")
    if objective_hold_request is not None:
        request = advance_result.get("war_objective_hold_request")
        admission = advance_result.get("war_objective_hold_admission")
        post_stop = advance_result.get("war_objective_hold_post_stop")
        expected_request = {
            "sentinel_scope": "stationary_objective_hold",
            "war_id": objective_hold_request[0],
            "subject_army_id": objective_hold_request[1],
            "objective_province_id": objective_hold_request[2],
            "target_date_raw": objective_hold_request[3],
        }
        if request != expected_request:
            errors.append("objective_hold_request_binding_failed")
        if not (
            isinstance(admission, dict)
            and admission.get("status") == "matched"
            and admission.get("sentinel_scope")
            == "stationary_objective_hold"
            and admission.get("war_id") == objective_hold_request[0]
            and admission.get("subject_army_id")
            == objective_hold_request[1]
            and admission.get("objective_province_id")
            == objective_hold_request[2]
            and admission.get("watch_army_ids") == watch
        ):
            errors.append("objective_hold_admission_binding_failed")
        if not (
            isinstance(post_stop, dict)
            and post_stop.get("status") in {"matched", "invalidated"}
            and post_stop.get("sentinel_scope")
            == "stationary_objective_hold"
            and post_stop.get("war_id") == objective_hold_request[0]
            and post_stop.get("subject_army_id")
            == objective_hold_request[1]
            and post_stop.get("objective_province_id")
            == objective_hold_request[2]
            and post_stop.get("watch_army_ids") == watch
            and post_stop.get("exact_war_terminal_watch") is False
            and post_stop.get("exact_active_war_set_watch") is False
        ):
            errors.append("objective_hold_post_stop_binding_failed")
        if not (
            advance_result.get("exact_war_terminal_watch") is False
            and advance_result.get("exact_active_war_set_watch") is False
            and advance_result.get(
                "maximum_omitted_state_detection_lag_days"
            )
            == 7
        ):
            errors.append("objective_hold_watch_boundary_misreported")
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
        and sentinel_scope == requested_scope
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
        "sentinel_scope": sentinel_scope,
        "watch_army_ids": list(watch) if isinstance(watch, list) else None,
    }


def _active_war_set_boundary_matches_result(
    boundary: object,
    advance_result: dict[str, object],
) -> bool:
    if not isinstance(boundary, dict):
        return False

    normalized: dict[str, tuple[int, ...]] = {}
    for key in (
        "before_war_ids",
        "after_war_ids",
        "added_war_ids",
        "removed_war_ids",
    ):
        value = boundary.get(key)
        if not isinstance(value, list):
            return False
        ids: list[int] = []
        for item in value:
            war_id = _native_int(item)
            if war_id is None or not 0 < war_id <= 2**31 - 1 or war_id in ids:
                return False
            ids.append(war_id)
        if ids != sorted(ids):
            return False
        normalized[key] = tuple(ids)

    before = normalized["before_war_ids"]
    after = normalized["after_war_ids"]
    before_set = set(before)
    after_set = set(after)
    before_text = ",".join(str(war_id) for war_id in before) or "-"
    after_text = ",".join(str(war_id) for war_id in after) or "-"
    if not (
        before != after
        and normalized["added_war_ids"]
        == tuple(sorted(after_set - before_set))
        and normalized["removed_war_ids"]
        == tuple(sorted(before_set - after_set))
        and (
            normalized["added_war_ids"]
            or normalized["removed_war_ids"]
        )
        and boundary.get("instance_id")
        == f"active-wars:{before_text}->{after_text}"
    ):
        return False

    summary_ids: list[tuple[int, ...]] = []
    for key in ("war_progress_before", "war_progress_after"):
        summary = advance_result.get(key)
        wars = summary.get("wars") if isinstance(summary, dict) else None
        if not isinstance(wars, list):
            return False
        ids: list[int] = []
        for war in wars:
            war_id = (
                _native_int(war.get("war_id"))
                if isinstance(war, dict)
                else None
            )
            if war_id is None or not 0 < war_id <= 2**31 - 1 or war_id in ids:
                return False
            ids.append(war_id)
        summary_ids.append(tuple(sorted(ids)))
    return summary_ids == [before, after]


def _battle_sentinel_player_decision_validation(
    advance_result: dict[str, object],
    *,
    expected_speed: int | None,
    expected_mode: str,
    requested_scope: str,
    decision_target: int | None,
    committed_route_request: tuple[int, int, int] | None,
    objective_hold_request: tuple[int, int, int, int] | None,
) -> dict[str, object]:
    """Validate a player-decision or paused-frame replan boundary."""

    step = advance_result.get("step")
    boundary = advance_result.get("player_decision_boundary")
    cancel = advance_result.get("player_decision_boundary_cancel")
    sentinel = advance_result.get("tactical_daily_sentinel")
    armed = advance_result.get("armed_tactical_daily_sentinel")
    start = _native_int(advance_result.get("starting_date_raw"))
    target = _native_int(advance_result.get("target_date_raw"))
    end = _native_int(advance_result.get("ending_date_raw"))
    elapsed = _native_int(advance_result.get("elapsed_days"))
    watch = advance_result.get("watch_army_ids")
    ticks = (
        _native_int(sentinel.get("completed_daily_ticks"))
        if isinstance(sentinel, dict)
        else None
    )
    maximum_horizon_days = (
        7
        if objective_hold_request is not None
        else _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS
    )
    expected_target = (
        decision_target
        if decision_target is not None
        else objective_hold_request[3]
        if objective_hold_request is not None
        else committed_route_request[2]
        if committed_route_request is not None
        else (
            start + _BATTLE_SENTINEL_ABSOLUTE_FALLBACK_DAYS * 24
            if start is not None
            else None
        )
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
        and target == expected_target
        and 1 <= (target - start) // 24 <= maximum_horizon_days
        and (target - start) % 24 == 0
        and start + elapsed * 24 == end
        and 0 <= elapsed
        and end <= target
        and 0 <= ticks <= elapsed
    ):
        errors.append("decision_boundary_date_reconciliation_failed")

    kind = boundary.get("kind") if isinstance(boundary, dict) else None
    active_event = advance_result.get("active_event")
    pending = advance_result.get("pending_character_interaction")
    common_boundary_identity_matches = bool(
        isinstance(boundary, dict)
        and boundary.get("observed_date_raw") == end
        and boundary.get("snapshot_id") == advance_result.get("snapshot_id")
        and boundary.get("revision") == advance_result.get("revision")
        and boundary.get("native_revision")
        == advance_result.get("native_revision")
        and boundary.get("bridge_pid") == advance_result.get("bridge_pid")
        and boundary.get("connection_generation")
        == advance_result.get("connection_generation")
        and boundary.get("episode_character_id")
        == advance_result.get("episode_character_id")
        and boundary.get("episode_run_id")
        == advance_result.get("episode_run_id")
        and boundary.get("played_character_id")
        == advance_result.get("played_character_id")
    )
    decision_identity_matches = bool(
        common_boundary_identity_matches
        and (
            (
                kind == "active_event"
                and boundary.get("instance_id") is not None
                and isinstance(active_event, dict)
                and active_event.get("instance_id")
                == boundary.get("instance_id")
            )
            or (
                kind == "pending_character_interaction"
                and boundary.get("instance_id") is not None
                and isinstance(pending, dict)
                and pending.get("instance_id")
                == boundary.get("instance_id")
            )
            or (
                kind == "one_life_terminal"
                and advance_result.get("one_life_terminal") is True
                and isinstance(
                    advance_result.get("one_life_terminal_reason"), str
                )
                and boundary.get("terminal_reason")
                == advance_result.get("one_life_terminal_reason")
                and boundary.get("played_character_alive")
                == advance_result.get("played_character_alive")
                and (
                    advance_result.get("played_character_alive") is False
                    or advance_result.get("played_character_id")
                    != advance_result.get("episode_character_id")
                )
            )
            or (
                kind == "active_war_set_changed"
                and _active_war_set_boundary_matches_result(
                    boundary, advance_result
                )
                and active_event is None
                and pending is None
            )
        )
    )
    if not decision_identity_matches:
        errors.append("player_decision_boundary_identity_invalid")

    combat_count = (
        _native_int(sentinel.get("combat_count"))
        if isinstance(sentinel, dict)
        else None
    )
    combat_scope_valid = bool(
        (requested_scope == "active_battle" and (combat_count or 0) > 0)
        or (
            requested_scope
            in {"committed_route", "stationary_objective_hold"}
            and combat_count == 0
        )
    )
    triggered_native_stop_valid = False
    if isinstance(sentinel, dict) and sentinel.get("state") == "triggered":
        # Reuse the complete native-stop contract; only decision precedence
        # intentionally changes the public stop kind.
        ordinary_result = dict(advance_result)
        ordinary_result["player_decision_boundary"] = None
        ordinary_result["stop_kind"] = (
            "terminal"
            if sentinel.get("terminal_observed") is True
            else "decision_epoch"
        )
        ordinary_validation = _battle_sentinel_advance_validation(
            ordinary_result
        )
        triggered_native_stop_valid = bool(
            isinstance(ordinary_validation, dict)
            and ordinary_validation.get("valid") is True
            and cancel is None
        )

    canceled_armed_status_valid = bool(
        isinstance(sentinel, dict)
        and sentinel.get("state") == "idle"
        and sentinel.get("abnormal") is False
        and isinstance(armed, dict)
        and armed.get("state") == "armed"
        and sentinel.get("generation") == armed.get("generation")
        and sentinel.get("starting_date_raw") == start
        and sentinel.get("target_date_raw") == target
        and sentinel.get("speed") == expected_speed
        and sentinel.get("mode") == expected_mode
        and sentinel.get("army_count") == len(watch or [])
        and combat_scope_valid
        and sentinel.get("last_observed_date_raw")
        == (start + ticks * 24 if start is not None and ticks is not None else None)
        and sentinel.get("trigger_date_raw") == 0
        and sentinel.get("intermediate_pause_count") == 0
        and sentinel.get("trigger_flags") == 0
        and sentinel.get("trigger_reasons") == []
        and sentinel.get("signed_date_delta_from_target_raw") == 0
        and sentinel.get("overshoot_days") == -1
        and sentinel.get("pause_wrapper_called") is False
        and sentinel.get("pause_observed") is False
        and sentinel.get("terminal_observed") is False
        and armed.get("generation") == sentinel.get("generation")
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
        and cancel
        == {
            "step": (
                "research-cancel-tactical-daily-sentinel-v1-generation-"
                f"{armed.get('generation')}"
            ),
            "status": "canceled",
            "generation": armed.get("generation"),
        }
    )
    if not (triggered_native_stop_valid or canceled_armed_status_valid):
        errors.append("decision_boundary_sentinel_status_invalid")

    boundary_pause_count = _native_int(
        advance_result.get("player_decision_boundary_pause_count")
    )
    sentinel_completion_valid = bool(
        (
            triggered_native_stop_valid
            and boundary_pause_count == 0
            and advance_result.get("external_pause_count") == 0
        )
        or (
            canceled_armed_status_valid
            and advance_result.get("terminal_reached") is False
            and advance_result.get("trigger_reasons") == []
            and advance_result.get("intermediate_pause_count") == 0
            and advance_result.get("overshoot_days") == -1
            and advance_result.get("zero_intermediate_pause") is True
            and boundary_pause_count in {0, 1}
            and advance_result.get("external_pause_count")
            == boundary_pause_count
        )
    )
    cleanup = advance_result.get("managed_failure_cleanup")
    if not (
        advance_result.get("progress_status") == "postcondition"
        and advance_result.get("requested_horizon_days")
        == (
            (target - start) // 24
            if target is not None and start is not None
            else None
        )
        and advance_result.get("timeline_speed") == expected_speed
        and advance_result.get("timeline_policy") == expected_mode
        and advance_result.get("sentinel_mode") == expected_mode
        and advance_result.get("sentinel_scope") == requested_scope
        and advance_result.get("stop_kind") == "player_decision"
        and advance_result.get("sentinel_generation")
        == sentinel.get("generation")
        and advance_result.get("completed_daily_ticks") == ticks
        and boundary_pause_count is not None
        and sentinel_completion_valid
        and advance_result.get("external_rich_query_count") == 0
        and advance_result.get("paused") is True
        and isinstance(cleanup, dict)
        and cleanup.get("attempted") is False
        and cleanup.get("error") is None
    ):
        errors.append("decision_boundary_composite_completion_invalid")

    if objective_hold_request is not None:
        request = advance_result.get("war_objective_hold_request")
        admission = advance_result.get("war_objective_hold_admission")
        post_stop = advance_result.get("war_objective_hold_post_stop")
        if request != {
            "sentinel_scope": "stationary_objective_hold",
            "war_id": objective_hold_request[0],
            "subject_army_id": objective_hold_request[1],
            "objective_province_id": objective_hold_request[2],
            "target_date_raw": objective_hold_request[3],
        }:
            errors.append("objective_hold_request_binding_failed")
        if not (
            isinstance(admission, dict)
            and admission.get("status") == "matched"
            and admission.get("war_id") == objective_hold_request[0]
            and admission.get("subject_army_id")
            == objective_hold_request[1]
            and admission.get("objective_province_id")
            == objective_hold_request[2]
            and admission.get("watch_army_ids") == watch
        ):
            errors.append("objective_hold_admission_binding_failed")
        common_post_stop_binding = bool(
            isinstance(post_stop, dict)
            and post_stop.get("war_id") == objective_hold_request[0]
            and post_stop.get("subject_army_id")
            == objective_hold_request[1]
            and post_stop.get("objective_province_id")
            == objective_hold_request[2]
            and post_stop.get("watch_army_ids") == watch
        )
        decision_post_stop_valid = bool(
            common_post_stop_binding
            and (
                (
                    kind == "active_war_set_changed"
                    and post_stop.get("status")
                    in {"matched", "invalidated"}
                )
                or (
                    kind != "active_war_set_changed"
                    and post_stop.get("status") == "invalidated"
                    and post_stop.get("reason") == "pending_player_decision"
                )
            )
        )
        if not decision_post_stop_valid:
            errors.append("objective_hold_decision_boundary_revalidation_failed")
        if not (
            advance_result.get("exact_war_terminal_watch") is False
            and advance_result.get("exact_active_war_set_watch") is False
            and advance_result.get(
                "maximum_omitted_state_detection_lag_days"
            )
            == 7
        ):
            errors.append("objective_hold_watch_boundary_misreported")

    return {
        "valid": not errors,
        "errors": errors,
        "step": step,
        "actual_elapsed_days": elapsed,
        "terminal_observed": False,
        "sentinel_scope": requested_scope,
        "watch_army_ids": list(watch) if isinstance(watch, list) else None,
        "stop_kind": "player_decision",
        "player_decision_kind": kind,
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
    main_reopened_by_reinforcement = False
    terminal_pursuit_skip = False
    before_side_armies = {
        role: {
            _native_int(row.get("public_cunit_id"))
            for row in (
                side.get("ordered_armies", [])
                if isinstance(side, dict)
                and isinstance(side.get("ordered_armies"), list)
                else []
            )
            if isinstance(row, dict)
            and _native_int(row.get("public_cunit_id")) is not None
        }
        for role, side in (
            ("attacker", before.get("attacker")),
            ("defender", before.get("defender")),
        )
    }
    after_side_armies = {
        role: {
            _native_int(row.get("public_cunit_id"))
            for row in (
                side.get("ordered_armies", [])
                if isinstance(side, dict)
                and isinstance(side.get("ordered_armies"), list)
                else []
            )
            if isinstance(row, dict)
            and _native_int(row.get("public_cunit_id")) is not None
        }
        for role, side in (
            ("attacker", after.get("attacker")),
            ("defender", after.get("defender")),
        )
    }
    reinforcement_strictly_added = bool(
        all(
            before_side_armies[role].issubset(after_side_armies[role])
            for role in ("attacker", "defender")
        )
        and any(
            before_side_armies[role] != after_side_armies[role]
            for role in ("attacker", "defender")
        )
    )
    if (
        after_phase == before_phase == 1
        and after_day < before_day
        and isinstance(sentinel_validation, dict)
        and sentinel_validation.get("valid") is True
        and 0 <= after_day <= actual_elapsed_days
        and after.get("winner_side") == "none"
        and after.get("forced_winner_side") == "none"
        and reinforcement_strictly_added
    ):
        # CK3 restarts the main-phase day counter when a new army joins the
        # same CombatID.  Accept only a strict per-side superset under the
        # exact multi-day sentinel; an unexplained regression remains RED.
        phase_path_legal = True
        main_reopened_by_reinforcement = True
    elif after_phase == before_phase:
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
    elif (
        isinstance(sentinel_validation, dict)
        and sentinel_validation.get("valid") is True
        and before_phase < 2
        and after_phase == 2
        and after_phase - before_phase <= actual_elapsed_days
        and 0 <= after_day <= actual_elapsed_days
        and after.get("winner_side") in {"attacker", "defender"}
    ):
        winner_side = str(after["winner_side"])
        losing_side = (
            after.get("defender")
            if winner_side == "attacker"
            else after.get("attacker")
        )
        terminal_pursuit_skip = bool(
            isinstance(losing_side, dict)
            and losing_side.get("derived_current_fighting_raw") == 0
        )
        phase_path_legal = terminal_pursuit_skip
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
            if pursuit_reopened_to_main or main_reopened_by_reinforcement
            else "same_combat_advanced"
        ),
        "reason": (
            "the same CombatID legally restarted its main-phase day counter "
            "after a strict participant reinforcement under the exact "
            "multi-day sentinel"
            if main_reopened_by_reinforcement
            else "the same CombatID legally reopened from pursuit into main "
            "with its winner reset"
            if pursuit_reopened_to_main
            else "the same CombatID reached a proven terminal pursuit state "
            "during one reconciled multi-day native sentinel advance"
            if terminal_pursuit_skip
            else "the same CombatID has a legal bounded phase/day or exact "
            "casualty-ledger transition"
        ),
        "phase_day_changed": phase_day_changed,
        "ledger_changed": ledger_changed,
        "pursuit_reopened_to_main": pursuit_reopened_to_main,
        "main_reopened_by_reinforcement": main_reopened_by_reinforcement,
        "reinforcement_strictly_added": reinforcement_strictly_added,
        "terminal_pursuit_skip": terminal_pursuit_skip,
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


def _current_battle_identity_pending(
    snapshot: dict[str, object] | None,
    *,
    subject_public_cunit_id: int,
) -> dict[str, object] | None:
    """Recognize only the exact frozen public-combat pending observation."""
    if not isinstance(snapshot, dict):
        return None
    armies = snapshot.get("player_armies")
    subject = next(
        (
            army
            for army in (armies if isinstance(armies, list) else [])
            if isinstance(army, dict)
            and army.get("army_id") == subject_public_cunit_id
        ),
        None,
    )
    if not (
        snapshot.get("paused") is True
        and snapshot.get("battle_control_snapshot_v1_status")
        == BATTLE_CONTROL_IDENTITY_PENDING_STATUS
        and snapshot.get("battle_control_snapshot_v1_diagnostic_reason")
        == BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
        and snapshot.get("battle_control_snapshot_v1_native_query_status")
        == "state_changed"
        and snapshot.get("battle_control_snapshot_v1_query_attempts")
        == _BATTLE_CONTROL_IDENTITY_PENDING_QUERY_ATTEMPTS
        and snapshot.get("battle_control_snapshot_v1") is None
        and snapshot.get("battle_control_snapshot_v1_subject_army_id")
        == subject_public_cunit_id
        and snapshot.get("battle_control_snapshot_v1_queried_snapshot_id")
        == snapshot.get("snapshot_id")
        and snapshot.get("battle_control_snapshot_v1_queried_revision")
        == snapshot.get("revision")
        and snapshot.get(
            "battle_control_snapshot_v1_queried_native_revision"
        )
        == snapshot.get("native_revision")
        and isinstance(subject, dict)
        and subject.get("controllable") is True
        and subject.get("in_combat") is True
    ):
        return None
    return {
        "status": BATTLE_CONTROL_IDENTITY_PENDING_STATUS,
        "diagnostic_reason": BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC,
        "subject_army_id": subject_public_cunit_id,
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
    }


def _battle_identity_materialization_for_current_pending(
    rows: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    subject_public_cunit_id: int,
) -> dict[str, object] | None:
    """Find a prior +24 materialization ending on this pending revision."""
    for row in reversed(rows):
        if row.get("ok") is not True or _effective_command(row) != "life-advance":
            continue
        result = _effective_command_result(row)
        materialization = (
            result.get("battle_identity_materialization")
            if isinstance(result, dict)
            else None
        )
        if not isinstance(materialization, dict):
            continue
        start_date_raw = _native_int(materialization.get("starting_date_raw"))
        end_date_raw = _native_int(materialization.get("ending_date_raw"))
        start_revision = _native_int(materialization.get("starting_revision"))
        end_revision = _native_int(materialization.get("ending_revision"))
        start_native_revision = _native_int(
            materialization.get("starting_native_revision")
        )
        end_native_revision = _native_int(
            materialization.get("ending_native_revision")
        )
        if not (
            materialization.get("schema_version") == 1
            and materialization.get("status") == "one_day_advanced"
            and materialization.get("proof_kind")
            == "battle_identity_materialization"
            and materialization.get("diagnostic_reason")
            == BATTLE_CONTROL_IDENTITY_PENDING_DIAGNOSTIC
            and materialization.get("subject_public_cunit_id")
            == subject_public_cunit_id
            and materialization.get("next_revision_requirement")
            == "full_combat_id"
            and start_date_raw is not None
            and end_date_raw == start_date_raw + 24
            and materialization.get("elapsed_days") == 1
            and start_revision is not None
            and end_revision is not None
            and end_revision > start_revision
            and start_native_revision is not None
            and start_native_revision > 0
            and end_native_revision is not None
            and end_native_revision > start_native_revision
            and materialization.get("ending_snapshot_id")
            == snapshot.get("snapshot_id")
            and end_revision == _native_int(snapshot.get("revision"))
            and end_native_revision
            == _native_int(snapshot.get("native_revision"))
            and end_date_raw == _native_int(snapshot.get("date_raw"))
            and result.get("paused") is True
            and result.get("timeline_speed") == 1
            and result.get("timeline_policy")
            == "exact_one_day_battle_identity_materialization"
        ):
            continue
        return materialization
    return None


def _battle_control_turn_state(
    rows: list[dict[str, object]],
    snapshot: dict[str, object] | None,
    controlled_armies: list[dict[str, object]],
) -> dict[str, object]:
    """Gate combat time advancement on exact pre/post battle frames."""
    scoped = _history_after_latest_restore(rows)
    # Battle queries are scoped to this process; persisted move proof is not.
    scope_offset = len(rows) - len(scoped)
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
            scope_offset + position
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
                for position, row in enumerate(rows, start=1)
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
        identity_pending = _current_battle_identity_pending(
            snapshot,
            subject_public_cunit_id=subject,
        )
        if identity_pending is None:
            continue
        prior_materialization = (
            _battle_identity_materialization_for_current_pending(
                scoped,
                snapshot,
                subject_public_cunit_id=subject,
            )
        )
        return {
            "status": (
                "identity_pending_after_materialization"
                if prior_materialization is not None
                else "identity_pending"
            ),
            "subject_army_id": subject,
            "identity_pending": identity_pending,
            "prior_materialization": prior_materialization,
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
            scope_offset + position
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
                for position, row in enumerate(rows, start=1)
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


def _forecast_required_war_entry_plan(
    declaration: dict[str, object],
    assessment: dict[str, object],
    candidate: dict[str, object],
    campaign_root: dict[str, object],
    available_steps: set[str],
) -> dict[str, object]:
    """Run the bounded prewar battle prior for a same-frame legal candidate."""

    advance = "life-advance" if "life-advance" in available_steps else None
    power_eu = _war_entry_power_eu_projection(assessment)
    declaration_id = declaration.get("declaration_id")
    forecast = forecast_prewar_power_battle(
        assessment,
        declaration_id=declaration_id if isinstance(declaration_id, str) else "",
    )
    admission = prewar_declaration_admission(forecast)
    typed_step = candidate.get("typed_declaration_step")
    if (
        admission["admitted"] is True
        and candidate.get("typed_declaration_available") is True
        and isinstance(typed_step, str)
        and typed_step in available_steps
    ):
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_declaration",
            "selected_step": typed_step,
            "reason": "the same-frame legal declaration passes the bounded aggregate battle prior's conservative risk budget",
            "decision": {
                "policy": candidate["rule_id"],
                "outcome": "DECLARE",
                "declaration_id": declaration_id,
                "target_character_id": declaration.get("target_character_id"),
                "casus_belli_key": declaration.get("casus_belli_key"),
                "claimant_character_id": declaration.get("claimant_character_id"),
                "native_power_assessment_consumed": True,
                "automatic_declaration_enabled": True,
                "forecast_model_fidelity": forecast["model_fidelity"],
            },
            "declaration": dict(declaration),
            "war_entry_assessment": dict(assessment),
            "war_entry_candidate": dict(candidate),
            "prewar_battle_forecast": forecast,
            "prewar_forecast_admission": admission,
            "prewar_forecast_admission_available": True,
        }
    return {
        "policy": "one-life-turn-v1",
        "phase": "native_war_entry_forecast_required",
        "selected_step": advance,
        "reason": (
            "the legal candidate was evaluated by the bounded aggregate "
            "battle prior, but its risk budget does not support this declaration"
        ),
        "decision": {
            "policy": candidate["rule_id"],
            "outcome": "NO_DECLARE",
            "declaration_id": declaration.get("declaration_id"),
            "target_character_id": declaration.get("target_character_id"),
            "casus_belli_key": declaration.get("casus_belli_key"),
            "claimant_character_id": declaration.get("claimant_character_id"),
            "native_power_assessment_consumed": True,
            "campaign_root_context_consumed": True,
            "forecast_required": True,
            "automatic_declaration_enabled": False,
            "eu_lower_raw": None,
            "advance_contract": "native_life_advance" if advance else None,
        },
        "required_capabilities": [
            "game.command.query-prewar-scope-v1-N",
            "game.command.query-prewar-combat-simulation-inputs-v3-N",
            "game.forecast.combat-monte-carlo-v1",
        ],
        "prewar_forecast_admission_available": forecast.get("status") == "estimated",
        "prewar_battle_forecast": forecast,
        "prewar_forecast_admission": admission,
        "declaration": dict(declaration),
        "war_entry_assessment": dict(assessment),
        "war_entry_expected_utility": power_eu,
        "war_entry_candidate": dict(candidate),
        "campaign_root_context": {
            key: campaign_root.get(key)
            for key in (
                "snapshot_revision",
                "date_raw",
                "player_character_id",
                "independent",
                "government",
                "player_monthly_gold_income",
                "player_domain_size",
                "player_domain_limit",
                "player_targeting_faction_count",
            )
        },
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


def _claim_cb_white_peace_candidate(
    war: dict[str, object],
    options: object,
) -> bool:
    if not isinstance(options, dict):
        return False
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
        war.get("player_side") == "attacker"
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


def _de_jure_no_safe_route_surrender_candidate(
    war: dict[str, object],
    options: object,
) -> bool:
    """Recognize the exact native-positive R767 emergency exit row.

    Route exhaustion is checked at the only call site.  Keeping that tactical
    fact out of this evidence predicate lets the negative-query lease reject a
    historical positive surrender row before route planning reaches its final
    branch.
    """
    if not isinstance(options, dict):
        return False
    score = war.get("player_relative_war_score")
    duration = options.get("war_duration_days")
    casus_belli = options.get("active_casus_belli_identity")
    option_rows = options.get("options")
    surrender = (
        option_rows.get("surrender")
        if isinstance(option_rows, dict)
        else None
    )
    response = (
        surrender.get("recipient_response")
        if isinstance(surrender, dict)
        else None
    )
    return bool(
        war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score") == score
        and isinstance(score, int)
        and not isinstance(score, bool)
        and score <= _DE_JURE_NO_SAFE_ROUTE_SURRENDER_MAX_SCORE
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration >= _DE_JURE_NO_SAFE_ROUTE_SURRENDER_MIN_DAYS
        and options.get("active_casus_belli_present") is True
        and isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key")
        == _DE_JURE_NO_SAFE_ROUTE_SURRENDER_CB
        and isinstance(surrender, dict)
        and surrender.get("outcome") == "attacker_defeat"
        and surrender.get("hostage_variant") == "none"
        and surrender.get("context_constructed") is True
        and surrender.get("native_validator_passed") is True
        and surrender.get("available") is True
        and surrender.get("auto_accept_observable") is True
        and surrender.get("auto_accept") is True
        and isinstance(response, dict)
        and response.get("status") == "available"
        and response.get("would_accept_now") is True
    )


def _terminal_score_surrender_ready(
    snapshot: dict[str, object],
    war: dict[str, object],
    options: object,
) -> bool:
    """Accept a native-proven defeat before CK3 auto-removes the WarID."""

    if not isinstance(options, dict):
        return False
    war_id = _native_int(war.get("war_id"))
    score = _native_int(war.get("player_relative_war_score"))
    rows = options.get("options")
    surrender = rows.get("surrender") if isinstance(rows, dict) else None
    response = (
        surrender.get("recipient_response")
        if isinstance(surrender, dict)
        else None
    )
    return bool(
        war_id is not None
        and snapshot.get("paused") is True
        and _same_frame_termination_row(snapshot, options, war_id)
        and war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and score == _TERMINAL_SCORE_SURRENDER_SCORE
        and options.get("player_relative_war_score") == score
        and options.get("absolute_war_scores_observable") is True
        and options.get("attacker_war_score") == score
        and options.get("defender_war_score") == -score
        and options.get("active_casus_belli_present") is True
        and isinstance(options.get("active_casus_belli_identity"), dict)
        and isinstance(surrender, dict)
        and surrender.get("outcome") == "attacker_defeat"
        and surrender.get("hostage_variant") == "none"
        and surrender.get("context_constructed") is True
        and surrender.get("native_validator_passed") is True
        and surrender.get("available") is True
        and surrender.get("auto_accept_observable") is True
        and surrender.get("auto_accept") is True
        and isinstance(response, dict)
        and response.get("status") == "available"
        and response.get("would_accept_now") is True
    )


def _de_jure_no_safe_route_white_peace_candidate(
    war: dict[str, object],
    options: object,
) -> bool:
    """Recognize only the R794 positive de-jure white-peace frame."""
    if not isinstance(options, dict):
        return False
    score = war.get("player_relative_war_score")
    duration = options.get("war_duration_days")
    casus_belli = options.get("active_casus_belli_identity")
    targeted_title_ids = war.get("targeted_title_ids")
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
    acceptance = (
        white_peace.get("ai_acceptance")
        if isinstance(white_peace, dict)
        else None
    )
    return bool(
        war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score") == score
        and isinstance(score, int)
        and not isinstance(score, bool)
        and 0 < score < 100
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration >= _DE_JURE_NO_SAFE_ROUTE_SURRENDER_MIN_DAYS
        and options.get("active_casus_belli_present") is True
        and isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key")
        == _DE_JURE_NO_SAFE_ROUTE_SURRENDER_CB
        and casus_belli.get("database_index")
        == _DE_JURE_NO_SAFE_ROUTE_CB_DATABASE_INDEX
        and isinstance(targeted_title_ids, list)
        and len(targeted_title_ids) == 1
        and (
            (target_title_id := _native_int(targeted_title_ids[0]))
            is not None
        )
        and target_title_id > 0
        and options.get("cb_allows_white_peace") is True
        and isinstance(white_peace, dict)
        and white_peace.get("outcome") == "white_peace"
        and white_peace.get("hostage_variant") == "none"
        and white_peace.get("context_constructed") is True
        and white_peace.get("native_validator_passed") is True
        and white_peace.get("available") is True
        and white_peace.get("ai_acceptance_observable") is True
        and isinstance(acceptance, dict)
        and isinstance(acceptance.get("raw"), int)
        and not isinstance(acceptance.get("raw"), bool)
        and acceptance.get("raw") > 0
        and isinstance(response, dict)
        and response.get("status") == "available"
        and response.get("would_accept_now") is True
    )


def _de_jure_no_safe_route_white_peace_ready(
    snapshot: dict[str, object],
    war: dict[str, object],
    options: object,
) -> bool:
    war_id = _native_int(war.get("war_id"))
    return bool(
        war_id is not None
        and snapshot.get("paused") is True
        and _same_frame_termination_row(snapshot, options, war_id)
        and _de_jure_no_safe_route_white_peace_candidate(war, options)
    )


def _de_jure_no_safe_route_surrender_ready(
    snapshot: dict[str, object],
    war: dict[str, object],
    options: object,
) -> bool:
    war_id = _native_int(war.get("war_id"))
    return bool(
        war_id is not None
        and snapshot.get("paused") is True
        and _same_frame_termination_row(snapshot, options, war_id)
        and _de_jure_no_safe_route_surrender_candidate(war, options)
    )


def _de_jure_no_safe_route_exit_plan(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    termination_by_war_id: dict[int, dict[str, object]],
    available_steps: set[str],
    active_war_summary: list[dict[str, object]],
    route_rejections: list[dict[str, object]],
) -> dict[str, object] | None:
    """Compare the three exact de-jure outcomes after route exhaustion."""
    for war in active_wars:
        if not isinstance(war, dict):
            continue
        war_id = _native_int(war.get("war_id"))
        options = termination_by_war_id.get(war_id) if war_id else None
        if war_id is None or not isinstance(options, dict):
            continue
        white_peace_ready = _de_jure_no_safe_route_white_peace_ready(
            snapshot, war, options
        )
        surrender_ready = _de_jure_no_safe_route_surrender_ready(
            snapshot, war, options
        )
        if not white_peace_ready and not surrender_ready:
            continue
        option_rows = options["options"]
        white_peace = option_rows.get("white_peace")
        white_response = (
            white_peace.get("recipient_response")
            if isinstance(white_peace, dict)
            else None
        )
        surrender = option_rows.get("surrender")
        surrender_response = (
            surrender.get("recipient_response")
            if isinstance(surrender, dict)
            else None
        )
        surrender_executable = bool(
            isinstance(surrender, dict)
            and surrender.get("outcome") == "attacker_defeat"
            and surrender.get("hostage_variant") == "none"
            and surrender.get("context_constructed") is True
            and surrender.get("native_validator_passed") is True
            and surrender.get("available") is True
            and surrender.get("auto_accept_observable") is True
            and surrender.get("auto_accept") is True
            and isinstance(surrender_response, dict)
            and surrender_response.get("status") == "available"
            and surrender_response.get("would_accept_now") is True
        )
        selected_outcome = (
            "white_peace" if white_peace_ready else "surrender"
        )
        step = (
            offer_white_peace_step(war_id)
            if white_peace_ready
            else surrender_war_step(war_id)
        )
        decision = {
            "policy": (
                "de-jure-no-safe-route-terminal-choice-v1"
                if white_peace_ready
                else "de-jure-no-safe-route-emergency-exit-v1"
            ),
            "selected_outcome": selected_outcome,
            "full_campaign_utility_ready": False,
            "candidates": {
                "continue": {
                    "legal": True,
                    "executable": False,
                    "reason": "no_safe_exact_route",
                },
                "white_peace": {
                    "legal": bool(
                        isinstance(white_peace, dict)
                        and white_peace.get("native_validator_passed") is True
                        and white_peace.get("available") is True
                    ),
                    "recipient_would_accept_now": (
                        white_response.get("would_accept_now")
                        if isinstance(white_response, dict)
                        else None
                    ),
                    "executable": white_peace_ready,
                },
                "surrender": {
                    "legal": bool(
                        isinstance(surrender, dict)
                        and surrender.get("native_validator_passed") is True
                        and surrender.get("available") is True
                    ),
                    "executable": surrender_executable,
                    "recipient_would_accept_now": (
                        surrender_response.get("would_accept_now")
                        if isinstance(surrender_response, dict)
                        else None
                    ),
                },
            },
            "war_score": war.get("player_relative_war_score"),
            "war_duration_days": options.get("war_duration_days"),
            "casus_belli": dict(options["active_casus_belli_identity"]),
        }
        if step not in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_no_safe_route_exit_unsupported",
                "selected_step": None,
                "required_step": step,
                "war_id": war_id,
                "decision": decision,
                "reason": "the selected same-frame native terminal is unreachable",
                "route_rejections": route_rejections,
                "active_wars": active_war_summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": (
                "native_war_de_jure_no_safe_route_white_peace"
                if white_peace_ready
                else "native_war_de_jure_no_safe_route_surrender"
            ),
            "selected_step": step,
            "war_id": war_id,
            "decision": decision,
            "reason": (
                "all exact objective routes are unsafe; the same frame "
                "compares continue, white peace, and surrender and selects "
                + (
                    "white peace over surrender"
                    if white_peace_ready
                    else "the sole executable surrender"
                )
            ),
            "route_rejections": route_rejections,
            "active_wars": active_war_summary,
        }
    return None

def _claim_cb_white_peace_base_ready(
    snapshot: dict[str, object],
    war: dict[str, object],
    options: object,
) -> bool:
    war_id = war.get("war_id")
    return bool(
        isinstance(war_id, int)
        and not isinstance(war_id, bool)
        and snapshot.get("paused") is True
        and _same_frame_termination_row(snapshot, options, war_id)
        and _claim_cb_white_peace_candidate(war, options)
    )


def _claim_cb_white_peace_duration_gate_raw(
    war: dict[str, object], options: object
) -> int | None:
    """Return time until the known 365-day claim_cb legality boundary."""
    if not isinstance(options, dict):
        return None
    score = war.get("player_relative_war_score")
    duration = options.get("war_duration_days")
    casus_belli = options.get("active_casus_belli_identity")
    if not (
        war.get("player_side") == "attacker"
        and war.get("player_is_primary_war_leader") is True
        and options.get("player_side") == "attacker"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score") == score
        and isinstance(score, int)
        and not isinstance(score, bool)
        and 0 <= score < 100
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and 0 <= duration < 365
        and options.get("active_casus_belli_present") is True
        and isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key") == "claim_cb"
        and options.get("cb_allows_white_peace") is True
    ):
        return None
    return max(1, 365 - duration) * 24


def _termination_negative_reuse_barrier(step: str | None) -> bool:
    return bool(
        parse_event_option_step(step) is not None
        or step
        in {
            "resolve-current-event",
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
            _ACCEPT_PENDING_CHARACTER_INTERACTION_STEP,
            _REJECT_PENDING_CHARACTER_INTERACTION_STEP,
            _BLOCK_PENDING_CHARACTER_INTERACTION_STEP,
            "death-terminal",
            "start-next-episode",
        }
    )


def _negative_war_termination_reuse(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    war: dict[str, object],
) -> dict[str, object] | None:
    """Reuse only a proven negative query classification for under 7 days."""
    if (
        snapshot.get("paused") is not True
        or snapshot.get("one_life_terminal_reason") is not None
        or isinstance(snapshot.get("active_event"), dict)
        or isinstance(snapshot.get("pending_character_interaction"), dict)
    ):
        return None
    played_character = snapshot.get("played_character")
    if not (
        isinstance(played_character, dict)
        and played_character.get("alive") is True
    ):
        return None
    current_character_id = _native_int(
        played_character.get("character_id")
    )
    current_date_raw = _native_int(snapshot.get("date_raw"))
    current_episode_run_id = snapshot.get("episode_run_id")
    diagnostics = snapshot.get("diagnostics")
    current_connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    active_war_signature = war_termination_active_war_signature(active_wars)
    war_id = _native_int(war.get("war_id"))
    if (
        current_character_id is None
        or current_date_raw is None
        or not isinstance(current_episode_run_id, str)
        or not current_episode_run_id
        or current_connection_generation is None
        or active_war_signature is None
        or war_id is None
    ):
        return None

    for row in reversed(_history_after_latest_restore(commands)):
        step = _effective_command(row)
        if _termination_negative_reuse_barrier(step):
            return None
        queried_war_id = parse_query_war_termination_options_step(step)
        if queried_war_id != war_id:
            continue
        if row.get("ok") is not True:
            return None
        result = _effective_command_result(row)
        context = (
            result.get("termination_query_context")
            if isinstance(result, dict)
            else None
        )
        options = (
            result.get("war_termination_options")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(result, dict)
            and result.get("step") == step
            and result.get("accepted") is True
            and result.get("status") == "available"
            and isinstance(context, dict)
            and context.get("schema_version") == 1
            and context.get("active_war_signature")
            == active_war_signature
            and context.get("queried_episode_run_id")
            == current_episode_run_id
            and context.get("queried_connection_generation")
            == current_connection_generation
            and context.get("queried_character_id")
            == current_character_id
        ):
            return None
        queried_date_raw = _native_int(context.get("queried_date_raw"))
        query_signature = war_termination_negative_query_signature(options)
        if (
            queried_date_raw is None
            or query_signature is None
            or context.get("negative_decision_signature")
            != query_signature
            or query_signature.get("war_id") != war_id
            or context.get("queried_war_duration_days")
            != (
                options.get("war_duration_days")
                if isinstance(options, dict)
                else None
            )
        ):
            return None
        elapsed_raw = current_date_raw - queried_date_raw
        lease_raw = _NEGATIVE_WAR_TERMINATION_REUSE_RAW
        duration_gate_raw = _claim_cb_white_peace_duration_gate_raw(
            war, options
        )
        if duration_gate_raw is not None:
            lease_raw = min(lease_raw, duration_gate_raw)
        if not 0 <= elapsed_raw < lease_raw:
            return None
        # Positive candidates are always current-frame-only.  In particular,
        # never turn a historical options row into a terms query or action.
        if (
            _claim_cb_white_peace_candidate(war, options)
            or _de_jure_no_safe_route_surrender_candidate(war, options)
            or _de_jure_no_safe_route_white_peace_candidate(war, options)
        ):
            return None
        return {
            "status": "negative_assessment_reused",
            "war_id": war_id,
            "queried_date_raw": queried_date_raw,
            "age_raw": elapsed_raw,
            "age_game_days": elapsed_raw // 24,
            "expires_date_raw": queried_date_raw + lease_raw,
            "query_sequence": result.get("query_sequence"),
        }
    return None


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
                "action_status": action.get("status"),
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


def _recent_postwar_reentry_cooldown(
    commands: list[dict[str, object]],
    *,
    date_raw: object,
    episode_run_id: object,
    active_war_ids: set[int],
) -> dict[str, object] | None:
    """Keep a material terminal result peaceful for one bounded month.

    R801 proved that CK3 could expose the same target/CB as declarable on the
    very frame after an accepted white peace.  A legal declaration there
    immediately recreated the war that the policy had just paid to end.  The
    existing 30-day terminal-action horizon is therefore also the minimum
    re-entry interval after the old WarID independently disappears.
    """

    if isinstance(date_raw, bool) or not isinstance(date_raw, int):
        return None
    for row in reversed(commands):
        command = _effective_command(row)
        if not isinstance(command, str) or not (
            command.startswith("offer-white-peace-")
            or command.startswith("surrender-war-")
        ):
            continue
        result = _effective_command_result(row)
        action = (
            result.get("war_termination_result")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(action, dict)
            and action.get("episode_run_id") == episode_run_id
            and action.get("status") in {"submitted_pending", "applied"}
        ):
            continue
        war_id = action.get("war_id")
        submitted_date_raw = action.get("submitted_date_raw")
        if (
            isinstance(war_id, bool)
            or not isinstance(war_id, int)
            or war_id in active_war_ids
            or isinstance(submitted_date_raw, bool)
            or not isinstance(submitted_date_raw, int)
        ):
            continue
        elapsed_raw = date_raw - submitted_date_raw
        if 0 <= elapsed_raw < _WHITE_PEACE_PROPOSAL_COOLDOWN_RAW:
            return {
                "status": "cooldown",
                "war_id": war_id,
                "outcome": action.get("outcome"),
                "submitted_date_raw": submitted_date_raw,
                "elapsed_raw": elapsed_raw,
                "remaining_raw": (
                    _WHITE_PEACE_PROPOSAL_COOLDOWN_RAW - elapsed_raw
                ),
                "history_index": row.get("index"),
            }
        return None
    return None


def _white_peace_no_safe_route_response_plan(
    commands: list[dict[str, object]],
    *,
    war_id: int,
    date_raw: object,
    episode_run_id: object,
    available_steps: set[str],
    active_war_summary: list[dict[str, object]],
    route_rejections: list[dict[str, object]],
) -> dict[str, object] | None:
    """Observe one submitted proposal through CK3's native reply window."""
    submission = _white_peace_submission_cooldown(
        commands,
        war_id=war_id,
        date_raw=date_raw,
        episode_run_id=episode_run_id,
    )
    if not (
        isinstance(submission, dict)
        and submission.get("status") == "cooldown"
        and submission.get("action_status") == "submitted_pending"
    ):
        return None
    elapsed_raw = _native_int(submission.get("elapsed_raw"))
    if elapsed_raw is None or elapsed_raw < 0:
        return None
    if elapsed_raw < _WHITE_PEACE_NATIVE_RESPONSE_OBSERVATION_RAW:
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_white_peace_response_window_advance",
                "selected_step": "life-advance",
                "war_id": war_id,
                "decision": {
                    "policy": "claim-cb-minimal-white-peace-v1",
                    "outcome": "white_peace",
                    "status": "submitted_pending",
                    "submission": submission,
                    "response_observation_deadline_raw": (
                        int(submission["submitted_date_raw"])
                        + _WHITE_PEACE_NATIVE_RESPONSE_OBSERVATION_RAW
                    ),
                },
                "reason": (
                    "all exact routes remain unsafe while the sole white-peace "
                    "proposal is inside CK3's observed asynchronous reply "
                    "window; advance one day without resubmitting"
                ),
                "route_rejections": route_rejections,
                "active_wars": active_war_summary,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_white_peace_response_window_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "war_id": war_id,
            "submission": submission,
            "reason": (
                "the submitted white-peace proposal is still inside the "
                "native reply window, but no one-day advance is available"
            ),
            "route_rejections": route_rejections,
            "active_wars": active_war_summary,
        }
    return {
        "policy": "one-life-turn-v1",
        "phase": "native_war_white_peace_postcondition_unresolved",
        "selected_step": None,
        "required_step": "old-WarID-disappearance",
        "war_id": war_id,
        "submission": submission,
        "reason": (
            "the native reply observation window elapsed with the old WarID "
            "still present; do not repeat the terminal action"
        ),
        "route_rejections": route_rejections,
        "active_wars": active_war_summary,
    }


def _de_jure_surrender_submission_state(
    commands: list[dict[str, object]],
    *,
    war_id: int,
    date_raw: object,
    episode_run_id: object,
) -> dict[str, object] | None:
    """Latch a terminal ACK until the old WarID independently disappears."""
    expected_step = surrender_war_step(war_id)
    for row in reversed(_history_after_latest_restore(commands)):
        if _effective_command(row) != expected_step or row.get("ok") is not True:
            continue
        result = _effective_command_result(row)
        action = (
            result.get("war_termination_result")
            if isinstance(result, dict)
            else None
        )
        if not (
            isinstance(action, dict)
            and action.get("war_id") == war_id
            and action.get("outcome") == "attacker_defeat"
            and action.get("episode_run_id") == episode_run_id
            and action.get("status") in {"submitted_pending", "applied"}
        ):
            continue
        if isinstance(date_raw, bool) or not isinstance(date_raw, int):
            return {"status": "invalid_current_date"}
        submitted_date_raw = _native_int(action.get("submitted_date_raw"))
        if submitted_date_raw is None:
            return {"status": "malformed_submission_history"}
        elapsed_raw = date_raw - submitted_date_raw
        return {
            "status": (
                "same_day_pending"
                if elapsed_raw == 0
                and action.get("status") == "submitted_pending"
                else "unresolved"
            ),
            "action_status": action.get("status"),
            "submitted_date_raw": submitted_date_raw,
            "elapsed_raw": elapsed_raw,
            "history_index": row.get("index"),
        }
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
    """Choose an exact Raiktor exit first, then the existing bounded turn."""
    steps = tuple(action_steps or ())
    capabilities = tuple(bridge_capabilities or ())
    formal = plan_raiktor_formal_exit(
        snapshot,
        _expanded_command_rows(commands),
        action_steps=steps,
        bridge_capabilities=capabilities,
    )
    if isinstance(formal, dict) and formal.get("status") != "continue_ready":
        return formal
    plan = _choose_one_life_turn_core(
        commands,
        snapshot=snapshot,
        action_steps=steps,
        bridge_capabilities=capabilities,
        next_run_plan=next_run_plan,
        battle_speed_readiness=battle_speed_readiness,
    )
    plan = _primary_defender_siege_forecast_ingress(
        plan,
        commands=_expanded_command_rows(commands),
        snapshot=snapshot,
        action_steps=set(steps),
        bridge_capabilities=set(capabilities),
    )
    plan = _general_battle_forecast_ingress(
        plan,
        commands=_expanded_command_rows(commands),
        snapshot=snapshot,
        action_steps=set(steps),
        bridge_capabilities=set(capabilities),
    )
    if not isinstance(formal, dict):
        return plan
    decision = formal["decision"]
    war_id = decision["war_id"]
    if plan.get("selected_step") in {
        offer_white_peace_step(war_id), surrender_war_step(war_id)
    }:
        emergency = plan.get("decision")
        if (
            isinstance(emergency, dict)
            and emergency.get("policy")
            == "de-jure-no-safe-route-emergency-exit-v1"
            and plan.get("selected_step") == surrender_war_step(war_id)
        ):
            return {
                **plan,
                "formal_three_way_decision": decision,
                "formal_continue_overridden_by_proven_route_exhaustion": True,
            }
        return {
            "policy": "raiktor-formal-three-way-exit-v1",
            "phase": "native_war_raiktor_threeway_conflicting_terminal",
            "selected_step": None,
            "reason": "bounded tactical planner chose a different terminal from the current three-way continue recommendation",
            "war_exit_decision": decision,
        }
    return {
        **plan,
        "war_exit_decision": decision,
        "bounded_continue_adapter": "existing-native-tactical-turn-v1",
    }


def consume_one_life_lifestyle_private_trial(
    baseline_plan: dict[str, object],
    *,
    same_frame_feudal_scope: dict[str, object],
    private_query: dict[str, object] | None,
) -> dict[str, object]:
    """Keep the existing forced-state/war choice, then consider one LIFE perk.

    The caller invokes this only for a controlled slot43 candidate.  Normal
    `choose_one_life_turn` and all public capability surfaces remain unchanged.
    """

    return consume_lifestyle_private_query(
        baseline_plan,
        scope=same_frame_feudal_scope,
        query=private_query,
    )


def _choose_one_life_turn_core(
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
            "stationary_objective_hold_sentinel_live_ready",
            "stationary_objective_hold_sentinel_canary_ready",
            "stationary_objective_hold_sentinel_speed_4_live_ready",
            "stationary_objective_hold_sentinel_speed_5_live_ready",
            "terminal_sentinel_live_ready",
            "overwhelming_matrix_live_ready",
        )
    }
    stationary_objective_hold_sentinel_speed = (
        _noncombat_sentinel_timeline_speed(
            battle_speed_readiness,
            sentinel_scope="stationary_objective_hold",
        )
    )
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
        raw_lifecycle = (
            snapshot.get("succession_lifecycle")
            if isinstance(snapshot, dict)
            else None
        )
        try:
            succession_lifecycle = normalize_succession_lifecycle_binding_v1(
                raw_lifecycle
                if raw_lifecycle is not None
                else legacy_rogue_one_life_binding_v1()
            )
        except ValueError:
            succession_lifecycle = unknown_succession_lifecycle_binding_v1()
        lifecycle = succession_lifecycle["lifecycle"]
        succession_reconciliation = (
            snapshot.get("succession_reconciliation")
            if isinstance(snapshot, dict)
            else None
        )
        if lifecycle == UNKNOWN_SUCCESSION_LIFECYCLE:
            return {
                "policy": "one-life-turn-v1",
                "phase": "terminal_succession_lifecycle_unbound",
                "selected_step": None,
                "reason": (
                    "the terminal frame has no valid frozen succession "
                    "lifecycle binding"
                ),
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "succession_lifecycle": succession_lifecycle,
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
            }
        if lifecycle == ORDINARY_CAMPAIGN_SUCCESSION:
            successor_continuation_ready = bool(
                terminal_reason == "played_character_changed"
                and isinstance(succession_reconciliation, dict)
                and succession_reconciliation.get("status") == "available"
                and succession_reconciliation.get("verdict") == "matched"
                and succession_reconciliation.get("successor_match") is True
                and succession_reconciliation.get(
                    "title_distribution_match"
                )
                is True
                and CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
                in available_steps
            )
            successor_reconciliation_red = bool(
                terminal_reason == "played_character_changed"
                and isinstance(succession_reconciliation, dict)
                and succession_reconciliation.get("status") == "available"
                and succession_reconciliation.get("verdict") != "matched"
            )
            successor_reconciliation_pending = bool(
                terminal_reason == "played_character_changed"
                and not successor_continuation_ready
                and not successor_reconciliation_red
            )
            return {
                "policy": "one-life-turn-v1",
                "phase": (
                    "ordinary_successor_reconciliation_red"
                    if successor_reconciliation_red
                    else (
                        "ordinary_successor_reconciliation_pending"
                        if successor_reconciliation_pending
                        else (
                            "ordinary_successor_continuation_ready"
                            if successor_continuation_ready
                            else "ordinary_campaign_terminal_no_successor"
                        )
                    )
                ),
                "selected_step": (
                    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
                    if successor_continuation_ready
                    else None
                ),
                "reason": (
                    "the ordinary campaign can continue on CK3's reconciled "
                    "played successor without a rogue settlement"
                    if successor_continuation_ready
                    else (
                        "the observed successor or inherited predecessor "
                        "estate disagrees with the retained expectation"
                        if successor_reconciliation_red
                        else (
                            "the played successor still requires a matched "
                            "predecessor-estate reconciliation"
                            if successor_reconciliation_pending
                            else "the ordinary campaign has no playable successor"
                        )
                    )
                ),
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "succession_lifecycle": succession_lifecycle,
                "settlement_required": False,
                "continue_as_heir_after_death": successor_continuation_ready,
                "heir_gameplay_actions": 0,
            }
        assert lifecycle == ROGUE_ONE_LIFE
        completed_terminal = _latest_effective_result(rows, "death-terminal")
        if (
            isinstance(completed_terminal, dict)
            and completed_terminal.get("terminal") is True
            and completed_terminal.get("score") is not None
            and completed_terminal.get("settlement_status")
            in {None, "complete"}
        ):
            successor_continuation_ready = bool(
                terminal_reason == "played_character_changed"
                and isinstance(succession_reconciliation, dict)
                and succession_reconciliation.get("status") == "available"
                and succession_reconciliation.get("verdict") == "matched"
                and succession_reconciliation.get("successor_match") is True
                and succession_reconciliation.get(
                    "title_distribution_match"
                )
                is True
                and CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
                in available_steps
            )
            successor_reconciliation_red = bool(
                terminal_reason == "played_character_changed"
                and isinstance(succession_reconciliation, dict)
                and succession_reconciliation.get("status") == "available"
                and succession_reconciliation.get("verdict") != "matched"
            )
            successor_reconciliation_pending = bool(
                terminal_reason == "played_character_changed"
                and not successor_continuation_ready
                and not successor_reconciliation_red
            )
            return {
                "policy": "one-life-turn-v1",
                "phase": (
                    "terminal_succession_reconciliation_red"
                    if successor_reconciliation_red
                    else (
                        "terminal_successor_reconciliation_pending"
                        if successor_reconciliation_pending
                        else "terminal_complete"
                    )
                ),
                "selected_step": (
                    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
                    if successor_continuation_ready
                    else (
                        "start-next-episode"
                        if (
                            terminal_reason != "played_character_changed"
                            and "start-next-episode" in available_steps
                        )
                        else None
                    )
                ),
                "reason": (
                    "the completed life can continue on CK3's reconciled "
                    "played successor"
                    if successor_continuation_ready
                    else (
                        "the observed successor or inherited predecessor "
                        "estate disagrees with the retained expectation"
                        if successor_reconciliation_red
                        else (
                            "the played successor still requires a matched "
                            "predecessor-estate reconciliation"
                            if successor_reconciliation_pending
                            else "this one-life episode is already settled"
                        )
                    )
                ),
                "terminal_reason": terminal_reason,
                "episode_character_id": episode_character_id,
                "succession_lifecycle": succession_lifecycle,
                "score": completed_terminal.get("score"),
                "continue_as_heir_after_death": (
                    successor_continuation_ready
                ),
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
                "succession_lifecycle": succession_lifecycle,
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
                "succession_lifecycle": succession_lifecycle,
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
            "succession_lifecycle": succession_lifecycle,
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

            played_character_id = (
                played_character.get("character_id")
                if isinstance(played_character, dict)
                else None
            )
            raiktor_decision = recommend_robert_raiktor_option_v1(
                event_context,
                snapshot,
                war_entry_assessments=_same_frame_war_entry_assessments(
                    rows, snapshot
                ),
                action_steps=available_steps,
                cross_run_focus=cross_run_focus,
                event_scope_query_supported=(
                    RAIKTOR_BOOKMARK_EVENT_SCOPE_CAPABILITY
                    in available_capabilities
                ),
            )
            if raiktor_decision is not None:
                event_summary["raiktor_decision"] = raiktor_decision
                if raiktor_decision["status"] == "query_required":
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_raiktor_power_query",
                        "selected_step": raiktor_decision["selected_step"],
                        "reason": raiktor_decision["reason"],
                        "active_event": event_summary,
                        "event_decision": raiktor_decision,
                    }
                if raiktor_decision["status"] == "blocked":
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_raiktor_contract_blocked",
                        "selected_step": None,
                        "reason": raiktor_decision["reason"],
                        "active_event": event_summary,
                        "event_decision": raiktor_decision,
                    }
                native_index = raiktor_decision["selected_native_option_index"]
                assert isinstance(native_index, int)
                option_number = native_index + 1
                exact_step = event_option_step(option_number)
                selected = next(
                    option
                    for option in materialized_options
                    if option["native_option_index"] == native_index
                )
                event_summary.update(
                    {
                        "selected_option_number": option_number,
                        "selected_option_index": native_index,
                        "selected_native_option_index": native_index,
                        "selected_rendered_index": selected.get("rendered_index"),
                        "semantic_optimal": False,
                    }
                )
                if exact_step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_raiktor_source_reviewed_choice",
                        "selected_step": exact_step,
                        "reason": raiktor_decision["reason"],
                        "active_event": event_summary,
                        "event_decision": raiktor_decision,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_raiktor_choice_unsupported",
                    "selected_step": None,
                    "required_step": exact_step,
                    "reason": f"source-reviewed option {option_number} needs {exact_step}",
                    "active_event": event_summary,
                    "event_decision": raiktor_decision,
                }
            registry_decision = (
                recommend_registered_vanilla_event_option_v1(
                    event_context,
                    played_character_id=played_character_id,
                    snapshot_option_count=active_event.get("option_count"),
                )
            )
            if registry_decision.get("status") == "recommended":
                material_postcondition = (
                    plan_registered_event_material_postcondition_v1(
                        registry_decision,
                        played_character,
                        played_character_gold=(
                            snapshot.get("played_character_gold")
                            if isinstance(snapshot, dict)
                            else None
                        ),
                        played_character_prestige=(
                            snapshot.get("played_character_prestige")
                            if isinstance(snapshot, dict)
                            else None
                        ),
                        snapshot_id=(
                            snapshot.get("snapshot_id")
                            if isinstance(snapshot, dict)
                            else None
                        ),
                        revision=(
                            snapshot.get("revision")
                            if isinstance(snapshot, dict)
                            else None
                        ),
                    )
                )
                if event_context.get("event_definition_key") == (
                    "tgp_japan_yearly_events.1190"
                ) and not (
                    isinstance(material_postcondition, dict)
                    and material_postcondition.get("status") == "ready"
                    and material_postcondition.get("metric")
                    == "played_character_prestige.raw"
                    and material_postcondition.get("expected_relation")
                    == "strictly_decreasing"
                    and isinstance(material_postcondition.get("starting_value"), int)
                    and not isinstance(
                        material_postcondition.get("starting_value"), bool
                    )
                    and material_postcondition["starting_value"] >= 7_500_000
                ):
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_registry_material_observation_blocked",
                        "selected_step": None,
                        "reason": (
                            "the source-reviewed night decision needs at least "
                            "75 same-frame prestige and an independently "
                            "verifiable prestige loss before selecting native 1"
                        ),
                        "active_event": event_summary,
                        "event_decision": {
                            **registry_decision,
                            "status": "blocked",
                            "unavailable_reason": (
                                "r0100_prestige_budget_or_observation_unavailable"
                            ),
                        },
                        "event_material_postcondition": material_postcondition,
                    }
                if event_context.get("event_definition_key") == (
                    "epidemic_events.5007"
                ) and not (
                    isinstance(material_postcondition, dict)
                    and material_postcondition.get("status") == "ready"
                    and material_postcondition.get("expected_relation")
                    == "strictly_increasing"
                ):
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_registry_material_observation_blocked",
                        "selected_step": None,
                        "reason": (
                            "the source-reviewed epidemic accusation route "
                            "needs the selected-option same-frame stress increase "
                            "indicator and played-character stress before "
                            "submitting a material-verifiable choice"
                        ),
                        "active_event": event_summary,
                        "event_decision": {
                            **registry_decision,
                            "status": "blocked",
                            "unavailable_reason": (
                                "r0092_material_stress_observation_unavailable"
                            ),
                        },
                        "event_material_postcondition": material_postcondition,
                    }
                if event_context.get("event_definition_key") == (
                    "stress_threshold_special.1001"
                ):
                    starting_stress = (
                        material_postcondition.get("starting_value")
                        if isinstance(material_postcondition, dict)
                        else None
                    )
                    if not (
                        isinstance(material_postcondition, dict)
                        and material_postcondition.get("status") == "ready"
                        and isinstance(starting_stress, int)
                        and not isinstance(starting_stress, bool)
                        and starting_stress > 0
                    ):
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "active_event_registry_material_observation_blocked",
                            "selected_step": None,
                            "reason": (
                                "the R0065 grief choice needs same-frame "
                                "positive played-character stress to verify "
                                "a material decrease after the typed option"
                            ),
                            "active_event": event_summary,
                            "event_decision": {
                                **registry_decision,
                                "status": "blocked",
                                "unavailable_reason": (
                                    "r0065_positive_stress_observation_unavailable"
                                ),
                            },
                            "required_capability": (
                                "game.state.played-character-stress-points"
                            ),
                        }
                if event_context.get("event_definition_key") == (
                    "epidemic_events.1020"
                ) and not (
                    isinstance(material_postcondition, dict)
                    and material_postcondition.get("status") == "ready"
                ):
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_registry_material_observation_blocked",
                        "selected_step": None,
                        "reason": (
                            "the source-reviewed flower choice requires same-frame "
                            "player gold before a typed option can be submitted"
                        ),
                        "active_event": event_summary,
                        "event_decision": {
                            **registry_decision,
                            "status": "blocked",
                            "unavailable_reason": (
                                "epidemic_flower_player_gold_unavailable"
                            ),
                        },
                        "required_capability": "game.state.played-character-gold",
                    }
                native_index = registry_decision.get(
                    "selected_native_option_index"
                )
                option_number = registry_decision.get(
                    "selected_option_number"
                )
                rendered_index = registry_decision.get(
                    "selected_rendered_index"
                )
                campaign_utility = registry_decision.get(
                    "campaign_utility_profile"
                )
                assert isinstance(native_index, int)
                assert isinstance(option_number, int)
                exact_step = event_option_step(option_number)
                event_summary.update(
                    {
                        "selected_option_number": option_number,
                        "selected_option_index": native_index,
                        "selected_native_option_index": native_index,
                        "selected_rendered_index": rendered_index,
                        "semantic_optimal": False,
                        "campaign_utility_ready": (
                            isinstance(campaign_utility, dict)
                        ),
                        "registry_decision": registry_decision,
                    }
                )
                if exact_step in available_steps:
                    plan = {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_registry_choice",
                        "selected_step": exact_step,
                        "reason": (
                            "the same-frame event identity, player root, "
                            "saved scopes and option projection match the "
                            "exact-build registry; choose its source-reviewed "
                            "bounded continuation"
                        ),
                        "active_event": event_summary,
                        "event_decision": registry_decision,
                    }
                    if material_postcondition is not None:
                        plan["event_material_postcondition"] = material_postcondition
                    if isinstance(campaign_utility, dict):
                        plan["event_campaign_utility"] = campaign_utility
                    return plan
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_registry_choice_unsupported",
                    "selected_step": None,
                    "required_step": exact_step,
                    "reason": (
                        "the exact-build registry selected authored option "
                        f"{option_number}/native {native_index}, but the "
                        f"backend did not advertise {exact_step}"
                    ),
                    "active_event": event_summary,
                    "event_decision": registry_decision,
                }
            if registry_decision.get("status") == "blocked":
                event_summary["registry_decision"] = registry_decision
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_registry_contract_blocked",
                    "selected_step": None,
                    "reason": (
                        "the event has an exact-build registry contract, but "
                        "the current direct projection cannot safely consume "
                        "it: "
                        f"{registry_decision.get('unavailable_reason')}"
                    ),
                    "active_event": event_summary,
                    "event_decision": registry_decision,
                }

            if not semantic_ready and len(eligible_options) == 1:
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
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "active_event_forced_presentation_choice",
                        "selected_step": exact_step,
                        "reason": (
                            "forced presentation choice: exactly one "
                            "materialized option is shown and enabled; this "
                            "is not a semantic optimum"
                        ),
                        "active_event": event_summary,
                        "event_decision": event_decision,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "active_event_forced_choice_unsupported",
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
            elif len(eligible_options) > 1:
                reason = (
                    "multiple materialized event options are shown and "
                    "enabled; an exact-build registry choice or semantic "
                    "policy is required"
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
            "war_termination_negative_reuse": war.get(
                "war_termination_negative_reuse"
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
    if battle_control_status == "identity_pending":
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_battle_identity_materialization",
                "selected_step": "life-advance",
                "reason": (
                    "the frozen paused public subject is in combat, but CK3 "
                    "has not materialized its CombatID; advance exactly one "
                    "day once, then require a non-missing full CombatID on "
                    "the next "
                    "revision"
                ),
                "battle_subject_army_id": battle_control_state.get(
                    "subject_army_id"
                ),
                "battle_identity_pending": battle_control_state.get(
                    "identity_pending"
                ),
                "next_revision_requirement": "full_combat_id",
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_identity_materialization_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": (
                "the frozen CombatID materialization boundary requires one "
                "explicit bounded day, but this backend cannot advance it"
            ),
            "battle_subject_army_id": battle_control_state.get(
                "subject_army_id"
            ),
        }
    if battle_control_status == "identity_pending_after_materialization":
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_identity_materialization_failed",
            "selected_step": None,
            "required_observation": "full-current-revision-CombatID",
            "reason": (
                "the single explicit one-day materialization was consumed, "
                "but the next frozen revision still lacks a non-missing "
                "CombatID; do not advance again"
            ),
            "battle_subject_army_id": battle_control_state.get(
                "subject_army_id"
            ),
            "battle_identity_pending": battle_control_state.get(
                "identity_pending"
            ),
            "battle_identity_materialization": battle_control_state.get(
                "prior_materialization"
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
            surrender_state = _de_jure_surrender_submission_state(
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
            if isinstance(surrender_state, dict):
                if surrender_state.get("status") == "same_day_pending":
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_surrender_response_advance",
                            "selected_step": "life-advance",
                            "war_id": war_id,
                            "decision": {
                                "policy": (
                                    "de-jure-no-safe-route-emergency-exit-v1"
                                ),
                                "outcome": "surrender",
                                "status": "submitted_pending",
                                "submission": surrender_state,
                            },
                            "reason": (
                                "the surrender was submitted on this game date; "
                                "advance once for native settlement without "
                                "repeating the terminal action"
                            ),
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_surrender_response_advance_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "war_id": war_id,
                        "reason": (
                            "a queued surrender requires one same-day advance; "
                            "the terminal action must not be repeated"
                        ),
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_surrender_postcondition_unresolved",
                    "selected_step": None,
                    "required_step": "old-WarID-disappearance",
                    "war_id": war_id,
                    "submission": surrender_state,
                    "reason": (
                        "a prior surrender ACK has not produced independent "
                        "WarID disappearance; do not repeat the terminal action"
                    ),
                    "active_wars": war_summary,
                }
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
                negative_reuse = _negative_war_termination_reuse(
                    rows,
                    snapshot,
                    active_wars=active_wars,
                    war=war,
                )
                if isinstance(negative_reuse, dict):
                    summary = next(
                        (
                            row
                            for row in war_summary
                            if row.get("war_id") == war_id
                        ),
                        None,
                    )
                    if isinstance(summary, dict):
                        # This is lease provenance only.  Historical option
                        # payloads never re-enter the current war summary.
                        summary["war_termination_negative_reuse"] = dict(
                            negative_reuse
                        )
                    continue
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
            if (
                isinstance(snapshot, dict)
                and _terminal_score_surrender_ready(snapshot, war, options)
            ):
                step = surrender_war_step(war_id)
                if step in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_terminal_score_surrender",
                        "selected_step": step,
                        "war_id": war_id,
                        "decision": {
                            "policy": "terminal-score-defeat-receipt-v1",
                            "selected_outcome": "surrender",
                            "player_relative_war_score": (
                                war.get("player_relative_war_score")
                            ),
                            "native_validator_passed": True,
                            "recipient_would_accept_now": True,
                        },
                        "reason": (
                            "the exact same-frame native termination row "
                            "proves a fully lost -100 attacker war and an "
                            "immediately accepted surrender; submit it before "
                            "CK3 auto-removes the WarID so defeat has an "
                            "explicit MCP receipt"
                        ),
                        "active_wars": war_summary,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_terminal_score_surrender_unsupported",
                    "selected_step": None,
                    "required_step": step,
                    "war_id": war_id,
                    "reason": (
                        "the exact native row proves terminal defeat, but the "
                        "surrender literal is not currently executable"
                    ),
                    "active_wars": war_summary,
                }
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
        unknown_primary_identity_defensive_wars = [
            summary
            for summary in war_summary
            if summary.get("player_side") == "defender"
            and summary.get("player_is_primary_war_leader") is None
        ]
        if unknown_primary_identity_defensive_wars:
            return {
                "policy": "one-life-turn-v1",
                "phase": "defensive_war_primary_identity_required",
                "selected_step": None,
                "required_capabilities": ["game.state.active-wars"],
                "reason": (
                    "the defensive war's primary-leader identity must be "
                    "observable before issuing further army or time commands"
                ),
                "defensive_wars": unknown_primary_identity_defensive_wars,
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

        # Exact split/merge recovery above owns its merge receipt.  The
        # generic fence is for independent consolidation merges such as the
        # R0028 pre-offensive action; applying both lifecycles would turn a
        # completed split recovery into an unresolved generic ACK.
        merge_lifecycle = (
            None
            if isinstance(split_recovery, dict)
            else _latest_merge_result_lifecycle(
                rows,
                snapshot if isinstance(snapshot, dict) else {},
            )
        )
        if (
            isinstance(merge_lifecycle, dict)
            and merge_lifecycle.get("status") != "applied"
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_merge_result_pending",
                "selected_step": None,
                "required_step": "fresh-paused-merge-postcondition",
                "reason": "the latest merge receipt lacks an independently published exact source-removal postcondition; keep the map paused and do not resubmit or advance time",
                "merge_result_lifecycle": merge_lifecycle,
                "active_wars": war_summary,
            }

        tactical_war = _stable_tactical_war(active_wars)
        tactical_war_id = (
            tactical_war.get("war_id")
            if isinstance(tactical_war, dict)
            else None
        )
        strength_balance = (
            _same_frame_army_strength_balance(snapshot, tactical_war_id)
            if isinstance(snapshot, dict)
            and isinstance(tactical_war_id, int)
            else None
        )
        strength_query_status = (
            snapshot.get("army_strengths_status")
            if isinstance(snapshot, dict)
            else None
        )
        if (
            isinstance(tactical_war_id, int)
            and route_threat_enemy_ids
            and strength_balance is None
            and strength_query_status is None
            and isinstance(snapshot, dict)
            and snapshot.get("paused") is True
            and QUERY_ARMY_STRENGTHS_STEP in available_steps
            and all(
                _army_tactical_state(army)
                not in {"combat", "retreating", "gathering"}
                for army in controlled_armies
            )
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_army_strength_query",
                "selected_step": QUERY_ARMY_STRENGTHS_STEP,
                "required_step": QUERY_ARMY_STRENGTHS_STEP,
                "reason": (
                    "read the exact current soldiers and native AI base "
                    "power for every published army on both war sides before "
                    "committing or advancing an offensive route"
                ),
                "war_id": tactical_war_id,
                "army_strength_scope": {
                    "player_army_ids": sorted(
                        int(army["army_id"])
                        for army in controlled_armies
                        if _native_int(army.get("army_id")) is not None
                    ),
                    "enemy_army_ids": list(route_threat_enemy_ids),
                },
                "active_wars": war_summary,
            }
        siege_relief = _primary_defender_siege_relief_assessment(
            snapshot if isinstance(snapshot, dict) else {},
            commands=rows,
            active_wars=active_wars,
            controlled_armies=controlled_armies,
            pursuit_army=(
                pursuit_army if isinstance(pursuit_army, dict) else None
            ),
            battle_control_state=battle_control_state,
        )
        if siege_relief.get("status") == "observation_unavailable":
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_defender_siege_relief_observation_blocked",
                "selected_step": None,
                "required_observation": siege_relief.get(
                    "required_observation"
                ),
                "reason": (
                    "an enemy siege is visible in a primary defensive war, "
                    "but the same-frame army assignment, hostile position, "
                    "route, or strength scope is incomplete; do not consume "
                    "another stationary hold slice"
                ),
                "siege_relief": siege_relief,
                "active_wars": war_summary,
            }
        if siege_relief.get("status") == "ready":
            relief_war_id = _native_int(siege_relief.get("war_id"))
            relief_war = next(
                (
                    war
                    for war in active_wars
                    if _native_int(war.get("war_id")) == relief_war_id
                ),
                None,
            )
            if isinstance(relief_war, dict) and relief_war_id is not None:
                tactical_war = relief_war
                tactical_war_id = relief_war_id
                strength_balance = _same_frame_army_strength_balance(
                    snapshot if isinstance(snapshot, dict) else {},
                    tactical_war_id,
                )
        if isinstance(strength_balance, dict):
            for summary in war_summary:
                if summary.get("war_id") == tactical_war_id:
                    summary["army_strength_balance"] = dict(
                        strength_balance
                    )
                    break
        consolidation = (
            _preoffensive_army_consolidation(
                snapshot,
                controlled_armies=controlled_armies,
                war_id=tactical_war_id,
            )
            if isinstance(snapshot, dict)
            and isinstance(tactical_war_id, int)
            and isinstance(strength_balance, dict)
            else None
        )
        if isinstance(consolidation, dict):
            consolidation_step = consolidation["step"]
            if (
                isinstance(consolidation_step, str)
                and consolidation_step in available_steps
            ):
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_preoffensive_army_consolidation",
                    "selected_step": consolidation_step,
                    "reason": (
                        "the exact post-declaration strength query shows "
                        "multiple same-province idle player stacks; merge "
                        "the strongest stack with one sibling before "
                        "choosing an offensive route"
                    ),
                    "war_id": tactical_war_id,
                    "consolidation": consolidation,
                    "army_strength_balance": strength_balance,
                    "active_wars": war_summary,
                }
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
        arrived_relief_target = (
            _native_int(siege_relief.get("target_province_id"))
            if siege_relief.get("status") == "arrived_sieging"
            else None
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
                if combat_id is None or combat_id == -1 or subject is None:
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
                and not active_assaults
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
                        "until the native hold-invalidation sentinel observes "
                        "an army, roster, route, contact, retreat, terminal, "
                        "native-pause, or absolute-bound change"
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
        if arrived_relief_target is not None:
            # The accepted relief move owns this army through arrival.  Keep
            # its observed siege in the ordinary siege/assault tree even
            # when a concurrent defensive war publishes another siege.
            completed_objectives.discard(arrived_relief_target)
            siege_objective_province_ids = [
                arrived_relief_target,
                *(
                    province_id
                    for province_id in siege_objective_province_ids
                    if province_id != arrived_relief_target
                ),
            ]
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
            and (
                current_province_id in siege_objective_province_ids
                or siege_relief.get("status") == "arrived_sieging"
            )
            and "life-advance" in available_steps
        ):
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_siege_progress",
                "selected_step": "life-advance",
                "reason": "the exact paused state confirms a player siege; advance one seven-day progress slice",
                "siege_state": exact_siege_status,
                **(
                    {"siege_relief": siege_relief}
                    if arrived_relief_target is not None
                    else {}
                ),
                "active_wars": war_summary,
            }
        if (
            army_state == "sieging"
            and observed_route_target is None
            and not stationary_threats
            and exact_siege_status is None
            and (
                current_province_id in siege_objective_province_ids
                or siege_relief.get("status") == "arrived_sieging"
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
                **(
                    {"siege_relief": siege_relief}
                    if arrived_relief_target is not None
                    else {}
                ),
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
                if passive_route_audit["status"] in {"safe", "unsafe"}:
                    if not route_contact_scope_supported:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": (
                                "native_war_active_route_contact_horizon_unsupported"
                            ),
                            "selected_step": None,
                            "required_observation": (
                                "fresh-full-hostile-route-contact-horizon"
                            ),
                            "reason": (
                                "an already committed route may advance only "
                                "from a fresh same-frame one-day proof over "
                                "the complete hostile scope; keep time paused"
                            ),
                            "route_audit": passive_route_audit,
                            "move_intent": observed_intent,
                            "active_wars": war_summary,
                        }
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
                        failed_query = (
                            _current_frame_route_contact_query_failure(
                                rows,
                                snapshot,
                                horizon_step,
                            )
                        )
                        if failed_query is not None:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_active_route_contact_horizon_unavailable"
                                ),
                                "selected_step": None,
                                "required_step": horizon_step,
                                "reason": (
                                    "the fresh full-hostile contact query "
                                    "failed in this unchanged frame; keep "
                                    "time paused without resubmitting"
                                ),
                                "route_audit": passive_route_audit,
                                "contact_query_attempt": failed_query,
                                "move_intent": observed_intent,
                                "active_wars": war_summary,
                            }
                        elif horizon_step in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_route_contact_horizon",
                                "selected_step": horizon_step,
                                "reason": "read the exact one-day native arrival/contact horizon over the full hostile scope before advancing the committed route",
                                "route_audit": passive_route_audit,
                                "move_intent": observed_intent,
                                "active_wars": war_summary,
                            }
                        elif horizon_step not in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_route_contact_horizon_unsupported",
                                "selected_step": None,
                                "required_step": horizon_step,
                                "reason": "the committed route requires a fresh same-frame full-hostile one-day contact horizon",
                                "route_audit": passive_route_audit,
                                "move_intent": observed_intent,
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
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_active_route_contact_blocked"
                                ),
                                "selected_step": None,
                                "required_observation": (
                                    "qualified-combat-permission-or-safe-route"
                                ),
                                "reason": (
                                    "a sibling's fresh horizon predicts contact; "
                                    "one contact-free subject proof cannot "
                                    "authorize global time without a qualified "
                                    "combat result"
                                ),
                                "route_audit": passive_route_audit,
                                "stationary_contact_horizons": (
                                    stationary_contact_horizons
                                ),
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
                                "reason": "the fresh same-frame native timeline proves the committed route and every other controllable army contact-free for at most the next day",
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
                    passive_route_audit = {
                        **passive_route_audit,
                        "contact_horizon": contact_horizon,
                        "contact_policy": (
                            "blocked_without_qualified_combat_permission"
                        ),
                    }
                    blocked_province_ids.add(observed_route_target)
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
        capital_regroup_intent = (
            _capital_regroup_intent(
                rows,
                snapshot,
                army_id=army_id,
                war_id=tactical_war_id,
            )
            if (
                isinstance(snapshot, dict)
                and isinstance(army_id, int)
                and isinstance(tactical_war_id, int)
                and not stationary_threats
                and not unsafe_armies
            )
            else None
        )
        if capital_regroup_intent is not None:
            if "life-advance" in available_steps:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_capital_regroup_progress",
                    "selected_step": "life-advance",
                    "reason": "the army independently arrived at the same-campaign capital regroup target; hold one bounded observation day before reconsidering the exhausted siege",
                    "regroup_intent": capital_regroup_intent,
                    "active_wars": war_summary,
                }
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_capital_regroup_progress_unsupported",
                "selected_step": None,
                "required_step": "life-advance",
                "reason": "the bounded capital regroup intent is active but the backend cannot advance its observation day",
                "regroup_intent": capital_regroup_intent,
                "active_wars": war_summary,
            }
        objective_kind = "pursuit"
        preview_selected_target: int | None = None
        capital_regroup_target: int | None = None
        selected_route_audit: dict[str, object] | None = None
        route_preview_required = bool(
            move_route_preview_supported
        )
        route_exact_candidates = [
            province_id
            for province_id in exact_objective_province_ids
            if province_id in siege_objective_province_ids
        ]
        route_candidate_source = "war_objective_province"
        if siege_relief.get("status") == "ready":
            relief_target = _native_int(
                siege_relief.get("target_province_id")
            )
            if relief_target is not None:
                route_exact_candidates = [relief_target]
                route_candidate_source = "enemy_siege_relief"
        defender_safe_objective_input = (
            _primary_defender_capital_hold_input(
                snapshot if isinstance(snapshot, dict) else {},
                active_wars=active_wars,
                controlled_armies=controlled_armies,
                tactical_war=(
                    tactical_war if isinstance(tactical_war, dict) else None
                ),
                pursuit_army=(
                    pursuit_army if isinstance(pursuit_army, dict) else None
                ),
                exact_objective_province_ids=exact_objective_province_ids,
                termination_by_war_id=termination_by_war_id,
                war_summary=war_summary,
                unsafe_armies=unsafe_armies,
                active_assaults=active_assaults,
                allow_observable_enemy_routes=True,
                allow_defeat_score_contact=True,
            )
            if stationary_threats and not route_exact_candidates
            else None
        )
        safe_objective_rally_binding = (
            _primary_defender_native_rally_hold_binding(
                rows,
                snapshot if isinstance(snapshot, dict) else {},
                war_id=(
                    tactical_war_id
                    if isinstance(tactical_war_id, int)
                    else None
                ),
                army_id=(
                    pursuit_army.get("army_id")
                    if isinstance(pursuit_army, dict)
                    else None
                ),
                current_province_id=(
                    current_province_id
                    if isinstance(current_province_id, int)
                    else None
                ),
            )
            if defender_safe_objective_input is not None
            else None
        )
        if (
            defender_safe_objective_input is not None
            and safe_objective_rally_binding is not None
        ):
            campaign_root = _same_frame_campaign_root_context(
                rows,
                snapshot if isinstance(snapshot, dict) else None,
            )
            county_capitals = (
                _complete_player_held_county_capital_province_ids(
                    campaign_root
                )
                if isinstance(campaign_root, dict)
                else None
            )
            if county_capitals is None:
                root_step = "query-campaign-root-context-v1"
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_safe_objective_context",
                    "selected_step": (
                        root_step if root_step in available_steps else None
                    ),
                    "required_step": root_step,
                    "reason": "the threatened primary defender requires a complete same-frame directly-held county-capital set before claiming that no alternate objective exists",
                    "defensive_hold": defender_safe_objective_input,
                    "native_rally_hold_binding": safe_objective_rally_binding,
                    "route_rejections": stationary_threats,
                    "active_wars": war_summary,
                }
            route_exact_candidates = [
                province_id
                for province_id in county_capitals
                if province_id != current_province_id
            ]
            route_candidate_source = "player_held_county_capital"
            if not route_exact_candidates:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_no_alternate_player_held_county",
                    "selected_step": None,
                    "required_observation": "broader-safe-war-objective-candidates",
                    "reason": "the complete directly-held county-capital set contains no alternate Province; broader native objective candidates remain unobserved",
                    "candidate_province_ids": county_capitals,
                    "defensive_hold": defender_safe_objective_input,
                    "native_rally_hold_binding": safe_objective_rally_binding,
                    "route_rejections": stationary_threats,
                    "active_wars": war_summary,
                }
            if not route_preview_required:
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_safe_objective_route_preview_unsupported",
                    "selected_step": None,
                    "required_observation": "fresh-native-route-preview",
                    "reason": "directly-held county fallback candidates are observed, but none may be selected without the native route preview",
                    "candidate_province_ids": route_exact_candidates,
                    "defensive_hold": defender_safe_objective_input,
                    "native_rally_hold_binding": safe_objective_rally_binding,
                    "route_rejections": stationary_threats,
                    "active_wars": war_summary,
                }
        if (
            route_preview_required
            and isinstance(army_id, int)
            and isinstance(current_province_id, int)
            and route_exact_candidates
        ):
            route_rejections: list[dict[str, object]] = []
            stationary_contact_transition: dict[str, object] | None = None
            # The exact set is already ranked by observable siege quality.
            # Stop at its first fully safe route instead of globally scanning
            # every objective for the shortest path.  This is not a fixed cap:
            # rejected candidates still fall through to the rest of the set.
            for objective_rank, province_id in enumerate(route_exact_candidates):
                if province_id == current_province_id:
                    if isinstance(exact_siege_rejection, dict):
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": "current_exact_siege_rejected",
                                "siege_status": exact_siege_rejection.get(
                                    "status"
                                ),
                            }
                        )
                        continue
                    if active_route_unsafe:
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": "cannot_replace_unsafe_active_route",
                            }
                        )
                        continue
                    if stationary_threats:
                        if route_contact_scope_supported:
                            stationary_contact_horizon = (
                                _fresh_route_contact_horizon(
                                    rows,
                                    snapshot,
                                    army_id=army_id,
                                    origin_province_id=current_province_id,
                                    target_province_id=province_id,
                                    hostile_army_ids=route_threat_enemy_ids,
                                    route_province_ids=[],
                                )
                            )
                            stationary_query_step = (
                                query_route_contact_horizon_step(
                                    army_id,
                                    province_id,
                                    route_threat_enemy_ids,
                                )
                            )
                            if stationary_contact_horizon is None:
                                failed_query = (
                                    _current_frame_route_contact_query_failure(
                                        rows,
                                        snapshot,
                                        stationary_query_step,
                                    )
                                )
                                if failed_query is not None:
                                    route_rejections.append(
                                        {
                                            "target_province_id": province_id,
                                            "status": "contact_timeline_unavailable",
                                            "conflicts": stationary_threats,
                                            "contact_query_attempt": failed_query,
                                        }
                                    )
                                    blocked_province_ids.add(province_id)
                                    continue
                                if stationary_query_step in available_steps:
                                    return {
                                        "policy": "one-life-turn-v1",
                                        "phase": "native_war_stationary_contact_horizon",
                                        "selected_step": stationary_query_step,
                                        "reason": "resolve geometric convergence on the occupied exact objective with the stationary subject and hostile native arrival timelines",
                                        "route_audit": {
                                            "status": "stationary_geometric_threat",
                                            "target_province_id": province_id,
                                            "conflicts": stationary_threats,
                                        },
                                        "route_rejections": route_rejections,
                                        "active_wars": war_summary,
                                    }
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": "native_war_stationary_contact_horizon_unsupported",
                                    "selected_step": None,
                                    "required_step": stationary_query_step,
                                    "reason": "the occupied exact objective requires a fresh stationary one-day contact horizon",
                                    "route_rejections": route_rejections,
                                    "active_wars": war_summary,
                                }
                            stationary_advance_step = (
                                advance_route_contact_horizon_step(
                                    army_id,
                                    province_id,
                                    route_threat_enemy_ids,
                                )
                            )
                            stationary_contact_free = (
                                stationary_contact_horizon.get(
                                    "one_day_contact_free"
                                )
                                is True
                            )
                            stationary_contact_unavoidable = (
                                unavoidable_current_province_contact_in_horizon(
                                    stationary_contact_horizon
                                )
                            )
                            if stationary_contact_free:
                                if stationary_advance_step in available_steps:
                                    return {
                                        "policy": "one-life-turn-v1",
                                        "phase": "native_war_stationary_contact_horizon_progress",
                                        "selected_step": stationary_advance_step,
                                        "reason": "the exact stationary timeline proves the occupied objective contact-free for the next day",
                                        "route_audit": {
                                            "status": "safe_one_day_stationary_contact_horizon",
                                            "target_province_id": province_id,
                                            "contact_horizon": stationary_contact_horizon,
                                        },
                                        "route_rejections": route_rejections,
                                        "active_wars": war_summary,
                                    }
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": "native_war_stationary_contact_horizon_progress_unsupported",
                                    "selected_step": None,
                                    "required_step": stationary_advance_step,
                                    "reason": "the fresh stationary horizon is actionable, but the proof-bound one-day advance is unavailable",
                                    "route_rejections": route_rejections,
                                    "active_wars": war_summary,
                                }
                            if stationary_contact_unavoidable:
                                # Do not accept contact while a later-ranked
                                # exact objective may still offer a safe exit.
                                # Keep the proof and finish the candidate
                                # sweep; only the all-alternatives-rejected
                                # branch may choose this hold transition.
                                stationary_contact_transition = {
                                    "advance_step": stationary_advance_step,
                                    "target_province_id": province_id,
                                    "contact_horizon": stationary_contact_horizon,
                                }
                        route_rejections.append(
                            {
                                "target_province_id": province_id,
                                "status": "unsafe",
                                "conflicts": stationary_threats,
                                **(
                                    {
                                        "contact_horizon": (
                                            stationary_contact_horizon
                                        )
                                    }
                                    if route_contact_scope_supported
                                    and isinstance(
                                        stationary_contact_horizon, dict
                                    )
                                    else {}
                                ),
                            }
                        )
                        continue
                    preview_selected_target = province_id
                    selected_route_audit = {
                        "status": "arrived",
                        "target_province_id": province_id,
                    }
                    break
                if province_id in blocked_province_ids:
                    route_rejections.append(
                        {"target_province_id": province_id, "status": "blocked"}
                    )
                    continue
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
                        failed_query = (
                            _current_frame_route_contact_query_failure(
                                rows,
                                snapshot,
                                horizon_step,
                            )
                        )
                        if failed_query is not None:
                            unavailable_audit = {
                                **audit,
                                "status": "contact_timeline_unavailable",
                                "contact_query_attempt": failed_query,
                            }
                            route_rejections.append(unavailable_audit)
                            blocked_province_ids.add(province_id)
                            continue
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
                        enemy_current_on_route = any(
                            conflict.get("kind") == "enemy_current_on_route"
                            for conflict in audit.get("conflicts", [])
                        )
                        if (
                            isinstance(strength_balance, dict)
                            and strength_balance.get(
                                "hostile_operational_overmatch"
                            )
                            is True
                            and (
                                route_candidate_source
                                == "player_held_county_capital"
                                or enemy_current_on_route
                            )
                        ):
                            audit = {
                                **audit,
                                "contact_horizon": contact_horizon,
                                "one_day_contact_horizon_rejected": (
                                    "hostile_operational_overmatch_"
                                    "player_held_county_fallback"
                                    if route_candidate_source
                                    == "player_held_county_capital"
                                    else "hostile_operational_overmatch_"
                                    "enemy_current_on_exact_route"
                                ),
                            }
                        else:
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
                        "policy": (
                            "first_safe_player_held_county_capital"
                            if route_candidate_source
                            == "player_held_county_capital"
                            else "first_safe_ranked_exact_objective"
                        ),
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
                if route_candidate_source == "player_held_county_capital":
                    geometrically_unsafe_target_ids = {
                        _native_int(rejection.get("target_province_id"))
                        for rejection in route_rejections
                        if isinstance(rejection, dict)
                        and rejection.get("status") == "unsafe"
                    }
                    capital_province_id = (
                        _native_int(campaign_root.get("capital_province_id"))
                        if isinstance(campaign_root, dict)
                        else None
                    )
                    native_rally_hold_ready = bool(
                        defender_safe_objective_input is not None
                        and safe_objective_rally_binding is not None
                        and isinstance(strength_balance, dict)
                        and strength_balance.get(
                            "hostile_operational_overmatch"
                        )
                        is True
                        and capital_province_id is not None
                        and capital_province_id != current_province_id
                        and len(route_rejections)
                        == len(route_exact_candidates)
                        and geometrically_unsafe_target_ids
                        == set(route_exact_candidates)
                    )
                    if native_rally_hold_ready:
                        defensive_hold = {
                            **defender_safe_objective_input,
                            "capital_province_id": capital_province_id,
                            "campaign_root_snapshot_revision": (
                                campaign_root.get("snapshot_revision")
                            ),
                            "campaign_root_date_raw": campaign_root.get(
                                "date_raw"
                            ),
                        }
                        contact_query_step = (
                            query_route_contact_horizon_step(
                                int(defensive_hold["army_id"]),
                                int(current_province_id),
                                route_threat_enemy_ids,
                            )
                        )
                        if not route_contact_scope_supported:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_defender_native_rally_"
                                    "contact_horizon_unsupported"
                                ),
                                "selected_step": None,
                                "required_step": contact_query_step,
                                "reason": "the threatened native-rally hold requires the existing complete-scope stationary contact-horizon capability",
                                "defensive_hold": defensive_hold,
                                "native_rally_hold_binding": (
                                    safe_objective_rally_binding
                                ),
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        contact_horizon = _fresh_route_contact_horizon(
                            rows,
                            snapshot,
                            army_id=int(defensive_hold["army_id"]),
                            origin_province_id=int(current_province_id),
                            target_province_id=int(current_province_id),
                            hostile_army_ids=route_threat_enemy_ids,
                            route_province_ids=[],
                        )
                        if contact_horizon is None:
                            failed_query = (
                                _current_frame_route_contact_query_failure(
                                    rows,
                                    snapshot,
                                    contact_query_step,
                                )
                            )
                            if failed_query is not None:
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": (
                                        "native_war_defender_native_rally_"
                                        "contact_horizon_unavailable"
                                    ),
                                    "selected_step": None,
                                    "required_observation": (
                                        "fresh-available-stationary-"
                                        "contact-horizon"
                                    ),
                                    "reason": "the current-frame stationary native-rally contact query failed or returned no usable exact timeline; keep the map paused",
                                    "defensive_hold": defensive_hold,
                                    "native_rally_hold_binding": (
                                        safe_objective_rally_binding
                                    ),
                                    "contact_query_attempt": failed_query,
                                    "route_rejections": route_rejections,
                                    "active_wars": war_summary,
                                }
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_defender_native_rally_"
                                    "contact_horizon"
                                ),
                                "selected_step": (
                                    contact_query_step
                                    if contact_query_step in available_steps
                                    else None
                                ),
                                "required_step": contact_query_step,
                                "reason": "prove the exact native-rally Province contact-free or unavoidable for one day before holding under hostile overmatch",
                                "defensive_hold": defensive_hold,
                                "native_rally_hold_binding": (
                                    safe_objective_rally_binding
                                ),
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        contact_advance_step = (
                            advance_route_contact_horizon_step(
                                int(defensive_hold["army_id"]),
                                int(current_province_id),
                                route_threat_enemy_ids,
                            )
                        )
                        if contact_horizon.get("one_day_contact_free") is True:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_defender_native_rally_"
                                    "contact_horizon_progress"
                                ),
                                "selected_step": (
                                    contact_advance_step
                                    if contact_advance_step in available_steps
                                    else None
                                ),
                                "required_step": contact_advance_step,
                                "reason": "the fresh stationary timeline proves the exact native-rally Province contact-free for one day",
                                "defensive_hold": defensive_hold,
                                "native_rally_hold_binding": (
                                    safe_objective_rally_binding
                                ),
                                "contact_horizon": contact_horizon,
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        if unavoidable_current_province_contact_in_horizon(
                            contact_horizon
                        ):
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_defender_native_rally_"
                                    "contact_transition"
                                ),
                                "selected_step": (
                                    contact_advance_step
                                    if contact_advance_step in available_steps
                                    else None
                                ),
                                "required_step": contact_advance_step,
                                "reason": "the exact native-rally hold has an unavoidable current-province contact within the proof-bound day",
                                "defensive_hold": defensive_hold,
                                "native_rally_hold_binding": (
                                    safe_objective_rally_binding
                                ),
                                "contact_horizon": contact_horizon,
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": (
                                "native_war_defender_native_rally_"
                                "contact_horizon_blocked"
                            ),
                            "selected_step": None,
                            "required_observation": (
                                "contact-free-or-unavoidable-current-"
                                "province-stationary-horizon"
                            ),
                            "reason": "the fresh stationary native-rally horizon is neither contact-free nor an exact unavoidable current-province transition",
                            "defensive_hold": defensive_hold,
                            "native_rally_hold_binding": (
                                safe_objective_rally_binding
                            ),
                            "contact_horizon": contact_horizon,
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_no_safe_player_held_county_route",
                        "selected_step": None,
                        "required_observation": "broader-safe-war-objective-candidates",
                        "reason": "every observed directly-held county-capital fallback route is blocked or unsafe; keep the map paused until broader native objective candidates are observable",
                        "candidate_province_ids": route_exact_candidates,
                        "native_rally_hold_binding": (
                            safe_objective_rally_binding
                        ),
                        "route_rejections": route_rejections,
                        "active_wars": war_summary,
                    }
                if isinstance(stationary_contact_transition, dict):
                    stationary_advance_step = stationary_contact_transition.get(
                        "advance_step"
                    )
                    stationary_target = stationary_contact_transition.get(
                        "target_province_id"
                    )
                    stationary_horizon = stationary_contact_transition.get(
                        "contact_horizon"
                    )
                    if (
                        isinstance(stationary_advance_step, str)
                        and stationary_advance_step in available_steps
                    ):
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_unavoidable_contact_transition",
                            "selected_step": stationary_advance_step,
                            "reason": "every alternate exact objective route was rejected; hold the occupied objective for one proof-bound day and require an observed contact transition",
                            "route_audit": {
                                "status": "stationary_current_province_contact",
                                "target_province_id": stationary_target,
                                "contact_horizon": stationary_horizon,
                            },
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_unavoidable_contact_transition_unsupported",
                        "selected_step": None,
                        "required_step": stationary_advance_step,
                        "reason": "every alternate exact objective route was rejected and the stationary contact proof is fresh, but no proof-bound one-day transition is available",
                        "route_rejections": route_rejections,
                        "active_wars": war_summary,
                    }
                white_peace_response = (
                    _white_peace_no_safe_route_response_plan(
                        rows,
                        war_id=tactical_war_id,
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
                        available_steps=available_steps,
                        active_war_summary=war_summary,
                        route_rejections=route_rejections,
                    )
                    if isinstance(tactical_war_id, int)
                    else None
                )
                if white_peace_response is not None:
                    return white_peace_response
                emergency_exit = (
                    _de_jure_no_safe_route_exit_plan(
                        snapshot,
                        active_wars=active_wars,
                        termination_by_war_id=termination_by_war_id,
                        available_steps=available_steps,
                        active_war_summary=war_summary,
                        route_rejections=route_rejections,
                    )
                    if isinstance(snapshot, dict)
                    else None
                )
                if emergency_exit is not None:
                    return emergency_exit
                capital_regroup_ready = _capital_regroup_input_ready(
                    snapshot if isinstance(snapshot, dict) else {},
                    active_wars=active_wars,
                    controlled_armies=controlled_armies,
                    tactical_war=(
                        tactical_war
                        if isinstance(tactical_war, dict)
                        else None
                    ),
                    current_province_id=current_province_id,
                    exact_objective_province_ids=(
                        exact_objective_province_ids
                    ),
                    exact_siege_rejection=(
                        exact_siege_rejection
                        if isinstance(exact_siege_rejection, dict)
                        else None
                    ),
                )
                capital_hold_ready = _attacker_capital_hold_input_ready(
                    snapshot if isinstance(snapshot, dict) else {},
                    active_wars=active_wars,
                    controlled_armies=controlled_armies,
                    tactical_war=(
                        tactical_war
                        if isinstance(tactical_war, dict)
                        else None
                    ),
                    current_province_id=current_province_id,
                    exact_objective_province_ids=(
                        exact_objective_province_ids
                    ),
                    route_rejections=route_rejections,
                )
                coalition_regroup_ready = (
                    _outnumbered_attacker_regroup_input_ready(
                        snapshot if isinstance(snapshot, dict) else {},
                        active_wars=active_wars,
                        controlled_armies=controlled_armies,
                        tactical_war=(
                            tactical_war
                            if isinstance(tactical_war, dict)
                            else None
                        ),
                        current_province_id=current_province_id,
                        route_rejections=route_rejections,
                        strength_balance=(
                            strength_balance
                            if isinstance(strength_balance, dict)
                            else None
                        ),
                    )
                )
                defender_regroup_ready = (
                    _outnumbered_primary_defender_regroup_input_ready(
                        snapshot if isinstance(snapshot, dict) else {},
                        active_wars=active_wars,
                        controlled_armies=controlled_armies,
                        tactical_war=(
                            tactical_war
                            if isinstance(tactical_war, dict)
                            else None
                        ),
                        current_province_id=current_province_id,
                        exact_objective_province_ids=route_exact_candidates,
                        route_rejections=route_rejections,
                        strength_balance=(
                            strength_balance
                            if isinstance(strength_balance, dict)
                            else None
                        ),
                        active_route_unsafe=active_route_unsafe,
                    )
                )
                if (
                    capital_regroup_ready
                    or capital_hold_ready
                    or coalition_regroup_ready
                    or defender_regroup_ready
                ):
                    campaign_root = _same_frame_campaign_root_context(
                        rows,
                        snapshot if isinstance(snapshot, dict) else None,
                    )
                    if campaign_root is None:
                        root_step = "query-campaign-root-context-v1"
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_capital_regroup_context",
                            "selected_step": (
                                root_step
                                if root_step in available_steps
                                else None
                            ),
                            "required_step": root_step,
                            "reason": "the exhausted exact siege may retreat only to a fresh same-frame campaign-root capital",
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    capital_province_id = _native_int(
                        campaign_root.get("capital_province_id")
                    )
                    if defender_regroup_ready and capital_province_id not in (
                        _complete_player_held_county_capital_province_ids(
                            campaign_root
                        )
                        or []
                    ):
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_defender_capital_regroup_ownership_blocked",
                            "selected_step": None,
                            "required_observation": "directly-held-capital-county",
                            "reason": "the primary defender's same-frame capital is not confirmed as a directly held county capital",
                            "capital_province_id": capital_province_id,
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    if (
                        capital_province_id == current_province_id
                        and (
                            capital_regroup_ready
                            or capital_hold_ready
                            or coalition_regroup_ready
                        )
                    ):
                        if "life-advance" in available_steps:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": (
                                    "native_war_capital_regroup_hold_progress"
                                ),
                                "selected_step": "life-advance",
                                "reason": (
                                    "every exact offensive route is unsafe, "
                                    "but the attacker is already at "
                                    "its fresh same-frame capital; hold there "
                                    "for one bounded slice and re-query the "
                                    "war termination and route state"
                                ),
                                "capital_province_id": capital_province_id,
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": (
                                "native_war_capital_regroup_hold_unsupported"
                            ),
                            "selected_step": None,
                            "required_step": "life-advance",
                            "reason": (
                                "the exhausted attacker is already holding "
                                "its fresh same-frame capital, but the backend "
                                "cannot execute a bounded observation slice"
                            ),
                            "capital_province_id": capital_province_id,
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    if (
                        (
                            capital_regroup_ready
                            or coalition_regroup_ready
                            or defender_regroup_ready
                        )
                        and
                        capital_province_id is not None
                        and capital_province_id != current_province_id
                    ):
                        preview = _fresh_move_route_preview(
                            rows,
                            army_id=army_id,
                            origin_province_id=current_province_id,
                            target_province_id=capital_province_id,
                            date_raw=_native_int(snapshot.get("date_raw")),
                        )
                        preview_step = preview_move_army_step(
                            army_id, capital_province_id
                        )
                        if preview is None:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_capital_regroup_preview",
                                "selected_step": (
                                    preview_step
                                    if preview_step in available_steps
                                    else None
                                ),
                                "required_step": preview_step,
                                "reason": (
                                    "preview the same-frame capital regroup "
                                    "route before leaving the unsafe offensive "
                                    "route"
                                ),
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        if preview.get("status") == "deferred":
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_capital_regroup_blocked",
                                "selected_step": None,
                                "required_step": "fresh-safe-capital-regroup-route",
                                "reason": "the exact capital regroup preview is deferred; do not advance or submit an unconfirmed retreat",
                                "route_preview": preview,
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        regroup_audit = _audit_war_route(
                            preview.get("route_province_ids"),
                            origin_province_id=current_province_id,
                            target_province_id=capital_province_id,
                            enemies=route_threat_enemies,
                        )
                        if defender_regroup_ready and not route_contact_scope_supported:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_capital_regroup_contact_horizon_unsupported",
                                "selected_step": None,
                                "required_step": "complete-scope-route-contact-horizon",
                                "reason": "the primary defender cannot leave an unsafe route without a complete hostile-scope contact horizon for the capital route",
                                "route_preview": preview,
                                "route_audit": regroup_audit,
                                "route_rejections": route_rejections,
                                "active_wars": war_summary,
                            }
                        if (
                            (
                                regroup_audit.get("status") == "unsafe"
                                or defender_regroup_ready
                            )
                            and route_contact_scope_supported
                        ):
                            regroup_horizon = _fresh_route_contact_horizon(
                                rows,
                                snapshot,
                                army_id=army_id,
                                origin_province_id=current_province_id,
                                target_province_id=capital_province_id,
                                hostile_army_ids=route_threat_enemy_ids,
                                route_province_ids=preview.get(
                                    "route_province_ids"
                                ),
                            )
                            horizon_step = query_route_contact_horizon_step(
                                army_id,
                                capital_province_id,
                                route_threat_enemy_ids,
                            )
                            if regroup_horizon is None:
                                failed_query = (
                                    _current_frame_route_contact_query_failure(
                                        rows,
                                        snapshot,
                                        horizon_step,
                                    )
                                )
                                if failed_query is not None:
                                    regroup_audit = {
                                        **regroup_audit,
                                        "status": (
                                            "contact_timeline_unavailable"
                                        ),
                                        "contact_query_attempt": failed_query,
                                    }
                                else:
                                    return {
                                        "policy": "one-life-turn-v1",
                                        "phase": "native_war_capital_regroup_contact_horizon",
                                        "selected_step": (
                                            horizon_step
                                            if horizon_step in available_steps
                                            else None
                                        ),
                                        "required_step": horizon_step,
                                        "reason": "the capital regroup route intersects hostile routing and requires a fresh exact contact horizon",
                                        "route_preview": preview,
                                        "route_audit": regroup_audit,
                                        "route_rejections": route_rejections,
                                        "active_wars": war_summary,
                                    }
                            if (
                                isinstance(regroup_horizon, dict)
                                and
                                regroup_horizon.get("one_day_contact_free")
                                is True
                            ):
                                regroup_audit = {
                                    **regroup_audit,
                                    "status": (
                                        "safe_one_day_contact_horizon"
                                    ),
                                    "contact_horizon": regroup_horizon,
                                }
                            elif defender_regroup_ready and isinstance(
                                regroup_horizon, dict
                            ):
                                regroup_audit = {
                                    **regroup_audit,
                                    "status": "contact_timeline_unsafe",
                                    "contact_horizon": regroup_horizon,
                                }
                        rollback_failure = _matching_rollback_war_failure(
                            snapshot,
                            war_id=tactical_war_id,
                            army_id=army_id,
                            origin_province_id=current_province_id,
                            target_province_id=capital_province_id,
                            route_province_ids=regroup_audit.get(
                                "route_province_ids"
                            ),
                        )
                        if (
                            regroup_audit.get("status")
                            in {"safe", "safe_one_day_contact_horizon"}
                            and rollback_failure is None
                        ):
                            preview_selected_target = capital_province_id
                            capital_regroup_target = capital_province_id
                            selected_route_audit = {
                                **regroup_audit,
                                "selection": {
                                    "policy": (
                                        "outnumbered_primary_defender_capital_regroup"
                                        if defender_regroup_ready
                                        else (
                                            "outnumbered_coalition_capital_regroup"
                                            if coalition_regroup_ready
                                            else "insufficient_siege_capital_regroup"
                                        )
                                    ),
                                    "evaluated_enemy_count": len(
                                        route_threat_enemy_ids
                                    ),
                                },
                            }
                        else:
                            route_rejections.append(
                                {
                                    **regroup_audit,
                                    **(
                                        {"failure": rollback_failure}
                                        if rollback_failure is not None
                                        else {}
                                    ),
                                }
                            )
                if preview_selected_target is None:
                    enemy_current_province_ids = {
                        _native_int(enemy.get("current_province_id"))
                        for enemy in route_threat_enemies
                        if _native_int(enemy.get("current_province_id"))
                        is not None
                    }
                    defensive_hold_ready = bool(
                        isinstance(strength_balance, dict)
                        and strength_balance.get(
                            "hostile_operational_overmatch"
                        )
                        is True
                        and isinstance(pursuit_army, dict)
                        and _army_tactical_state(pursuit_army) == "regular"
                        and pursuit_army.get("in_combat") is not True
                        and pursuit_army.get("retreating") is not True
                        and pursuit_army.get("move_target_province_id")
                        is None
                        and isinstance(
                            pursuit_army.get("route_province_ids"), list
                        )
                        and not pursuit_army["route_province_ids"]
                        and isinstance(current_province_id, int)
                        and current_province_id
                        not in enemy_current_province_ids
                        and not stationary_threats
                        and not unsafe_armies
                    )
                    if defensive_hold_ready and "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_no_safe_route_defensive_hold_progress",
                            "selected_step": "life-advance",
                            "reason": "all exact offensive and capital routes are unsafe under hostile operational overmatch; hold the current uncontested Province for one bounded day and re-query every route and army strength",
                            "route_rejections": route_rejections,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_no_safe_exact_route",
                        "selected_step": None,
                        "required_step": "safe-exact-war-route",
                        "reason": "every remaining exact objective route and any eligible capital regroup route is blocked or unsafe",
                        "route_rejections": route_rejections,
                        "active_wars": war_summary,
                    }
        if (
            active_route_unsafe
            and preview_selected_target is None
        ):
            white_peace_response = (
                _white_peace_no_safe_route_response_plan(
                    rows,
                    war_id=tactical_war_id,
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
                    available_steps=available_steps,
                    active_war_summary=war_summary,
                    route_rejections=[passive_route_audit],
                )
                if isinstance(tactical_war_id, int)
                else None
            )
            if white_peace_response is not None:
                return white_peace_response
            emergency_exit = (
                _de_jure_no_safe_route_exit_plan(
                    snapshot,
                    active_wars=active_wars,
                    termination_by_war_id=termination_by_war_id,
                    available_steps=available_steps,
                    active_war_summary=war_summary,
                    route_rejections=[passive_route_audit],
                )
                if isinstance(snapshot, dict)
                else None
            )
            if emergency_exit is not None:
                return emergency_exit
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
            enemy = (
                next(
                    (
                        row
                        for row in visible_enemies
                        if _native_int(row.get("army_id"))
                        == _native_int(siege_relief.get("enemy_army_id"))
                    ),
                    None,
                )
                if route_candidate_source == "enemy_siege_relief"
                else None
            )
            target_source = (
                "player_capital_regroup"
                if preview_selected_target == capital_regroup_target
                else route_candidate_source
            )
            objective_kind = (
                "regroup"
                if preview_selected_target == capital_regroup_target
                or route_candidate_source == "player_held_county_capital"
                else "relief"
                if route_candidate_source == "enemy_siege_relief"
                else "siege"
            )
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
                defender_capital_contact = (
                    _primary_defender_capital_hold_input(
                        snapshot if isinstance(snapshot, dict) else {},
                        active_wars=active_wars,
                        controlled_armies=controlled_armies,
                        tactical_war=(
                            tactical_war
                            if isinstance(tactical_war, dict)
                            else None
                        ),
                        pursuit_army=(
                            pursuit_army
                            if isinstance(pursuit_army, dict)
                            else None
                        ),
                        exact_objective_province_ids=(
                            exact_objective_province_ids
                        ),
                        termination_by_war_id=termination_by_war_id,
                        war_summary=war_summary,
                        unsafe_armies=unsafe_armies,
                        active_assaults=active_assaults,
                        allow_observable_enemy_routes=True,
                        allow_defeat_score_contact=True,
                    )
                )
                if defender_capital_contact is not None:
                    campaign_root = _same_frame_campaign_root_context(
                        rows,
                        snapshot if isinstance(snapshot, dict) else None,
                    )
                    if campaign_root is None:
                        root_step = "query-campaign-root-context-v1"
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_defender_capital_contact_context",
                            "selected_step": (
                                root_step
                                if root_step in available_steps
                                else None
                            ),
                            "required_step": root_step,
                            "reason": "a threatened primary-defender hold may query contact timing only at a fresh same-frame exact campaign capital",
                            "defensive_hold": defender_capital_contact,
                            "route_rejections": stationary_threats,
                            "active_wars": war_summary,
                        }
                    capital_province_id = _native_int(
                        campaign_root.get("capital_province_id")
                    )
                    if capital_province_id == current_province_id:
                        defensive_hold = {
                            **defender_capital_contact,
                            "capital_province_id": capital_province_id,
                            "campaign_root_snapshot_revision": (
                                campaign_root.get("snapshot_revision")
                            ),
                            "campaign_root_date_raw": campaign_root.get(
                                "date_raw"
                            ),
                        }
                        contact_query_step = (
                            query_route_contact_horizon_step(
                                int(defensive_hold["army_id"]),
                                int(capital_province_id),
                                route_threat_enemy_ids,
                            )
                        )
                        if not route_contact_scope_supported:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_defender_capital_contact_horizon_unsupported",
                                "selected_step": None,
                                "required_step": contact_query_step,
                                "reason": "the threatened capital hold requires the existing complete-scope stationary contact-horizon capability",
                                "defensive_hold": defensive_hold,
                                "route_rejections": stationary_threats,
                                "active_wars": war_summary,
                            }
                        contact_horizon = _fresh_route_contact_horizon(
                            rows,
                            snapshot,
                            army_id=int(defensive_hold["army_id"]),
                            origin_province_id=int(current_province_id),
                            target_province_id=int(capital_province_id),
                            hostile_army_ids=route_threat_enemy_ids,
                            route_province_ids=[],
                        )
                        if contact_horizon is None:
                            failed_query = (
                                _current_frame_route_contact_query_failure(
                                    rows,
                                    snapshot,
                                    contact_query_step,
                                )
                            )
                            if failed_query is not None:
                                return {
                                    "policy": "one-life-turn-v1",
                                    "phase": "native_war_defender_capital_contact_horizon_unavailable",
                                    "selected_step": None,
                                    "required_observation": "fresh-available-stationary-contact-horizon",
                                    "reason": "the current-frame stationary capital contact query failed or returned no usable exact timeline; keep the map paused",
                                    "defensive_hold": defensive_hold,
                                    "contact_query_attempt": failed_query,
                                    "route_rejections": stationary_threats,
                                    "active_wars": war_summary,
                                }
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_defender_capital_contact_horizon",
                                "selected_step": (
                                    contact_query_step
                                    if contact_query_step in available_steps
                                    else None
                                ),
                                "required_step": contact_query_step,
                                "reason": "replace geometric convergence on the exact defender capital with the existing stationary one-day contact timeline",
                                "defensive_hold": defensive_hold,
                                "route_rejections": stationary_threats,
                                "active_wars": war_summary,
                            }
                        contact_advance_step = (
                            advance_route_contact_horizon_step(
                                int(defensive_hold["army_id"]),
                                int(capital_province_id),
                                route_threat_enemy_ids,
                            )
                        )
                        if contact_horizon.get("one_day_contact_free") is True:
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_defender_capital_contact_horizon_progress",
                                "selected_step": (
                                    contact_advance_step
                                    if contact_advance_step in available_steps
                                    else None
                                ),
                                "required_step": contact_advance_step,
                                "reason": "the fresh stationary timeline proves the exact defender capital contact-free for one day",
                                "defensive_hold": defensive_hold,
                                "contact_horizon": contact_horizon,
                                "route_rejections": stationary_threats,
                                "active_wars": war_summary,
                            }
                        if unavoidable_current_province_contact_in_horizon(
                            contact_horizon
                        ):
                            return {
                                "policy": "one-life-turn-v1",
                                "phase": "native_war_defender_capital_contact_transition",
                                "selected_step": (
                                    contact_advance_step
                                    if contact_advance_step in available_steps
                                    else None
                                ),
                                "required_step": contact_advance_step,
                                "reason": "the exact defender-capital hold has an unavoidable current-province contact within the proof-bound day",
                                "defensive_hold": defensive_hold,
                                "contact_horizon": contact_horizon,
                                "route_rejections": stationary_threats,
                                "active_wars": war_summary,
                            }
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_defender_capital_contact_horizon_blocked",
                            "selected_step": None,
                            "required_observation": "contact-free-or-unavoidable-current-province-stationary-horizon",
                            "reason": "the fresh stationary capital horizon is neither contact-free nor an exact unavoidable current-province transition",
                            "defensive_hold": defensive_hold,
                            "contact_horizon": contact_horizon,
                            "route_rejections": stationary_threats,
                            "active_wars": war_summary,
                        }
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
            defender_capital_hold = _primary_defender_capital_hold_input(
                snapshot if isinstance(snapshot, dict) else {},
                active_wars=active_wars,
                controlled_armies=controlled_armies,
                tactical_war=(
                    tactical_war if isinstance(tactical_war, dict) else None
                ),
                pursuit_army=(
                    pursuit_army if isinstance(pursuit_army, dict) else None
                ),
                exact_objective_province_ids=exact_objective_province_ids,
                termination_by_war_id=termination_by_war_id,
                war_summary=war_summary,
                unsafe_armies=unsafe_armies,
                active_assaults=active_assaults,
            )
            if defender_capital_hold is not None:
                campaign_root = _same_frame_campaign_root_context(
                    rows,
                    snapshot if isinstance(snapshot, dict) else None,
                )
                if campaign_root is None:
                    root_step = "query-campaign-root-context-v1"
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_defender_capital_hold_context",
                        "selected_step": (
                            root_step if root_step in available_steps else None
                        ),
                        "required_step": root_step,
                        "reason": "the primary defender may hold only at a fresh same-frame exact campaign capital",
                        "defensive_hold": defender_capital_hold,
                        "active_wars": war_summary,
                    }
                capital_province_id = _native_int(
                    campaign_root.get("capital_province_id")
                )
                if capital_province_id == current_province_id:
                    defensive_hold = {
                        **defender_capital_hold,
                        "capital_province_id": capital_province_id,
                        "campaign_root_snapshot_revision": campaign_root.get(
                            "snapshot_revision"
                        ),
                        "campaign_root_date_raw": campaign_root.get("date_raw"),
                    }
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_defender_capital_hold_progress",
                            "selected_step": "life-advance",
                            "reason": "the primary defender has no exact territorial objective and its sole regular army is holding the fresh same-frame campaign capital; use the existing bounded tactical horizon and re-observe immediately on war, army, or stationary-threat change",
                            "defensive_hold": defensive_hold,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_defender_capital_hold_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the exact primary-defender capital hold is ready but this backend cannot execute its bounded observation slice",
                        "defensive_hold": defensive_hold,
                        "active_wars": war_summary,
                    }
            defender_native_rally_hold = _primary_defender_capital_hold_input(
                snapshot if isinstance(snapshot, dict) else {},
                active_wars=active_wars,
                controlled_armies=controlled_armies,
                tactical_war=(
                    tactical_war if isinstance(tactical_war, dict) else None
                ),
                pursuit_army=(
                    pursuit_army if isinstance(pursuit_army, dict) else None
                ),
                exact_objective_province_ids=exact_objective_province_ids,
                termination_by_war_id=termination_by_war_id,
                war_summary=war_summary,
                unsafe_armies=unsafe_armies,
                active_assaults=active_assaults,
                allow_observable_enemy_routes=True,
            )
            native_rally_hold_binding = (
                _primary_defender_native_rally_hold_binding(
                    rows,
                    snapshot if isinstance(snapshot, dict) else {},
                    war_id=(
                        tactical_war_id
                        if isinstance(tactical_war_id, int)
                        else None
                    ),
                    army_id=(
                        pursuit_army.get("army_id")
                        if isinstance(pursuit_army, dict)
                        else None
                    ),
                    current_province_id=(
                        current_province_id
                        if isinstance(current_province_id, int)
                        else None
                    ),
                )
                if defender_native_rally_hold is not None
                else None
            )
            if native_rally_hold_binding is not None:
                campaign_root = _same_frame_campaign_root_context(
                    rows,
                    snapshot if isinstance(snapshot, dict) else None,
                )
                if campaign_root is None:
                    root_step = "query-campaign-root-context-v1"
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_defender_native_rally_hold_context",
                        "selected_step": (
                            root_step if root_step in available_steps else None
                        ),
                        "required_step": root_step,
                        "reason": "the primary-defender native-rally hold requires a fresh same-frame campaign root so an arbitrary noncapital province cannot inherit this authorization",
                        "defensive_hold": defender_native_rally_hold,
                        "native_rally_hold_binding": (
                            native_rally_hold_binding
                        ),
                        "active_wars": war_summary,
                    }
                capital_province_id = _native_int(
                    campaign_root.get("capital_province_id")
                )
                if (
                    capital_province_id is not None
                    and capital_province_id != current_province_id
                ):
                    defensive_hold = {
                        **defender_native_rally_hold,
                        "capital_province_id": capital_province_id,
                        "campaign_root_snapshot_revision": campaign_root.get(
                            "snapshot_revision"
                        ),
                        "campaign_root_date_raw": campaign_root.get("date_raw"),
                    }
                    if "life-advance" in available_steps:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_defender_native_rally_hold_progress",
                            "selected_step": "life-advance",
                            "reason": "the sole primary-defender army is still stationary at the exact province produced by its durable native raise receipt; advance only through the existing active-war tactical horizon and re-observe immediately",
                            "defensive_hold": defensive_hold,
                            "native_rally_hold_binding": (
                                native_rally_hold_binding
                            ),
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_defender_native_rally_hold_progress_unsupported",
                        "selected_step": None,
                        "required_step": "life-advance",
                        "reason": "the exact native-raised defender rally hold is ready, but this backend cannot execute its bounded observation slice",
                        "defensive_hold": defensive_hold,
                        "native_rally_hold_binding": native_rally_hold_binding,
                        "active_wars": war_summary,
                    }
            # A non-leading attacker cannot submit this war's termination and
            # has no exact siege objective in the R0088 ally-war shape.  Its
            # own stationary capital is a defensive observation point, not an
            # inferred enemy target.  Reuse the exact one-day contact proof;
            # an unavailable or unsafe proof still leaves the map paused.
            ally_hold = bool(
                len(active_wars) == 1
                and tactical_war is active_wars[0]
                and isinstance(tactical_war, dict)
                and tactical_war.get("player_side") == "attacker"
                and tactical_war.get("player_is_primary_war_leader") is False
                and not exact_objective_province_ids
                and len(controlled_armies) == 1
                and pursuit_army is controlled_armies[0]
                and isinstance(army_id, int)
                and isinstance(current_province_id, int)
                and _army_tactical_state(pursuit_army) == "regular"
                and pursuit_army.get("in_combat") is False
                and pursuit_army.get("retreating") is False
                and pursuit_army.get("move_target_province_id") is None
                and pursuit_army.get("route_province_ids") == []
                and not stationary_threats
                and not unsafe_armies
                and not active_assaults
                and len(route_threat_enemies) == len(
                    enemy_armies_from_wars(active_wars)
                )
                and len(route_threat_enemy_ids) == len(route_threat_enemies)
                and route_threat_enemies
                and all(
                    _native_int(hostile.get("army_id")) is not None
                    and _native_int(hostile.get("current_province_id"))
                    is not None
                    and hostile.get("current_province_id")
                    != current_province_id
                    and "move_target_province_id" in hostile
                    and isinstance(hostile.get("route_province_ids"), list)
                    and (
                        not hostile["route_province_ids"]
                        and hostile.get("move_target_province_id") is None
                        or bool(hostile["route_province_ids"])
                        and hostile["route_province_ids"][-1]
                        == hostile.get("move_target_province_id")
                    )
                    for hostile in route_threat_enemies
                )
                and isinstance(strength_balance, dict)
                and strength_balance.get("status") == "available"
                and isinstance(strength_balance.get("friendly_army_ids"), list)
                and len(strength_balance.get("friendly_army_ids", [])) >= 2
            )
            termination = (
                termination_by_war_id.get(tactical_war_id)
                if isinstance(tactical_war_id, int)
                else None
            )
            negative_termination = (
                war_summary[0].get("war_termination_negative_reuse")
                if ally_hold
                else None
            )
            termination_unavailable = bool(
                isinstance(negative_termination, dict)
                and negative_termination.get("status")
                == "negative_assessment_reused"
                or isinstance(termination, dict)
                and termination.get("player_is_primary_war_leader") is False
                and isinstance(termination.get("options"), dict)
                and all(
                    isinstance(termination["options"].get(outcome), dict)
                    and termination["options"][outcome].get("available")
                    is False
                    for outcome in ("surrender", "white_peace", "victory")
                )
            )
            if ally_hold and termination_unavailable:
                campaign_root = _same_frame_campaign_root_context(
                    rows, snapshot if isinstance(snapshot, dict) else None
                )
                if campaign_root is None:
                    root_step = "query-campaign-root-context-v1"
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_attacker_ally_capital_hold_context",
                        "selected_step": (
                            root_step if root_step in available_steps else None
                        ),
                        "required_step": root_step,
                        "reason": "bind the non-leading attacker's stationary hold to its same-frame directly held capital",
                        "active_wars": war_summary,
                    }
                own_counties = _complete_player_held_county_capital_province_ids(
                    campaign_root
                )
                if (
                    campaign_root.get("capital_province_id")
                    == current_province_id
                    and isinstance(own_counties, list)
                    and current_province_id in own_counties
                ):
                    contact_step = query_route_contact_horizon_step(
                        army_id, current_province_id, route_threat_enemy_ids
                    )
                    if not route_contact_scope_supported:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_attacker_ally_capital_contact_unsupported",
                            "selected_step": None,
                            "required_step": contact_step,
                            "reason": "the non-leading attacker requires a complete-scope one-day stationary contact proof",
                            "active_wars": war_summary,
                        }
                    contact = _fresh_route_contact_horizon(
                        rows,
                        snapshot,
                        army_id=army_id,
                        origin_province_id=current_province_id,
                        target_province_id=current_province_id,
                        hostile_army_ids=route_threat_enemy_ids,
                        route_province_ids=[],
                    )
                    if contact is None:
                        failed = _current_frame_route_contact_query_failure(
                            rows, snapshot, contact_step
                        )
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": (
                                "native_war_attacker_ally_capital_contact_unavailable"
                                if failed is not None
                                else "native_war_attacker_ally_capital_contact_query"
                            ),
                            "selected_step": (
                                contact_step
                                if failed is None and contact_step in available_steps
                                else None
                            ),
                            "required_step": contact_step,
                            "reason": "query the exact stationary one-day contact horizon before any allied-war time advance",
                            "contact_query_attempt": failed,
                            "active_wars": war_summary,
                        }
                    advance_step = advance_route_contact_horizon_step(
                        army_id, current_province_id, route_threat_enemy_ids
                    )
                    if contact.get("one_day_contact_free") is True:
                        return {
                            "policy": "one-life-turn-v1",
                            "phase": "native_war_attacker_ally_capital_contact_progress",
                            "selected_step": (
                                advance_step if advance_step in available_steps else None
                            ),
                            "required_step": advance_step,
                            "reason": "the non-leading attacker's directly held capital is contact-free for exactly one day; re-observe the allied war immediately",
                            "contact_horizon": contact,
                            "active_wars": war_summary,
                        }
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_attacker_ally_capital_contact_blocked",
                        "selected_step": None,
                        "required_observation": "contact-free-stationary-horizon",
                        "reason": "the same-frame stationary capital horizon does not prove one contact-free day",
                        "contact_horizon": contact,
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
                if target_source == "enemy_siege_relief":
                    pursuit["siege_relief"] = dict(siege_relief)
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
                        baseline_plan = {
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
                        sentinel_plan = (
                            _stationary_objective_hold_sentinel_substitution(
                                baseline_plan,
                                snapshot=(
                                    snapshot
                                    if isinstance(snapshot, dict)
                                    else {}
                                ),
                                active_wars=active_wars,
                                player_armies=player_armies,
                                war_summary=war_summary,
                                enabled=bool(
                                    battle_speed_gates[
                                        "stationary_objective_hold_sentinel_live_ready"
                                    ]
                                    or battle_speed_gates[
                                        "stationary_objective_hold_sentinel_canary_ready"
                                    ]
                                ),
                                action_available=(
                                    _WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP
                                    in available_steps
                                ),
                                timeline_speed=(
                                    stationary_objective_hold_sentinel_speed
                                ),
                                high_speed_ab=bool(
                                    isinstance(
                                        battle_speed_readiness, dict
                                    )
                                    and battle_speed_readiness.get(
                                        "noncombat_sentinel_high_speed_ab"
                                    )
                                    is True
                                ),
                            )
                        )
                        return sentinel_plan or baseline_plan
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
                            else "move the overmatching primary-defender army along the previewed contact-safe route to relieve an observed enemy siege"
                            if target_source == "enemy_siege_relief"
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

    council_management_supported = (
        {
            QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
            ASSIGN_COUNCILLOR_V1_CAPABILITY,
        }
        <= available_capabilities
    )
    if council_management_supported:
        if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
            return {
                "policy": "one-life-turn-v1",
                "phase": "council_composition_pause_required",
                "selected_step": (
                    "pause-map" if "pause-map" in available_steps else None
                ),
                "required_step": "pause-map",
                "reason": (
                    "pause CK3 before reading the exact steward candidate frame"
                ),
            }
        if QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP not in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "council_composition_query_unavailable",
                "selected_step": None,
                "required_step": QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
                "required_capability": (
                    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY
                ),
                "reason": (
                    "the backend advertises Council19 but cannot route its "
                    "paused query"
                ),
            }
        council_observation = _same_frame_council_composition_candidates_v1(
            rows, snapshot
        )
        if council_observation is None:
            return {
                "policy": "one-life-turn-v1",
                "phase": "council_composition_query",
                "selected_step": (
                    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP
                ),
                "reason": (
                    "read native steward candidates, final eligibility and "
                    "same-frame skill inputs before considering an assignment"
                ),
                "position_key": STEWARD_POSITION_KEY,
            }
        if council_observation is not None:
            council_decision = _plan_steward_composition_v1(
                council_observation,
                available_capabilities=available_capabilities,
            )
            if council_decision["outcome"] in {
                "ASSIGN_REQUIRED",
                "REPLACE_REQUIRED",
            }:
                if ASSIGN_COUNCILLOR_V1_STEP in available_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "council_composition_action",
                        "selected_step": ASSIGN_COUNCILLOR_V1_STEP,
                        "reason": (
                            "submit the deterministic native-legal steward "
                            "choice and require an independent later-frame "
                            "incumbent receipt"
                        ),
                        "council_assignment": {
                            "observation": council_observation,
                            "candidate_character_id": council_decision[
                                "selected_candidate"
                            ]["character_id"],
                        },
                        "council_decision": council_decision,
                    }
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "council_composition_action_unavailable",
                    "selected_step": None,
                    "required_capability": ASSIGN_COUNCILLOR_V1_CAPABILITY,
                    "reason": (
                        "Council policy found a deterministic native-legal "
                        "composition change, but no routed semantic action exists"
                    ),
                    "council_decision": council_decision,
                }
            continued = choose_one_life_turn(
                rows,
                snapshot=snapshot,
                action_steps=available_steps,
                bridge_capabilities=(
                    capability
                    for capability in available_capabilities
                    if capability
                    != QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY
                ),
                next_run_plan=next_run_plan,
                battle_speed_readiness=battle_speed_readiness,
            )
            return {
                **continued,
                "council_observation_consumed": True,
                "council_decision": council_decision,
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

    active_war_ids = {
        war_id
        for war_id in (
            war.get("war_id")
            for war in (
                snapshot.get("active_wars", [])
                if isinstance(snapshot, dict)
                and isinstance(snapshot.get("active_wars"), list)
                else []
            )
            if isinstance(war, dict)
        )
        if isinstance(war_id, int) and not isinstance(war_id, bool)
    }
    postwar_reentry = _recent_postwar_reentry_cooldown(
        rows,
        date_raw=(snapshot.get("date_raw") if isinstance(snapshot, dict) else None),
        episode_run_id=(
            snapshot.get("episode_run_id") if isinstance(snapshot, dict) else None
        ),
        active_war_ids=active_war_ids,
    )
    if isinstance(postwar_reentry, dict):
        if "life-advance" in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_postwar_reentry_cooldown",
                "selected_step": "life-advance",
                "reason": (
                    "the previous terminal war action has materialized; keep "
                    "the verified peaceful state for the bounded 30-day "
                    "horizon before considering another declaration"
                ),
                "postwar_reentry": postwar_reentry,
            }
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_postwar_reentry_cooldown_unsupported",
            "selected_step": None,
            "required_step": "life-advance",
            "reason": (
                "the previous terminal war action is inside its peaceful "
                "re-entry horizon, but this backend cannot advance time"
            ),
            "postwar_reentry": postwar_reentry,
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
    raw_declarations = (
        snapshot.get("declarable_wars") if isinstance(snapshot, dict) else None
    )
    played_character = (
        snapshot.get("played_character") if isinstance(snapshot, dict) else None
    )
    actor_character_id = (
        played_character.get("character_id")
        if isinstance(played_character, dict)
        else None
    )
    at_peace = (
        isinstance(snapshot, dict)
        and isinstance(snapshot.get("active_wars"), list)
        and not snapshot["active_wars"]
    )
    player_claims = _player_claim_declarations(
        raw_declarations,
        actor_character_id=actor_character_id,
    )
    campaign_root = _same_frame_campaign_root_context(
        rows, snapshot if isinstance(snapshot, dict) else None
    )
    if player_claims and at_peace:
        root_step = "query-campaign-root-context-v1"
        if campaign_root is None and root_step in available_steps:
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_player_claim_scope_assessment",
                "selected_step": root_step,
                "reason": (
                    "read the same-frame feudal, independence, adjacency, county "
                    "and peacetime-budget scope before evaluating player claims"
                ),
                "claim_declarations": player_claims,
            }
        root_readiness = (
            campaign_root.get("readiness")
            if isinstance(campaign_root, dict)
            else None
        )
        claim_scope_ready = (
            isinstance(root_readiness, dict)
            and root_readiness.get(
                "adjacent_external_province_holders_ready"
            )
            is True
            and root_readiness.get("related_character_contexts_ready") is True
        )
        if not claim_scope_ready:
            selected_step = (
                "life-advance" if "life-advance" in available_steps else None
            )
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_player_claim_evidence_required",
                "selected_step": selected_step,
                "reason": (
                    "player claims are final-legal, but the same-frame adjacent "
                    "independent county scope is incomplete; choose NO_DECLARE"
                ),
                "decision": {
                    "policy": _CONSERVATIVE_FEUDAL_PLAYER_CLAIM_WAR_ENTRY[
                        "rule_id"
                    ],
                    "outcome": "NO_DECLARE",
                    "automatic_declaration_enabled": False,
                },
                "claim_declarations": player_claims,
            }
        bounded_claims = _adjacent_independent_county_player_claims(
            player_claims, campaign_root
        )
        missing_claim_targets = sorted(
            {
                int(declaration["target_character_id"])
                for declaration in bounded_claims
                if int(declaration["target_character_id"])
                not in war_entry_assessment_rows
            }
        )
        if missing_claim_targets:
            assessment_step = query_war_entry_assessments_step(
                [missing_claim_targets[0]]
            )
            if assessment_step in available_steps:
                declaration = next(
                    row
                    for row in bounded_claims
                    if row["target_character_id"] == missing_claim_targets[0]
                )
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_player_claim_power_assessment",
                    "selected_step": assessment_step,
                    "reason": (
                        "read every same-frame adjacent independent county claim "
                        "target before comparing complete native power totals"
                    ),
                    "declaration": declaration,
                    "remaining_unassessed_target_character_ids": (
                        missing_claim_targets
                    ),
                }
            selected_step = (
                "life-advance" if "life-advance" in available_steps else None
            )
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_player_claim_evidence_required",
                "selected_step": selected_step,
                "reason": (
                    "one or more adjacent independent county claims lack a "
                    "same-frame native power assessment; choose NO_DECLARE"
                ),
                "decision": {
                    "policy": _CONSERVATIVE_FEUDAL_PLAYER_CLAIM_WAR_ENTRY[
                        "rule_id"
                    ],
                    "outcome": "NO_DECLARE",
                    "automatic_declaration_enabled": False,
                },
                "missing_target_character_ids": missing_claim_targets,
            }
        if bounded_claims:
            claim_entry = _conservative_feudal_player_claim_war_entry(
                bounded_claims,
                war_entry_assessment_rows,
                campaign_root,
                available_steps,
                at_peace=at_peace,
            )
            if claim_entry["status"] == "forecast_required":
                declaration = claim_entry["declaration"]
                assessment_row = claim_entry["assessment"]
                return _forecast_required_war_entry_plan(
                    declaration,
                    assessment_row,
                    claim_entry,
                    campaign_root,
                    available_steps,
                )
    declaration = _preferred_native_declaration(
        raw_declarations,
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
        conservative_entry = _conservative_feudal_de_jure_war_entry(
            declaration,
            assessment_row,
            campaign_root,
            available_steps,
            at_peace=at_peace,
        )
        if conservative_entry["status"] == "forecast_required":
            return _forecast_required_war_entry_plan(
                declaration,
                assessment_row,
                conservative_entry,
                campaign_root,
                available_steps,
            )
        # A final-legal native declaration can still be compared with the
        # bounded aggregate battle prior when the narrow historical county
        # canaries do not match.  The model's low fidelity stays explicit in
        # the returned decision instead of making missing regiment detail an
        # automatic NO_DECLARE.
        declaration_id = declaration.get("declaration_id")
        try:
            typed_declaration_step = (
                declare_war_step(declaration_id)
                if isinstance(declaration_id, str) else None
            )
        except ValueError:
            typed_declaration_step = None
        government = campaign_root.get("government") if isinstance(campaign_root, dict) else None
        monthly_income = (
            campaign_root.get("player_monthly_gold_income")
            if isinstance(campaign_root, dict) else None
        )
        same_frame_general_scope = bool(
            isinstance(campaign_root, dict)
            and campaign_root.get("independent") is True
            and isinstance(government, dict)
            and government.get("key") == "feudal_government"
            and campaign_root.get("player_targeting_faction_count") == 0
            and isinstance(campaign_root.get("player_domain_size"), int)
            and isinstance(campaign_root.get("player_domain_limit"), int)
            and campaign_root["player_domain_size"] <= campaign_root["player_domain_limit"]
            and isinstance(monthly_income, dict)
            and monthly_income.get("scale") == WAR_ENTRY_FIXED_POINT_SCALE
            and isinstance(monthly_income.get("raw"), int)
            and monthly_income["raw"] > 0
        )
        claimant = declaration.get("claimant_character_id")
        claimant_valid = bool(
            declaration.get("casus_belli_key") != "claim_cb"
            or (
                isinstance(campaign_root, dict)
                and claimant == campaign_root.get("player_character_id")
                and isinstance(claimant, int) and claimant > 0
            )
        )
        if (
            at_peace
            and fresh_assessment
            and same_frame_general_scope
            and claimant_valid
            and assessment_row.get("actor_network_contribution_raw") == 0
            and assessment_row.get("actor_power_total_raw") == assessment_row.get("actor_power_base_raw")
            and declaration.get("source") == "native"
            and isinstance(typed_declaration_step, str)
            and typed_declaration_step in available_steps
        ):
            return _forecast_required_war_entry_plan(
                declaration,
                assessment_row,
                {
                    "rule_id": "general-native-war-entry-battle-prior-v1",
                    "typed_declaration_step": typed_declaration_step,
                    "typed_declaration_available": True,
                    "status": "forecast_required",
                },
                campaign_root if isinstance(campaign_root, dict) else {},
                available_steps,
            )
        # A legal declaration can still lack the independent, same-frame
        # identity/economy/action scope used by this bounded prior.  Report
        # that concrete mismatch rather than treating imperfect native combat
        # parity as a blanket reason never to use the model.
        prior_scope_blockers = [
            name for name, satisfied in (
                ("at_peace", at_peace),
                ("fresh_power_assessment", fresh_assessment),
                ("independent_feudal_economic_scope", same_frame_general_scope),
                ("claimant_identity", claimant_valid),
                ("actor_power_without_unbounded_allies", assessment_row.get("actor_network_contribution_raw") == 0
                 and assessment_row.get("actor_power_total_raw") == assessment_row.get("actor_power_base_raw")),
                ("native_declaration", declaration.get("source") == "native"),
                ("typed_declaration_available", isinstance(typed_declaration_step, str)
                 and typed_declaration_step in available_steps),
            ) if not satisfied
        ]
        required_capabilities = [
            QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
            "game.forecast.combat-monte-carlo-v1",
            "game.command.query-war-entry-assessments-v1-N",
        ]
        shared_evidence = {
            "required_capabilities": required_capabilities,
            "general_battle_prior_scope_blockers": prior_scope_blockers,
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
                    "the native declaration is legal but does not satisfy "
                    "the bounded battle prior's same-frame strategy scope; "
                    "choose NO_DECLARE and reassess after one bounded interval"
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
                "the native declaration is legal but does not satisfy "
                "the bounded battle prior's same-frame strategy scope"
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


def _capital_regroup_input_ready(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
    tactical_war: dict[str, object] | None,
    current_province_id: int | None,
    exact_objective_province_ids: list[int],
    exact_siege_rejection: dict[str, object] | None,
) -> bool:
    """Admit only the observed R838 insufficient-siege retreat shape."""

    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and len(active_wars) == 1
        and tactical_war is active_wars[0]
        and isinstance(tactical_war, dict)
        and tactical_war.get("player_side") == "attacker"
        and tactical_war.get("player_is_primary_war_leader") is True
        and len(controlled_armies) == 1
        and current_province_id is not None
        and exact_objective_province_ids == [current_province_id]
        and isinstance(exact_siege_rejection, dict)
        and exact_siege_rejection.get("status")
        == "insufficient_strength"
        and snapshot.get("war_objective_occupation_supported") is True
        and snapshot.get("war_objective_garrison_supported") is True
        and snapshot.get("war_objective_siege_progress_supported") is True
        and snapshot.get("war_objective_assault_supported") is True
    ):
        return False
    army = controlled_armies[0]
    army_id = _native_int(army.get("army_id"))
    if not (
        army_id is not None
        and _native_int(army.get("current_province_id"))
        == current_province_id
        and _army_tactical_state(army) == "sieging"
        and army.get("in_combat") is not True
        and army.get("retreating") is not True
        and "move_target_province_id" in army
        and army.get("move_target_province_id") is None
        and isinstance(army.get("route_province_ids"), list)
        and not army["route_province_ids"]
    ):
        return False
    states = tactical_war.get("objective_province_states")
    if not isinstance(states, list) or len(states) != 1:
        return False
    state = states[0]
    if not (
        isinstance(state, dict)
        and _native_int(state.get("province_id")) == current_province_id
        and state.get("occupation_observable") is True
        and state.get("is_occupied") is False
        and state.get("siege_observable") is True
    ):
        return False
    siege = state.get("active_siege")
    garrison = _native_int(state.get("garrison_size"))
    strength = _native_int(state.get("besieging_strength"))
    if not (
        isinstance(siege, dict)
        and _native_int(siege.get("siege_id")) is not None
        and _native_int(siege.get("besieging_army_id")) == army_id
        and siege.get("player_army_besieging") is True
        and siege.get("assault_observable") is True
        and siege.get("assault_in_progress") is False
        and strength == 399
        and garrison == 400
    ):
        return False
    enemies = [
        enemy
        for enemy in enemy_armies_from_wars(active_wars)
        if _army_tactical_state(enemy) != "retreating"
    ]
    return bool(
        enemies
        and len(enemies) <= 64
        and all(
            _native_int(enemy.get("army_id")) is not None
            and _native_int(enemy.get("current_province_id")) is not None
            and "move_target_province_id" in enemy
            and isinstance(enemy.get("route_province_ids"), list)
            and all(
                _native_int(province_id) is not None
                for province_id in enemy["route_province_ids"]
            )
            for enemy in enemies
        )
    )


def _attacker_capital_hold_input_ready(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
    tactical_war: dict[str, object] | None,
    current_province_id: int | None,
    exact_objective_province_ids: list[int],
    route_rejections: list[dict[str, object]],
) -> bool:
    """Admit the observed R18 defeated-armies-at-capital hold shape."""

    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and len(active_wars) == 1
        and tactical_war is active_wars[0]
        and isinstance(tactical_war, dict)
        and tactical_war.get("player_side") == "attacker"
        and tactical_war.get("player_is_primary_war_leader") is True
        and (_native_int(tactical_war.get("player_relative_war_score")) or 0)
        < 0
        and current_province_id is not None
        and exact_objective_province_ids
        and current_province_id not in exact_objective_province_ids
        and controlled_armies
        and len(controlled_armies) <= 64
    ):
        return False
    if not all(
        _native_int(army.get("army_id")) is not None
        and _native_int(army.get("current_province_id"))
        == current_province_id
        and _army_tactical_state(army) == "regular"
        and army.get("in_combat") is not True
        and army.get("retreating") is not True
        and army.get("move_target_province_id") is None
        and isinstance(army.get("route_province_ids"), list)
        and not army["route_province_ids"]
        for army in controlled_armies
    ):
        return False
    expected_targets = set(exact_objective_province_ids)
    rejected_targets = {
        _native_int(rejection.get("target_province_id"))
        for rejection in route_rejections
        if isinstance(rejection, dict)
        and (
            rejection.get("status") == "blocked"
            or (
                rejection.get("status") == "unavailable"
                and rejection.get("reason") == "route_does_not_reach_target"
            )
        )
    }
    if not expected_targets.issubset(rejected_targets):
        return False
    enemies = [
        enemy
        for enemy in enemy_armies_from_wars(active_wars)
        if _army_tactical_state(enemy) != "retreating"
    ]
    return bool(
        enemies
        and all(
            _native_int(enemy.get("army_id")) is not None
            and _native_int(enemy.get("current_province_id"))
            in expected_targets
            and enemy.get("in_combat") is not True
            and enemy.get("retreating") is not True
            for enemy in enemies
        )
    )


def _outnumbered_attacker_regroup_input_ready(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
    tactical_war: dict[str, object] | None,
    current_province_id: int | None,
    route_rejections: list[dict[str, object]],
    strength_balance: dict[str, object] | None,
) -> bool:
    """Permit a live attacker to break an unsafe route under coalition risk."""

    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and len(active_wars) == 1
        and tactical_war is active_wars[0]
        and isinstance(tactical_war, dict)
        and tactical_war.get("player_side") == "attacker"
        and tactical_war.get("player_is_primary_war_leader") is True
        and isinstance(tactical_war.get("player_relative_war_score"), int)
        and -100 < int(tactical_war["player_relative_war_score"]) < 100
        and isinstance(current_province_id, int)
        and controlled_armies
        and len(controlled_armies) <= 64
        and isinstance(strength_balance, dict)
        and strength_balance.get("hostile_operational_overmatch") is True
        and route_rejections
        and any(
            rejection.get("status") in {"unsafe", "blocked"}
            for rejection in route_rejections
            if isinstance(rejection, dict)
        )
    ):
        return False
    regroup_subjects = [
        army
        for army in controlled_armies
        if _native_int(army.get("current_province_id"))
        == current_province_id
        and _army_tactical_state(army) in {"regular", "moving", "sieging"}
        and army.get("in_combat") is not True
        and army.get("retreating") is not True
    ]
    return bool(
        len(regroup_subjects) == 1
        and _native_int(regroup_subjects[0].get("army_id")) is not None
        and all(
            _native_int(army.get("army_id")) is not None
            and army.get("in_combat") is not True
            and army.get("retreating") is not True
            for army in controlled_armies
        )
    )


def _outnumbered_primary_defender_regroup_input_ready(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
    tactical_war: dict[str, object] | None,
    current_province_id: int | None,
    exact_objective_province_ids: list[int],
    route_rejections: list[dict[str, object]],
    strength_balance: dict[str, object] | None,
    active_route_unsafe: bool,
) -> bool:
    """Try an exact capital reroute only for the observed R0101 defender shape.

    This opens the existing preview/contact-horizon sequence, not the move:
    a deferred or unsafe capital route remains blocked.
    """

    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and len(active_wars) == 1
        and tactical_war is active_wars[0]
        and isinstance(tactical_war, dict)
        and tactical_war.get("player_side") == "defender"
        and tactical_war.get("player_is_primary_war_leader") is True
        and isinstance(tactical_war.get("player_relative_war_score"), int)
        and -100 < int(tactical_war["player_relative_war_score"]) < 100
        and len(controlled_armies) == 1
        and isinstance(current_province_id, int)
        and isinstance(strength_balance, dict)
        and strength_balance.get("hostile_operational_overmatch") is True
        and active_route_unsafe
        and exact_objective_province_ids
    ):
        return False
    rejected_targets = {
        _native_int(rejection.get("target_province_id"))
        for rejection in route_rejections
        if isinstance(rejection, dict)
        and rejection.get("status") in {"blocked", "unsafe"}
    }
    army = controlled_armies[0]
    move_target = _native_int(army.get("move_target_province_id"))
    route = army.get("route_province_ids")
    if not (
        set(exact_objective_province_ids).issubset(rejected_targets)
        and move_target in rejected_targets
        and _native_int(army.get("army_id")) is not None
        and _native_int(army.get("current_province_id"))
        == current_province_id
        and _army_tactical_state(army) == "moving"
        and army.get("in_combat") is not True
        and army.get("retreating") is not True
        and isinstance(route, list)
        and bool(route)
        and route[-1] == move_target
    ):
        return False
    enemies = enemy_armies_from_wars(active_wars)
    return bool(
        enemies
        and len(enemies) <= 64
        and all(
            _native_int(enemy.get("army_id")) is not None
            and _native_int(enemy.get("current_province_id")) is not None
            and isinstance(enemy.get("route_province_ids"), list)
            and all(
                _native_int(province_id) is not None
                for province_id in enemy["route_province_ids"]
            )
            for enemy in enemies
        )
    )


def _primary_defender_capital_hold_input(
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
    tactical_war: dict[str, object] | None,
    pursuit_army: dict[str, object] | None,
    exact_objective_province_ids: list[int],
    termination_by_war_id: dict[int, dict[str, object]],
    war_summary: list[dict[str, object]],
    unsafe_armies: list[dict[str, object]],
    active_assaults: list[dict[str, object]],
    allow_observable_enemy_routes: bool = False,
    allow_defeat_score_contact: bool = False,
) -> dict[str, object] | None:
    """Admit idle hold or proof-bound threatened-route observation."""

    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and len(active_wars) == 1
        and tactical_war is active_wars[0]
        and isinstance(tactical_war, dict)
        and tactical_war.get("player_side") == "defender"
        and tactical_war.get("player_is_primary_war_leader") is True
        and isinstance(tactical_war.get("player_relative_war_score"), int)
        and not isinstance(tactical_war.get("player_relative_war_score"), bool)
        and (
            -100 < int(tactical_war["player_relative_war_score"]) < 100
            or (
                tactical_war["player_relative_war_score"] == -100
                and allow_observable_enemy_routes
                and allow_defeat_score_contact
            )
        )
        and exact_objective_province_ids == []
        and len(controlled_armies) == 1
        and pursuit_army is controlled_armies[0]
        and not unsafe_armies
        and not active_assaults
    ):
        return None
    army = controlled_armies[0]
    army_id = _native_int(army.get("army_id"))
    current_province_id = _native_int(army.get("current_province_id"))
    if not (
        army_id is not None
        and current_province_id is not None
        and _army_tactical_state(army) == "regular"
        and army.get("in_combat") is False
        and army.get("retreating") is False
        and "move_target_province_id" in army
        and army.get("move_target_province_id") is None
        and isinstance(army.get("route_province_ids"), list)
        and not army["route_province_ids"]
    ):
        return None
    enemies = [
        enemy
        for enemy in enemy_armies_from_wars(active_wars)
        if _army_tactical_state(enemy) != "retreating"
    ]
    idle_gathering_enemies = all(
        _native_int(enemy.get("army_id")) is not None
        and _native_int(enemy.get("current_province_id")) is not None
        and _army_tactical_state(enemy) == "gathering"
        and enemy.get("in_combat") is False
        and enemy.get("retreating") is False
        and "move_target_province_id" in enemy
        and enemy.get("move_target_province_id") is None
        and isinstance(enemy.get("route_province_ids"), list)
        and not enemy["route_province_ids"]
        for enemy in enemies
    )
    observable_noncombat_enemies = all(
        _native_int(enemy.get("army_id")) is not None
        and _native_int(enemy.get("current_province_id")) is not None
        and _army_tactical_state(enemy)
        in {"gathering", "regular", "moving", "sieging", "embarked"}
        and enemy.get("in_combat") is False
        and enemy.get("retreating") is False
        and "move_target_province_id" in enemy
        and isinstance(enemy.get("route_province_ids"), list)
        and all(
            _native_int(province_id) is not None
            for province_id in enemy["route_province_ids"]
        )
        and (
            (
                enemy.get("move_target_province_id") is None
                and not enemy["route_province_ids"]
            )
            or (
                _native_int(enemy.get("move_target_province_id")) is not None
                and bool(enemy["route_province_ids"])
                and enemy["route_province_ids"][-1]
                == enemy.get("move_target_province_id")
            )
        )
        for enemy in enemies
    )
    if not (
        enemies
        and len(enemies) <= MAX_ROUTE_CONTACT_HOSTILE_IDS
        and (
            observable_noncombat_enemies
            if allow_observable_enemy_routes
            else idle_gathering_enemies
        )
    ):
        return None
    war_id = _native_int(tactical_war.get("war_id"))
    summary = next(
        (
            row
            for row in war_summary
            if war_id is not None and row.get("war_id") == war_id
        ),
        None,
    )
    if war_id is None or not isinstance(summary, dict):
        return None
    reuse = summary.get("war_termination_negative_reuse")
    options = termination_by_war_id.get(war_id)
    if (
        isinstance(reuse, dict)
        and reuse.get("status") == "negative_assessment_reused"
    ):
        termination_evidence = {
            "status": "negative_assessment_reused",
            "queried_date_raw": reuse.get("queried_date_raw"),
            "expires_date_raw": reuse.get("expires_date_raw"),
        }
    elif (
        _same_frame_termination_row(snapshot, options, war_id)
        and isinstance(options, dict)
        and options.get("player_side") == "defender"
        and options.get("player_is_primary_war_leader") is True
        and options.get("player_relative_war_score")
        == tactical_war.get("player_relative_war_score")
        and not _claim_cb_white_peace_candidate(tactical_war, options)
        and not _de_jure_no_safe_route_white_peace_candidate(
            tactical_war, options
        )
        and not _de_jure_no_safe_route_surrender_candidate(
            tactical_war, options
        )
    ):
        termination_evidence = {
            "status": "same_frame_no_authorized_exit",
            "queried_snapshot_id": options.get("queried_snapshot_id"),
            "queried_revision": options.get("queried_revision"),
        }
    else:
        return None
    return {
        "status": "ready",
        "war_id": war_id,
        "army_id": army_id,
        "current_province_id": current_province_id,
        "termination_evidence": termination_evidence,
        "enemy_army_ids": sorted(
            int(enemy["army_id"])
            for enemy in enemies
            if _native_int(enemy.get("army_id")) is not None
        ),
    }


def _primary_defender_native_rally_hold_binding(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    war_id: int | None,
    army_id: object,
    current_province_id: int | None,
) -> dict[str, object] | None:
    """Bind a remote defender hold to one factual native raise receipt."""

    current_army_id = _native_int(army_id)
    played_character = snapshot.get("played_character")
    actor_id = (
        _native_int(played_character.get("character_id"))
        if isinstance(played_character, dict)
        else None
    )
    episode_run_id = snapshot.get("episode_run_id")
    current_date_raw = _native_int(snapshot.get("date_raw"))
    if not (
        war_id is not None
        and current_army_id is not None
        and current_province_id is not None
        and actor_id is not None
        and current_date_raw is not None
        and (episode_run_id is None or isinstance(episode_run_id, str))
    ):
        return None

    current_armies = snapshot.get("player_armies")
    current_army = next(
        (
            row
            for row in current_armies
            if isinstance(row, dict)
            and _native_int(row.get("army_id")) == current_army_id
        ),
        None,
    ) if isinstance(current_armies, list) else None
    if not (
        isinstance(current_army, dict)
        and _native_int(current_army.get("owner_character_id")) == actor_id
        and _native_int(current_army.get("current_province_id"))
        == current_province_id
    ):
        return None

    raise_position = -1
    raise_row: dict[str, object] | None = None
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        if _effective_command(row) != RAISE_TROOPS_STEP:
            continue
        raise_position = position
        raise_row = row
        break
    if raise_row is None or raise_row.get("ok") is not True:
        return None
    raise_history_index = _native_int(raise_row.get("index"))
    raise_result = _effective_command_result(raise_row)
    raise_action = (
        raise_result.get("war_action")
        if isinstance(raise_result, dict)
        else None
    )
    raised_army_ids = (
        raise_action.get("raised_army_ids")
        if isinstance(raise_action, dict)
        else None
    )
    raised_armies = (
        raise_result.get("player_armies")
        if isinstance(raise_result, dict)
        else None
    )
    raised_army = (
        raised_armies[0]
        if isinstance(raised_armies, list) and len(raised_armies) == 1
        else None
    )
    if not (
        raise_history_index is not None
        and isinstance(raise_result, dict)
        and raise_result.get("accepted") is True
        and raise_result.get("status") == "submitted"
        and isinstance(raise_action, dict)
        and raise_action.get("status") == "raised"
        and raised_army_ids == [current_army_id]
        and isinstance(raised_army, dict)
        and _native_int(raised_army.get("army_id")) == current_army_id
        and _native_int(raised_army.get("owner_character_id")) == actor_id
        and _native_int(raised_army.get("current_province_id"))
        == current_province_id
        and raised_army.get("controllable") is True
        and _army_tactical_state(raised_army) == "gathering"
        and raised_army.get("in_combat") is False
        and raised_army.get("retreating") is False
        and "move_target_province_id" in raised_army
        and raised_army.get("move_target_province_id") is None
        and isinstance(raised_army.get("route_province_ids"), list)
        and not raised_army["route_province_ids"]
    ):
        return None

    query_position = -1
    query_row: dict[str, object] | None = None
    query_step = query_war_termination_options_step(war_id)
    for position in range(raise_position - 1, -1, -1):
        row = commands[position]
        if _effective_command(row) == query_step:
            query_position = position
            query_row = row
            break
    if query_row is None or query_row.get("ok") is not True:
        return None
    query_history_index = _native_int(query_row.get("index"))
    query_result = _effective_command_result(query_row)
    query_options = (
        query_result.get("war_termination_options")
        if isinstance(query_result, dict)
        else None
    )
    query_context = (
        query_result.get("termination_query_context")
        if isinstance(query_result, dict)
        else None
    )
    active_signature = (
        query_context.get("active_war_signature")
        if isinstance(query_context, dict)
        else None
    )
    signature = (
        active_signature[0]
        if isinstance(active_signature, list) and len(active_signature) == 1
        else None
    )
    query_date_raw = (
        _native_int(query_context.get("queried_date_raw"))
        if isinstance(query_context, dict)
        else None
    )
    if not (
        query_history_index is not None
        and isinstance(query_result, dict)
        and query_result.get("accepted") is True
        and query_result.get("status") == "available"
        and query_result.get("queried_episode_run_id") == episode_run_id
        and isinstance(query_options, dict)
        and _native_int(query_options.get("war_id")) == war_id
        and query_options.get("player_side") == "defender"
        and query_options.get("player_is_primary_war_leader") is True
        and isinstance(query_context, dict)
        and query_context.get("queried_episode_run_id") == episode_run_id
        and _native_int(query_context.get("queried_character_id")) == actor_id
        and query_date_raw is not None
        and query_date_raw <= current_date_raw
        and isinstance(signature, dict)
        and _native_int(signature.get("war_id")) == war_id
        and signature.get("player_side") == "defender"
        and signature.get("player_is_primary_war_leader") is True
    ):
        return None

    crossed_restore_history_indices: list[int] = []
    for row in commands[query_position + 1 : raise_position]:
        if _effective_command(row) != "restore-checkpoint":
            continue
        restore_result = _effective_command_result(row)
        checkpoint = (
            restore_result.get("checkpoint")
            if isinstance(restore_result, dict)
            else None
        )
        if not (
            row.get("ok") is True
            and isinstance(restore_result, dict)
            and restore_result.get("status") == "restored"
            and isinstance(checkpoint, dict)
            and _native_int(checkpoint.get("history_index")) is not None
            and int(checkpoint["history_index"]) >= query_history_index
            and _native_int(checkpoint.get("episode_character_id"))
            == actor_id
            and checkpoint.get("episode_run_id") == episode_run_id
        ):
            return None

    def stable_progress_army(army: dict[str, object] | None) -> bool:
        return bool(
            isinstance(army, dict)
            and _native_int(army.get("army_id")) == current_army_id
            and _native_int(army.get("current_province_id"))
            == current_province_id
            and _army_tactical_state(army) in {"gathering", "regular"}
            and army.get("in_combat") is False
            and army.get("retreating") is False
            and "move_target_province_id" in army
            and army.get("move_target_province_id") is None
            and isinstance(army.get("route_province_ids"), list)
            and not army["route_province_ids"]
        )

    for row in commands[raise_position + 1 :]:
        command = _effective_command(row)
        if command == "restore-checkpoint":
            restore_result = _effective_command_result(row)
            checkpoint = (
                restore_result.get("checkpoint")
                if isinstance(restore_result, dict)
                else None
            )
            restore_history_index = _native_int(row.get("index"))
            if not (
                row.get("ok") is True
                and restore_history_index is not None
                and isinstance(restore_result, dict)
                and restore_result.get("status") == "restored"
                and isinstance(checkpoint, dict)
                and _native_int(checkpoint.get("history_index")) is not None
                and int(checkpoint["history_index"]) >= raise_history_index
                and _native_int(checkpoint.get("episode_character_id"))
                == actor_id
                and checkpoint.get("episode_run_id") == episode_run_id
            ):
                return None
            crossed_restore_history_indices.append(restore_history_index)
            continue
        parsed_move = parse_move_army_step(command)
        parsed_split = parse_split_army_half_step(command)
        parsed_merge = parse_merge_armies_step(command)
        if (
            command == RAISE_TROOPS_STEP
            or parsed_move is not None
            and parsed_move[0] == current_army_id
            or parsed_split == current_army_id
            or isinstance(parsed_merge, tuple)
            and current_army_id in parsed_merge
            or command == disband_army_step(current_army_id)
            or command == "war-disband-armies"
            or parse_start_assault_step(command) is not None
            or parse_stop_assault_step(command) is not None
        ):
            return None
        if not is_life_advance_step(command):
            continue
        if row.get("ok") is not True:
            return None
        result = _effective_command_result(row)
        before_date, before_war = _progress_slice(
            result, "war_progress_before", war_id
        )
        after_date, after_war = _progress_slice(
            result, "war_progress_after", war_id
        )
        before_army = _progress_army(
            before_war, "player_armies", current_army_id
        )
        after_army = _progress_army(
            after_war, "player_armies", current_army_id
        )
        if not (
            before_date is not None
            and after_date is not None
            and after_date >= before_date
            and stable_progress_army(before_army)
            and stable_progress_army(after_army)
        ):
            return None

    return {
        "status": "ready",
        "war_id": war_id,
        "army_id": current_army_id,
        "owner_character_id": actor_id,
        "rally_province_id": current_province_id,
        "raise_history_index": raise_history_index,
        "raise_snapshot_id": raise_result.get("snapshot_id"),
        "raise_revision": raise_result.get("revision"),
        "war_query_history_index": query_history_index,
        "war_query_date_raw": query_date_raw,
        "crossed_restore_history_indices": crossed_restore_history_indices,
    }


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


def _preoffensive_army_consolidation(
    snapshot: dict[str, object],
    *,
    controlled_armies: list[dict[str, object]],
    war_id: int,
) -> dict[str, object] | None:
    """Select one exact same-province merge before an offensive march."""

    if not (
        snapshot.get("paused") is True
        and len(controlled_armies) > 1
    ):
        return None
    provinces = {
        _native_int(army.get("current_province_id"))
        for army in controlled_armies
    }
    if len(provinces) != 1 or None in provinces:
        return None
    if not all(
        _native_int(army.get("army_id")) is not None
        and _army_tactical_state(army) == "regular"
        and army.get("in_combat") is not True
        and army.get("retreating") is not True
        and army.get("move_target_province_id") is None
        and isinstance(army.get("route_province_ids"), list)
        and not army["route_province_ids"]
        for army in controlled_armies
    ):
        return None
    strengths = {
        int(row["army_id"]): int(row["current_soldiers"])
        for row in snapshot.get("army_strengths", [])
        if isinstance(row, dict)
        and row.get("status") == "available"
        and row.get("scope_role") == "player"
        and isinstance(row.get("war_ids"), list)
        and war_id in row["war_ids"]
        and _native_int(row.get("army_id")) is not None
        and _native_int(row.get("current_soldiers")) is not None
    }
    army_ids = {
        int(army["army_id"])
        for army in controlled_armies
        if _native_int(army.get("army_id")) is not None
    }
    if set(strengths) != army_ids:
        return None
    ordered = sorted(army_ids, key=lambda army_id: (-strengths[army_id], army_id))
    destination_army_id, source_army_id = ordered[:2]
    return {
        "status": "ready",
        "war_id": war_id,
        "province_id": next(iter(provinces)),
        "destination_army_id": destination_army_id,
        "destination_current_soldiers": strengths[destination_army_id],
        "source_army_id": source_army_id,
        "source_current_soldiers": strengths[source_army_id],
        "remaining_player_army_ids": ordered[2:],
        "step": merge_armies_step(destination_army_id, source_army_id),
    }


def _same_frame_army_strength_balance(
    snapshot: dict[str, object], war_id: int | None
) -> dict[str, object] | None:
    """Summarize the exact paused strength query as an operational risk gate.

    This is deliberately not a battle-win forecast.  It only records the
    current published force totals after every participant has materialized,
    so a post-declaration coalition cannot be mistaken for the single ruler
    assessed before the war began.
    """

    if not (
        isinstance(war_id, int)
        and not isinstance(war_id, bool)
        and war_id > 0
        and snapshot.get("paused") is True
        and snapshot.get("army_strengths_status") == "available"
        and isinstance(snapshot.get("army_strengths"), list)
    ):
        return None
    rows = [
        row
        for row in snapshot["army_strengths"]
        if isinstance(row, dict)
        and row.get("status") == "available"
        and isinstance(row.get("war_ids"), list)
        and war_id in row["war_ids"]
    ]
    if not rows:
        return None
    friendly = [
        row
        for row in rows
        if row.get("scope_role") in {"player", "active_war_ally"}
    ]
    enemies = [
        row for row in rows if row.get("scope_role") == "active_war_enemy"
    ]
    if not friendly or not enemies:
        return None
    numeric_fields = (
        "current_soldiers",
        "maximum_soldiers",
        "ai_base_power_raw",
    )
    if any(
        _native_int(row.get(field)) is None
        for row in [*friendly, *enemies]
        for field in numeric_fields
    ):
        return None

    def total(group: list[dict[str, object]], field: str) -> int:
        return sum(int(row[field]) for row in group)

    friendly_current = total(friendly, "current_soldiers")
    enemy_current = total(enemies, "current_soldiers")
    friendly_power_raw = total(friendly, "ai_base_power_raw")
    enemy_power_raw = total(enemies, "ai_base_power_raw")
    # Requiring a 25% hostile margin keeps this a conservative operational
    # routing signal instead of pretending raw soldiers are battle odds.
    hostile_operational_overmatch = bool(
        enemy_current * 4 > friendly_current * 5
        or enemy_power_raw * 4 > friendly_power_raw * 5
    )
    return {
        "status": "available",
        "war_id": war_id,
        "friendly_army_ids": sorted(int(row["army_id"]) for row in friendly),
        "enemy_army_ids": sorted(int(row["army_id"]) for row in enemies),
        "friendly_current_soldiers": friendly_current,
        "enemy_current_soldiers": enemy_current,
        "friendly_maximum_soldiers": total(friendly, "maximum_soldiers"),
        "enemy_maximum_soldiers": total(enemies, "maximum_soldiers"),
        "friendly_ai_base_power_raw": friendly_power_raw,
        "enemy_ai_base_power_raw": enemy_power_raw,
        "hostile_operational_overmatch": hostile_operational_overmatch,
        "interpretation": "operational_routing_risk_not_battle_win_odds",
    }


def _general_battle_forecast_ingress(
    baseline: dict[str, object],
    *,
    commands: list[dict[str, object]],
    snapshot: dict[str, object] | None,
    action_steps: set[str],
    bridge_capabilities: set[str],
) -> dict[str, object]:
    """Review any proposed army move into an observed hostile-held province.

    This covers ordinary offensive and defensive wars.  The older siege relief
    canary keeps its own narrower policy; it is not evaluated twice here.
    """
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return baseline
    if "provisional_forecast" in baseline or "qualified_forecast" in baseline:
        return baseline
    parsed = parse_move_army_step(baseline.get("selected_step"))
    if parsed is None:
        return baseline
    army_id, target = parsed
    player_armies = snapshot.get("player_armies")
    active_wars = snapshot.get("active_wars")
    if not isinstance(player_armies, list) or not isinstance(active_wars, list):
        return baseline
    army = next(
        (row for row in player_armies if isinstance(row, dict) and row.get("army_id") == army_id),
        None,
    )
    if not isinstance(army, dict):
        return baseline
    origin = _native_int(army.get("current_province_id"))
    enemy_rows = [
        enemy
        for war in active_wars if isinstance(war, dict)
        for enemy in (war.get("enemy_armies") if isinstance(war.get("enemy_armies"), list) else [])
        if isinstance(enemy, dict)
    ]
    defenders = tuple(sorted({
        enemy_id
        for enemy in enemy_rows
        if enemy.get("current_province_id") == target
        and _army_tactical_state(enemy) != "retreating"
        and (enemy_id := _native_int(enemy.get("army_id"))) is not None
        and enemy_id > 0
    }))
    if origin is None or origin == target or not defenders:
        return baseline

    def bounded(phase: str, selected_step: str | None, reason: str, **details: object) -> dict[str, object]:
        return {
            "policy": "general-battle-forecast-v1",
            "phase": phase,
            "selected_step": selected_step,
            "reason": reason,
            "baseline_phase": baseline.get("phase"),
            "baseline_selected_step": baseline.get("selected_step"),
            "encounter": {
                "attacker_army_ids": [army_id],
                "defender_army_ids": list(defenders),
                "target_province_id": target,
            },
            **details,
        }

    preview_step = preview_move_army_step(army_id, target)
    preview = _fresh_move_route_preview(
        commands, army_id=army_id, origin_province_id=origin,
        target_province_id=target, date_raw=_native_int(snapshot.get("date_raw")),
    )
    if preview is None:
        return bounded(
            "native_war_general_battle_route_query",
            preview_step if preview_step in action_steps else None,
            "read the current native route before forecasting an observed enemy contact",
        )
    route = preview.get("route_province_ids")
    if not (
        preview.get("status") == "available"
        and isinstance(route, list) and route and route[-1] == target
    ):
        return bounded("native_war_general_battle_route_blocked", None,
                       "the current native route is not an exact route to the contact", route_preview=preview)
    entry = route[-2] if len(route) > 1 else origin
    hostile_ids = tuple(sorted({
        enemy_id
        for enemy in enemy_rows
        if _army_tactical_state(enemy) != "retreating"
        and (enemy_id := _native_int(enemy.get("army_id"))) is not None
        and enemy_id > 0
    }))
    if not hostile_ids or len(hostile_ids) > MAX_ROUTE_CONTACT_HOSTILE_IDS:
        return bounded("native_war_general_battle_roster_blocked", None,
                       "the observed hostile roster exceeds the route query contract")
    contact_step = query_route_contact_horizon_step(army_id, target, hostile_ids)
    contact = _fresh_route_contact_horizon(
        commands, snapshot, army_id=army_id, origin_province_id=origin,
        target_province_id=target, hostile_army_ids=hostile_ids,
        route_province_ids=route,
    )
    if contact is None:
        return bounded(
            "native_war_general_battle_contact_query",
            contact_step if contact_step in action_steps else None,
            "read all possible hostile contacts on the proposed route",
            route_preview=preview,
        )
    conflicts = contact.get("conflicts")
    if not isinstance(conflicts, list) or any(
        not isinstance(row, dict)
        or row.get("province_id") != target
        or _native_int(row.get("hostile_army_id")) not in defenders
        for row in conflicts
    ):
        return bounded(
            "native_war_general_battle_contact_blocked", None,
            "another encounter can occur before the simulated target battle",
            route_preview=preview, route_contact_horizon=contact,
        )
    query_step = query_combat_simulation_inputs_v3_step(target, entry, [army_id], list(defenders))
    payload = snapshot.get("combat_simulation_inputs_v3")
    def current_query_row(row: dict[str, object]) -> bool:
        result = _effective_command_result(row)
        return bool(
            row.get("ok") is True
            and parse_query_combat_simulation_inputs_v3_step(_effective_command(row))
            == (target, entry, [army_id], list(defenders))
            and (_native_int(row.get("index")) or 0) > _latest_life_advance_index(commands)
            and isinstance(result, dict)
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == snapshot.get("native_revision")
            and result.get("status") == snapshot.get("combat_simulation_inputs_v3_status")
        )
    exact_cached = bool(
        isinstance(payload, dict)
        and snapshot.get("combat_simulation_inputs_v3_target_province_id") == target
        and snapshot.get("combat_simulation_inputs_v3_attacker_entry_province_id") == entry
        and snapshot.get("combat_simulation_inputs_v3_attacker_army_ids") == [army_id]
        and snapshot.get("combat_simulation_inputs_v3_defender_army_ids") == list(defenders)
        and snapshot.get("combat_simulation_inputs_v3_queried_snapshot_id") == snapshot.get("snapshot_id")
        and snapshot.get("combat_simulation_inputs_v3_queried_revision") == snapshot.get("revision")
        and any(current_query_row(row) for row in _history_after_latest_restore(commands))
    )
    if not exact_cached:
        return bounded(
            "native_war_general_battle_inputs_query",
            query_step if query_step in action_steps and QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY in bridge_capabilities else None,
            "obtain same-frame per-regiment inputs for this encounter",
            route_preview=preview, route_contact_horizon=contact,
        )
    assert isinstance(payload, dict)
    forecast = forecast_fixed_contact(
        payload, target_province_id=target,
        attacker_entry_province_id=entry,
        attacker_army_ids=(army_id,), defender_army_ids=defenders,
        capture={key: snapshot.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw"
        )},
    )
    admission = contact_admission(forecast)
    if admission["admitted"] is not True:
        return bounded(
            "native_war_general_battle_model_rejected", None,
            "the bounded whole-battle model exceeds the configured contact risk budget",
            battle_forecast=forecast, contact_admission=admission,
        )
    if len(route) != 1:
        if contact.get("one_day_contact_free") is not True:
            return bounded(
                "native_war_general_battle_short_route_blocked", None,
                "the first travel day has another possible contact",
                battle_forecast=forecast, contact_admission=admission,
            )
        first_hop = route[0]
        first_preview_step = preview_move_army_step(army_id, first_hop)
        first_preview = _fresh_move_route_preview(
            commands, army_id=army_id, origin_province_id=origin,
            target_province_id=first_hop, date_raw=_native_int(snapshot.get("date_raw")),
        )
        if first_preview is None:
            return bounded(
                "native_war_general_battle_short_preview",
                first_preview_step if first_preview_step in action_steps else None,
                "prove an exact first waypoint before a distant predicted contact",
                battle_forecast=forecast, contact_admission=admission,
            )
        if first_preview.get("status") != "available" or first_preview.get("route_province_ids") != [first_hop]:
            return bounded("native_war_general_battle_short_preview_blocked", None,
                           "the first waypoint does not have an exact one-hop route",
                           battle_forecast=forecast, contact_admission=admission)
        first_contact_step = query_route_contact_horizon_step(army_id, first_hop, hostile_ids)
        first_contact = _fresh_route_contact_horizon(
            commands, snapshot, army_id=army_id, origin_province_id=origin,
            target_province_id=first_hop, hostile_army_ids=hostile_ids,
            route_province_ids=[first_hop],
        )
        if first_contact is None:
            return bounded(
                "native_war_general_battle_short_contact_query",
                first_contact_step if first_contact_step in action_steps else None,
                "prove the first waypoint has no near-term hostile contact",
                battle_forecast=forecast, contact_admission=admission,
            )
        first_move_step = move_army_step(army_id, first_hop)
        if not (
            first_contact.get("one_day_contact_free") is True
            and first_contact.get("conflicts") == []
            and first_move_step in action_steps
        ):
            return bounded("native_war_general_battle_short_contact_blocked", None,
                           "the first waypoint is not proved contact-free",
                           battle_forecast=forecast, contact_admission=admission)
        return bounded(
            "native_war_general_battle_short_move", first_move_step,
            "move one proved contact-free waypoint and refresh the battle estimate next turn",
            battle_forecast=forecast, contact_admission=admission,
            general_battle_forecast_used_for_decision=True,
        )
    subject_route = contact.get("subject_route")
    arrivals = subject_route.get("arrival_date_raws") if isinstance(subject_route, dict) else None
    final_arrival = _native_int(arrivals[-1]) if isinstance(arrivals, list) and arrivals else None
    date_raw = _native_int(snapshot.get("date_raw"))
    if final_arrival is None or date_raw is None or not date_raw < final_arrival <= date_raw + 24:
        return bounded(
            "native_war_general_battle_arrival_blocked", None,
            "the single-step contact is outside the current one-day decision horizon",
            battle_forecast=forecast, contact_admission=admission,
        )
    return {
        **baseline,
        "general_battle_forecast": forecast,
        "general_battle_contact_admission": admission,
        "general_battle_forecast_used_for_decision": True,
    }


def _primary_defender_siege_forecast_ingress(
    baseline: dict[str, object],
    *,
    commands: list[dict[str, object]],
    snapshot: dict[str, object] | None,
    action_steps: set[str],
    bridge_capabilities: set[str],
) -> dict[str, object]:
    """Read a siege encounter and admit a bounded provisional defense trial."""
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        return baseline
    phase = baseline.get("phase")
    if phase not in {
        "native_war_no_safe_exact_route",
        "native_war_stationary_objective_hold_sentinel",
        "native_war_reconnaissance",
        "native_war_route_preview",
        "native_war_route_preview_unsupported",
        "native_war_pursuit",
        "native_war_pursuit_progress",
    }:
        # In particular, retain a legal terminal action or an independently
        # proved capital/defensive escape chosen by the ordinary planner.
        return baseline
    active_wars = snapshot.get("active_wars")
    player_armies = snapshot.get("player_armies")
    if not isinstance(active_wars, list) or not isinstance(player_armies, list):
        return baseline
    controlled = controllable_armies(
        [army for army in player_armies if isinstance(army, dict)]
    )
    if len(controlled) != 1:
        return baseline
    candidate = _primary_defender_siege_relief_assessment(
        snapshot,
        commands=commands,
        active_wars=[war for war in active_wars if isinstance(war, dict)],
        controlled_armies=controlled,
        pursuit_army=controlled[0],
    )
    if candidate.get("status") != "forecast_required":
        return baseline
    army_id = _native_int(candidate.get("army_id"))
    war_id = _native_int(candidate.get("war_id"))
    target = _native_int(candidate.get("target_province_id"))
    origin = _native_int(controlled[0].get("current_province_id"))
    if None in {army_id, war_id, target, origin}:
        return baseline
    assert army_id is not None and war_id is not None
    assert target is not None and origin is not None
    if phase in {"native_war_route_preview", "native_war_route_preview_unsupported"}:
        preview_target = (
            baseline.get("route_preview", {}).get("target_province_id")
            if isinstance(baseline.get("route_preview"), dict)
            else None
        )
        if preview_target != target:
            return baseline
    if phase in {"native_war_pursuit", "native_war_pursuit_progress"}:
        pursuit = baseline.get("pursuit")
        if not (
            isinstance(pursuit, dict)
            and pursuit.get("war_id") == war_id
            and pursuit.get("target_province_id") == target
        ):
            # An idle army can be holding a different siege objective while
            # this observed hostile siege continues.  Do not let that hold
            # advance bypass the relief forecast; preserve other typed plans.
            if not (
                phase == "native_war_pursuit_progress"
                and baseline.get("selected_step") == "life-advance"
            ):
                return baseline

    evidence = {
        "siege_relief": candidate,
        "baseline_phase": phase,
        "baseline_selected_step": baseline.get("selected_step"),
        "forecast_status": "research_only",
        "active_attack_allowed": False,
    }

    def blocked(
        reason: str, required: str, *, detail: dict[str, object] | None = None
    ) -> dict[str, object]:
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_siege_forecast_observation_blocked",
            "selected_step": None,
            "required_observation": required,
            "reason": reason,
            **evidence,
            **(detail or {}),
        }

    if origin == target:
        return blocked(
            "the subject is already at the hostile siege; a route-entry encounter cannot be inferred",
            "fresh-route-entry-and-contact-scope",
        )
    preview_step = preview_move_army_step(army_id, target)
    preview = _fresh_move_route_preview(
        commands,
        army_id=army_id,
        origin_province_id=origin,
        target_province_id=target,
        date_raw=_native_int(snapshot.get("date_raw")),
    )
    if preview is None:
        if preview_step not in action_steps:
            return blocked("the exact route preview is unavailable", preview_step)
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_siege_forecast_route_preview",
            "selected_step": preview_step,
            "reason": "read the route to the observed enemy siege before deriving its battle entry Province",
            **evidence,
        }
    route = preview.get("route_province_ids")
    if not (
        preview.get("status") == "available"
        and isinstance(route, list)
        and route
        and route[-1] == target
        and all(_native_int(hop) is not None and hop > 0 for hop in route)
    ):
        return blocked(
            "the native preview does not prove a complete route into the siege Province",
            "fresh-complete-siege-route-preview",
            detail={"route_preview": preview},
        )
    entry = route[-2] if len(route) > 1 else origin
    if entry == target:
        return blocked(
            "the route does not identify a distinct final entry Province",
            "exact-adjacent-attacker-entry",
            detail={"route_preview": preview},
        )
    hostile_ids = tuple(
        sorted(
            {
                enemy_id
                for enemy in enemy_armies_from_wars(active_wars)
                if isinstance(enemy, dict)
                and _army_tactical_state(enemy) != "retreating"
                and (enemy_id := _native_int(enemy.get("army_id"))) is not None
                and enemy_id > 0
            }
        )
    )
    if not 0 < len(hostile_ids) <= MAX_ROUTE_CONTACT_HOSTILE_IDS:
        return blocked("the full hostile contact roster is unavailable", "complete-hostile-contact-roster")
    contact_step = query_route_contact_horizon_step(army_id, target, hostile_ids)
    contact = _fresh_route_contact_horizon(
        commands,
        snapshot,
        army_id=army_id,
        origin_province_id=origin,
        target_province_id=target,
        hostile_army_ids=hostile_ids,
        route_province_ids=route,
    )
    if contact is None:
        if contact_step not in action_steps:
            return blocked("the exact route contact query is unavailable", contact_step)
        return {
            "policy": "one-life-turn-v1",
            "phase": "native_war_siege_forecast_contact_query",
            "selected_step": contact_step,
            "reason": "read the full hostile contact timeline before forming a hypothetical siege battle input",
            "route_preview": preview,
            **evidence,
        }
    contact_conflicts = contact.get("conflicts")
    target_enemy_ids = {
        _native_int(row.get("army_id"))
        for war in active_wars
        if isinstance(war, dict) and war.get("war_id") == war_id
        for row in war.get("enemy_armies", [])
        if isinstance(row, dict)
        and row.get("current_province_id") == target
        and _native_int(row.get("army_id")) is not None
    }
    target_only_contact = bool(
        isinstance(contact_conflicts, list)
        and contact_conflicts
        and all(
            isinstance(conflict, dict)
            and conflict.get("province_id") == target
            and _native_int(conflict.get("hostile_army_id")) in target_enemy_ids
            for conflict in contact_conflicts
        )
    )
    if contact.get("one_day_contact_free") is not True and not target_only_contact:
        return blocked(
            "contact can occur outside the proposed siege encounter; this target forecast would not cover it",
            "contact-safe-entry-to-siege-target",
            detail={"route_preview": preview, "route_contact_horizon": contact},
        )
    balance = candidate.get("army_strength_balance")
    war = next(
        (row for row in active_wars if isinstance(row, dict) and row.get("war_id") == war_id),
        None,
    )
    enemy_rows = war.get("enemy_armies") if isinstance(war, dict) else None
    defenders = (
        tuple(sorted(_native_int(row.get("army_id")) for row in enemy_rows))
        if isinstance(enemy_rows, list)
        and enemy_rows
        and all(
            isinstance(row, dict)
            and _native_int(row.get("army_id")) is not None
            and row.get("current_province_id") == target
            and _army_tactical_state(row) == "sieging"
            for row in enemy_rows
        )
        else ()
    )
    if not (
        isinstance(balance, dict)
        and balance.get("friendly_army_ids") == [army_id]
        and sorted(balance.get("enemy_army_ids", [])) == list(defenders)
        and defenders
    ):
        return blocked(
            "the observed siege does not prove a complete one-encounter participant partition",
            "exact-attacker-defender-participant-scope",
            detail={"route_preview": preview, "route_contact_horizon": contact},
        )
    query_step = query_combat_simulation_inputs_v3_step(
        target, entry, [army_id], list(defenders)
    )
    attempted_on_current_date = False
    for row in reversed(_history_after_latest_restore(commands)):
        if parse_query_combat_simulation_inputs_v3_step(_effective_command(row)) != (
            target, entry, [army_id], list(defenders)
        ):
            continue
        result = _effective_command_result(row)
        attempted_on_current_date = bool(
            _native_int(row.get("index")) is not None
            and int(row["index"]) > _latest_life_advance_index(commands)
        )
        if not (
            isinstance(result, dict)
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == snapshot.get("native_revision")
        ):
            break
        payload = snapshot.get("combat_simulation_inputs_v3")
        completeness = payload.get("completeness") if isinstance(payload, dict) else None
        if not (
            snapshot.get("combat_simulation_inputs_v3_target_province_id") == target
            and snapshot.get("combat_simulation_inputs_v3_attacker_entry_province_id") == entry
            and snapshot.get("combat_simulation_inputs_v3_attacker_army_ids") == [army_id]
            and snapshot.get("combat_simulation_inputs_v3_defender_army_ids") == list(defenders)
            and snapshot.get("combat_simulation_inputs_v3_queried_snapshot_id") == snapshot.get("snapshot_id")
            and snapshot.get("combat_simulation_inputs_v3_queried_revision") == snapshot.get("revision")
            and snapshot.get("combat_simulation_inputs_v3_status") == result.get("status")
            and isinstance(completeness, dict)
        ):
            return blocked(
                "the v3 query returned but its generation-bound cached readback is absent or mismatched",
                "fresh-v3-cache-readback",
                detail={"route_preview": preview, "route_contact_horizon": contact},
            )
        qualified = _qualified_siege_forecast_move(
            snapshot,
            war_id=war_id,
            army_id=army_id,
            target_province_id=target,
            entry_province_id=entry,
            defender_army_ids=defenders,
            contact_scope_safe=(
                contact.get("one_day_contact_free") is True
                or target_only_contact
            ),
        )
        if qualified.get("status") == "ready":
            move_step = move_army_step(army_id, target)
            if move_step not in action_steps:
                return blocked(
                    "the qualified forecast has no advertised typed move action",
                    move_step,
                    detail={"qualified_forecast": qualified},
                )
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_siege_forecast_move",
                "selected_step": move_step,
                "reason": "the same-frame qualified combat forecast favors siege relief over avoid and wait/reinforce within its risk limits",
                "route_preview": preview,
                "route_contact_horizon": contact,
                "qualified_forecast": qualified,
                **{**evidence, "forecast_status": "qualified", "active_attack_allowed": True},
            }
        provisional = _provisional_defense_research_assessment(
            snapshot,
            target_province_id=target,
            entry_province_id=entry,
            attacker_army_id=army_id,
            defender_army_ids=defenders,
            friendly_current_soldiers=int(balance["friendly_current_soldiers"]),
        )
        if provisional.get("status") == "provisional_admissible":
            # The native route is a real proposal, but the v3 battle is a
            # conditional encounter at its final entry.  A long route must
            # stop at its first waypoint; it cannot spend today's model result
            # on an encounter many days in the future.
            termination_rows = snapshot.get("war_termination_options")
            same_frame_termination = [
                row for row in termination_rows
                if isinstance(row, dict)
                and _same_frame_termination_row(snapshot, row, war_id)
            ] if isinstance(termination_rows, list) else []
            if len(same_frame_termination) != 1:
                terminal_step = query_war_termination_options_step(war_id)
                if terminal_step in action_steps:
                    return {
                        "policy": "one-life-turn-v1",
                        "phase": "native_war_provisional_defense_terminal_query",
                        "selected_step": terminal_step,
                        "reason": "compare same-frame war exits before a provisional relief march",
                        "provisional_forecast": provisional,
                        **evidence,
                    }
                return blocked(
                    "same-frame war exit options are unavailable",
                    terminal_step,
                    detail={"provisional_forecast": provisional},
                )
            terminal = same_frame_termination[0]
            option_rows = terminal.get("options")
            if not isinstance(option_rows, dict):
                return blocked(
                    "same-frame war exit options are incomplete",
                    "complete-same-frame-war-termination-options",
                    detail={"provisional_forecast": provisional},
                )
            safe_exit = any(
                isinstance(option_rows.get(name), dict)
                and option_rows[name].get("available") is True
                and option_rows[name].get("terms_observable") is True
                and (
                    name == "victory"
                    or (
                        isinstance(option_rows[name].get("recipient_response"), dict)
                        and option_rows[name]["recipient_response"].get("would_accept_now") is True
                    )
                )
                for name in ("victory", "white_peace")
            )
            if safe_exit:
                return blocked(
                    "a legal, observable and accepted noncombat war exit is available",
                    "compare-or-select-safe-war-termination",
                    detail={"provisional_forecast": provisional},
                )
            trial = {
                "provisional_forecast": provisional,
                "terminal_comparison": {
                    "war_id": war_id,
                    "safe_noncombat_exit_available": False,
                    "surrender_terms_observable": (
                        option_rows.get("surrender", {}).get("terms_observable")
                        if isinstance(option_rows.get("surrender"), dict) else None
                    ),
                },
                "model_error_policy": "reobserve_route_roster_and_simulation_before_contact",
                "qualified_forecast": qualified,
            }
            arrival_raws = (
                contact.get("subject_route", {}).get("arrival_date_raws")
                if isinstance(contact.get("subject_route"), dict) else None
            )
            final_arrival = (
                _native_int(arrival_raws[-1])
                if isinstance(arrival_raws, list) and arrival_raws else None
            )
            date_raw = _native_int(snapshot.get("date_raw"))
            if (
                len(route) == 1
                and target_only_contact
                and final_arrival is not None
                and date_raw is not None
                and date_raw < final_arrival <= date_raw + 24
            ):
                move_step = move_army_step(army_id, target)
                if move_step not in action_steps:
                    return blocked("typed contact move is unavailable", move_step, detail=trial)
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_provisional_defense_contact_move",
                    "selected_step": move_step,
                    "reason": "fresh same-frame research trial admits one immediate siege contact within its provisional loss budget",
                    "route_preview": preview,
                    "route_contact_horizon": contact,
                    **trial,
                    **{**evidence, "forecast_status": "provisional_trial", "active_attack_allowed": True},
                }
            if not (
                len(route) > 1
                and contact.get("one_day_contact_free") is True
                and contact_conflicts == []
            ):
                return blocked(
                    "the route is neither a contact-free first segment nor an immediate proved contact",
                    "fresh-short-segment-or-immediate-contact",
                    detail=trial,
                )
            first_hop = route[0]
            short_preview_step = preview_move_army_step(army_id, first_hop)
            short_preview = _fresh_move_route_preview(
                commands, army_id=army_id, origin_province_id=origin,
                target_province_id=first_hop, date_raw=date_raw,
            )
            if short_preview is None:
                if short_preview_step not in action_steps:
                    return blocked("first-hop route preview is unavailable", short_preview_step, detail=trial)
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_provisional_defense_short_preview",
                    "selected_step": short_preview_step,
                    "reason": "read a first-hop route that cannot commit the distant siege contact",
                    **trial, **evidence,
                }
            if not (
                short_preview.get("status") == "available"
                and short_preview.get("route_province_ids") == [first_hop]
            ):
                return blocked("first-hop preview has another route", "exact-one-hop-preview", detail=trial)
            short_contact_step = query_route_contact_horizon_step(army_id, first_hop, hostile_ids)
            short_contact = _fresh_route_contact_horizon(
                commands, snapshot, army_id=army_id, origin_province_id=origin,
                target_province_id=first_hop, hostile_army_ids=hostile_ids,
                route_province_ids=[first_hop],
            )
            if short_contact is None:
                if short_contact_step not in action_steps:
                    return blocked("first-hop contact query is unavailable", short_contact_step, detail=trial)
                return {
                    "policy": "one-life-turn-v1",
                    "phase": "native_war_provisional_defense_short_contact_query",
                    "selected_step": short_contact_step,
                    "reason": "read next-day contact safety for the short relief segment",
                    "short_route_preview": short_preview,
                    **trial, **evidence,
                }
            if not (
                short_contact.get("one_day_contact_free") is True
                and short_contact.get("conflicts") == []
            ):
                return blocked(
                    "the first segment has a possible next-day contact",
                    "contact-free-first-segment",
                    detail={**trial, "short_route_contact_horizon": short_contact},
                )
            move_step = move_army_step(army_id, first_hop)
            if move_step not in action_steps:
                return blocked("typed first-hop move is unavailable", move_step, detail=trial)
            return {
                "policy": "one-life-turn-v1",
                "phase": "native_war_provisional_defense_short_move",
                "selected_step": move_step,
                "reason": "the provisional model favors relief; commit only one contact-free waypoint, then observe again",
                "route_preview": preview,
                "route_contact_horizon": contact,
                "short_route_preview": short_preview,
                "short_route_contact_horizon": short_contact,
                **trial,
                **{**evidence, "forecast_status": "provisional_trial", "active_attack_allowed": False},
            }
        return blocked(
            "the exact v3 input readback has no qualified battle probability and expected-utility decision authorizing contact",
            "qualified-same-frame-combat-forecast-and-expected-utility",
            detail={
                "phase": "native_war_siege_forecast_inputs_observed",
                "route_preview": preview,
                "route_contact_horizon": contact,
                "qualified_forecast": qualified,
                "provisional_forecast": provisional,
                "combat_inputs_v3_query": {
                    "step": query_step,
                    "accepted": result.get("accepted"),
                    "status": result.get("status"),
                    "queried_snapshot_id": result.get("queried_snapshot_id"),
                    "queried_revision": result.get("queried_revision"),
                    "queried_native_revision": result.get("queried_native_revision"),
                    "monte_carlo_ready": (
                        completeness.get("monte_carlo_ready")
                        if isinstance(completeness, dict)
                        else None
                    ),
                    "planner_usable": (
                        completeness.get("planner_usable")
                        if isinstance(completeness, dict)
                        else None
                    ),
                },
            },
        )
    if attempted_on_current_date:
        return blocked(
            "the same siege input query was already attempted in this date epoch without a reusable current-frame result",
            "fresh-v3-query-after-state-change",
            detail={"route_preview": preview, "route_contact_horizon": contact},
        )
    if QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY not in bridge_capabilities:
        return blocked("the exact v3 read-only query is unavailable", query_step)
    return {
        "policy": "one-life-turn-v1",
        "phase": "native_war_siege_forecast_inputs_query",
        "selected_step": query_step,
        "reason": "read exact same-frame combat v3 inputs for the observed siege encounter; no attack is authorized",
        "route_preview": preview,
        "route_contact_horizon": contact,
        **evidence,
    }


def _provisional_defense_research_assessment(
    snapshot: dict[str, object],
    *,
    target_province_id: int,
    entry_province_id: int,
    attacker_army_id: int,
    defender_army_ids: tuple[int, ...],
    friendly_current_soldiers: int,
) -> dict[str, object]:
    """Use the current v3 frame as a bounded, explicitly imperfect trial."""

    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    lifecycle = snapshot.get("succession_lifecycle")
    if not (
        isinstance(hello, dict)
        and hello.get("ck3_build_match") is True
        and hello.get("expected_ck3_sha256")
        == "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
        and isinstance(lifecycle, dict)
        and lifecycle.get("lifecycle") == ORDINARY_CAMPAIGN_SUCCESSION
        and lifecycle.get("xar_enabled") == "xar_off"
    ):
        return {"status": "exact_build_or_profile_unavailable"}
    payload = snapshot.get("combat_simulation_inputs_v3")
    if not isinstance(payload, dict):
        return {"status": "same_frame_v3_unavailable"}
    completeness = payload.get("completeness")
    base = payload.get("base_inputs")
    scenario = base.get("scenario") if isinstance(base, dict) else None
    if not (
        isinstance(completeness, dict)
        and completeness.get("input_observation_ready") is True
        and isinstance(base, dict)
        and isinstance(scenario, dict)
        and base.get("target_province_id") == target_province_id
        and scenario.get("attacker_entry_province_id") == entry_province_id
        and scenario.get("attacker_army_ids") == [attacker_army_id]
        and scenario.get("defender_army_ids") == list(defender_army_ids)
        and scenario.get("attacker_side") == "player_or_allied"
        and scenario.get("defender_side") == "enemy"
        and scenario.get("actual_route_dependency") is False
        and len(defender_army_ids) == 1
        and friendly_current_soldiers > 0
    ):
        return {"status": "same_frame_encounter_scope_mismatch"}
    forecast = forecast_fixed_contact(
        payload,
        target_province_id=target_province_id,
        attacker_entry_province_id=entry_province_id,
        attacker_army_ids=(attacker_army_id,),
        defender_army_ids=defender_army_ids,
        capture={
            key: snapshot.get(key)
            for key in ("snapshot_id", "revision", "native_revision", "date_raw")
        },
        sample_count=_PROVISIONAL_DEFENSE_TRIALS,
        horizon_days=_PROVISIONAL_DEFENSE_HORIZON_DAYS,
    )
    if forecast.get("status") != "estimated":
        return {
            "status": "research_trial_unavailable",
            "model_status": forecast.get("status"),
        }
    admission = contact_admission(forecast, defensive_relief=True)
    wilson = forecast.get("resolved_win_wilson95")
    wilson_low = wilson.get("lower") if isinstance(wilson, dict) else None
    p90_hard_loss = forecast.get("player_p90_hard_loss_raw")
    hard_loss_budget_raw = (
        friendly_current_soldiers
        * 100_000
        * _PROVISIONAL_DEFENSE_MAX_P90_HARD_LOSS_PERCENT
        // 100
    )
    admitted = bool(
        admission["admitted"] is True
        and isinstance(p90_hard_loss, int)
        and p90_hard_loss <= hard_loss_budget_raw
    )
    return {
        "status": "provisional_admissible" if admitted else "model_risk_budget_exceeded",
        "model_fidelity": "research_only_phase_events_disabled",
        "calibrated_win_probability_available": False,
        "input_sha256": forecast["input_sha256"],
        "simulator_build": forecast["simulator_build"],
        "sample_count": forecast["sample_count"],
        "player_wins": forecast["player_wins"],
        "player_losses": forecast["player_losses"],
        "no_resolution": forecast["no_resolution"],
        "model_resolved_win_wilson_low": wilson_low,
        "model_p90_hard_loss_raw": p90_hard_loss,
        "hard_loss_budget_raw": hard_loss_budget_raw,
        "model_stack_wipe_fraction": forecast["player_stack_wipe_probability"],
        "model_character_death_fraction": forecast["commander_or_knight_death_probability"],
        "unmodeled_domains": forecast["missing_required_domains"],
        "contact_admission": admission,
        "observation_identity": {
            key: snapshot.get(key)
            for key in ("episode_run_id", "snapshot_id", "revision", "native_revision", "date_raw")
        },
    }


def _qualified_siege_forecast_move(
    snapshot: dict[str, object],
    *,
    war_id: int,
    army_id: int,
    target_province_id: int,
    entry_province_id: int,
    defender_army_ids: tuple[int, ...],
    contact_scope_safe: bool,
) -> dict[str, object]:
    """Consume the existing combat-entry EU contract for one exact encounter.

    The production contract currently has no qualified forecast producer or
    activation.  A separately bound trial-component tape may still be assessed
    here so the same calculator used by research and film reaches the agent's
    actual decision seam without bypassing the fidelity gate.
    """
    payload = snapshot.get("combat_entry_eu_v1")
    if not isinstance(payload, dict):
        return {"status": "producer_unavailable"}
    identity = payload.get("identity")
    if not isinstance(identity, dict):
        return {"status": "identity_unavailable"}
    frame = identity.get("observation")
    expected_frame = {
        key: snapshot.get(key)
        for key in (
            "episode_run_id", "snapshot_id", "revision", "native_revision"
        )
    }
    if not (
        isinstance(frame, dict)
        and frame == expected_frame
        and identity.get("forecast") == expected_frame
        and identity.get("war_id") == war_id
        and identity.get("target_province_id") == target_province_id
        and identity.get("entry_province_id") == entry_province_id
        and identity.get("player_ordered_army_ids") == [army_id]
        and identity.get("opponent_ordered_army_ids") == list(defender_army_ids)
    ):
        return {"status": "encounter_identity_mismatch"}
    try:
        assessment = combat_entry_eu.assess_combat_entry_eu_contract(
            payload,
            action_components=snapshot.get("combat_entry_action_components_v1"),
        )
    except (combat_entry_eu.CombatEntryEuContractError, KeyError, TypeError, ValueError):
        return {"status": "contract_invalid"}
    result: dict[str, object] = {
        "status": "contract_blocked",
        "assessment_sha256": assessment.get("assessment_sha256"),
        "contract_status": assessment.get("status"),
        "blockers": assessment.get("blockers"),
        "action_components_ready": assessment.get("action_components_ready", False),
        "candidate_action": assessment.get("candidate_action"),
    }
    if not (
        combat_entry_eu.COMBAT_ENTRY_EU_ACTIVATION_ENABLED
        and contact_scope_safe
        and assessment.get("contract_sha256")
        == combat_entry_eu.COMBAT_ENTRY_EU_CONTRACT_SHA256
        and assessment.get("external_inputs_ready") is True
        and assessment.get("automatic_attack_enabled") is True
        and assessment.get("decision_status") == "selected"
        and assessment.get("selected_action") == "attack"
    ):
        return result
    policy = payload.get("utility_policy")
    distribution = payload.get("distribution")
    tails = payload.get("character_tails")
    if not (
        isinstance(policy, dict)
        and isinstance(distribution, dict)
        and isinstance(tails, dict)
        and isinstance(policy.get("risk_constraints"), dict)
        and isinstance(distribution.get("resolved_win_wilson95"), dict)
    ):
        return result
    risk = policy["risk_constraints"]
    wilson_low = distribution["resolved_win_wilson95"].get("low_raw")
    stack_wipe = distribution.get("player_stack_wipe_probability_raw")
    catastrophe = tails.get("player_one_life_catastrophic_probability_raw")
    attack = assessment.get("eu_attack_raw")
    avoid = assessment.get("eu_avoid_raw")
    wait = assessment.get("eu_wait_reinforce_raw")
    margin = assessment.get("attack_margin_raw")
    minimum_margin = policy.get("minimum_attack_margin_raw")
    if not all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in (wilson_low, stack_wipe, catastrophe, attack, avoid,
                      wait, margin, minimum_margin)
    ):
        return result
    if not (
        wilson_low >= risk["min_resolved_win_wilson_low_raw"]
        and stack_wipe <= risk["max_player_stack_wipe_probability_raw"]
        and catastrophe
        <= risk["max_player_one_life_catastrophic_probability_raw"]
        and margin == attack - max(avoid, wait)
        and margin > minimum_margin
    ):
        return result
    return {
        "status": "ready",
        "assessment_sha256": assessment["assessment_sha256"],
        "simulator_version": payload["experiment"]["simulator_version"],
        "simulator_sha256": payload["experiment"]["simulator_sha256"],
        "player_win_probability_raw": distribution["player_win_probability_raw"],
        "resolved_win_wilson95_low_raw": wilson_low,
        "player_stack_wipe_probability_raw": stack_wipe,
        "player_one_life_catastrophic_probability_raw": catastrophe,
        "eu_attack_raw": attack,
        "eu_avoid_raw": avoid,
        "eu_wait_reinforce_raw": wait,
        "attack_margin_raw": margin,
    }


def _primary_defender_siege_relief_assessment(
    snapshot: dict[str, object],
    *,
    commands: list[dict[str, object]],
    active_wars: list[dict[str, object]],
    controlled_armies: list[dict[str, object]],
    pursuit_army: dict[str, object] | None,
    battle_control_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Select one observed hostile siege for a proof-bound relief route.

    R0160 showed that a seven-day objective hold can lose an occupied county
    while a much stronger sole army remains stationary.  Strength is only a
    participant-scope observation here, never permission to make contact.
    Every complete relief candidate needs the same route/contact/v3 before
    either a qualified forecast or a bounded provisional model/loss-budget
    decision can select a typed move.
    """

    siege_rows: list[tuple[dict[str, object], dict[str, object]]] = []
    for war in active_wars:
        if not (
            isinstance(war, dict)
            and war.get("player_side") == "defender"
            and war.get("player_is_primary_war_leader") is True
            and _native_int(war.get("war_id")) is not None
            and isinstance(war.get("player_relative_war_score"), int)
            and not isinstance(war.get("player_relative_war_score"), bool)
            and -100 < int(war["player_relative_war_score"]) < 100
        ):
            continue
        enemies = war.get("enemy_armies")
        if not isinstance(enemies, list):
            continue
        for enemy in enemies:
            if (
                isinstance(enemy, dict)
                and _army_tactical_state(enemy) == "sieging"
                and enemy.get("retreating") is not True
            ):
                siege_rows.append((war, enemy))
    if not siege_rows:
        return {"status": "not_applicable"}

    if len(controlled_armies) != 1 or pursuit_army is not controlled_armies[0]:
        return {"status": "not_applicable"}
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
    ):
        return {
            "status": "observation_unavailable",
            "required_observation": "single-idle-controllable-army-binding",
        }
    army = controlled_armies[0]
    army_id = _native_int(army.get("army_id"))
    if _army_tactical_state(army) == "combat":
        frames = (
            battle_control_state.get("full_frames")
            if isinstance(battle_control_state, dict)
            and battle_control_state.get("status") == "ready"
            else None
        )
        current_province_id = _native_int(army.get("current_province_id"))
        if (
            army.get("in_combat") is True
            and army.get("retreating") is False
            and army_id is not None
            and current_province_id is not None
            and isinstance(frames, list)
            and len(frames) == 1
            and isinstance(frames[0], dict)
            and frames[0].get("status") == "available"
            and frames[0].get("battle_control_ready") is True
            and _native_int(frames[0].get("subject_public_cunit_id"))
            == army_id
            and _native_int(frames[0].get("province_id"))
            == current_province_id
            and _native_int(frames[0].get("observed_date_raw"))
            == _native_int(snapshot.get("date_raw"))
            and (_native_int(frames[0].get("combat_id")) or 0) > 0
        ):
            return {
                "status": "active_combat",
                "army_id": army_id,
                "combat_id": frames[0]["combat_id"],
            }
        return {
            "status": "observation_unavailable",
            "required_observation": "same-frame-active-combat-binding",
        }
    observed_target = _native_int(army.get("move_target_province_id"))
    observed_route = army.get("route_province_ids")
    complete_observed_route = bool(
        observed_target is not None
        and observed_target > 0
        and isinstance(observed_route, list)
        and observed_route
        and all(
            _native_int(province_id) is not None
            and int(province_id) > 0
            for province_id in observed_route
        )
        and observed_route[-1] == observed_target
    )
    # R0176: CK3 can retain siege stance while an accepted march still has
    # an exact target and route.  Keep that case behind the existing typed
    # move proof rather than treating the Army as idle relief capacity.
    routed_siege_stance = bool(
        _army_tactical_state(army) == "sieging"
        and army.get("in_combat") is False
        and army.get("retreating") is False
        and complete_observed_route
    )
    moving = bool(
        _army_tactical_state(army) in {"moving", "embarked"}
        or _native_int(army.get("army_state_code")) in {4, 7}
        or routed_siege_stance
    )
    if moving:
        intent = (
            _active_native_move_intent(
                commands,
                snapshot,
                army_id=army_id,
                target_province_id=observed_target,
            )
            if army_id is not None
            and complete_observed_route
            else None
        )
        if isinstance(intent, dict):
            return {
                "status": "active_move_intent",
                "army_id": army_id,
                "target_province_id": observed_target,
                "route_province_ids": list(observed_route),
                "move_intent": intent,
            }
        return {
            "status": "observation_unavailable",
            "required_observation": (
                "complete-matching-active-native-move-intent-route"
            ),
        }
    current_province_id = _native_int(army.get("current_province_id"))
    if (
        _army_tactical_state(army) == "sieging"
        and army.get("in_combat") is False
        and army.get("retreating") is False
        and "move_target_province_id" in army
        and army.get("move_target_province_id") is None
        and army.get("route_province_ids") == []
        and army_id is not None
        and current_province_id is not None
    ):
        arrival = _accepted_native_move_arrival(
            commands,
            snapshot,
            army_id=army_id,
            target_province_id=current_province_id,
        )
        if isinstance(arrival, dict):
            return {
                "status": "arrived_sieging",
                "army_id": army_id,
                "target_province_id": current_province_id,
                "move_arrival": arrival,
            }
        return {
            "status": "observation_unavailable",
            "required_observation": (
                "accepted-native-move-arrival-for-current-siege"
            ),
        }
    if not (
        army_id is not None
        and current_province_id is not None
        and _army_tactical_state(army) == "regular"
        and army.get("in_combat") is False
        and army.get("retreating") is False
        and "move_target_province_id" in army
        and army.get("move_target_province_id") is None
        and army.get("route_province_ids") == []
    ):
        return {
            "status": "observation_unavailable",
            "required_observation": "single-idle-controllable-army-binding",
        }

    forecast_candidates: list[
        tuple[int, int, int, int, dict[str, object]]
    ] = []
    incomplete_war_ids: set[int] = set()
    for war, enemy in siege_rows:
        war_id = int(war["war_id"])
        enemy_id = _native_int(enemy.get("army_id"))
        target = _native_int(enemy.get("current_province_id"))
        route = enemy.get("route_province_ids")
        complete_stationary_siege = bool(
            enemy_id is not None
            and target is not None
            and target > 0
            and enemy.get("in_combat") is False
            and enemy.get("retreating") is False
            and "move_target_province_id" in enemy
            and enemy.get("move_target_province_id") is None
            and isinstance(route, list)
            and not route
        )
        balance = _same_frame_army_strength_balance(snapshot, war_id)
        if not complete_stationary_siege or not isinstance(balance, dict):
            incomplete_war_ids.add(war_id)
            continue
        friendly_ids = balance.get("friendly_army_ids")
        enemy_ids = balance.get("enemy_army_ids")
        published_enemy_ids = {
            enemy_id
            for row in war.get("enemy_armies", [])
            if isinstance(row, dict)
            and _army_tactical_state(row) != "retreating"
            and (enemy_id := _native_int(row.get("army_id"))) is not None
        }
        numeric = (
            _native_int(balance.get("friendly_current_soldiers")),
            _native_int(balance.get("enemy_current_soldiers")),
            _native_int(balance.get("friendly_ai_base_power_raw")),
            _native_int(balance.get("enemy_ai_base_power_raw")),
        )
        if not (
            isinstance(friendly_ids, list)
            and army_id in friendly_ids
            and isinstance(enemy_ids, list)
            and enemy_id in enemy_ids
            and set(enemy_ids) == published_enemy_ids
            and all(value is not None and value > 0 for value in numeric)
        ):
            incomplete_war_ids.add(war_id)
            continue
        forecast_candidates.append(
            (
                int(war["player_relative_war_score"]),
                war_id,
                int(enemy_id),
                int(target),
                balance,
            )
        )
    if incomplete_war_ids:
        return {
            "status": "observation_unavailable",
            "required_observation": (
                "complete-same-frame-siege-position-and-war-strength"
            ),
            "war_ids": sorted(incomplete_war_ids),
        }
    score, war_id, enemy_id, target, balance = min(forecast_candidates)
    return {
        "status": "forecast_required",
        "selection_policy": "lowest-score-then-war-enemy-province",
        "war_id": war_id,
        "player_relative_war_score": score,
        "army_id": army_id,
        "enemy_army_id": enemy_id,
        "target_province_id": target,
        "army_strength_balance": dict(balance),
        "candidate_count": len(forecast_candidates),
        "reason": "qualified_same_frame_combat_forecast_required_for_siege_contact",
    }


def _native_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _noncombat_sentinel_timeline_speed(
    readiness: dict[str, object] | None,
    *,
    sentinel_scope: str,
) -> int:
    """Select one explicitly configured and admitted noncombat speed.

    Production remains speed 3 until the requested scope has its own live
    matrix.  The shared research flag is the only pre-live route to speed
    4/5, so one scope cannot accidentally inherit another scope's evidence.
    """
    configured = (
        _native_int(readiness.get("noncombat_sentinel_timeline_speed"))
        if isinstance(readiness, dict)
        else None
    )
    if configured not in {1, 2, 3, 4, 5}:
        return 3
    if configured <= 3:
        return configured
    if (
        isinstance(readiness, dict)
        and readiness.get("noncombat_sentinel_high_speed_ab") is True
    ):
        return configured
    readiness_prefix = {
        "committed_route": "committed_route_sentinel",
        "stationary_objective_hold": "stationary_objective_hold_sentinel",
    }.get(sentinel_scope)
    if (
        readiness_prefix is not None
        and isinstance(readiness, dict)
        and readiness.get(
            f"{readiness_prefix}_speed_{configured}_live_ready"
        )
        is True
    ):
        return configured
    return 3


def _army_tactical_state(army: dict[str, object]) -> str | None:
    # CK3 can keep the retreat bit set while the named movement state changes
    # to ``embarked``.  The native sentinel admission already treats those
    # explicit booleans as authoritative; give them the same precedence here
    # so the planner never submits a committed-route sentinel for a retreat.
    if army.get("retreating") is True:
        return "retreating"
    if army.get("in_combat") is True:
        return "combat"
    named = army.get("army_state")
    if isinstance(named, str):
        return named.casefold()
    code = _native_int(army.get("army_state_code"))
    if code is not None:
        return {2: "combat", 3: "sieging", 6: "retreating", 7: "moving"}.get(code)
    return None


def _stationary_objective_hold_sentinel_substitution(
    baseline_plan: dict[str, object],
    snapshot: dict[str, object],
    *,
    active_wars: list[dict[str, object]],
    player_armies: list[dict[str, object]],
    war_summary: list[dict[str, object]],
    enabled: bool,
    action_available: bool,
    timeline_speed: int,
    high_speed_ab: bool,
) -> dict[str, object] | None:
    """Replace one already-selected stationary ``life-advance`` action.

    This helper is intentionally downstream of the ordinary war planner.  It
    receives the baseline decision, then proves that its exact tactical WarID,
    controllable subject and preferred objective are the same binding that the
    native sentinel will watch.  It never searches a second war or chooses a
    different objective merely because that objective happens to be occupied.
    """
    pursuit = baseline_plan.get("pursuit")
    if not (
        enabled
        and action_available
        and baseline_plan.get("phase") == "native_war_pursuit_progress"
        and baseline_plan.get("selected_step") == "life-advance"
        and isinstance(pursuit, dict)
        and pursuit.get("target_source") == "war_objective_province"
        and pursuit.get("objective_kind") == "siege"
    ):
        return None
    war_id = _native_int(pursuit.get("war_id"))
    subject_army_id = _native_int(pursuit.get("army_id"))
    objective_province_id = _native_int(
        pursuit.get("target_province_id")
    )
    if (
        war_id is None
        or war_id <= 0
        or subject_army_id is None
        or subject_army_id <= 0
        or objective_province_id is None
        or objective_province_id <= 0
    ):
        return None
    tactical_war = _stable_tactical_war(active_wars)
    if not (
        isinstance(tactical_war, dict)
        and _native_int(tactical_war.get("war_id")) == war_id
        and objective_province_id
        in war_objective_province_ids([tactical_war])
    ):
        return None
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and player_armies
    ):
        return None
    army_by_id: dict[int, dict[str, object]] = {}
    watch_ids: list[int] = []
    for army in player_armies:
        army_id = _native_int(army.get("army_id"))
        named_state = army.get("army_state")
        state_code = _native_int(army.get("army_state_code"))
        regular = bool(
            (
                isinstance(named_state, str)
                and named_state.casefold() == "regular"
            )
            or (named_state is None and state_code == 1)
        )
        route = army.get("route_province_ids")
        current = _native_int(army.get("current_province_id"))
        if (
            army_id is None
            or army_id <= 0
            or army_id in army_by_id
            or not regular
            or current is None
            or current <= 0
            or army.get("move_target_province_id") is not None
            or not isinstance(route, list)
            or route
            or army.get("in_combat") is True
            or army.get("retreating") is True
        ):
            return None
        army_by_id[army_id] = army
        if army.get("controllable") is True:
            watch_ids.append(army_id)
    if not (
        watch_ids
        and len(watch_ids) == len(set(watch_ids))
        and len(watch_ids) <= _BATTLE_SENTINEL_MAX_WATCH_ARMIES
    ):
        return None
    subject = army_by_id.get(subject_army_id)
    if not (
        isinstance(subject, dict)
        and subject.get("controllable") is True
        and _native_int(subject.get("current_province_id"))
        == objective_province_id
        and subject.get("move_target_province_id") is None
    ):
        return None

    # Deep objective rows are an optional corroborating source, not an
    # admission prerequisite: the live snapshot can publish an exact
    # objective ID while omitting objective_province_states.  A published
    # player siege still invalidates the hold, while the all-army regular
    # state above independently excludes an unreported player siege/assault.
    for war in active_wars:
        states = war.get("objective_province_states")
        if not isinstance(states, list):
            continue
        for state in states:
            if not isinstance(state, dict):
                continue
            active_siege = state.get("active_siege")
            if (
                isinstance(active_siege, dict)
                and active_siege.get("player_army_besieging") is True
            ):
                return None

    start_date_raw = _native_int(snapshot.get("date_raw"))
    target_date_raw = (
        _stationary_objective_hold_target_date_raw(
            start_date_raw,
            war_summary,
        )
        if start_date_raw is not None
        else None
    )
    if target_date_raw is None:
        return None
    return {
        "policy": "one-life-turn-v1",
        "phase": "native_war_stationary_objective_hold_sentinel",
        "selected_step": war_objective_hold_sentinel_advance_step(
            war_id,
            subject_army_id,
            objective_province_id,
            target_date_raw,
            timeline_speed=timeline_speed,
        ),
        "reason": (
            "the ordinary planner already selected life-advance for this "
            f"same WarID, subject and preferred objective; use its speed-"
            f"{timeline_speed} native sentinel as a seven-day execution-only "
            "substitute without changing the war or target decision"
        ),
        "timeline_policy": (
            f"war_stationary_objective_hold_speed_{timeline_speed}"
        ),
        "timeline_speed": timeline_speed,
        "research_high_speed_ab": bool(
            timeline_speed > 3 and high_speed_ab
        ),
        "sentinel_mode": "decision_epoch",
        "sentinel_scope": "stationary_objective_hold",
        "absolute_target_date_raw": target_date_raw,
        "watch_army_ids": sorted(watch_ids),
        "war_id": war_id,
        "subject_army_id": subject_army_id,
        "objective_province_id": objective_province_id,
        "baseline_decision": {
            "phase": baseline_plan["phase"],
            "selected_step": baseline_plan["selected_step"],
            "war_id": war_id,
            "subject_army_id": subject_army_id,
            "objective_province_id": objective_province_id,
        },
        "exact_war_terminal_watch": False,
        "exact_active_war_set_watch": False,
        "maximum_omitted_state_detection_lag_days": 7,
        "omitted_native_watch_fields": [
            "active_war_set",
            "war_id",
            "war_score",
            "objective_membership",
            "occupation",
            "current_province",
            "army_state",
        ],
        "pursuit": dict(pursuit),
        "active_wars": war_summary,
    }


def _stationary_objective_hold_target_date_raw(
    starting_date_raw: int,
    war_summary: list[dict[str, object]],
) -> int | None:
    """Bound a hold by both its seven-day lease and reused query leases."""
    target = starting_date_raw + 7 * 24
    for war in war_summary:
        reuse = war.get("war_termination_negative_reuse")
        if not isinstance(reuse, dict):
            continue
        expires = _native_int(reuse.get("expires_date_raw"))
        if expires is None:
            continue
        target = min(target, expires)
    return target if target > starting_date_raw else None


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
        before_army_id = _native_int(before.get("besieging_army_id"))
        after_army_id = _native_int(after.get("besieging_army_id"))
        before_army = (
            _progress_army(before_war, "player_armies", before_army_id)
            if before_army_id is not None
            else None
        )
        after_army = (
            _progress_army(after_war, "player_armies", after_army_id)
            if after_army_id is not None
            else None
        )
        if not (
            before_army_id is not None
            and before_army_id == after_army_id
            and isinstance(before_army, dict)
            and isinstance(after_army, dict)
            and _army_tactical_state(before_army) == "sieging"
            and _army_tactical_state(after_army) == "sieging"
            and _native_int(before_army.get("current_province_id"))
            == province_id
            and _native_int(after_army.get("current_province_id"))
            == province_id
        ):
            # CK3 keeps the same SiegeID and primary-besieger flag while the
            # army fights on the objective.  That interval cannot make siege
            # work and therefore breaks, rather than extends, a stall streak.
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


def _latest_merge_result_lifecycle(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
) -> dict[str, object] | None:
    """Fence every merge ACK, including non-split consolidation merges."""
    failed_duplicates: list[dict[str, object]] = []
    for row in reversed(_history_after_latest_restore(commands)):
        step = _effective_command(row)
        parsed = parse_merge_armies_step(step)
        if parsed is None:
            continue
        if row.get("ok") is not True:
            failed_duplicates.append(
                {
                    "status": "submission_failed",
                    "destination_army_id": parsed[0],
                    "source_army_id": parsed[1],
                    "merge_step": step,
                    "history_index": _native_int(row.get("index")),
                    "error": row.get("error"),
                }
            )
            continue
        if failed_duplicates and any(
            failure.get("merge_step") != step
            for failure in failed_duplicates
        ):
            return failed_duplicates[0]
        result = _effective_command_result(row)
        observed = observe_merge_armies_postcondition_v1(
            step, result, snapshot
        )
        lifecycle = {
            **observed,
            "merge_step": step,
            "history_index": _native_int(row.get("index")),
            "war_action": (
                copy.deepcopy(result.get("war_action"))
                if isinstance(result, dict)
                else None
            ),
        }
        if failed_duplicates:
            lifecycle["duplicate_attempt"] = copy.deepcopy(
                failed_duplicates[0]
            )
            lifecycle["duplicate_attempts"] = copy.deepcopy(
                failed_duplicates
            )
        return lifecycle
    if failed_duplicates:
        return failed_duplicates[0]
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
        tactical_state = _army_tactical_state(army)
        if tactical_state in {"combat", "retreating", "gathering"}:
            # CK3 can retain a route target and remaining-route array on the
            # exact frame where an army enters combat. It is no longer a
            # moving sibling for the global route-time conjunction; combat
            # control owns its next transition.
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
            and _army_tactical_state(enemy) != "retreating"
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
            and local_enemy_ids
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
    latest = _latest_accepted_native_move_row(commands, army_id=army_id)
    if latest is None:
        return None
    latest_position, latest_row = latest
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


def _accepted_native_move_arrival(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    army_id: int,
    target_province_id: int,
) -> dict[str, object] | None:
    """Bind a completed route to its accepted typed move.

    R0162 reached the relief target and entered CK3's native sieging state.
    At that point the active intent is correctly closed, but a concurrent
    hostile siege must not erase the proof that this army is already carrying
    out the selected relief operation.
    """

    latest = _latest_accepted_native_move_row(commands, army_id=army_id)
    if latest is None:
        return None
    latest_position, latest_row = latest
    if parse_move_army_step(_effective_command(latest_row)) != (
        army_id,
        target_province_id,
    ):
        return None
    result = latest_row.get("result")
    action = result.get("war_action") if isinstance(result, dict) else None
    if (
        not isinstance(action, dict)
        or action.get("status") not in {"move_submitted", "moving"}
        or result.get("accepted") is False
        or action.get("army_id") not in {None, army_id}
        or action.get("target_province_id")
        not in {None, target_province_id}
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
    if not (
        isinstance(army, dict)
        and _native_int(army.get("current_province_id"))
        == target_province_id
        and _army_tactical_state(army) == "sieging"
        and army.get("in_combat") is False
        and army.get("retreating") is False
        and "move_target_province_id" in army
        and army.get("move_target_province_id") is None
        and army.get("route_province_ids") == []
    ):
        return None
    elapsed_days = _move_intent_elapsed_days(
        commands,
        latest_position=latest_position,
        action=action,
        snapshot=snapshot,
    )
    if (
        elapsed_days >= _NATIVE_MOVE_INTENT_MAX_GAME_DAYS
        and not _accepted_native_move_siege_continuity(
            commands,
            move_position=latest_position,
            army_id=army_id,
            target_province_id=target_province_id,
            submitted_date_raw=_native_int(action.get("submitted_date_raw")),
            current_date_raw=_native_int(snapshot.get("date_raw")),
        )
    ):
        return None
    return {
        "status": "arrived",
        "army_id": army_id,
        "target_province_id": target_province_id,
        "elapsed_days": elapsed_days,
        "timeout_days": _NATIVE_MOVE_INTENT_MAX_GAME_DAYS,
    }


def _accepted_native_move_siege_continuity(
    commands: list[dict[str, object]],
    *,
    move_position: int,
    army_id: int,
    target_province_id: int,
    submitted_date_raw: int | None,
    current_date_raw: int | None,
) -> bool:
    """Keep an arrived siege bound after the travel intent window expires."""

    if submitted_date_raw is None or current_date_raw is None:
        return False
    expected_date_raw = submitted_date_raw
    progress_state = "moving"
    for row in commands[move_position + 1 :]:
        if row.get("ok") is not True:
            continue
        result = _effective_command_result(row)
        before = result.get("war_progress_before") if isinstance(result, dict) else None
        after = result.get("war_progress_after") if isinstance(result, dict) else None
        if not isinstance(before, dict) or not isinstance(after, dict):
            if is_life_advance_step(_effective_command(row)):
                return False
            continue
        before_date_raw = _native_int(before.get("date_raw"))
        after_date_raw = _native_int(after.get("date_raw"))
        if (
            before_date_raw != expected_date_raw
            or after_date_raw is None
            or after_date_raw <= before_date_raw
        ):
            return False
        before_army = _progress_summary_player_army(before, army_id)
        after_army = _progress_summary_player_army(after, army_id)
        if before_army is None or after_army is None:
            return False
        if progress_state == "sieging":
            if not (
                _army_is_sieging_target(before_army, target_province_id)
                and _army_is_sieging_target(after_army, target_province_id)
            ):
                return False
        elif progress_state == "combat":
            if not _army_is_combat_at_target(before_army, target_province_id):
                return False
            if _army_is_sieging_target(after_army, target_province_id):
                progress_state = "sieging"
            elif not _army_is_combat_at_target(after_army, target_province_id):
                return False
        else:
            if not _army_is_moving_to_target(before_army, target_province_id):
                return False
            if _army_is_sieging_target(after_army, target_province_id):
                progress_state = "sieging"
            elif _army_is_combat_at_target(after_army, target_province_id):
                progress_state = "combat"
            elif not _army_is_moving_to_target(after_army, target_province_id):
                return False
        expected_date_raw = after_date_raw
    return progress_state == "sieging" and expected_date_raw == current_date_raw


def _progress_summary_player_army(
    summary: dict[str, object], army_id: int
) -> dict[str, object] | None:
    wars = summary.get("wars")
    if not isinstance(wars, list):
        return None
    armies = [
        army
        for war in wars
        if isinstance(war, dict)
        for army in (war.get("player_armies") or [])
        if isinstance(army, dict) and _native_int(army.get("army_id")) == army_id
    ]
    return armies[0] if armies and all(army == armies[0] for army in armies) else None


def _army_is_moving_to_target(
    army: dict[str, object], target_province_id: int
) -> bool:
    route = army.get("route_province_ids")
    return (
        _army_tactical_state(army) in {"moving", "embarked"}
        and _native_int(army.get("move_target_province_id")) == target_province_id
        and isinstance(route, list)
        and bool(route)
        and _native_int(route[-1]) == target_province_id
        and army.get("in_combat") is False
        and army.get("retreating") is False
    )


def _army_is_sieging_target(
    army: dict[str, object], target_province_id: int
) -> bool:
    return (
        _army_tactical_state(army) == "sieging"
        and _native_int(army.get("current_province_id")) == target_province_id
        and army.get("move_target_province_id") is None
        and army.get("route_province_ids") == []
        and army.get("in_combat") is False
        and army.get("retreating") is False
    )


def _army_is_combat_at_target(
    army: dict[str, object], target_province_id: int
) -> bool:
    return (
        _army_tactical_state(army) == "combat"
        and _native_int(army.get("current_province_id")) == target_province_id
        and army.get("move_target_province_id") is None
        and army.get("route_province_ids") == []
        and army.get("in_combat") is True
        and army.get("retreating") is False
    )


def _latest_accepted_native_move_row(
    commands: list[dict[str, object]],
    *,
    army_id: int,
) -> tuple[int, dict[str, object]] | None:
    """Return the latest move across individually persisted cold restores.

    A move before the latest restore is eligible only when an official saved
    checkpoint between the move and restore has the exact identity consumed
    by that restore.  The current native snapshot still has to prove the
    active route or completed arrival in the caller.
    """

    restores: list[tuple[int, dict[str, object]]] = []
    for position in range(len(commands) - 1, -1, -1):
        row = commands[position]
        if _successful_merge_barrier(row, army_id):
            return None
        command = _effective_command(row)
        if command == "restore-checkpoint" and row.get("ok") is True:
            restores.append((position, row))
            continue
        parsed = parse_move_army_step(command)
        if parsed is None or parsed[0] != army_id:
            continue
        if row.get("ok") is not True:
            return None
        preceding_boundary = position
        for restore_position, restore_row in reversed(restores):
            if not _native_move_persisted_through_restore(
                commands,
                move_position=preceding_boundary,
                restore_position=restore_position,
                restore_row=restore_row,
            ):
                return None
            preceding_boundary = restore_position
        return position, row
    return None


def _native_move_persisted_through_restore(
    commands: list[dict[str, object]],
    *,
    move_position: int,
    restore_position: int,
    restore_row: dict[str, object],
) -> bool:
    restore_result = restore_row.get("result")
    restore_checkpoint = (
        restore_result.get("checkpoint")
        if isinstance(restore_result, dict)
        else None
    )
    if not (
        isinstance(restore_result, dict)
        and restore_result.get("status") == "restored"
        and restore_result.get("source") == "native-session-cold-start"
        and isinstance(restore_checkpoint, dict)
    ):
        return False
    restore_history_index = _native_int(
        restore_checkpoint.get("history_index")
    )
    restore_date_raw = _native_int(restore_checkpoint.get("date_raw"))
    restore_sha256 = restore_checkpoint.get("sha256")
    if not (
        restore_history_index is not None
        and restore_date_raw is not None
        and isinstance(restore_sha256, str)
        and bool(restore_sha256)
    ):
        return False
    # An official cold restore can consume the same saved checkpoint again
    # without writing a new save. The preceding restore was already checked
    # against the save (or an earlier adjacent restore) by the caller.
    if (
        restore_position == move_position + 1
        and _effective_command(commands[move_position]) == "restore-checkpoint"
    ):
        previous = commands[move_position]
        previous_result = previous.get("result")
        previous_checkpoint = (
            previous_result.get("checkpoint")
            if isinstance(previous_result, dict)
            else None
        )
        if not (
            previous.get("ok") is True
            and isinstance(previous_result, dict)
            and previous_result.get("status") == "restored"
            and previous_result.get("source") == "native-session-cold-start"
            and isinstance(previous_checkpoint, dict)
        ):
            return False
        identity_fields = (
            "history_index",
            "date_raw",
            "sha256",
            "size",
            "name",
            "episode_character_id",
            "episode_run_id",
        )
        return all(
            previous_checkpoint.get(field) is not None
            and restore_checkpoint.get(field) is not None
            and previous_checkpoint[field] == restore_checkpoint[field]
            for field in identity_fields
        )
    for position in range(restore_position - 1, move_position, -1):
        row = commands[position]
        if _effective_command(row) != "save-checkpoint" or row.get("ok") is not True:
            continue
        result = row.get("result")
        checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
        if (
            isinstance(checkpoint, dict)
            and _native_int(checkpoint.get("history_index"))
            == restore_history_index
            and _native_int(checkpoint.get("date_raw")) == restore_date_raw
            and checkpoint.get("sha256") == restore_sha256
        ):
            return True
    return False


def _capital_regroup_intent(
    commands: list[dict[str, object]],
    snapshot: dict[str, object],
    *,
    army_id: int,
    war_id: int,
) -> dict[str, object] | None:
    """Hold one observed day after an exact capital-regroup arrival."""

    scoped = _history_after_latest_restore(commands)
    latest_position = -1
    latest_row: dict[str, object] | None = None
    target_province_id: int | None = None
    for position in range(len(scoped) - 1, -1, -1):
        row = scoped[position]
        if _successful_merge_barrier(row, army_id):
            return None
        parsed = parse_move_army_step(_effective_command(row))
        if parsed is None or parsed[0] != army_id:
            continue
        latest_position = position
        latest_row = row
        target_province_id = parsed[1]
        break
    if (
        latest_row is None
        or latest_row.get("ok") is not True
        or target_province_id is None
    ):
        return None
    result = _effective_command_result(latest_row)
    action = result.get("war_action") if isinstance(result, dict) else None
    submitted_date_raw = (
        _native_int(action.get("submitted_date_raw"))
        if isinstance(action, dict)
        else None
    )
    if not (
        isinstance(action, dict)
        and action.get("status") in {"move_submitted", "moving", "arrived"}
        and result.get("accepted") is not False
        and _native_int(action.get("army_id")) in {None, army_id}
        and _native_int(action.get("target_province_id"))
        in {None, target_province_id}
        and submitted_date_raw is not None
    ):
        return None
    played_character = snapshot.get("played_character")
    actor_id = (
        _native_int(played_character.get("character_id"))
        if isinstance(played_character, dict)
        else None
    )
    historical_root: dict[str, object] | None = None
    for row in reversed(scoped[:latest_position]):
        if (
            _effective_command(row) != "query-campaign-root-context-v1"
            or row.get("ok") is not True
        ):
            continue
        query_result = _effective_command_result(row)
        candidate = (
            query_result.get("campaign_root_context")
            if isinstance(query_result, dict)
            else None
        )
        readiness = (
            candidate.get("readiness")
            if isinstance(candidate, dict)
            else None
        )
        if (
            isinstance(candidate, dict)
            and candidate.get("status") == "available"
            and candidate.get("date_raw") == submitted_date_raw
            and candidate.get("player_character_id") == actor_id
            and candidate.get("capital_province_id") == target_province_id
            and isinstance(readiness, dict)
            and readiness.get("ready") is True
        ):
            historical_root = candidate
            break
    if historical_root is None:
        return None
    preview_origin: int | None = None
    for row in reversed(scoped[:latest_position]):
        if (
            parse_preview_move_army_step(_effective_command(row))
            != (army_id, target_province_id)
            or row.get("ok") is not True
        ):
            continue
        preview_result = _effective_command_result(row)
        preview = (
            preview_result.get("route_preview")
            if isinstance(preview_result, dict)
            else None
        )
        if (
            isinstance(preview, dict)
            and preview.get("status") == "available"
            and preview.get("previewed_date_raw") == submitted_date_raw
        ):
            preview_origin = _native_int(
                preview.get("origin_province_id")
            )
            break
    active_wars = snapshot.get("active_wars")
    bound_war = (
        next(
            (
                war
                for war in active_wars
                if isinstance(war, dict) and war.get("war_id") == war_id
            ),
            None,
        )
        if isinstance(active_wars, list)
        else None
    )
    if not (
        preview_origin is not None
        and isinstance(bound_war, dict)
        and bound_war.get("player_side") == "attacker"
        and bound_war.get("player_is_primary_war_leader") is True
        and bound_war.get("war_objective_province_ids") == [preview_origin]
    ):
        return None
    armies = snapshot.get("player_armies")
    army = (
        next(
            (
                row
                for row in armies
                if isinstance(row, dict) and row.get("army_id") == army_id
            ),
            None,
        )
        if isinstance(armies, list)
        else None
    )
    if not (
        isinstance(army, dict)
        and _native_int(army.get("current_province_id"))
        == target_province_id
        and army.get("move_target_province_id") is None
        and isinstance(army.get("route_province_ids"), list)
        and not army["route_province_ids"]
        and _army_tactical_state(army) not in {"combat", "retreating"}
    ):
        return None

    arrival_date_raw: int | None = (
        submitted_date_raw if action.get("status") == "arrived" else None
    )
    if arrival_date_raw is None:
        for row in scoped[latest_position + 1 :]:
            if (
                not is_life_advance_step(_effective_command(row))
                or row.get("ok") is not True
            ):
                continue
            after_date_raw, after_war = _progress_slice(
                row.get("result"), "war_progress_after", war_id
            )
            after_army = _progress_army(
                after_war, "player_armies", army_id
            )
            if (
                after_date_raw is not None
                and isinstance(after_army, dict)
                and _native_int(after_army.get("current_province_id"))
                == target_province_id
                and after_army.get("move_target_province_id") is None
                and isinstance(after_army.get("route_province_ids"), list)
                and not after_army["route_province_ids"]
            ):
                arrival_date_raw = after_date_raw
                break
    current_date_raw = _native_int(snapshot.get("date_raw"))
    if current_date_raw is None:
        return None
    if arrival_date_raw is None:
        arrival_date_raw = current_date_raw
    if current_date_raw < arrival_date_raw:
        return None
    elapsed_days = (current_date_raw - arrival_date_raw) // 24
    if elapsed_days >= _NATIVE_CAPITAL_REGROUP_MIN_GAME_DAYS:
        return None
    return {
        "status": "holding",
        "army_id": army_id,
        "war_id": war_id,
        "capital_province_id": target_province_id,
        "arrival_date_raw": arrival_date_raw,
        "elapsed_days": elapsed_days,
        "minimum_days": _NATIVE_CAPITAL_REGROUP_MIN_GAME_DAYS,
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
