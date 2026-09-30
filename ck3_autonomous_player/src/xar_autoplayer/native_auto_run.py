"""Bounded production owner for a pure native-headless CK3 gameplay loop.

The pipe driver must exist before CK3 is launched, while the managed session
must remain alive beside it to service process-level restore requests.  This
module owns both lifetimes in one process and never imports a visual backend.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
import hashlib
import json
import math
from pathlib import Path
import threading
import time
import uuid

from .bridge.driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
    UnsupportedStepError,
)
from .bridge.event_contract import parse_event_option_step
from .bridge.campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from .bridge.native_driver import (
    DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED,
    NativeHeadlessGameplayDriver,
)
from .bridge.activity_stage5_feast_full_cost_private_transport import (
    STEP as _PRIVATE_ACTIVITY_STAGE5_FULL_COST_READ_STEP,
    query_activity_stage5_feast_full_cost_private_v1,
)
from .bridge.activity_feast_stage5_start_private_transport import (
    INPUT_STEP as _PRIVATE_ACTIVITY_STAGE5_START_INPUT_STEP,
    POST_STEP as _PRIVATE_ACTIVITY_FEAST_HOSTED_POST_STEP,
    START_STEP as _PRIVATE_ACTIVITY_FEAST_START_STEP,
    query_activity_feast_stage5_start_inputs_private_v1,
)
from .bridge.activity_feast_guest_candidate_private_transport import (
    STEP as _PRIVATE_ACTIVITY_GUEST_CANDIDATE_STEP,
    query_activity_feast_guest_candidate_private_v1,
)
from .bridge.activity_feast_guest_route_proof_private_transport import (
    STEP as _PRIVATE_ACTIVITY_GUEST_ROUTE_PROOF_STEP,
    query_activity_feast_guest_route_proof_private_v1,
)
from .bridge.activity_feast_guest_target_private_transport import (
    STEP as _PRIVATE_ACTIVITY_GUEST_TARGET_STEP,
    query_activity_feast_guest_target_private_v1,
)
from .bridge.activity_feast_guest_opinion_private_transport import (
    STEP as _PRIVATE_ACTIVITY_GUEST_OPINION_STEP,
    query_activity_feast_guest_opinion_private_v1,
)
from .bridge.activity_feast_guest_rule_private_transport import (
    QUERY_STEP as _PRIVATE_ACTIVITY_GUEST_RULE_QUERY_STEP,
    query_activity_feast_guest_rule_private_v1,
)
from .bridge.activity_feast_guest_rule_provenance_private_transport import (
    STEP as _PRIVATE_ACTIVITY_GUEST_RULE_PROVENANCE_STEP,
    query_activity_feast_guest_rule_provenance_private_v1,
)
from .activity_feast_stage5_start_formal_consumer import (
    LEDGER_FILE as PRIVATE_FEAST_START_LEDGER_FILE,
    assess_feast_start_private_v1,
    consume_feast_start_private_v1,
    consume_feast_start_following_turn,
    read_feast_start_ledger,
)
from .activity_feast_stage5_budget_v1 import observe_feast_start_budget_v1
from .bridge.pending_character_interaction_context_contract import (
    normalize_pending_interaction_id,
)
from .bridge.council_assign_councillor_action_contract import (
    ASSIGN_COUNCILLOR_V1_STEP,
)
from .lifestyle_formal_consumer import (
    FOCUS_SUBMIT_STEP as PRIVATE_LIFESTYLE_FOCUS_SUBMIT_STEP,
    RECEIPT_STEP as PRIVATE_LIFESTYLE_RECEIPT_STEP,
)
from .bridge.player_lifestyle_private_transport_v1 import (
    FOCUS_TARGET as PRIVATE_LIFESTYLE_WEALTH_FOCUS,
    MARTIAL_TARGET as PRIVATE_LIFESTYLE_MARTIAL_FOCUS,
    STATE_QUERY_STEP as PRIVATE_LIFESTYLE_STATE_QUERY_STEP,
    query_player_lifestyle_private_v1,
)
from .construction_formal_consumer import (
    RECEIPT_STEP as PRIVATE_CONSTRUCTION_RECEIPT_STEP,
    SUBMIT_STEP as PRIVATE_CONSTRUCTION_SUBMIT_STEP,
    read_construction_ledger,
)
from .family_marriage_formal_consumer import (
    SUBMIT_STEP as PRIVATE_FAMILY_MARRIAGE_SUBMIT_STEP,
    read_family_marriage_ledger,
)
from .first_heir_companion_paused_observer import (
    observe_first_heir_companion_after_child,
)
from .player_child_matrilineal_formal_consumer import (
    RESULT_STEP as PRIVATE_CHILD_MATRILINEAL_RESULT_STEP,
    SUBMIT_STEP as PRIVATE_CHILD_MATRILINEAL_SUBMIT_STEP,
    read_child_matrilineal_ledger,
)
from .player_child_default_formal_consumer import (
    ALLIANCE_RESULT_STEP as PRIVATE_CHILD_DEFAULT_ALLIANCE_STEP,
    RESULT_STEP as PRIVATE_CHILD_DEFAULT_RESULT_STEP,
    SUBMIT_STEP as PRIVATE_CHILD_DEFAULT_SUBMIT_STEP,
    consume_child_default_result_checkpoint,
    read_child_default_ledger,
)
from .prisoner_ransom_formal_consumer import (
    SUBMIT_STEP as PRIVATE_PRISONER_RANSOM_SUBMIT_STEP,
    RECEIPT_STEP as PRIVATE_PRISONER_RANSOM_RECEIPT_STEP,
    read_ransom_ledger,
)
from .sway_formal_consumer import (
    LEDGER_FILE as PRIVATE_SWAY_LEDGER_FILE,
    consume_sway_private_once,
    consume_sway_following_turn,
)
from .bridge.service import GameplayBridgeService
from .bridge.war_hotspot_camera import LandedProvinceIndex, follow_war_hotspot
from .bridge.camera_cursor_parking import park_foreground_ck3_cursor
from .bridge.settlement_contract import (
    normalize_fixed_score,
    normalize_one_life_settlement,
    settlement_ready_for_episode,
)
from .bridge.succession_transition_contract import (
    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
    ORDINARY_CAMPAIGN_SUCCESSION,
    ROGUE_ONE_LIFE,
    bind_succession_lifecycle_from_environment_v1,
    legacy_rogue_one_life_binding_v1,
)
from .bridge.war_contract import (
    is_life_advance_step,
    observe_merge_armies_postcondition_v1,
    parse_merge_armies_step,
    parse_offer_white_peace_step,
    parse_surrender_war_step,
    war_termination_active_war_signature,
)
from .environment import EnvironmentSpec, ensure_state_path_safe
from .epidemic_recovery_formal_observer import (
    EVENT_KEY as EPIDEMIC_RECOVERY_EVENT_KEY,
    OPTION_STEP as EPIDEMIC_RECOVERY_OPTION_STEP,
    capture_epidemic_recovery_before_option,
    observe_epidemic_recovery_after_option,
)
from .errors import AgentError
from .exact_war_move_stop import (
    validate_contract as validate_exact_war_move_stop_contract,
    expected_step as exact_war_move_step,
    check_before as check_exact_war_move_before,
    check_poststate as check_exact_war_move_poststate,
    check_checkpoint as check_exact_war_move_checkpoint,
)
from .native_session import (
    native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)


PURE_NATIVE_MODE = "native-headless"
CHECKPOINT_EVERY_ELIGIBLE_ADVANCES = 3
READINESS_STABLE_SECONDS = 0.5
READINESS_POLL_SECONDS = 0.05
SESSION_TIMEOUT_GRACE_SECONDS = 90.0
_ELIGIBLE_ADVANCE_STEPS = frozenset(
    {
        "life-advance",
        "economic-event-cycle",
        "battle-decision-epoch-advance",
        "battle-terminal-cruise",
    }
)
_TERMINAL_STEPS = frozenset({"death-terminal", "strategy-review"})
_RECOVERY_STEPS = frozenset(
    {
        "restore-checkpoint",
        "start-next-episode",
        CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
    }
)
_PENDING_INTERACTION_REPLY_STATUSES = {
    "accept-pending-character-interaction": "accepted",
    "reject-pending-character-interaction": "rejected",
    "acknowledge-pending-character-interaction": "acknowledged",
}
_DE_JURE_NO_SAFE_ROUTE_CB = "individual_county_de_jure_cb"
_DE_JURE_NO_SAFE_ROUTE_CB_DATABASE_INDEX = 17
_DE_JURE_NO_SAFE_ROUTE_MIN_DAYS = 180
_RAIKTOR_TERMINAL_CONTROL_CB = "raiktor_claim_cb"
_RAIKTOR_TERMINAL_CONTROL_SCORE = -100
_RAIKTOR_LONG_WAR_SURRENDER_MIN_DAYS = 730
_RAIKTOR_LONG_WAR_SURRENDER_MAX_SCORE = -1
_OPENING_FOCUS_LIFESTYLE_BY_TARGET = {
    PRIVATE_LIFESTYLE_WEALTH_FOCUS: "stewardship_lifestyle",
    PRIVATE_LIFESTYLE_MARTIAL_FOCUS: "martial_lifestyle",
}


def _registered_event_material_postcondition_issue(
    plan: object, result: object
) -> str | None:
    if not isinstance(plan, dict):
        return None
    expectation = plan.get("event_material_postcondition")
    if not isinstance(expectation, dict) or expectation.get("status") != "ready":
        return None
    observed = (
        result.get("event_material_postcondition")
        if isinstance(result, dict)
        else None
    )
    if not isinstance(observed, dict):
        return "unavailable"
    status = observed.get("status")
    if status == "failed":
        return "failed"
    if (
        expectation.get("event_definition_key")
        == "stress_threshold_special.1001"
        and isinstance(expectation.get("starting_value"), int)
        and not isinstance(expectation.get("starting_value"), bool)
        and expectation["starting_value"] > 0
        and status == "verified_no_change"
    ):
        return "no_material_change"
    if status not in {"verified_change", "verified_no_change"}:
        return "unavailable"
    return None


def _timeline_typed_boolean(
    context: object, field: str, expected: bool
) -> bool:
    value = context.get(field) if isinstance(context, dict) else None
    return bool(
        isinstance(value, dict)
        and value.get("status") == "available"
        and value.get("value") is expected
        and value.get("unavailable_reason") is None
    )


def _ordinary_succession_timeline_state(query: object) -> str | None:
    """Classify one normalized private timeline query without guessing."""

    context = (
        query.get("current_timeline_blocker_context")
        if isinstance(query, dict)
        else None
    )
    if not isinstance(context, dict) or context.get("status") != "available":
        return None
    identity = context.get("identity")
    if (
        identity == "death_succession_modal"
        and _timeline_typed_boolean(context, "can_continue", True)
        and _timeline_typed_boolean(context, "blocks_simulation", True)
        and _timeline_typed_boolean(context, "has_open_succession", True)
    ):
        return "close_required"
    if (
        identity == "none"
        and _timeline_typed_boolean(context, "blocks_simulation", False)
        and _timeline_typed_boolean(context, "has_open_succession", False)
    ):
        return "already_clear"
    return None


def _ordinary_succession_close_issue(
    result: object,
    *,
    starting_date_raw: int,
    successor_character_id: int,
) -> str | None:
    """Require the existing private Close route's independent material proof."""

    if not isinstance(result, dict):
        return "result_unavailable"
    if result.get("status") != "materially_verified":
        return str(result.get("status") or "unknown_status")
    if result.get("material_result_verified") is not True:
        return "material_result_unverified"
    if result.get("starting_date_raw") != starting_date_raw:
        return "starting_date_mismatch"
    ending_date_raw = result.get("ending_date_raw")
    if (
        isinstance(ending_date_raw, bool)
        or not isinstance(ending_date_raw, int)
        or ending_date_raw <= starting_date_raw
    ):
        return "date_not_advanced"
    ack = result.get("submission_ack")
    if not (
        isinstance(ack, dict)
        and ack.get("accepted") is True
        and ack.get("status") == "submitted"
        and ack.get("played_character_id") == successor_character_id
        and ack.get("close_invocations") == 1
        and ack.get("material_result_verified") is False
    ):
        return "close_ack_invalid"
    if (
        _ordinary_succession_timeline_state(result.get("initial_query"))
        != "close_required"
    ):
        return "initial_modal_not_bound"
    if _ordinary_succession_timeline_state(
        result.get("postcondition_query")
    ) != "already_clear":
        return "independent_clear_not_observed"
    ending_revision = result.get("ending_revision")
    ending_native_revision = result.get("ending_native_revision")
    if (
        isinstance(ending_revision, bool)
        or not isinstance(ending_revision, int)
        or ending_revision < 0
        or isinstance(ending_native_revision, bool)
        or not isinstance(ending_native_revision, int)
        or ending_native_revision <= 0
    ):
        return "ending_revision_invalid"
    return None


def _council_assignment_postcondition_issue(
    step: object,
    result: object,
    after_snapshot: object,
) -> str | None:
    """Require the formal action's distinct receipt to match public state."""

    if step != ASSIGN_COUNCILLOR_V1_STEP:
        return None
    if not isinstance(result, dict) or not isinstance(after_snapshot, dict):
        return "result_or_snapshot_unavailable"
    ack = result.get("council_assign_councillor_ack")
    receipt = result.get("council_assign_councillor_receipt")
    played = after_snapshot.get("played_character")
    if not (
        isinstance(ack, dict)
        and ack.get("status")
        == "native_helper_invoked_verification_pending"
        and ack.get("native_helper_invoked") is True
        and ack.get("queue_acceptance_observed") is False
        and ack.get("verification_pending") is True
        and isinstance(receipt, dict)
        and receipt.get("status") == "applied"
        and receipt.get("postcondition_verified") is True
        and receipt.get("action_request_id")
        == ack.get("action_request_id")
        and receipt.get("incumbent_character_id")
        == ack.get("candidate_character_id")
        and after_snapshot.get("paused") is True
        and after_snapshot.get("snapshot_id")
        == receipt.get("post_snapshot_id")
        and after_snapshot.get("revision")
        == receipt.get("post_public_revision")
        and after_snapshot.get("native_revision")
        == receipt.get("post_native_revision")
        and after_snapshot.get("date_raw") == receipt.get("post_date_raw")
        and isinstance(played, dict)
        and played.get("character_id") == receipt.get("owner_character_id")
    ):
        return "receipt_or_public_binding_mismatch"
    return None


class NativeReadinessTimeoutError(AgentError):
    """A native readiness wait expired with its last bridge evidence."""

    def __init__(
        self,
        message: str,
        *,
        readiness_diagnostics: dict[str, object] | None,
        last_observation: dict[str, object] | None,
    ) -> None:
        super().__init__(message)
        self.readiness_diagnostics = copy.deepcopy(readiness_diagnostics)
        self.last_observation = copy.deepcopy(last_observation)


def _require_private_child_pending_result(
    candidate: Mapping[str, object], pending: Mapping[str, object],
) -> None:
    """Limit the paired cold recovery to its existing proposal result read."""
    plan = candidate.get("plan")
    selected_pending = (plan.get("child_matrilineal_pending")
                        if isinstance(plan, dict) else None)
    if (candidate.get("selected_step") != PRIVATE_CHILD_MATRILINEAL_RESULT_STEP
            or selected_pending != dict(pending)
            or plan.get("child_matrilineal_cold_recovery") is not True):
        raise AgentError(
            "private child pending recovery permits only the paired cold result step"
        )


def native_auto_run(
    spec: EnvironmentSpec,
    *,
    turn_count: int,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    cold_start_checkpoint: bool = False,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
    checkpoint_every_eligible_advances: int = (
        CHECKPOINT_EVERY_ELIGIBLE_ADVANCES
    ),
    completion_contract: str = "bounded",
    route_contact_timeline_speed: int = (
        DEFAULT_ROUTE_CONTACT_TIMELINE_SPEED
    ),
    allow_route_contact_high_speed_ab: bool = False,
    allow_stationary_objective_hold_sentinel_canary: bool = False,
    allow_private_lifestyle_formal_trial: bool = False,
    require_initial_lifestyle_focus_before_date_advance: bool = False,
    allow_private_construction_formal_trial: bool = False,
    allow_private_family_marriage_formal_trial: bool = False,
    allow_private_guy_default_formal_trial: bool = False,
    private_guy_default_first_heir_companion: bool = False,
    private_child_matrilineal_target: tuple[int, int] | None = None,
    private_child_matrilineal_pending_read_target: tuple[int, int] | None = None,
    private_child_matrilineal_first_heir_companion: bool = False,
    private_child_matrilineal_pending_recovery_only: bool = False,
    allow_private_faction_gift_formal_trial: bool = False,
    allow_private_m5_joint_collector: bool = False,
    allow_private_epidemic_recovery_near_pair: bool = False,
    allow_private_prisoner_collection_observation: bool = False,
    private_active_scheme_sway_target: int | None = None,
    allow_private_active_scheme_sway_formal_trial: bool = False,
    private_realm_law_paused_query: bool = False,
    private_activity_planner_diag_query: bool = False,
    private_activity_feast_planner_open: bool = False,
    private_activity_feast_stage1_option_read: bool = False,
    private_activity_cost_slot12_raw_read: bool = False,
    private_activity_feast_stage1_confirm: bool = False,
    private_activity_feast_stage2_gate_read: bool = False,
    private_activity_feast_stage2_location_candidate_province_ids: tuple[int, ...] | None = None,
    private_activity_feast_stage2_destination_province_id: int | None = None,
    private_activity_feast_stage5_full_cost_read: bool = False,
    private_activity_feast_stage5_start_read: bool = False,
    allow_private_activity_feast_stage5_start_formal_trial: bool = False,
    private_activity_feast_guest_candidate_read: bool = False,
    private_activity_feast_guest_route_proof_read: bool = False,
    private_activity_feast_guest_target_character_id: int | None = None,
    private_activity_feast_guest_opinion_character_id: int | None = None,
    private_activity_feast_guest_rule_key: str | None = None,
    private_activity_feast_guest_rule_candidate_id: int | None = None,
    allow_private_prisoner_ransom_formal_trial: bool = False,
    private_faction_round_id: str | None = None,
    succession_lifecycle: str = ROGUE_ONE_LIFE,
    ordinary_campaign_no_pact: bool = False,
    exact_war_move_stop_contract: dict[str, object] | None = None,
    operator_stop_event: threading.Event | None = None,
    before_submit: Callable[[dict[str, object]], dict[str, object] | None]
    | None = None,
    after_intercept: Callable[
        [NativeHeadlessGameplayDriver, dict[str, object]],
        dict[str, object],
    ]
    | None = None,
) -> dict[str, object]:
    """Own one bounded observe-plan-act-verify native gameplay run."""
    _positive_integer(turn_count, "turn_count")
    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds"
    )
    stable_seconds = _nonnegative_seconds(
        readiness_stable_seconds, "readiness_stable_seconds"
    )
    poll_seconds = _positive_seconds(
        poll_interval_seconds, "poll_interval_seconds"
    )
    checkpoint_cadence = _positive_integer(
        checkpoint_every_eligible_advances,
        "checkpoint_every_eligible_advances",
    )
    route_contact_speed = _route_contact_speed(
        route_contact_timeline_speed,
        allow_high_speed_ab=allow_route_contact_high_speed_ab,
    )
    strict_completion_contracts = {"one_generation", "next_episode"}
    if completion_contract not in {"bounded", *strict_completion_contracts}:
        raise AgentError(
            "completion_contract must be 'bounded', 'one_generation', or "
            "'next_episode'"
        )
    if (
        succession_lifecycle == ORDINARY_CAMPAIGN_SUCCESSION
        and completion_contract in strict_completion_contracts
    ):
        raise AgentError(
            "ordinary campaign succession requires the bounded campaign contract"
        )
    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != PURE_NATIVE_MODE:
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "native-auto-run requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )
    if completion_contract in strict_completion_contracts and not cold_start_checkpoint:
        raise AgentError(
            f"{completion_contract} completion requires an exact cold-start "
            "checkpoint"
        )
    if (
        allow_private_lifestyle_formal_trial is True
        and completion_contract != "bounded"
    ):
        raise AgentError(
            "private LIFE slot43 trial only admits a bounded contract"
        )
    if (
        require_initial_lifestyle_focus_before_date_advance is True
        and allow_private_lifestyle_formal_trial is not True
    ):
        raise AgentError(
            "initial LIFE focus gate requires the private bounded LIFE trial"
        )
    if allow_private_construction_formal_trial is True and completion_contract != "bounded":
        raise AgentError("private construction trial only admits a bounded contract")
    if allow_private_family_marriage_formal_trial is True and completion_contract != "bounded":
        raise AgentError("private first-heir marriage trial only admits a bounded contract")
    if allow_private_guy_default_formal_trial is True and completion_contract != "bounded":
        raise AgentError("private child default trial only admits a bounded contract")
    if (private_guy_default_first_heir_companion is True
            and (allow_private_guy_default_formal_trial is not True
                 or allow_private_family_marriage_formal_trial is True)):
        raise AgentError("Guy companion needs the bounded default trial with family trial off")
    if private_child_matrilineal_target is not None:
        if (completion_contract != "bounded"
                or not isinstance(private_child_matrilineal_target, tuple)
                or len(private_child_matrilineal_target) != 2
                or any(type(value) is not int or not 0 < value < 2**31
                       for value in private_child_matrilineal_target)
                or private_child_matrilineal_target[0] == private_child_matrilineal_target[1]):
            raise AgentError("private child proposal needs bounded positive subject/candidate IDs")
    if private_child_matrilineal_pending_read_target is not None:
        pair = private_child_matrilineal_pending_read_target
        if (completion_contract != "bounded"
                or private_child_matrilineal_target is not None
                or not isinstance(pair, tuple) or len(pair) != 2
                or any(type(value) is not int or not 0 < value < 2**31
                       for value in pair) or pair[0] == pair[1]):
            raise AgentError("private child pending read needs one bounded distinct pair")
    if (private_child_matrilineal_first_heir_companion is True
            and (private_child_matrilineal_pending_read_target is None
                 or turn_count != 1
                 or allow_private_family_marriage_formal_trial is True)):
        raise AgentError("first-heir companion needs one child pending read turn")
    child_recovery_pending = None
    if private_child_matrilineal_pending_recovery_only is True:
        if (private_child_matrilineal_target is None
                or private_child_matrilineal_pending_read_target is not None
                or allow_private_lifestyle_formal_trial is not True
                or turn_count != 1):
            raise AgentError("private child pending recovery needs one bounded LIFE result turn")
        child_recovery_pending = read_child_matrilineal_ledger(spec.state_dir)["pending"]
        if (not isinstance(child_recovery_pending, dict)
                or child_recovery_pending.get("status") != "receipt_pending"
                or child_recovery_pending.get("material_result") is not False
                or child_recovery_pending.get("heir_character_id")
                != private_child_matrilineal_target[0]
                or child_recovery_pending.get("candidate_character_id")
                != private_child_matrilineal_target[1]):
            raise AgentError("private child recovery lacks the specified unresolved proposal")
    if (
        allow_private_faction_gift_formal_trial is True
        and completion_contract != "bounded"
    ):
        raise AgentError(
            "private faction gift trial only admits a bounded contract"
        )
    if (
        allow_private_m5_joint_collector is True
        and completion_contract != "bounded"
    ):
        raise AgentError(
            "private M5 peacetime collector only admits a bounded contract"
        )
    if (
        allow_private_epidemic_recovery_near_pair is True
        and completion_contract != "bounded"
    ):
        raise AgentError(
            "private epidemic recovery near pair only admits a bounded contract"
        )
    if (
        allow_private_prisoner_collection_observation is True
        and completion_contract != "bounded"
    ):
        raise AgentError(
            "private prisoner collection observation only admits a bounded contract"
        )
    if private_active_scheme_sway_target is not None and (
        completion_contract != "bounded"
        or type(private_active_scheme_sway_target) is not int
        or not 0 < private_active_scheme_sway_target <= 0xFFFFFFFF
    ):
        raise AgentError("private sway read needs a bounded full target ID")
    if allow_private_active_scheme_sway_formal_trial is True and (
        private_active_scheme_sway_target is None
        or completion_contract != "bounded"
    ):
        raise AgentError("private Sway action needs a bounded explicit target")
    if private_realm_law_paused_query is True and completion_contract != "bounded":
        raise AgentError("private realm-law read needs a bounded contract")
    if private_activity_planner_diag_query is True and completion_contract != "bounded":
        raise AgentError("private activity planner read needs a bounded contract")
    if (private_activity_feast_planner_open is True
            or private_activity_feast_stage1_option_read is True
            or private_activity_cost_slot12_raw_read is True
            or private_activity_feast_stage1_confirm is True):
        if completion_contract != "bounded":
            raise AgentError("private feast planner open needs a bounded contract")
        if (private_child_matrilineal_pending_read_target is not None
                or private_activity_planner_diag_query is True):
            raise AgentError("private feast planner open needs its own paused frame run")
        if (private_activity_feast_planner_open is True
                and private_activity_feast_stage1_option_read is True):
            raise AgentError("select one private feast paused frame route")
        if (private_activity_cost_slot12_raw_read is True
                and private_activity_feast_stage1_option_read is True):
            raise AgentError("select one private feast read on this paused frame")
        if private_activity_feast_stage1_confirm is True and (
            private_activity_feast_planner_open is True
            or private_activity_feast_stage1_option_read is True
            or private_activity_cost_slot12_raw_read is True
        ):
            raise AgentError("stage-1 Confirm needs its own private paused frame run")
    if (private_activity_feast_stage2_gate_read is True
            and private_activity_feast_stage1_confirm is not True):
        raise AgentError("private stage-2 gate read requires stage-1 Confirm")
    if private_activity_feast_stage2_location_candidate_province_ids is not None:
        candidates = private_activity_feast_stage2_location_candidate_province_ids
        if private_activity_feast_stage1_confirm is not True:
            raise AgentError("private stage-2 location read requires stage-1 Confirm")
        if (not isinstance(candidates, tuple) or not 1 <= len(candidates) <= 8
                or len(set(candidates)) != len(candidates)
                or any(type(value) is not int or not 0 < value <= 0x7FFFFFFF
                       for value in candidates)):
            raise AgentError("private stage-2 location candidates must be 1-8 distinct positive int32 province IDs")
    if private_activity_feast_stage2_destination_province_id is not None:
        province_id = private_activity_feast_stage2_destination_province_id
        if (private_activity_feast_stage1_confirm is not True
                or private_activity_feast_stage2_location_candidate_province_ids is None
                or province_id not in private_activity_feast_stage2_location_candidate_province_ids
                or type(province_id) is not int
                or not 0 < province_id <= 0x7FFFFFFF):
            raise AgentError("private stage-2 destination needs a queried positive int32 province ID and stage-1 Confirm")
    if (private_activity_feast_stage5_full_cost_read is True
            and private_activity_feast_stage2_destination_province_id is None):
        raise AgentError("private stage-5 full-cost read requires verified stage-2 destination selection")
    if (private_activity_feast_stage5_start_read is True
            and private_activity_feast_stage5_full_cost_read is not True):
        raise AgentError("private stage-5 Start read requires the full-cost Stage-5 route")
    if (allow_private_activity_feast_stage5_start_formal_trial is True
            and (private_activity_feast_stage5_start_read is not True
                 or completion_contract != "bounded")):
        raise AgentError("private feast Start formal trial requires bounded Start input assessment")
    if (private_activity_feast_guest_candidate_read is True
            and private_activity_feast_stage5_full_cost_read is not True):
        raise AgentError("private feast guest candidate read requires the full-cost Stage-5 route")
    if (private_activity_feast_guest_route_proof_read is True
            and private_activity_feast_stage5_full_cost_read is not True):
        raise AgentError("private feast guest route proof requires the full-cost Stage-5 route")
    if private_activity_feast_guest_target_character_id is not None and (
        completion_contract != "bounded"
        or type(private_activity_feast_guest_target_character_id) is not int
        or not 0 < private_activity_feast_guest_target_character_id <= 0x7FFFFFFF
        or private_activity_feast_stage5_full_cost_read is not True
    ):
        raise AgentError("private feast guest target read needs a full CharacterID and Stage-5 cost route")
    combined_target_opinion = (
        private_activity_feast_guest_target_character_id is not None
        and private_activity_feast_guest_opinion_character_id
            == private_activity_feast_guest_target_character_id
        and private_activity_feast_guest_rule_key is not None
        and private_activity_feast_guest_rule_candidate_id
            == private_activity_feast_guest_target_character_id
    )
    if private_activity_feast_guest_opinion_character_id is not None:
        if (completion_contract != "bounded"
                or type(private_activity_feast_guest_opinion_character_id) is not int
                or not 0 < private_activity_feast_guest_opinion_character_id <= 0x7FFFFFFF):
            raise AgentError("private feast guest opinion read needs a bounded full CharacterID")
        if (not combined_target_opinion
                and (private_activity_feast_planner_open is True
                or private_activity_feast_stage1_option_read is True
                or private_activity_feast_stage1_confirm is True
                or private_activity_feast_stage2_gate_read is True
                or private_activity_feast_stage2_location_candidate_province_ids is not None
                or private_activity_feast_stage2_destination_province_id is not None
                or private_activity_feast_stage5_full_cost_read is True
                or private_activity_feast_stage5_start_read is True
                or private_activity_feast_guest_candidate_read is True
                or private_activity_feast_guest_route_proof_read is True
                or private_activity_feast_guest_rule_key is not None)):
            raise AgentError("private feast guest opinion read uses its own paused frame run")
    if (private_activity_feast_guest_rule_key is not None
            and private_activity_feast_stage5_full_cost_read is not True):
        raise AgentError("private feast guest rule read requires the full-cost Stage-5 route")
    if private_activity_feast_guest_rule_key is not None and (
        not isinstance(private_activity_feast_guest_rule_key, str)
        or not 0 < len(private_activity_feast_guest_rule_key) <= 96
        or not private_activity_feast_guest_rule_key.startswith("activity_invite_rule_")
        or len(private_activity_feast_guest_rule_key) <= len("activity_invite_rule_")
        or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_"
               for ch in private_activity_feast_guest_rule_key)
    ):
        raise AgentError("private feast guest rule key is malformed")
    if private_activity_feast_guest_rule_candidate_id is not None and (
        completion_contract != "bounded"
        or type(private_activity_feast_guest_rule_candidate_id) is not int
        or not 0 < private_activity_feast_guest_rule_candidate_id <= 0x7FFFFFFF
        or private_activity_feast_guest_rule_key is None
        or (private_activity_feast_guest_candidate_read is not True
            and private_activity_feast_guest_target_character_id
                != private_activity_feast_guest_rule_candidate_id)
    ):
        raise AgentError("private feast rule provenance needs a named rule and same-run candidate read")
    if (allow_private_prisoner_ransom_formal_trial is True
            and completion_contract != "bounded"):
        raise AgentError("private prisoner ransom only admits a bounded contract")
    if allow_private_faction_gift_formal_trial is True and not (
        isinstance(private_faction_round_id, str)
        and private_faction_round_id.startswith("R")
        and private_faction_round_id[1:].isdigit()
    ):
        raise AgentError(
            "private faction gift trial requires --private-faction-round-id R<number>"
        )
    if after_intercept is not None and before_submit is None:
        raise AgentError(
            "after_intercept requires a before_submit candidate interceptor"
        )
    exact_move_contract = (
        validate_exact_war_move_stop_contract(exact_war_move_stop_contract)
        if exact_war_move_stop_contract is not None else None
    )
    if exact_move_contract is not None and (completion_contract != "bounded" or before_submit is not None):
        raise AgentError("exact war move stop requires a bounded run without another interceptor")

    ensure_state_path_safe(spec.state_dir)
    try:
        if spec.manifest_path.is_file():
            environment_manifest = json.loads(
                spec.manifest_path.read_text(encoding="utf-8-sig")
            )
            succession_lifecycle_binding = (
                bind_succession_lifecycle_from_environment_v1(
                    environment_manifest,
                    lifecycle=succession_lifecycle,
                    ordinary_campaign_no_pact=ordinary_campaign_no_pact,
                )
            )
        elif (
            succession_lifecycle == ROGUE_ONE_LIFE
            and ordinary_campaign_no_pact is not True
        ):
            # Unit/fake drivers predate the prepared-profile binding.  Real
            # native-session startup still requires its environment manifest.
            succession_lifecycle_binding = legacy_rogue_one_life_binding_v1()
        else:
            raise ValueError(
                "ordinary campaign succession requires a prepared environment"
            )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise AgentError(
            f"succession lifecycle profile is not runnable: {error}"
        ) from error
    fixed_seed = (
        validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
        if completion_contract in strict_completion_contracts
        or cold_start_checkpoint
        else None
    )
    if exact_move_contract is not None:
        if not cold_start_checkpoint or not isinstance(fixed_seed, dict):
            raise AgentError("exact war move stop requires an exact cold-start checkpoint")
        driver_state_path = spec.state_dir / "native-session" / "driver-state.json"
        if (str(fixed_seed.get("sha256", "")).lower()
                != str(exact_move_contract["source_save_sha256"]).lower()
                or not driver_state_path.is_file()
                or hashlib.sha256(driver_state_path.read_bytes()).hexdigest()
                != str(exact_move_contract["source_driver_sha256"]).lower()):
            raise AgentError("exact war move stop source pair differs from prepared state")
    if succession_lifecycle_binding["lifecycle"] == ORDINARY_CAMPAIGN_SUCCESSION:
        if not cold_start_checkpoint or not isinstance(fixed_seed, dict):
            raise AgentError(
                "ordinary campaign succession requires an explicit frozen "
                "cold-start checkpoint"
            )
        if fixed_seed.get("succession_lifecycle") != succession_lifecycle_binding:
            raise AgentError(
                "ordinary campaign checkpoint lifecycle differs from the "
                "prepared environment"
            )
    session_profile_options = (
        {"prepared_xar_enabled": "xar_off"}
        if succession_lifecycle_binding["xar_enabled"] == "xar_off"
        else {}
    )
    started_wall = utc_now()
    started = time.monotonic()
    run_deadline = started + timeout
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {
        "report": None,
        "error": None,
    }
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    turns: list[dict[str, object]] = []
    checkpoints: list[dict[str, object]] = []
    counts = {
        "query": 0,
        "gameplay": 0,
        "checkpoint": 0,
        "recovery": 0,
        "terminal": 0,
    }
    eligible_since_checkpoint = 0
    dirty_gameplay_since_checkpoint = False
    visible_gameplay_turns = 0
    date_advanced = False
    terminal_pending = False
    modal_decision_pending = False
    terminal_proof: dict[str, object] | None = None
    next_episode_transition: dict[str, object] | None = None
    natural_succession_transitions: list[dict[str, object]] = []
    post_transition_visible_gameplay_turns = 0
    post_transition_last_gameplay_turn_index: int | None = None
    post_transition_checkpoint: dict[str, object] | None = None
    initial_episode: dict[str, object] | None = None
    current_episode: dict[str, object] | None = None
    same_episode_binding = True
    status = "starting"
    primary_error: str | None = None
    current_attempt: dict[str, object] | None = None
    first_failure: dict[str, object] | None = None
    readiness_timeout_diagnostics: dict[str, object] | None = None
    candidate_interception: dict[str, object] | None = None
    candidate_resolution: dict[str, object] | None = None
    exact_move_pre_submit_seen = False
    exact_move_poststate: dict[str, object] | None = None
    exact_move_checkpoint: dict[str, object] | None = None
    private_prisoner_collection_observation: dict[str, object] | None = None
    private_active_scheme_sway_observation: dict[str, object] | None = None
    private_active_scheme_sway_formal: dict[str, object] | None = None
    private_active_scheme_sway_following_turn: dict[str, object] | None = None
    private_child_matrilineal_pending_observation: dict[str, object] | None = None
    private_first_heir_companion_observation: dict[str, object] | None = None
    private_realm_law_paused_observation: dict[str, object] | None = None
    private_activity_planner_diag_observation: dict[str, object] | None = None
    private_activity_feast_planner_open_observation: dict[str, object] | None = None
    private_activity_feast_stage1_option_observation: dict[str, object] | None = None
    private_activity_cost_slot12_raw_observation: dict[str, object] | None = None
    private_activity_feast_stage1_confirm_observation: dict[str, object] | None = None
    private_activity_feast_stage2_option_observation: dict[str, object] | None = None
    private_activity_feast_stage2_gate_observation: dict[str, object] | None = None
    private_activity_feast_stage2_location_observation: dict[str, object] | None = None
    private_activity_feast_stage2_destination_observation: dict[str, object] | None = None
    private_activity_feast_stage5_full_cost_observation: dict[str, object] | None = None
    private_activity_feast_stage5_start_observation: dict[str, object] | None = None
    private_activity_feast_stage5_start_formal: dict[str, object] | None = None
    private_activity_feast_guest_candidate_observation: dict[str, object] | None = None
    private_activity_feast_guest_route_proof_observation: dict[str, object] | None = None
    private_activity_feast_guest_target_observation: dict[str, object] | None = None
    private_activity_feast_guest_target_recheck_observation: dict[str, object] | None = None
    private_activity_feast_guest_opinion_observation: dict[str, object] | None = None
    private_activity_feast_guest_rule_observation: dict[str, object] | None = None
    private_activity_feast_stage5_start_following_turn: dict[str, object] | None = None
    opening_focus_gate: dict[str, object] | None = (
        {"stage": "await_submit", "action_request_id": None,
         "target_key": None, "checkpoint_saved": False}
        if require_initial_lifestyle_focus_before_date_advance else None
    )

    def capture_first_failure(
        *,
        stage: str,
        kind: str,
        message: str,
        error: BaseException | None = None,
    ) -> None:
        nonlocal first_failure
        if first_failure is not None:
            return
        attempt = current_attempt if isinstance(current_attempt, dict) else {}
        before = attempt.get("before")
        after = attempt.get("after")
        attempt_stage = attempt.get("stage")
        selected_step = attempt.get("selected_step")
        checkpoint_invalidation_reason = None
        if attempt_stage == "checkpoint":
            checkpoint_invalidation_reason = (
                "checkpoint_submit_not_fully_verified"
            )
        elif attempt_stage == "opaque_auto_turn" and (
            not isinstance(selected_step, str)
            or selected_step == "save-checkpoint"
        ):
            checkpoint_invalidation_reason = (
                "opaque_auto_turn_may_have_submitted_checkpoint"
            )
        if isinstance(error, PreSubmissionRevisionMismatchError):
            checkpoint_invalidation_reason = None
        checkpoint_recovery_invalidated = (
            checkpoint_invalidation_reason is not None
        )
        last_checkpoint = (
            None
            if checkpoint_recovery_invalidated
            else (checkpoints[-1] if checkpoints else fixed_seed)
        )
        first_failure = {
            "observed_at": utc_now(),
            "turn_index": attempt.get("turn_index", 0),
            "stage": stage,
            "kind": kind,
            "status": status,
            "completion_contract": completion_contract,
            "message": message,
            "error_type": type(error).__name__ if error is not None else None,
            "error": (
                f"{type(error).__name__}: {error}"
                if error is not None
                else message
            ),
            "initial_episode": (
                {
                    key: readiness.get(key)
                    for key in (
                        "episode_character_id",
                        "episode_run_id",
                        "date_raw",
                        "played_character_alive",
                    )
                }
                if isinstance(readiness, dict)
                else None
            ),
            "before": copy.deepcopy(before),
            "camera_follow": copy.deepcopy(attempt.get("camera_follow")),
            "plan": copy.deepcopy(attempt.get("plan")),
            "selected_step": attempt.get("selected_step"),
            "result": _compact_failure_step_result(attempt.get("result")),
            "after": copy.deepcopy(after),
            "active_context": copy.deepcopy(
                after.get("active_context")
                if isinstance(after, dict)
                else (
                    before.get("active_context")
                    if isinstance(before, dict)
                    else None
                )
            ),
            "last_durable_checkpoint": copy.deepcopy(last_checkpoint),
            "recoverable_from_checkpoint": last_checkpoint is not None,
            "checkpoint_recovery_invalidated": (
                checkpoint_recovery_invalidated
            ),
            "checkpoint_recovery_invalidation_reason": (
                checkpoint_invalidation_reason
            ),
            "cleanup": None,
        }
        if isinstance(attempt.get("epidemic_recovery_pre"), dict):
            first_failure["epidemic_recovery_pre"] = copy.deepcopy(
                attempt["epidemic_recovery_pre"]
            )
        retry_diagnostics = (
            getattr(error, "read_only_query_retry", None)
            if error is not None
            else attempt.get("read_only_query_retry")
        )
        if isinstance(retry_diagnostics, dict):
            first_failure["read_only_query_retry"] = copy.deepcopy(
                retry_diagnostics
            )
        failure_readiness_diagnostics = getattr(
            error, "readiness_diagnostics", None
        )
        if isinstance(failure_readiness_diagnostics, dict):
            first_failure["readiness_diagnostics"] = copy.deepcopy(
                failure_readiness_diagnostics
            )
        failure_last_observation = getattr(error, "last_observation", None)
        if isinstance(failure_last_observation, dict):
            first_failure["last_readiness_observation"] = copy.deepcopy(
                failure_last_observation
            )

    def mark_checkpoint_submit_started() -> None:
        if isinstance(current_attempt, dict):
            current_attempt["stage"] = "checkpoint"

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=poll_seconds,
                cold_start_checkpoint=cold_start_checkpoint,
                stop_event=stop_event,
                **session_profile_options,
            )
        except BaseException as error:  # returned to the owning thread
            session_state["error"] = (
                f"{type(error).__name__}: {error}"
            )
        finally:
            session_done.set()

    try:
        current_attempt = {
            "turn_index": 0,
            "stage": "startup",
            "before": None,
            "plan": None,
            "selected_step": None,
            "result": None,
            "after": None,
        }
        # NativeNamedPipeServer.start() completes in the constructor.  CK3 is
        # deliberately launched only after this endpoint can accept the DLL.
        private_lifestyle_driver_options = (
            {"allow_private_lifestyle_formal_trial": True}
            if allow_private_lifestyle_formal_trial is True
            else {}
        )
        private_faction_driver_options = (
            {
                "allow_private_faction_gift_formal_trial": True,
                "private_faction_round_id": private_faction_round_id,
            }
            if allow_private_faction_gift_formal_trial is True
            else {}
        )
        private_m5_driver_options = (
            {"allow_private_m5_joint_collector": True}
            if allow_private_m5_joint_collector is True
            else {}
        )
        private_child_driver_options = (
            {"allow_private_player_child_marriage_subject_query": True}
            if (private_child_matrilineal_target is not None
                or private_child_matrilineal_pending_read_target is not None
                or allow_private_guy_default_formal_trial is True) else {}
        )
        private_epidemic_driver_options = (
            {"allow_private_epidemic_recovery_query": True}
            if allow_private_epidemic_recovery_near_pair is True
            else {}
        )
        private_prisoner_driver_options = (
            {"allow_private_prisoner_collection_query": True,
             **({"allow_private_prisoner_ransom_action": True}
                if allow_private_prisoner_ransom_formal_trial is True else {})}
            if (allow_private_prisoner_collection_observation is True
                or allow_private_prisoner_ransom_formal_trial is True) else {}
        )
        private_scheme_driver_options = (
            {"allow_private_active_scheme_sway_query": True,
             "allow_private_active_scheme_sway_action": (
                 allow_private_active_scheme_sway_formal_trial is True
             )}
            if private_active_scheme_sway_target is not None else {}
        )
        private_realm_law_driver_options = (
            {"allow_private_realm_law_paused_query": True}
            if private_realm_law_paused_query is True else {}
        )
        private_activity_planner_driver_options = (
            {"allow_private_activity_planner_diag_query": True}
            if private_activity_planner_diag_query is True else {}
        )
        ordinary_succession_driver_options = (
            {
                "allow_private_current_timeline_blocker_query": True,
                "allow_private_death_succession_modal_continue": True,
            }
            if succession_lifecycle_binding["lifecycle"]
            == ORDINARY_CAMPAIGN_SUCCESSION
            else {}
        )
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            route_contact_timeline_speed=route_contact_speed,
            allow_route_contact_high_speed_ab=(
                allow_route_contact_high_speed_ab
            ),
            allow_stationary_objective_hold_sentinel_canary=(
                allow_stationary_objective_hold_sentinel_canary
            ),
            **private_lifestyle_driver_options,
            **private_faction_driver_options,
            **private_m5_driver_options,
            **private_child_driver_options,
            **private_epidemic_driver_options,
            **private_prisoner_driver_options,
            **private_scheme_driver_options,
            **private_realm_law_driver_options,
            **private_activity_planner_driver_options,
            **ordinary_succession_driver_options,
        )
        # This controlled, private Python route does not change the native
        # driver's public action registration or capability advertisement.
        driver.allow_private_construction_formal_trial = (
            allow_private_construction_formal_trial is True
        )
        driver.allow_private_family_marriage_formal_trial = (
            allow_private_family_marriage_formal_trial is True
        )
        driver.allow_private_activity_stage5_feast_full_cost_query = (
            private_activity_feast_stage5_full_cost_read is True
        )
        driver.allow_private_activity_feast_stage5_start_query = (
            private_activity_feast_stage5_start_read is True
        )
        driver.allow_private_activity_feast_guest_candidate_query = (
            private_activity_feast_guest_candidate_read is True
        )
        driver.allow_private_activity_feast_guest_route_proof_query = (
            private_activity_feast_guest_route_proof_read is True
        )
        driver.allow_private_activity_feast_guest_target_query = (
            private_activity_feast_guest_target_character_id is not None
        )
        driver.allow_private_activity_feast_guest_opinion_query = (
            private_activity_feast_guest_opinion_character_id is not None
        )
        driver.allow_private_activity_feast_guest_rule_query = (
            private_activity_feast_guest_rule_key is not None
        )
        driver.allow_private_activity_feast_guest_rule_provenance_query = (
            private_activity_feast_guest_rule_candidate_id is not None
        )
        # Category membership and target value are not yet observable.  A
        # successful category read does not authorize activation.
        driver.allow_private_activity_feast_guest_rule_action = False
        driver.allow_private_activity_feast_stage5_start_action = (
            allow_private_activity_feast_stage5_start_formal_trial is True
        )
        driver.allow_private_player_child_matrilineal_action = (
            private_child_matrilineal_target is not None
            or private_child_matrilineal_pending_read_target is not None
        )
        driver.allow_private_guy_default_formal_trial = (
            allow_private_guy_default_formal_trial is True
        )
        driver.allow_private_player_child_default_action = (
            allow_private_guy_default_formal_trial is True
        )
        driver.child_matrilineal_target_v1 = private_child_matrilineal_target
        # Reuse the same bounded family opt-in for the exact current-heir read.
        # The query remains private and unadvertised by the driver.
        driver.allow_private_current_first_heir_relationship_query = (
            allow_private_family_marriage_formal_trial is True
            or private_child_matrilineal_first_heir_companion is True
            or private_guy_default_first_heir_companion is True
        )
        if opening_focus_gate is not None:
            driver.require_initial_lifestyle_focus_before_date_advance = True
            driver.initial_lifestyle_focus_gate_stage = "await_submit"
        bind_succession_lifecycle = getattr(
            driver, "bind_succession_lifecycle_v1", None
        )
        if callable(bind_succession_lifecycle):
            bind_succession_lifecycle(succession_lifecycle_binding)
        elif succession_lifecycle_binding != legacy_rogue_one_life_binding_v1():
            raise AgentError(
                "selected succession lifecycle requires a binding-capable driver"
            )
        service = GameplayBridgeService(driver)
        landed_title_dir = spec.game_dir / "game" / "common" / "landed_titles"
        camera_index = (
            LandedProvinceIndex.from_game_dir(spec.game_dir)
            if landed_title_dir.is_dir()
            else None
        )
        session_thread = threading.Thread(
            target=supervise,
            name="xar-native-auto-run-session",
            daemon=False,
        )
        session_thread.start()
        session_started = True

        current_attempt["stage"] = "readiness"
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=min(
                readiness_timeout, max(0.001, run_deadline - time.monotonic())
            ),
            stable_seconds=stable_seconds,
            poll_interval_seconds=poll_seconds,
            cold_start_checkpoint=cold_start_checkpoint,
            allow_terminal=False,
            require_post_ready_pump=True,
        )
        current_attempt["before"] = _public_binding(readiness)
        initial_episode = {
            "episode_character_id": readiness.get("episode_character_id"),
            "episode_run_id": readiness.get("episode_run_id"),
            "date_raw": readiness.get("date_raw"),
        }
        current_episode = copy.deepcopy(initial_episode)
        if opening_focus_gate is not None:
            opening_focus_gate["episode_run_id"] = readiness.get("episode_run_id")
        if completion_contract in strict_completion_contracts:
            try:
                _verify_one_generation_binding(readiness, initial_episode)
            except AgentError as error:
                same_episode_binding = False
                capture_first_failure(
                    stage="readiness",
                    kind="identity_violation",
                    message=str(error),
                    error=error,
                )
                raise
        status = "running"

        opening_date_raw = readiness.get("date_raw")
        epidemic_recovery_pre: dict[str, object] | None = None

        def opening_guard_before_submit(
            candidate: dict[str, object],
        ) -> dict[str, object] | None:
            nonlocal epidemic_recovery_pre, exact_move_pre_submit_seen
            if private_child_matrilineal_pending_recovery_only is True:
                _require_private_child_pending_result(candidate, child_recovery_pending)
            if exact_move_contract is not None:
                current_attempt["plan"] = copy.deepcopy(candidate.get("plan"))
                current_attempt["selected_step"] = candidate.get("selected_step")
                if exact_move_pre_submit_seen:
                    raise AgentError("exact war move already submitted; refusing a second action")
                if check_exact_war_move_before(candidate, before, exact_move_contract):
                    exact_move_pre_submit_seen = True
            if opening_focus_gate is not None:
                selected = candidate.get("selected_step")
                plan = candidate.get("plan")
                if opening_focus_gate["stage"] == "await_submit":
                    existing = (
                        plan.get("initial_lifestyle_focus_existing")
                        if isinstance(plan, dict) else None
                    )
                    if existing is not None:
                        source = (
                            existing.get("source_frame")
                            if isinstance(existing, dict) else None
                        )
                        focus = (
                            existing.get("current_focus")
                            if isinstance(existing, dict) else None
                        )
                        progress = (
                            existing.get("current_lifestyle_progress")
                            if isinstance(existing, dict) else None
                        )
                        if not (
                            selected == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
                            and isinstance(source, dict)
                            and source.get("snapshot_id") == candidate.get("snapshot_id")
                            and source.get("revision") == candidate.get("revision")
                            and isinstance(focus, dict)
                            and focus.get("presence") == "present"
                            and isinstance(focus.get("key"), str)
                            and focus.get("key")
                            and isinstance(progress, dict)
                            and progress.get("presence") == "present"
                            and progress.get("lifestyle_key") == focus.get("lifestyle_key")
                            and all(
                                isinstance(progress.get(key), int)
                                and not isinstance(progress.get(key), bool)
                                and progress[key] >= 0
                                for key in (
                                    "xp_total_raw", "xp_within_level_raw",
                                    "xp_per_level", "unspent_perk_points",
                                    "used_perk_points",
                                )
                            )
                            and progress["xp_per_level"] > 0
                            and (
                                existing.get("readback_source")
                                == "native_current_state_only"
                                or existing.get("stock_focus_native_legal")
                                in {True, False}
                            )
                        ):
                            raise AgentError(
                                "existing opening LIFE focus proof is incomplete"
                            )
                        opening_focus_gate["stage"] = "complete"
                        opening_focus_gate["existing_focus"] = focus["key"]
                        driver.require_initial_lifestyle_focus_before_date_advance = (
                            False
                        )
                if opening_focus_gate["stage"] == "await_consumption":
                    consumed = (
                        plan.get("lifestyle_receipt_consumed")
                        if isinstance(plan, dict) else None
                    )
                    if (
                        isinstance(consumed, dict)
                        and consumed.get("kind") == "focus"
                        and consumed.get("action_request_id")
                        == opening_focus_gate["action_request_id"]
                        and consumed.get("target_key")
                        == opening_focus_gate["target_key"]
                        and consumed.get("postcondition_verified") is True
                        and opening_focus_gate["checkpoint_saved"] is True
                    ):
                        opening_focus_gate["stage"] = "complete"
                        driver.require_initial_lifestyle_focus_before_date_advance = (
                            False
                        )
                if opening_focus_gate["stage"] != "complete":
                    permitted = (
                        isinstance(selected, str)
                        and (
                            (
                                opening_focus_gate["stage"] == "await_submit"
                                and selected == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
                                and isinstance(plan, dict)
                                and plan.get("opening_lifestyle_readback")
                                == "absent_native_legal"
                            )
                            or (
                                opening_focus_gate["stage"] == "await_submit"
                                and selected == PRIVATE_LIFESTYLE_FOCUS_SUBMIT_STEP
                            )
                            or (
                                opening_focus_gate["stage"] == "await_receipt"
                                and selected == PRIVATE_LIFESTYLE_RECEIPT_STEP
                            )
                        )
                    )
                    if not permitted:
                        raise AgentError(
                            "initial LIFE focus gate has no verified focus "
                            "receipt, following-turn consumption and checkpoint; "
                            f"refusing {selected!r} before first date advance"
                        )
            interception = (
                before_submit(candidate) if before_submit is not None else None
            )
            if interception is not None:
                return interception
            if allow_private_epidemic_recovery_near_pair is True:
                epidemic_recovery_pre = capture_epidemic_recovery_before_option(
                    service, candidate
                )
                event_plan = candidate.get("plan")
                event_decision = (
                    event_plan.get("event_decision")
                    if isinstance(event_plan, dict) else None
                )
                if (
                    candidate.get("selected_step") == EPIDEMIC_RECOVERY_OPTION_STEP
                    and isinstance(event_decision, dict)
                    and event_decision.get("event_definition_key")
                    == EPIDEMIC_RECOVERY_EVENT_KEY
                    and epidemic_recovery_pre is None
                ):
                    raise AgentError(
                        "exact epidemic recovery option lacks its pre-action county capture"
                    )
                if epidemic_recovery_pre is not None:
                    current_attempt["epidemic_recovery_pre"] = copy.deepcopy(
                        epidemic_recovery_pre
                    )
            return None

        def finish_private_feast_start_trial(
            formal: dict[str, object], *, before: dict[str, object], turn_index: int,
        ) -> str:
            nonlocal visible_gameplay_turns
            result = formal["result"]
            if formal["status"] == "held":
                return "private_activity_feast_stage5_start_held"
            result_status = result["status"]
            if result_status in {
                "applied", "already_applied", "submission_unresolved",
                "pending_post_read_red", "pending_post_unresolved",
            }:
                current_attempt["stage"] = "private_activity_feast_stage5_start_checkpoint"
                checkpoint, snapshot = _materialize_checkpoint(
                    service, driver, spec.profile_dir / "save games",
                    session_done=session_done, session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout, max(0.001, run_deadline - time.monotonic())),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                actor = snapshot.get("played_character")
                if (checkpoint.get("date_raw") != before.get("date_raw")
                        or not isinstance(actor, dict)
                        or actor.get("character_id") != before.get("played_character_id")):
                    raise AgentError("private feast Start checkpoint changed actor/date")
                counts["checkpoint"] += 1
                checkpoints.append({"turn_index": turn_index,
                                    "phase": "private_feast_start_" + result_status,
                                    **checkpoint})
                formal["checkpoint_saved"] = True
            after = _compact_binding(driver.capabilities(), driver.take_snapshot())
            current_attempt["after"] = _public_binding(after)
            current_attempt["result"] = result
            material = result.get("postcondition_verified") is True
            action_attempted = formal["action_attempted"] is True
            turn_class = "gameplay" if action_attempted else "query"
            selected_step = (_PRIVATE_ACTIVITY_FEAST_START_STEP if action_attempted
                             else _PRIVATE_ACTIVITY_FEAST_HOSTED_POST_STEP)
            current_attempt["selected_step"] = selected_step
            counts[turn_class] += 1
            if material and action_attempted:
                visible_gameplay_turns += 1
            turns.append(_turn_record(
                turn_index, formal["started_at"], turn_class=turn_class,
                outcome={"status": "executed" if material else "pending",
                         "selected_step": selected_step, "result": result},
                before=before, after=after,
                evidence=["private_feast_hosted_identity_and_resource_post"
                          if material and action_attempted
                          else "private_feast_restored_hosted_identity"
                          if material else "private_feast_start_unresolved"],
            ))
            if not material:
                current_attempt["stage"] = "private_activity_feast_stage5_start_postcondition"
                raise StepPostconditionError(
                    "private feast Start lacks independent material poststate",
                    step_result=result, selected_step=selected_step)
            return "private_activity_feast_stage5_start_" + result_status

        for turn_index in range(1, turn_count + 1):
            # A first Ctrl+C is deferred by the CLI until the previous typed
            # action and its independent postcondition have both completed.
            # An in-flight command can have an unknown outcome; never save or
            # relaunch from that intermediate state merely to honour a stop.
            if operator_stop_event is not None and operator_stop_event.is_set():
                status = "operator_stop_requested"
                break
            current_attempt = {
                "turn_index": turn_index,
                "stage": "session",
                "before": None,
                "plan": None,
                "selected_step": None,
                "result": None,
                "after": None,
                "read_only_query_retry": None,
                "camera_follow": None,
            }
            if session_done.is_set():
                raise AgentError(_premature_session_exit(session_state))
            remaining = run_deadline - time.monotonic()
            if remaining <= 0:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message="native-auto-run gameplay timeout expired",
                )
                raise AgentError("native-auto-run gameplay timeout expired")
            current_attempt["stage"] = "readiness"
            before = _wait_for_readiness(
                driver,
                session_done=session_done,
                session_state=session_state,
                timeout_seconds=min(readiness_timeout, remaining),
                stable_seconds=0.0,
                poll_interval_seconds=poll_seconds,
                cold_start_checkpoint=False,
                allow_terminal=True,
            )
            current_attempt["before"] = _public_binding(before)
            if allow_private_activity_feast_stage5_start_formal_trial is True:
                feast_ledger = read_feast_start_ledger(driver.state_dir)
                if feast_ledger["pending"] is not None or feast_ledger["resolved"] is not None:
                    current_attempt["stage"] = "private_activity_feast_stage5_start_recovery"
                    private_activity_feast_stage5_start_formal = {
                        "status": "recovery", "started_at": utc_now(),
                        "action_attempted": False, "checkpoint_saved": False,
                        "result": consume_feast_start_private_v1(driver, inputs={}),
                    }
                    status = finish_private_feast_start_trial(
                        private_activity_feast_stage5_start_formal,
                        before=before, turn_index=turn_index)
                    break
            if private_child_matrilineal_pending_read_target is not None:
                current_attempt["stage"] = "private_child_matrilineal_pending_read"
                private_child_matrilineal_pending_observation = (
                    _observe_private_child_matrilineal_pending_once(
                        driver, service=service, before=before,
                        pair=private_child_matrilineal_pending_read_target,
                        turn_index=turn_index,
                    )
                )
                if private_child_matrilineal_first_heir_companion is True:
                    current_attempt["stage"] = "private_first_heir_companion_read"
                    private_first_heir_companion_observation = (
                        observe_first_heir_companion_after_child(
                            driver, service, before=before,
                            child_observation=private_child_matrilineal_pending_observation,
                            first_heir_resolved=read_family_marriage_ledger(
                                driver.state_dir)["resolved"],
                            turn_index=turn_index,
                        )
                    )
                status = "private_child_matrilineal_pending_observed"
                break
            if private_activity_planner_diag_query is True:
                current_attempt["stage"] = "private_activity_planner_diag_read"
                private_activity_planner_diag_observation = (
                    _observe_private_activity_planner_diag_once(
                        driver, service=service, before=before,
                        turn_index=turn_index,
                    )
                )
                status = "private_activity_planner_diag_observed"
                break
            if (private_activity_feast_guest_opinion_character_id is not None
                    and not combined_target_opinion):
                current_attempt["stage"] = "private_activity_feast_guest_opinion_read"
                status = "private_activity_feast_guest_opinion_unresolved"
                private_activity_feast_guest_opinion_observation = (
                    _read_private_activity_feast_guest_opinion_once(
                        driver, service=service, before=before,
                        guest_character_id=private_activity_feast_guest_opinion_character_id,
                        turn_index=turn_index,
                    )
                )
                status = "private_activity_feast_guest_opinion_read"
                break
            if (private_activity_feast_planner_open is True
                    or private_activity_feast_stage1_option_read is True
                    or private_activity_feast_stage1_confirm is True):
                current_attempt["stage"] = "private_activity_feast_planner_open"
                private_activity_feast_planner_open_observation = (
                    _open_private_activity_feast_planner_once(
                        driver, service=service, before=before,
                        turn_index=turn_index,
                    )
                )
                if (private_activity_feast_stage1_option_read is True
                        or private_activity_feast_stage1_confirm is True):
                    current_attempt["stage"] = "private_activity_feast_stage1_option_read"
                    private_activity_feast_stage1_option_observation = (
                        _read_private_activity_feast_stage1_option_once(
                            driver, service=service, before=before,
                            open_observation=private_activity_feast_planner_open_observation,
                            turn_index=turn_index,
                        )
                    )
                    if private_activity_feast_stage1_confirm is True:
                        current_attempt["stage"] = "private_activity_feast_stage1_confirm"
                        private_activity_feast_stage1_confirm_observation = (
                            _confirm_private_activity_feast_stage1_once(
                                driver, service=service, before=before,
                                option_observation=(
                                    private_activity_feast_stage1_option_observation
                                ),
                                turn_index=turn_index,
                            )
                        )
                        current_attempt["stage"] = "private_activity_feast_stage2_option_read"
                        private_activity_feast_stage2_option_observation = (
                            _read_private_activity_feast_stage2_option_once(
                                driver, service=service, before=before,
                                confirm_observation=(
                                    private_activity_feast_stage1_confirm_observation
                                ),
                                turn_index=turn_index,
                            )
                        )
                        if private_activity_feast_stage2_gate_read is True:
                            current_attempt["stage"] = "private_activity_feast_stage2_gate_read"
                            private_activity_feast_stage2_gate_observation = (
                                _read_private_activity_feast_stage2_gate_once(
                                    driver, service=service, before=before,
                                    confirm_observation=(
                                        private_activity_feast_stage1_confirm_observation
                                    ),
                                    option_observation=(
                                        private_activity_feast_stage2_option_observation
                                    ),
                                    turn_index=turn_index,
                                )
                            )
                            status = "private_activity_feast_stage2_gate_observed"
                        else:
                            status = "private_activity_feast_stage1_confirm_verified"
                        if private_activity_feast_stage2_location_candidate_province_ids is not None:
                            current_attempt["stage"] = "private_activity_feast_stage2_location_read"
                            private_activity_feast_stage2_location_observation = (
                                _read_private_activity_feast_stage2_location_once(
                                    driver, service=service, before=before,
                                    confirm_observation=(
                                        private_activity_feast_stage1_confirm_observation
                                    ),
                                    option_observation=(
                                        private_activity_feast_stage2_option_observation
                                    ),
                                    candidate_province_ids=(
                                        private_activity_feast_stage2_location_candidate_province_ids
                                    ),
                                    turn_index=turn_index,
                                )
                            )
                            status = "private_activity_feast_stage2_location_observed"
                            if private_activity_feast_stage2_destination_province_id is not None:
                                current_attempt["stage"] = "private_activity_feast_stage2_destination_select"
                                private_activity_feast_stage2_destination_observation = (
                                    _select_private_activity_feast_stage2_destination_once(
                                        driver, service=service, before=before,
                                        location_observation=(
                                            private_activity_feast_stage2_location_observation
                                        ),
                                        province_id=private_activity_feast_stage2_destination_province_id,
                                        turn_index=turn_index,
                                    )
                                )
                                status = "private_activity_feast_stage2_destination_selected"
                                if private_activity_feast_stage5_full_cost_read is True:
                                    current_attempt["stage"] = "private_activity_feast_stage5_full_cost_read"
                                    private_activity_feast_stage5_full_cost_observation = (
                                        _read_private_activity_feast_stage5_full_cost_once(
                                            driver, service=service, before=before,
                                            destination_observation=(
                                                private_activity_feast_stage2_destination_observation
                                            ),
                                            turn_index=turn_index,
                                        )
                                    )
                                    status = "private_activity_feast_stage5_full_cost_observed"
                                    if private_activity_feast_guest_candidate_read is True:
                                        current_attempt["stage"] = "private_activity_feast_guest_candidate_read"
                                        status = "private_activity_feast_guest_candidate_unresolved"
                                        private_activity_feast_guest_candidate_observation = (
                                            _read_private_activity_feast_guest_candidate_once(
                                                driver, service=service, before=before,
                                                cost_observation=(
                                                    private_activity_feast_stage5_full_cost_observation
                                                ), turn_index=turn_index,
                                            )
                                        )
                                        status = "private_activity_feast_guest_candidate_read"
                                    if private_activity_feast_guest_route_proof_read is True:
                                        current_attempt["stage"] = "private_activity_feast_guest_route_proof_read"
                                        status = "private_activity_feast_guest_route_proof_unresolved"
                                        private_activity_feast_guest_route_proof_observation = (
                                            _read_private_activity_feast_guest_route_proof_once(
                                                driver, service=service, before=before,
                                                cost_observation=(
                                                    private_activity_feast_stage5_full_cost_observation
                                                ), turn_index=turn_index,
                                            )
                                        )
                                        status = "private_activity_feast_guest_route_proof_read"
                                    if private_activity_feast_guest_target_character_id is not None:
                                        current_attempt["stage"] = "private_activity_feast_guest_target_read"
                                        status = "private_activity_feast_guest_target_unresolved"
                                        private_activity_feast_guest_target_observation = (
                                            _read_private_activity_feast_guest_target_once(
                                                driver, service=service, before=before,
                                                cost_observation=(
                                                    private_activity_feast_stage5_full_cost_observation
                                                ),
                                                target_character_id=(
                                                    private_activity_feast_guest_target_character_id
                                                ), turn_index=turn_index,
                                            )
                                        )
                                        status = "private_activity_feast_guest_target_read"
                                    if private_activity_feast_guest_rule_key is not None:
                                        current_attempt["stage"] = "private_activity_feast_guest_rule_read"
                                        private_activity_feast_guest_rule_observation = (
                                            _read_private_activity_feast_guest_rule_once(
                                                driver, service=service, before=before,
                                                cost_observation=(
                                                    private_activity_feast_stage5_full_cost_observation
                                                ),
                                                authored_rule_key=private_activity_feast_guest_rule_key,
                                                candidate_character_id=(
                                                    private_activity_feast_guest_rule_candidate_id
                                                ),
                                                candidate_observation=(
                                                    private_activity_feast_guest_candidate_observation
                                                ),
                                                target_observation=(
                                                    private_activity_feast_guest_target_observation
                                                ),
                                                turn_index=turn_index,
                                            )
                                        )
                                        status = "private_activity_feast_guest_rule_read"
                                    if (private_activity_feast_guest_target_character_id is not None
                                            and private_activity_feast_guest_rule_candidate_id
                                                == private_activity_feast_guest_target_character_id):
                                        current_attempt["stage"] = "private_activity_feast_guest_target_recheck"
                                        private_activity_feast_guest_target_recheck_observation = (
                                            _read_private_activity_feast_guest_target_once(
                                                driver, service=service, before=before,
                                                cost_observation=(
                                                    private_activity_feast_stage5_full_cost_observation
                                                ),
                                                target_character_id=(
                                                    private_activity_feast_guest_target_character_id
                                                ), turn_index=turn_index,
                                            )
                                        )
                                        first_target = private_activity_feast_guest_target_observation[
                                            "target_read"]
                                        repeated_target = private_activity_feast_guest_target_recheck_observation[
                                            "target_read"]
                                        rule_membership = private_activity_feast_guest_rule_observation[
                                            "candidate_category_membership"]
                                        if (not _private_activity_feast_guest_target_same_source(
                                                first_target, repeated_target)
                                                or (rule_membership is True
                                                    and first_target["native_filtered_member"] is not True)):
                                            raise StepPostconditionError(
                                                "private feast target and named rule crossed native source",
                                                step_result={
                                                    "step": _PRIVATE_ACTIVITY_GUEST_TARGET_STEP,
                                                    "status": "red", "accepted": False,
                                                    "postcondition_verified": False,
                                                    "first_target": first_target,
                                                    "repeated_target": repeated_target,
                                                    "rule_membership": rule_membership,
                                                },
                                                selected_step=_PRIVATE_ACTIVITY_GUEST_TARGET_STEP,
                                            )
                                    if combined_target_opinion:
                                        current_attempt["stage"] = "private_activity_feast_guest_opinion_read"
                                        status = "private_activity_feast_guest_opinion_unresolved"
                                        private_activity_feast_guest_opinion_observation = (
                                            _read_private_activity_feast_guest_opinion_once(
                                                driver, service=service, before=before,
                                                guest_character_id=(
                                                    private_activity_feast_guest_target_character_id
                                                ), turn_index=turn_index,
                                            )
                                        )
                                        status = "private_activity_feast_guest_opinion_read"
                                    if private_activity_feast_stage5_start_read is True:
                                        current_attempt["stage"] = "private_activity_feast_stage5_start_read"
                                        private_activity_feast_stage5_start_observation = (
                                            _read_private_activity_feast_stage5_start_once(
                                                driver, service=service, before=before,
                                                cost_observation=(
                                                    private_activity_feast_stage5_full_cost_observation
                                                ), turn_index=turn_index,
                                            )
                                        )
                                        status = "private_activity_feast_stage5_start_assessed"
                                        if allow_private_activity_feast_stage5_start_formal_trial is True:
                                            observation = private_activity_feast_stage5_start_observation
                                            policy = observation["policy_assessment"]
                                            observation.update({
                                                "decision": policy["decision"],
                                                "decision_reason": policy.get("reason"),
                                                "formal_action_ready": policy["decision"] == "start",
                                            })
                                            private_activity_feast_stage5_start_formal = {
                                                "status": "submitted" if policy["decision"] == "start" else "held",
                                                "started_at": utc_now(),
                                                "action_attempted": policy["decision"] == "start",
                                                "checkpoint_saved": False,
                                                "result": policy,
                                            }
                                            if policy["decision"] == "start":
                                                current_attempt["stage"] = "private_activity_feast_stage5_start_formal"
                                                private_activity_feast_stage5_start_formal["result"] = (
                                                    consume_feast_start_private_v1(
                                                        driver, inputs=observation["inputs"],
                                                        budget=observation["budget_observation"]["budget"],
                                                    )
                                                )
                                            status = finish_private_feast_start_trial(
                                                private_activity_feast_stage5_start_formal,
                                                before=before, turn_index=turn_index)
                    else:
                        status = "private_activity_feast_stage1_option_observed"
                elif private_activity_cost_slot12_raw_read is True:
                    current_attempt["stage"] = "private_activity_cost_slot12_raw_read"
                    private_activity_cost_slot12_raw_observation = (
                        _read_private_activity_cost_slot12_raw_once(
                            driver, service=service, before=before,
                            open_observation=private_activity_feast_planner_open_observation,
                            turn_index=turn_index,
                        )
                    )
                    status = "private_activity_cost_slot12_raw_observed"
                else:
                    status = "private_activity_feast_planner_open_observed"
                break
            if private_activity_cost_slot12_raw_read is True:
                current_attempt["stage"] = "private_activity_cost_slot12_raw_read"
                private_activity_cost_slot12_raw_observation = (
                    _read_private_activity_cost_slot12_raw_once(
                        driver, service=service, before=before,
                        open_observation=None, turn_index=turn_index,
                    )
                )
                status = "private_activity_cost_slot12_raw_observed"
                break
            if private_realm_law_paused_query is True:
                current_attempt["stage"] = "private_realm_law_paused_read"
                private_realm_law_paused_observation = (
                    _observe_private_realm_law_paused_once(
                        driver, service=service, before=before,
                        turn_index=turn_index,
                    )
                )
                status = "private_realm_law_paused_observed"
                break
            if private_active_scheme_sway_target is not None:
                current_attempt["stage"] = "private_active_scheme_sway_read"
                private_active_scheme_sway_observation = (
                    _observe_private_active_scheme_sway_once(
                        driver, service=service, before=before,
                        target_character_id=private_active_scheme_sway_target,
                        turn_index=turn_index,
                    )
                )
                if allow_private_active_scheme_sway_formal_trial is True:
                    current_attempt["stage"] = "private_active_scheme_sway_formal"
                    private_active_scheme_sway_formal = consume_sway_private_once(
                        driver,
                        target_character_id=private_active_scheme_sway_target,
                        snapshot=before,
                        readback=private_active_scheme_sway_observation["readback"],
                    )
                    if private_active_scheme_sway_formal["status"] in {
                        "receipt_pending", "postcondition_pending", "applied",
                    }:
                        current_attempt["stage"] = "private_active_scheme_sway_checkpoint"
                        sway_checkpoint, sway_checkpoint_snapshot = (
                            _materialize_checkpoint(
                                service, driver,
                                spec.profile_dir / "save games",
                                session_done=session_done,
                                session_state=session_state,
                                timeout_seconds=min(
                                    readiness_timeout,
                                    max(0.001, run_deadline - time.monotonic()),
                                ),
                                poll_interval_seconds=poll_seconds,
                                on_checkpoint_submit=mark_checkpoint_submit_started,
                            )
                        )
                        sway_checkpoint_actor = sway_checkpoint_snapshot.get(
                            "played_character")
                        if (sway_checkpoint.get("date_raw") != before.get("date_raw")
                                or not isinstance(sway_checkpoint_actor, dict)
                                or sway_checkpoint_actor.get("character_id")
                                != before.get("played_character_id")):
                            raise AgentError(
                                "private Sway checkpoint changed actor/date")
                        counts["checkpoint"] += 1
                        checkpoints.append({
                            "turn_index": turn_index,
                            "phase": "private_active_scheme_sway_" + str(
                                private_active_scheme_sway_formal["status"]),
                            **sway_checkpoint,
                        })
                        private_active_scheme_sway_formal["checkpoint_saved"] = True
                    status = "private_active_scheme_sway_" + str(
                        private_active_scheme_sway_formal["status"])
                else:
                    status = "private_active_scheme_sway_observed"
                break
            if (
                allow_private_prisoner_collection_observation is True
                and private_prisoner_collection_observation is None
            ):
                private_prisoner_collection_observation = (
                    _observe_private_prisoner_collection_once(
                        driver, before=before, turn_index=turn_index
                    )
                )
            if (
                opening_focus_gate is not None
                and opening_focus_gate["stage"] == "complete"
                and natural_succession_transitions
                and opening_focus_gate.get("episode_run_id")
                != current_episode.get("episode_run_id")
                and before.get("episode_run_id")
                == current_episode.get("episode_run_id")
                and before.get("episode_character_id")
                == current_episode.get("episode_character_id")
                and before.get("paused") is True
                and before.get("map_ready") is True
                and before.get("one_life_terminal") is not True
                and isinstance(before.get("active_context"), dict)
                and before["active_context"].get("active_event") is None
                and before["active_context"].get("pending_character_interaction")
                is None
            ):
                # The predecessor's completed gate cannot certify the new
                # character. Wait until modal decisions clear, then reuse the
                # original focus/receipt/checkpoint path on this episode.
                opening_focus_gate.pop("existing_focus", None)
                opening_focus_gate.update({
                    "stage": "await_submit",
                    "episode_run_id": current_episode["episode_run_id"],
                    "action_request_id": None,
                    "target_key": None,
                    "checkpoint_saved": False,
                })
                opening_date_raw = before.get("date_raw")
                driver.require_initial_lifestyle_focus_before_date_advance = True
                driver.initial_lifestyle_focus_gate_stage = "await_submit"
            if camera_index is not None:
                try:
                    semantic = before.get("_semantic")
                    if not isinstance(semantic, dict):
                        raise ValueError("readiness frame has no bound war snapshot")
                    current_attempt["camera_follow"] = follow_war_hotspot(
                        service, {
                            "revision": before.get("revision"),
                            "active_wars": semantic.get("active_wars"),
                        }, camera_index,
                        park_cursor=park_foreground_ck3_cursor,
                    )
                except (BridgeUnavailableError, UnsupportedStepError, ValueError, OSError) as error:
                    # Presentation failure cannot invent or replace a gameplay
                    # action.  The failed follow remains visible in this turn.
                    current_attempt["camera_follow"] = {
                        "status": "unavailable",
                        "reason": f"{type(error).__name__}: {error}",
                    }
            if (
                opening_focus_gate is not None
                and opening_focus_gate["stage"] != "complete"
                and before.get("date_raw") != opening_date_raw
            ):
                raise AgentError(
                    "initial LIFE focus gate observed date advance before a "
                    "verified and consumed focus receipt"
                )
            if completion_contract in strict_completion_contracts:
                try:
                    if next_episode_transition is None:
                        _verify_one_generation_binding(
                            before, initial_episode
                        )
                    else:
                        _verify_next_episode_binding(
                            before, next_episode_transition
                        )
                except AgentError as error:
                    same_episode_binding = False
                    capture_first_failure(
                        stage="readiness",
                        kind="identity_violation",
                        message=str(error),
                        error=error,
                    )
                    raise
            turn_started = utc_now()
            epidemic_recovery_pre = None
            # GameplayBridgeService.auto_turn() owns planning and execution in
            # one call.  Until it returns a typed step, an exception may have
            # occurred after a planner-selected save already overwrote the
            # canonical checkpoint path.
            current_attempt["stage"] = "opaque_auto_turn"
            pre_submission_revision_replans = 0
            while True:
                try:
                    outcome = (
                        service.auto_turn(before_submit=opening_guard_before_submit)
                        if (
                            opening_focus_gate is not None
                            or private_child_matrilineal_pending_recovery_only is True
                            or before_submit is not None
                            or exact_move_contract is not None
                            or allow_private_epidemic_recovery_near_pair is True
                        )
                        else service.auto_turn()
                    )
                    break
                except PreSubmissionRevisionMismatchError as error:
                    exact_move_pre_submit_seen = False
                    epidemic_recovery_pre = None
                    current_attempt.pop("epidemic_recovery_pre", None)
                    if isinstance(error.plan, dict):
                        current_attempt["plan"] = copy.deepcopy(error.plan)
                    if (
                        isinstance(error.selected_step, str)
                        and error.selected_step
                    ):
                        current_attempt["selected_step"] = error.selected_step
                    if pre_submission_revision_replans >= 1:
                        error.replan_count = pre_submission_revision_replans
                        raise
                    pre_submission_revision_replans += 1
                    current_attempt["stage"] = "revision_replan_readiness"
                    remaining = run_deadline - time.monotonic()
                    if remaining <= 0:
                        raise AgentError(
                            "native-auto-run gameplay timeout expired during "
                            "revision replan"
                        )
                    before = _wait_for_readiness(
                        driver,
                        session_done=session_done,
                        session_state=session_state,
                        timeout_seconds=min(readiness_timeout, remaining),
                        stable_seconds=0.0,
                        poll_interval_seconds=poll_seconds,
                        cold_start_checkpoint=False,
                        allow_terminal=True,
                    )
                    current_attempt["before"] = _public_binding(before)
                    if completion_contract in strict_completion_contracts:
                        try:
                            if next_episode_transition is None:
                                _verify_one_generation_binding(
                                    before, initial_episode
                                )
                            else:
                                _verify_next_episode_binding(
                                    before, next_episode_transition
                                )
                        except AgentError as binding_error:
                            same_episode_binding = False
                            capture_first_failure(
                                stage="readiness",
                                kind="identity_violation",
                                message=str(binding_error),
                                error=binding_error,
                            )
                            raise
                    current_attempt["stage"] = "opaque_auto_turn"
            outcome["pre_submission_revision_replans"] = (
                pre_submission_revision_replans
            )
            outcome_status = outcome.get("status")
            plan = outcome.get("plan")
            selected_step = outcome.get("selected_step")
            if not isinstance(selected_step, str) and isinstance(plan, dict):
                selected_step = plan.get("selected_step")
            step = selected_step if isinstance(selected_step, str) else None
            current_attempt["plan"] = copy.deepcopy(plan)
            current_attempt["selected_step"] = step
            current_attempt["result"] = copy.deepcopy(outcome.get("result"))
            turn_class = _turn_class(step, outcome_status, plan)
            retry = outcome.get("read_only_query_retry")
            if retry is not None:
                current_attempt["read_only_query_retry"] = (
                    _compact_root_query_retry(retry)
                )
                retried_before = _retried_root_query_binding(
                    driver, before=before, retry=retry,
                    selected_step=step, status=outcome_status,
                )
                if retried_before is None:
                    capture_first_failure(
                        stage="postcondition",
                        kind="read_only_query_retry_anchor_invalid",
                        message=(
                            "rejected campaign-root read did not retain a "
                            "same-campaign paused retry anchor"
                        ),
                    )
                    raise AgentError(
                        "rejected campaign-root read lacks a valid paused retry anchor"
                    )
                before = retried_before
                current_attempt["before"] = _public_binding(before)

            if outcome_status == "intercepted":
                if before_submit is None or step is None:
                    raise AgentError("unexpected pre-submission interception")
                current_attempt["stage"] = "checkpoint"
                remaining = run_deadline - time.monotonic()
                if remaining <= 0:
                    raise AgentError(
                        "native-auto-run timeout expired before candidate checkpoint"
                    )
                checkpoint, after_snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(readiness_timeout, remaining),
                    poll_interval_seconds=poll_seconds,
                )
                checkpoint = {
                    **checkpoint,
                    "phase": "candidate_terminal_intercept",
                    "turn_index": turn_index,
                }
                checkpoints.append(checkpoint)
                counts["checkpoint"] += 1
                counts["terminal"] += 1
                candidate_interception = {
                    "status": "intercepted-before-submit",
                    "selected_step": step,
                    "plan": copy.deepcopy(plan),
                    "interception": copy.deepcopy(outcome.get("interception")),
                    "checkpoint": copy.deepcopy(checkpoint),
                    "before": _public_binding(before),
                    "after_checkpoint": _public_binding(after_snapshot),
                }
                turns.append(
                    _turn_record(
                        turn_index,
                        turn_started,
                        turn_class="terminal",
                        outcome=outcome,
                        before=before,
                        after=after_snapshot,
                        evidence=[
                            "formal_plan_intercepted_before_submission",
                            "candidate_checkpoint_saved",
                        ],
                        camera_follow=current_attempt["camera_follow"],
                    )
                )
                if after_intercept is None:
                    status = "candidate_terminal_intercepted"
                    break
                current_attempt["stage"] = "candidate_resolution"
                try:
                    resolution = after_intercept(
                        driver,
                        candidate_interception,
                    )
                except BaseException as error:
                    candidate_resolution = {
                        "ok": False,
                        "status": "callback_exception",
                        "error": f"{type(error).__name__}: {error}",
                    }
                    current_attempt["result"] = copy.deepcopy(
                        candidate_resolution
                    )
                    raise AgentError(
                        "after-intercept callback raised: "
                        f"{type(error).__name__}: {error}"
                    ) from error
                if not isinstance(resolution, Mapping):
                    candidate_resolution = {
                        "ok": False,
                        "status": "invalid_callback_result",
                        "error": (
                            "after-intercept callback returned a non-mapping "
                            f"result: {type(resolution).__name__}"
                        ),
                    }
                    current_attempt["result"] = copy.deepcopy(
                        candidate_resolution
                    )
                    raise AgentError(str(candidate_resolution["error"]))
                candidate_resolution = copy.deepcopy(dict(resolution))
                current_attempt["result"] = copy.deepcopy(
                    candidate_resolution
                )
                if candidate_resolution.get("ok") is not True:
                    detail = candidate_resolution.get(
                        "error",
                        candidate_resolution.get(
                            "reason",
                            candidate_resolution.get("status", "unknown"),
                        ),
                    )
                    raise AgentError(
                        "after-intercept callback did not report success: "
                        f"{detail}"
                    )
                status = "candidate_terminal_resolved"
                break

            if outcome_status == "blocked":
                current_attempt["stage"] = "planning"
                counts["terminal"] += 1
                turns.append(
                    _turn_record(
                        turn_index,
                        turn_started,
                        turn_class="terminal",
                        outcome=outcome,
                        before=before,
                        after=before,
                        evidence=[],
                        camera_follow=current_attempt["camera_follow"],
                    )
                )
                status = "blocked"
                capture_first_failure(
                    stage="planning",
                    kind="planner_blocked",
                    message=str(
                        plan.get("reason")
                        if isinstance(plan, dict)
                        else "no executable step"
                    ),
                )
                raise AgentError(
                    "native planner is blocked: "
                    + str(
                        plan.get("reason")
                        if isinstance(plan, dict)
                        else "no executable step"
                    )
                )
            if outcome_status == "terminal":
                current_attempt["stage"] = "planning"
                counts["terminal"] += 1
                turns.append(
                    _turn_record(
                        turn_index,
                        turn_started,
                        turn_class="terminal",
                        outcome=outcome,
                        before=before,
                        after=before,
                        evidence=[],
                        camera_follow=current_attempt["camera_follow"],
                    )
                )
                if completion_contract in strict_completion_contracts:
                    status = "terminal_preexisting"
                    capture_first_failure(
                        stage="readiness",
                        kind="preexisting_terminal",
                        message=(
                            f"{completion_contract} completion requires "
                            "death-terminal to be executed and verified by "
                            "this run"
                        ),
                    )
                    raise AgentError(
                        f"{completion_contract} completion requires "
                        "death-terminal to be executed and verified by this "
                        "run"
                    )
                status = "terminal_preexisting"
                break
            if outcome_status != "executed" or step is None:
                capture_first_failure(
                    stage="planning_or_action",
                    kind="malformed_auto_turn_outcome",
                    message=(
                        "native auto-turn returned a malformed outcome: "
                        f"status={outcome_status!r}, step={step!r}"
                    ),
                )
                raise AgentError(
                    "native auto-turn returned a malformed outcome: "
                    f"status={outcome_status!r}, step={step!r}"
                )

            current_attempt["stage"] = (
                "checkpoint"
                if turn_class == "checkpoint"
                else "postcondition_observation"
            )
            after_snapshot = (
                service.snapshot()
                if step == "save-checkpoint"
                else _runner_semantic_snapshot(driver)
            )
            merge_observation: dict[str, object] | None = None
            if parse_merge_armies_step(step) is not None:
                result = outcome.get("result")
                merge_observation = observe_merge_armies_postcondition_v1(
                    step, result, after_snapshot
                )
                if merge_observation.get("status") != "applied":
                    current_attempt["stage"] = (
                        "merge_postcondition_observation"
                    )
                if isinstance(result, dict):
                    result["merge_postcondition"] = copy.deepcopy(
                        merge_observation
                    )
                    current_attempt["result"] = copy.deepcopy(result)
                after = _compact_binding(
                    driver.capabilities(), after_snapshot
                )
                current_attempt["after"] = _public_binding(after)
                if merge_observation.get("status") != "applied":
                    capture_first_failure(
                        stage="merge_postcondition_observation",
                        kind="merge_result_postcondition_pending",
                        message=(
                            "native merge ACK lacks an independently published "
                            "exact source-removal postcondition"
                        ),
                    )
                    raise AgentError(
                        "native merge result remains pending; the exact merge "
                        "receipt was retained and the command was not resubmitted"
                    )
            terminal_pending = bool(
                after_snapshot.get("one_life_terminal") is True
                or isinstance(
                    after_snapshot.get("one_life_terminal_reason"), str
                )
            )
            modal_decision_pending = _player_decision_pending(after_snapshot)
            after = _compact_binding(driver.capabilities(), after_snapshot)
            current_attempt["after"] = _public_binding(after)
            if exact_move_contract is not None and step == exact_war_move_step(exact_move_contract):
                if not exact_move_pre_submit_seen or terminal_pending or modal_decision_pending:
                    raise AgentError("exact war move poststate has no gated submit or is unsafe")
                exact_move_poststate = check_exact_war_move_poststate(
                    before, outcome.get("result"), after_snapshot, exact_move_contract
                )
                current_attempt["exact_war_move_poststate"] = copy.deepcopy(exact_move_poststate)
            semantic_evidence = _semantic_delta(before, after_snapshot, after)
            evidence = list(semantic_evidence)
            if step == PRIVATE_PRISONER_RANSOM_RECEIPT_STEP:
                ransom_result = outcome.get("result")
                if (not isinstance(ransom_result, dict)
                        or ransom_result.get("status") == "ambiguous"):
                    raise AgentError("prisoner ransom receipt lacks material attribution")
                if ransom_result.get("status") == "applied":
                    if (ransom_result.get("postcondition_verified") is not True
                            or ransom_result.get("prisoner_no_longer_held") is not True
                            or ransom_result.get("material_result") is not True):
                        raise AgentError("prisoner ransom applied receipt is incomplete")
                    evidence.append("prisoner_ransom_custody_and_gold_material_readback")
            if (
                opening_focus_gate is not None
                and opening_focus_gate["stage"] != "complete"
                and after_snapshot.get("date_raw") != opening_date_raw
            ):
                raise AgentError(
                    "initial LIFE focus gate observed date advance before a "
                    "verified and consumed focus receipt"
                )
            if (
                isinstance(merge_observation, dict)
                and merge_observation.get("status") == "applied"
            ):
                evidence.append(
                    "army_merge_source_removed_independent_paused_frame"
                )
            if step == PRIVATE_LIFESTYLE_FOCUS_SUBMIT_STEP and opening_focus_gate is not None:
                focus_submit = outcome.get("result")
                if not (
                    opening_focus_gate["stage"] == "await_submit"
                    and isinstance(focus_submit, dict)
                    and focus_submit.get("status") == "submitted_verification_pending"
                    and focus_submit.get("kind") == "focus"
                    and focus_submit.get("target_key")
                    in _OPENING_FOCUS_LIFESTYLE_BY_TARGET
                    and isinstance(focus_submit.get("action_request_id"), str)
                ):
                    raise AgentError("initial LIFE focus typed submit is not pending verification")
                opening_focus_gate["stage"] = "await_receipt"
                driver.initial_lifestyle_focus_gate_stage = "await_receipt"
                opening_focus_gate["action_request_id"] = focus_submit["action_request_id"]
                opening_focus_gate["target_key"] = focus_submit["target_key"]
            if step == PRIVATE_LIFESTYLE_RECEIPT_STEP:
                receipt = outcome.get("result")
                receipt_kind = receipt.get("kind") if isinstance(receipt, dict) else None
                material_verified = (
                    receipt.get("post_has_current_focus") is True
                    and receipt.get("post_current_focus_key") == receipt.get("target_key")
                    if receipt_kind == "focus" and isinstance(receipt, dict)
                    else receipt.get("post_target_perk_owned") is True
                    if receipt_kind == "perk" and isinstance(receipt, dict)
                    else False
                )
                if not (
                    isinstance(receipt, dict)
                    and receipt.get("status") == "applied"
                    and receipt.get("postcondition_verified") is True
                    and material_verified
                    and receipt.get("post_snapshot_id")
                    == after_snapshot.get("snapshot_id")
                    and receipt.get("post_public_revision")
                    == after_snapshot.get("native_revision")
                    and receipt.get("episode_run_id")
                    == after_snapshot.get("episode_run_id")
                ):
                    capture_first_failure(
                        stage="lifestyle_receipt",
                        kind="lifestyle_material_postcondition_failed",
                        message="the private LIFE receipt lost its independent published frame",
                    )
                    raise AgentError(
                        "private LIFE receipt did not match the next paused game frame"
                    )
                if receipt_kind == "focus":
                    target_lifestyle_key = _OPENING_FOCUS_LIFESTYLE_BY_TARGET.get(
                        receipt.get("target_key")
                    )
                    post_life2 = query_player_lifestyle_private_v1(
                        driver,
                        expected_revision=int(after_snapshot["revision"]),
                        query_step=PRIVATE_LIFESTYLE_STATE_QUERY_STEP,
                    )
                    post_state = post_life2.get("snapshot")
                    post_source = post_life2.get("source_frame")
                    post_focus = (
                        post_state.get("current_focus")
                        if isinstance(post_state, dict) else None
                    )
                    post_progress = (
                        post_state.get("current_lifestyle_progress")
                        if isinstance(post_state, dict) else None
                    )
                    if not (
                        post_life2.get("status") == "available"
                        and isinstance(post_source, dict)
                        and post_source.get("snapshot_id")
                        == after_snapshot.get("snapshot_id")
                        and post_source.get("native_revision")
                        == after_snapshot.get("native_revision")
                        and post_source.get("date_raw")
                        == after_snapshot.get("date_raw")
                        and isinstance(post_focus, dict)
                        and post_focus.get("presence") == "present"
                        and post_focus.get("key") == receipt.get("target_key")
                        and target_lifestyle_key is not None
                        and isinstance(post_progress, dict)
                        and post_progress.get("presence") == "present"
                        and post_progress.get("lifestyle_key")
                        == target_lifestyle_key
                        and isinstance(post_progress.get("xp_total_raw"), int)
                        and not isinstance(post_progress.get("xp_total_raw"), bool)
                        and post_progress.get("xp_total_raw") >= 0
                        and isinstance(post_progress.get("unspent_perk_points"), int)
                        and not isinstance(post_progress.get("unspent_perk_points"), bool)
                        and post_progress.get("unspent_perk_points") >= 0
                    ):
                        raise AgentError(
                            "private LIFE focus receipt lacks independent LIFE2 "
                            "current focus and XP/point readback"
                        )
                    receipt["post_life2_current_state"] = {
                        "snapshot_id": post_source["snapshot_id"],
                        "current_focus": dict(post_focus),
                        "current_lifestyle_progress": dict(post_progress),
                    }
                    current_attempt["result"] = copy.deepcopy(receipt)
                    if opening_focus_gate is not None:
                        if not (
                            opening_focus_gate["stage"] == "await_receipt"
                            and receipt.get("action_request_id")
                            == opening_focus_gate["action_request_id"]
                            and receipt.get("target_key")
                            == opening_focus_gate["target_key"]
                        ):
                            raise AgentError("initial LIFE focus receipt does not match its one typed submit")
                        opening_focus_gate["stage"] = "await_consumption"
                        driver.initial_lifestyle_focus_gate_stage = "await_consumption"
                    evidence.append("lifestyle_focus_independent_later_frame")
                else:
                    evidence.append("lifestyle_has_perk_independent_later_frame")
            if step == PRIVATE_CONSTRUCTION_RECEIPT_STEP:
                receipt = outcome.get("result")
                if (
                    isinstance(receipt, dict)
                    and receipt.get("status") == "restored_before_action"
                    and receipt.get("postcondition_verified") is True
                    and receipt.get("post_snapshot_id") == after_snapshot.get("snapshot_id")
                    and receipt.get("post_public_revision") == after_snapshot.get("revision")
                    and receipt.get("episode_run_id") == after_snapshot.get("episode_run_id")
                ):
                    evidence.append("construction_prior_action_rolled_back_by_cold_restore")
                else:
                    if not (
                        isinstance(receipt, dict)
                        and receipt.get("status") == "applied"
                        and receipt.get("postcondition_verified") is True
                        and receipt.get("post_snapshot_id") == after_snapshot.get("snapshot_id")
                        and receipt.get("post_public_revision") == after_snapshot.get("revision")
                        and receipt.get("episode_run_id") == after_snapshot.get("episode_run_id")
                    ):
                        capture_first_failure(
                            stage="construction_receipt",
                            kind="construction_material_postcondition_failed",
                            message="private construction receipt lost its independent paused frame",
                        )
                        raise AgentError("private construction receipt does not match paused game frame")
                    evidence.append("construction_active_independent_later_frame")
            # A marriage result is a same-frame query. Its status remains in
            # the typed result; it is not evidence of a gameplay mutation.
            if "date_advanced" in evidence:
                date_advanced = True
            if parse_event_option_step(step) is not None:
                result = outcome.get("result")
                selection = (
                    result.get("event_selection")
                    if isinstance(result, dict)
                    else None
                )
                if not (
                    "event_changed" in evidence
                    and isinstance(selection, dict)
                    and selection.get("status")
                    == "event_instance_advanced"
                    and selection.get("postcondition_verified") is True
                    and selection.get("old_event_instance_id")
                    != selection.get("new_event_instance_id")
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind="event_lifecycle_postcondition_failed",
                        message=(
                            "native event selection lacks an old-instance "
                            "lifecycle postcondition"
                        ),
                    )
                    raise AgentError(
                        "native event selection lacks an old-instance lifecycle postcondition"
                    )
                if epidemic_recovery_pre is not None:
                    if step != epidemic_recovery_pre["option_step"]:
                        raise AgentError(
                            "epidemic recovery capture did not match the submitted option"
                        )
                    if selection.get("old_event_instance_id") != (
                        epidemic_recovery_pre["event_instance_id"]
                    ):
                        raise AgentError(
                            "epidemic recovery selection changed the event identity"
                        )
                    near_pair = observe_epidemic_recovery_after_option(
                        service, epidemic_recovery_pre, after_snapshot
                    )
                    result["epidemic_recovery_near_pair"] = near_pair
                    current_attempt["result"] = copy.deepcopy(result)
                    current_attempt["epidemic_recovery_near_pair"] = (
                        copy.deepcopy(near_pair)
                    )
                    if near_pair["status"] == "verified_new_modifier_presence":
                        evidence.append("epidemic_recovery_counties_new_same_day")
                material_issue = _registered_event_material_postcondition_issue(
                    plan, result
                )
                if material_issue is not None:
                    capture_first_failure(
                        stage="postcondition",
                        kind=f"event_material_postcondition_{material_issue}",
                        message=(
                            "registered native event material postcondition "
                            f"is {material_issue}"
                        ),
                    )
                    raise AgentError(
                        "registered native event material postcondition "
                        f"is {material_issue}"
                    )
                material = (
                    result.get("event_material_postcondition")
                    if isinstance(result, dict)
                    else None
                )
                if isinstance(material, dict):
                    if material.get("status") == "verified_change":
                        evidence.append("event_material_change")
                    elif material.get("status") == "verified_no_change":
                        evidence.append("event_material_no_change")
            if step in _PENDING_INTERACTION_REPLY_STATUSES:
                result = outcome.get("result")
                if not _pending_interaction_lifecycle_verified(
                    step,
                    result,
                    before=before,
                    after_snapshot=after_snapshot,
                    evidence=evidence,
                    plan=plan,
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind=(
                            "pending_interaction_lifecycle_postcondition_failed"
                        ),
                        message=(
                            "native pending-interaction reply lacks a typed "
                            "old-instance lifecycle postcondition"
                        ),
                    )
                    raise AgentError(
                        "native pending-interaction reply lacks a typed "
                        "old-instance lifecycle postcondition"
                    )
            council_issue = _council_assignment_postcondition_issue(
                step, outcome.get("result"), after_snapshot
            )
            if council_issue is not None:
                capture_first_failure(
                    stage="postcondition",
                    kind="council_assignment_postcondition_failed",
                    message=(
                        "native council assignment lacks a typed later-frame "
                        f"receipt: {council_issue}"
                    ),
                )
                raise AgentError(
                    "native council assignment lacks a typed later-frame "
                    f"receipt: {council_issue}"
                )
            if step == ASSIGN_COUNCILLOR_V1_STEP:
                evidence.append("council_incumbent_changed")
            war_termination_submission_pending = False
            if parse_offer_white_peace_step(step) is not None:
                result = outcome.get("result")
                if not _white_peace_lifecycle_verified(
                    step,
                    result,
                    before=before,
                    after_snapshot=after_snapshot,
                    evidence=evidence,
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind="white_peace_lifecycle_postcondition_failed",
                        message=(
                            "native white-peace submission lacks a typed "
                            "same-WarID applied-or-pending postcondition"
                        ),
                    )
                    raise AgentError(
                        "native white-peace submission lacks a typed "
                        "same-WarID applied-or-pending postcondition"
                    )
                assert isinstance(result, dict)
                war_termination_result = result.get(
                    "war_termination_result"
                )
                assert isinstance(war_termination_result, dict)
                war_termination_submission_pending = (
                    war_termination_result.get("status")
                    == "submitted_pending"
                )
            if parse_surrender_war_step(step) is not None:
                result = outcome.get("result")
                if not _emergency_surrender_lifecycle_verified(
                    step,
                    result,
                    before=before,
                    after_snapshot=after_snapshot,
                    evidence=evidence,
                ):
                    capture_first_failure(
                        stage="postcondition",
                        kind="surrender_lifecycle_postcondition_failed",
                        message=(
                            "native emergency surrender lacks a typed "
                            "same-WarID applied-or-pending postcondition"
                        ),
                    )
                    raise AgentError(
                        "native emergency surrender lacks a typed same-WarID "
                        "applied-or-pending postcondition"
                    )
                assert isinstance(result, dict)
                war_termination_result = result.get(
                    "war_termination_result"
                )
                assert isinstance(war_termination_result, dict)
                war_termination_submission_pending = (
                    war_termination_result.get("status")
                    == "submitted_pending"
                )
            if war_termination_submission_pending:
                if terminal_pending or modal_decision_pending:
                    capture_first_failure(
                        stage="checkpoint_preflight",
                        kind="war_termination_pending_checkpoint_unsafe",
                        message=(
                            "submitted war termination reached a terminal or "
                            "player-decision frame before its durable checkpoint"
                        ),
                    )
                    raise AgentError(
                        "submitted war termination cannot be checkpointed on a "
                        "terminal or player-decision frame"
                    )
                current_attempt["stage"] = (
                    "war_termination_pending_checkpoint_preflight"
                )
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                pending_fence = _verify_pending_war_termination_checkpoint(
                    checkpoint,
                    snapshot=checkpoint_snapshot,
                    submitted_step=step,
                )
                counts["checkpoint"] += 1
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "war_termination_submitted_pending",
                        "pending_action": pending_fence,
                        **checkpoint,
                    }
                )
                evidence.append("war_termination_pending_checkpoint_saved")
                after_snapshot = checkpoint_snapshot
                after = _compact_binding(
                    driver.capabilities(), checkpoint_snapshot
                )
                current_attempt["after"] = _public_binding(after)
                current_attempt["stage"] = (
                    "war_termination_pending_checkpoint_complete"
                )
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            if step == PRIVATE_CONSTRUCTION_SUBMIT_STEP:
                # An accepted native receiver ACK is still pending material
                # verification.  Save its game state beside the durable
                # request ID before another turn can query or advance it.
                if terminal_pending or modal_decision_pending:
                    capture_first_failure(
                        stage="construction_pending_checkpoint_preflight",
                        kind="construction_pending_checkpoint_unsafe",
                        message="construction ACK reached an unsafe save frame",
                    )
                    raise AgentError(
                        "pending construction cannot be checkpointed on a "
                        "terminal or player-decision frame"
                    )
                current_attempt["stage"] = (
                    "construction_pending_checkpoint_preflight"
                )
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                pending_fence = _verify_pending_construction_checkpoint(
                    checkpoint,
                    snapshot=checkpoint_snapshot,
                    submitted_result=outcome.get("result"),
                    ledger=read_construction_ledger(driver.state_dir),
                )
                counts["checkpoint"] += 1
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "construction_submitted_pending",
                        "pending_action": pending_fence,
                        **checkpoint,
                    }
                )
                evidence.append("construction_pending_checkpoint_saved")
                after_snapshot = checkpoint_snapshot
                after = _compact_binding(
                    driver.capabilities(), checkpoint_snapshot
                )
                current_attempt["after"] = _public_binding(after)
                current_attempt["stage"] = (
                    "construction_pending_checkpoint_complete"
                )
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            if step in {PRIVATE_FAMILY_MARRIAGE_SUBMIT_STEP,
                        PRIVATE_CHILD_MATRILINEAL_SUBMIT_STEP,
                        PRIVATE_CHILD_DEFAULT_SUBMIT_STEP}:
                if terminal_pending or modal_decision_pending:
                    raise AgentError("pending first-heir marriage cannot be checkpointed on a decision frame")
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service, driver, spec.profile_dir / "save games",
                    session_done=session_done, session_state=session_state,
                    timeout_seconds=min(readiness_timeout,
                                        max(0.001, run_deadline - time.monotonic())),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                child_proposal = step in {
                    PRIVATE_CHILD_MATRILINEAL_SUBMIT_STEP,
                    PRIVATE_CHILD_DEFAULT_SUBMIT_STEP}
                pending_fence = _verify_pending_family_marriage_checkpoint(
                    checkpoint, snapshot=checkpoint_snapshot,
                    submitted_result=outcome.get("result"),
                    ledger=(read_child_default_ledger(driver.state_dir)
                            if step == PRIVATE_CHILD_DEFAULT_SUBMIT_STEP else
                            read_child_matrilineal_ledger(driver.state_dir)
                            if child_proposal else
                            read_family_marriage_ledger(driver.state_dir)),
                    expected_step=step,
                )
                counts["checkpoint"] += 1
                checkpoints.append({"turn_index": turn_index,
                                    "phase": ("player_child_default_submitted_pending"
                                              if step == PRIVATE_CHILD_DEFAULT_SUBMIT_STEP else
                                              "player_child_matrilineal_submitted_pending"
                                              if child_proposal else
                                              "first_heir_marriage_submitted_pending"),
                                    "pending_action": pending_fence, **checkpoint})
                evidence.append("child_default_pending_checkpoint_saved"
                                if step == PRIVATE_CHILD_DEFAULT_SUBMIT_STEP else
                                "child_matrilineal_pending_checkpoint_saved"
                                if child_proposal else
                                "first_heir_marriage_pending_checkpoint_saved")
                after_snapshot = checkpoint_snapshot
                after = _compact_binding(driver.capabilities(), checkpoint_snapshot)
                current_attempt["after"] = _public_binding(after)
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            if step == PRIVATE_PRISONER_RANSOM_SUBMIT_STEP:
                if terminal_pending or modal_decision_pending:
                    raise AgentError("pending prisoner ransom cannot be checkpointed on a decision frame")
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service, driver, spec.profile_dir / "save games",
                    session_done=session_done, session_state=session_state,
                    timeout_seconds=min(readiness_timeout,
                                        max(0.001, run_deadline - time.monotonic())),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                pending = read_ransom_ledger(driver.state_dir)["pending"]
                played = checkpoint_snapshot.get("played_character")
                if (not isinstance(pending, dict)
                        or pending != outcome.get("result")
                        or pending.get("stage") != "receipt_pending"
                        or pending.get("pre_date_raw") != checkpoint.get("date_raw")
                        or pending.get("pre_date_raw") != checkpoint_snapshot.get("date_raw")
                        or not isinstance(played, dict)
                        or pending.get("player_character_id") != played.get("character_id")):
                    raise AgentError("ransom ACK lacks a paired pending checkpoint")
                counts["checkpoint"] += 1
                checkpoints.append({"turn_index": turn_index,
                                    "phase": "prisoner_ransom_submitted_pending",
                                    "pending_action": copy.deepcopy(pending), **checkpoint})
                evidence.append("prisoner_ransom_pending_checkpoint_saved")
                after_snapshot = checkpoint_snapshot
                after = _compact_binding(driver.capabilities(), checkpoint_snapshot)
                current_attempt["after"] = _public_binding(after)
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            if completion_contract in strict_completion_contracts:
                try:
                    if (
                        completion_contract == "next_episode"
                        and step == "start-next-episode"
                    ):
                        next_episode_transition = (
                            _verify_next_episode_transition(
                                outcome.get("result"),
                                snapshot=after_snapshot,
                                binding=after,
                                initial_episode=initial_episode,
                            )
                        )
                    elif next_episode_transition is None:
                        _verify_one_generation_binding(
                            after, initial_episode
                        )
                    else:
                        _verify_next_episode_binding(
                            after, next_episode_transition
                        )
                except AgentError as error:
                    same_episode_binding = False
                    capture_first_failure(
                        stage="postcondition",
                        kind="identity_violation",
                        message=str(error),
                        error=error,
                    )
                    raise
            if step == CONTINUE_AS_RECONCILED_SUCCESSOR_STEP:
                try:
                    natural_transition = (
                        _verify_natural_succession_transition(
                            outcome.get("result"),
                            snapshot=after_snapshot,
                            binding=after,
                            before=before,
                            succession_lifecycle=(
                                succession_lifecycle_binding
                            ),
                        )
                    )
                except AgentError as error:
                    capture_first_failure(
                        stage="postcondition",
                        kind="natural_succession_transition_invalid",
                        message=str(error),
                        error=error,
                    )
                    raise
                natural_succession_transitions.append(natural_transition)
                current_episode = {
                    "episode_character_id": natural_transition[
                        "successor_character_id"
                    ],
                    "episode_run_id": natural_transition[
                        "episode_run_id"
                    ],
                    "date_raw": natural_transition["date_raw"],
                }
                evidence.append("natural_successor_continued")
                if (
                    succession_lifecycle_binding["lifecycle"]
                    == ORDINARY_CAMPAIGN_SUCCESSION
                ):
                    current_attempt["stage"] = (
                        "ordinary_successor_timeline_query"
                    )
                    successor_revision = after_snapshot.get("revision")
                    successor_character_id = natural_transition[
                        "successor_character_id"
                    ]
                    successor_episode_run_id = natural_transition[
                        "episode_run_id"
                    ]
                    successor_date_raw = after_snapshot.get("date_raw")
                    if (
                        isinstance(successor_revision, bool)
                        or not isinstance(successor_revision, int)
                        or successor_revision < 0
                        or isinstance(successor_date_raw, bool)
                        or not isinstance(successor_date_raw, int)
                    ):
                        raise AgentError(
                            "ordinary successor lacks a stable paused timeline binding"
                        )
                    try:
                        timeline_query = (
                            service.query_current_timeline_blocker_context_v1(
                                expected_revision=successor_revision
                            )
                        )
                    except (
                        BridgeUnavailableError,
                        UnsupportedStepError,
                        ValueError,
                    ) as error:
                        capture_first_failure(
                            stage="ordinary_successor_timeline_query",
                            kind="natural_succession_timeline_query_failed",
                            message=str(error),
                            error=error,
                        )
                        raise AgentError(
                            "ordinary natural successor timeline query failed: "
                            + str(error)
                        ) from error
                    timeline_state = _ordinary_succession_timeline_state(
                        timeline_query
                    )
                    if timeline_state is None:
                        capture_first_failure(
                            stage="ordinary_successor_timeline_query",
                            kind="natural_succession_timeline_state_ambiguous",
                            message=(
                                "ordinary successor timeline state is neither "
                                "a bound death modal nor independently clear"
                            ),
                        )
                        raise AgentError(
                            "ordinary successor timeline state is ambiguous"
                        )
                    timeline_continuation: dict[str, object] = {
                        "status": timeline_state,
                        "initial_query": copy.deepcopy(timeline_query),
                        "close_result": None,
                    }
                    natural_transition["timeline_blocker_continuation"] = (
                        timeline_continuation
                    )
                    if timeline_state == "close_required":
                        current_attempt["stage"] = (
                            "ordinary_successor_timeline_close"
                        )
                        try:
                            close_result = (
                                service.continue_death_succession_modal_private_v1(
                                    expected_revision=successor_revision,
                                    expected_played_character_id=(
                                        successor_character_id
                                    ),
                                    expected_episode_run_id=(
                                        successor_episode_run_id
                                    ),
                                )
                            )
                        except (
                            BridgeUnavailableError,
                            UnsupportedStepError,
                            ValueError,
                        ) as error:
                            capture_first_failure(
                                stage="ordinary_successor_timeline_close",
                                kind="natural_succession_timeline_close_failed",
                                message=str(error),
                                error=error,
                            )
                            raise AgentError(
                                "ordinary natural successor typed Close failed: "
                                + str(error)
                            ) from error
                        timeline_continuation["close_result"] = copy.deepcopy(
                            close_result
                        )
                        close_issue = _ordinary_succession_close_issue(
                            close_result,
                            starting_date_raw=successor_date_raw,
                            successor_character_id=successor_character_id,
                        )
                        if close_issue is not None:
                            capture_first_failure(
                                stage="ordinary_successor_timeline_close",
                                kind=(
                                    "natural_succession_timeline_close_"
                                    + close_issue
                                ),
                                message=(
                                    "ordinary successor typed Close lacks its "
                                    "material postcondition: " + close_issue
                                ),
                            )
                            raise AgentError(
                                "ordinary successor typed Close lacks its material "
                                "postcondition: " + close_issue
                            )
                        timeline_continuation["status"] = "materially_cleared"
                        refreshed_snapshot = service.snapshot()
                        refreshed_played = refreshed_snapshot.get(
                            "played_character"
                        )
                        if not (
                            isinstance(refreshed_played, dict)
                            and refreshed_played.get("alive") is True
                            and refreshed_played.get("character_id")
                            == successor_character_id
                            and refreshed_snapshot.get("episode_character_id")
                            == successor_character_id
                            and refreshed_snapshot.get("episode_run_id")
                            == successor_episode_run_id
                            and refreshed_snapshot.get("date_raw")
                            == close_result.get("ending_date_raw")
                            and refreshed_snapshot.get("revision")
                            == close_result.get("ending_revision")
                            and refreshed_snapshot.get("native_revision")
                            == close_result.get("ending_native_revision")
                        ):
                            raise AgentError(
                                "ordinary successor changed identity after typed Close"
                            )
                        after_snapshot = refreshed_snapshot
                        after = _compact_binding(
                            driver.capabilities(), after_snapshot
                        )
                        current_attempt["after"] = _public_binding(after)
                        current_episode["date_raw"] = after_snapshot[
                            "date_raw"
                        ]
                        modal_decision_pending = _player_decision_pending(
                            after_snapshot
                        )
                        date_advanced = True
                        evidence.extend(
                            [
                                "natural_successor_timeline_blocker_cleared",
                                "date_advanced",
                            ]
                        )
                    else:
                        evidence.append(
                            "natural_successor_timeline_already_clear"
                        )
                if modal_decision_pending:
                    natural_transition["successor_checkpoint"] = {
                        "status": "deferred_player_decision",
                        "episode_character_id": current_episode[
                            "episode_character_id"
                        ],
                        "episode_run_id": current_episode["episode_run_id"],
                        "date_raw": current_episode["date_raw"],
                    }
                    current_attempt["stage"] = (
                        "successor_checkpoint_deferred_player_decision"
                    )
                    evidence.append(
                        "natural_successor_checkpoint_deferred_player_decision"
                    )
                else:
                    current_attempt["stage"] = "successor_checkpoint_preflight"
                    successor_checkpoint, _ = _materialize_checkpoint(
                        service,
                        driver,
                        spec.profile_dir / "save games",
                        session_done=session_done,
                        session_state=session_state,
                        timeout_seconds=min(
                            readiness_timeout,
                            max(0.001, run_deadline - time.monotonic()),
                        ),
                        poll_interval_seconds=poll_seconds,
                        on_checkpoint_submit=mark_checkpoint_submit_started,
                    )
                    if (
                        successor_checkpoint.get("episode_character_id")
                        != current_episode["episode_character_id"]
                        or successor_checkpoint.get("episode_run_id")
                        != current_episode["episode_run_id"]
                        or successor_checkpoint.get("succession_lifecycle")
                        != succession_lifecycle_binding
                    ):
                        raise AgentError(
                            "natural successor checkpoint differs from the new "
                            "episode lifecycle"
                        )
                    counts["checkpoint"] += 1
                    checkpoints.append(
                        {
                            "turn_index": turn_index,
                            "phase": "natural_successor_checkpoint",
                            **successor_checkpoint,
                        }
                    )
                    natural_transition["successor_checkpoint"] = copy.deepcopy(
                        successor_checkpoint
                    )
                    current_attempt["stage"] = "successor_checkpoint_complete"
                    evidence.append("natural_successor_checkpoint_saved")
            counts[turn_class] += 1
            if (
                turn_class == "gameplay"
                and evidence
                and not war_termination_submission_pending
                and step != PRIVATE_CONSTRUCTION_SUBMIT_STEP
                and step != PRIVATE_FAMILY_MARRIAGE_SUBMIT_STEP
                and step != PRIVATE_CHILD_MATRILINEAL_SUBMIT_STEP
                and step != PRIVATE_CHILD_DEFAULT_SUBMIT_STEP
                and step != PRIVATE_PRISONER_RANSOM_SUBMIT_STEP
                and step != PRIVATE_LIFESTYLE_FOCUS_SUBMIT_STEP
            ):
                visible_gameplay_turns += 1
                if next_episode_transition is not None:
                    post_transition_visible_gameplay_turns += 1
                    post_transition_last_gameplay_turn_index = turn_index
                dirty_gameplay_since_checkpoint = True
            turns.append(
                _turn_record(
                    turn_index,
                    turn_started,
                    turn_class=turn_class,
                    outcome=outcome,
                    before=before,
                    after=after,
                    evidence=evidence,
                    camera_follow=current_attempt["camera_follow"],
                )
            )
            if (turn_class == "gameplay" and evidence
                    and (spec.state_dir / PRIVATE_SWAY_LEDGER_FILE).exists()):
                private_active_scheme_sway_following_turn = (
                    consume_sway_following_turn(spec.state_dir, after)
                )
            if (turn_class == "gameplay" and evidence
                    and (spec.state_dir / PRIVATE_FEAST_START_LEDGER_FILE).exists()):
                private_activity_feast_stage5_start_following_turn = (
                    consume_feast_start_following_turn(spec.state_dir, after)
                )
            if exact_move_poststate is not None:
                status = "exact_war_move_poststate_verified"
                break
            if (
                opening_focus_gate is not None
                and step in {
                    PRIVATE_LIFESTYLE_FOCUS_SUBMIT_STEP,
                    PRIVATE_LIFESTYLE_RECEIPT_STEP,
                }
            ):
                if terminal_pending or modal_decision_pending:
                    raise AgentError(
                        "initial LIFE focus cannot checkpoint on a terminal "
                        "or player-decision frame"
                    )
                current_attempt["stage"] = "initial_lifestyle_focus_checkpoint"
                focus_checkpoint, focus_checkpoint_snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                if focus_checkpoint.get("date_raw") != opening_date_raw:
                    raise AgentError(
                        "initial LIFE focus checkpoint changed the opening date"
                    )
                counts["checkpoint"] += 1
                checkpoints.append({
                    "turn_index": turn_index,
                    "phase": (
                        "initial_lifestyle_focus_submitted_pending"
                        if step == PRIVATE_LIFESTYLE_FOCUS_SUBMIT_STEP
                        else "initial_lifestyle_focus_applied"
                    ),
                    **focus_checkpoint,
                })
                opening_focus_gate["checkpoint_saved"] = True
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
                after_snapshot = focus_checkpoint_snapshot
                after = _compact_binding(driver.capabilities(), after_snapshot)
                current_attempt["after"] = _public_binding(after)
                current_attempt["stage"] = "initial_lifestyle_focus_checkpoint_complete"
            if step == "death-terminal":
                if (
                    succession_lifecycle_binding["lifecycle"]
                    != ROGUE_ONE_LIFE
                ):
                    raise AgentError(
                        "ordinary campaign succession cannot execute the "
                        "rogue death-terminal contract"
                    )
                try:
                    terminal_proof = _verify_one_generation_terminal(
                        outcome.get("result"),
                        snapshot=after_snapshot,
                        binding=after,
                        initial_episode=current_episode,
                        succession_lifecycle=(
                            succession_lifecycle_binding
                        ),
                    )
                except AgentError as error:
                    capture_first_failure(
                        stage="postcondition",
                        kind="settlement_invalid",
                        message=str(error),
                        error=error,
                    )
                    raise
            if turn_class == "query" and (
                semantic_evidence or not _same_native_frame(before, after)
            ):
                capture_first_failure(
                    stage="postcondition",
                    kind="read_only_query_changed_frame",
                    message="read-only native query changed its paused semantic frame",
                )
                raise AgentError(
                    "read-only native query changed its paused semantic frame"
                )
            if step in {
                PRIVATE_CHILD_DEFAULT_RESULT_STEP,
                PRIVATE_CHILD_DEFAULT_ALLIANCE_STEP,
            }:
                # These readbacks update the durable child ledger. Pair each
                # ledger state with the unchanged game save before a cold PID.
                child_ledger = read_child_default_ledger(driver.state_dir)
                result = outcome.get("result")
                source = (
                    plan.get("child_default_pending")
                    if step == PRIVATE_CHILD_DEFAULT_RESULT_STEP else
                    plan.get("child_default_resolved")
                ) if isinstance(plan, dict) else None
                if (not isinstance(result, dict)
                        or not isinstance(source, dict)
                        or (step == PRIVATE_CHILD_DEFAULT_RESULT_STEP
                            and not (
                                isinstance(child_ledger.get("pending"), dict)
                                and child_ledger["pending"].get("heir_character_id")
                                    == source.get("heir_character_id")
                                and child_ledger["pending"].get("candidate_character_id")
                                    == source.get("candidate_character_id")
                                or isinstance(child_ledger.get("resolved"), dict)
                                and child_ledger["resolved"].get("source_pending")
                                    == source))
                        or (step == PRIVATE_CHILD_DEFAULT_ALLIANCE_STEP
                            and (not isinstance(child_ledger.get("resolved"), dict)
                                 or child_ledger["resolved"].get(
                                     "actual_alliance_result") != result))):
                    raise AgentError("child default readback lacks paired durable identity")
                if terminal_pending or modal_decision_pending:
                    raise AgentError("child default readback cannot checkpoint on a decision frame")
                if (step == PRIVATE_CHILD_DEFAULT_RESULT_STEP
                        and private_guy_default_first_heir_companion is True):
                    current_attempt["stage"] = "private_guy_default_first_heir_companion_read"
                    private_first_heir_companion_observation = (
                        observe_first_heir_companion_after_child(
                            driver, service, before=before,
                            child_observation={"same_frame": True},
                            first_heir_resolved=read_family_marriage_ledger(
                                driver.state_dir)["resolved"],
                            turn_index=turn_index,
                        )
                    )
                    turns[-1]["evidence"].append(
                        "guy_default_first_heir_companion_observed")
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service, driver, spec.profile_dir / "save games",
                    session_done=session_done, session_state=session_state,
                    timeout_seconds=min(readiness_timeout,
                                        max(0.001, run_deadline - time.monotonic())),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                if (checkpoint.get("date_raw") != before.get("date_raw")
                        or checkpoint.get("episode_run_id") != before.get("episode_run_id")
                        or read_child_default_ledger(driver.state_dir) != child_ledger):
                    raise AgentError("child default readback checkpoint changed pair or date")
                if step == PRIVATE_CHILD_DEFAULT_RESULT_STEP:
                    consume_child_default_result_checkpoint(
                        driver, ledger=child_ledger, before=before,
                        snapshot=checkpoint_snapshot,
                    )
                counts["checkpoint"] += 1
                checkpoints.append({
                    "turn_index": turn_index,
                    "phase": ("player_child_default_result_" +
                              str(result.get("status"))
                              if step == PRIVATE_CHILD_DEFAULT_RESULT_STEP else
                              "player_child_default_actual_alliance"),
                    **checkpoint,
                })
                after_snapshot = checkpoint_snapshot
                after = _compact_binding(driver.capabilities(), checkpoint_snapshot)
                current_attempt["after"] = _public_binding(after)
                turns[-1]["after"] = _public_binding(after)
                turns[-1]["evidence"].append(
                    "child_default_readback_checkpoint_saved")
            if (private_child_matrilineal_pending_recovery_only is True
                    and step == PRIVATE_CHILD_MATRILINEAL_RESULT_STEP):
                # The result reader changes the durable sidecar even when the
                # proposal remains pending. Save the same game frame beside
                # that ledger before this one-turn recovery can finish.
                result = outcome.get("result")
                child_ledger = read_child_matrilineal_ledger(driver.state_dir)
                pending_now = child_ledger.get("pending")
                resolved_now = child_ledger.get("resolved")
                result_status = result.get("status") if isinstance(result, dict) else None
                if not (
                    (result_status == "pending" and isinstance(pending_now, dict)
                     and child_ledger.get("resolved") is None
                     and all(pending_now.get(key) == child_recovery_pending.get(key)
                             for key in ("played_character_id", "episode_run_id",
                                         "heir_character_id", "candidate_character_id",
                                         "recipient_character_id", "source_bridge_pid")))
                    or (result_status in {"marriage", "betrothal", "refused", "invalidated"}
                        and pending_now is None and isinstance(resolved_now, dict)
                        and resolved_now.get("status") == result_status
                        and resolved_now.get("source_pending") == child_recovery_pending)
                ):
                    raise AgentError("child result did not update its paired pending ledger")
                if terminal_pending or modal_decision_pending:
                    raise AgentError("child result cannot checkpoint on a decision frame")
                current_attempt["stage"] = "child_matrilineal_result_checkpoint"
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service, driver, spec.profile_dir / "save games",
                    session_done=session_done, session_state=session_state,
                    timeout_seconds=min(readiness_timeout,
                                        max(0.001, run_deadline - time.monotonic())),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                if (checkpoint.get("date_raw") != before.get("date_raw")
                        or checkpoint.get("episode_character_id")
                        != before.get("episode_character_id")
                        or checkpoint.get("episode_run_id")
                        != before.get("episode_run_id")
                        or read_child_matrilineal_ledger(driver.state_dir)
                        != child_ledger):
                    raise AgentError("child result checkpoint changed its pair or date")
                counts["checkpoint"] += 1
                checkpoints.append({
                    "turn_index": turn_index,
                    "phase": "player_child_matrilineal_result_" + str(result_status),
                    "ledger_status": result_status,
                    **checkpoint,
                })
                after_snapshot = checkpoint_snapshot
                after = _compact_binding(driver.capabilities(), checkpoint_snapshot)
                current_attempt["after"] = _public_binding(after)
                turns[-1]["after"] = _public_binding(after)
                turns[-1]["evidence"].append("child_matrilineal_result_checkpoint_saved")
                current_attempt["stage"] = "child_matrilineal_result_checkpoint_complete"
            if time.monotonic() >= run_deadline:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message="native-auto-run gameplay timeout expired during auto-turn",
                )
                raise AgentError(
                    "native-auto-run gameplay timeout expired during auto-turn"
                )

            if turn_class == "checkpoint":
                current_attempt["stage"] = "checkpoint"
                checkpoint = _verify_checkpoint_result(
                    outcome.get("result"),
                    snapshot=after_snapshot,
                    expected_save_dir=spec.profile_dir / "save games",
                )
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "planner_checkpoint",
                        **checkpoint,
                    }
                )
                current_attempt["stage"] = "checkpoint_complete"
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            elif turn_class == "recovery":
                # A restore discards the factual tail and a new episode owns
                # a different cadence.  Neither may inherit advance debt.
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
            elif _eligible_advance(step, outcome, evidence):
                eligible_since_checkpoint += 1

            if (
                eligible_since_checkpoint
                >= checkpoint_cadence
                and not terminal_pending
                and not modal_decision_pending
            ):
                checkpoint_binding = _public_binding(after)
                current_attempt = {
                    "turn_index": turn_index,
                    "stage": "checkpoint_preflight",
                    "before": copy.deepcopy(checkpoint_binding),
                    "plan": {"phase": "periodic_checkpoint"},
                    "selected_step": "save-checkpoint",
                    "result": None,
                    "after": copy.deepcopy(checkpoint_binding),
                }
                checkpoint, checkpoint_snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
                counts["checkpoint"] += 1
                checkpoints.append(
                    {
                        "turn_index": turn_index,
                        "phase": "periodic_checkpoint",
                        "eligible_advance_ordinal": checkpoint_cadence,
                        **checkpoint,
                    }
                )
                current_attempt["stage"] = "checkpoint_complete"
                eligible_since_checkpoint = 0
                dirty_gameplay_since_checkpoint = False
                after = _compact_binding(
                    driver.capabilities(), checkpoint_snapshot
                )
                current_attempt["after"] = _public_binding(after)
                if time.monotonic() >= run_deadline:
                    status = "timeout"
                    capture_first_failure(
                        stage="bound",
                        kind="wall_clock_bound_exhausted",
                        message=(
                            "native-auto-run gameplay timeout expired during "
                            "periodic checkpoint"
                        ),
                    )
                    raise AgentError(
                        "native-auto-run gameplay timeout expired during "
                        "periodic checkpoint"
                    )

            if (
                completion_contract == "next_episode"
                and next_episode_transition is not None
                and post_transition_visible_gameplay_turns > 0
                and post_transition_last_gameplay_turn_index is not None
                and checkpoints
                and _checkpoint_proves_next_episode_ooda(
                    checkpoints[-1],
                    transition=next_episode_transition,
                    last_gameplay_turn_index=(
                        post_transition_last_gameplay_turn_index
                    ),
                )
            ):
                post_transition_checkpoint = copy.deepcopy(checkpoints[-1])
                status = "next_episode_checkpointed"
                break
            if step == "death-terminal":
                if completion_contract == "next_episode":
                    status = "next_episode_pending"
                elif (
                    completion_contract == "bounded"
                    and isinstance(outcome.get("result"), dict)
                    and outcome["result"].get("terminal_reason")
                    == "played_character_changed"
                ):
                    status = "natural_successor_continuation_pending"
                    continue
                else:
                    status = "episode_complete"
                    break
            if step in _TERMINAL_STEPS:
                if (
                    completion_contract == "next_episode"
                    and step == "death-terminal"
                ):
                    continue
                status = "terminal_non_death_step"
                break
        else:
            status = (
                "operator_stop_requested"
                if operator_stop_event is not None
                and operator_stop_event.is_set()
                else "turn_limit_terminal_pending"
                if terminal_pending
                else "turn_limit_player_decision_pending"
                if modal_decision_pending
                else "turn_limit"
            )
        if exact_move_contract is not None and status == "turn_limit":
            status = "exact_war_move_not_reached"
            capture_first_failure(
                stage="bound", kind="exact_war_move_not_reached",
                message="bounded run ended before the exact typed move and independent poststate",
            )
        if (
            status == "turn_limit"
            and opening_focus_gate is not None
            and opening_focus_gate["stage"] != "complete"
        ):
            status = "initial_lifestyle_focus_incomplete"
            capture_first_failure(
                stage="initial_lifestyle_focus_gate",
                kind="initial_lifestyle_focus_incomplete",
                message=(
                    "bounded run ended before one typed focus, independent "
                    "paused receipt, checkpoint and following-turn consumption"
                ),
            )

        # A bounded production run must not knowingly discard a visible tail.
        # Queries never dirty this tail, and terminal/unknown frames are never
        # forced through a save operation.
        if status == "operator_stop_requested" and (
            terminal_pending or modal_decision_pending
        ):
            status = "operator_stop_checkpoint_deferred"
        final_checkpoint_needed = (
            status in {"operator_stop_requested", "exact_war_move_poststate_verified"}
            or (status == "turn_limit" and dirty_gameplay_since_checkpoint)
        )
        if final_checkpoint_needed:
            last_after = turns[-1].get("after") if turns else readiness
            final_phase = (
                "exact_war_move_checkpoint"
                if status == "exact_war_move_poststate_verified"
                else "operator_stop_checkpoint"
                if status == "operator_stop_requested"
                else "final_checkpoint"
            )
            current_attempt = {
                "turn_index": len(turns),
                "stage": "checkpoint_preflight",
                "before": copy.deepcopy(last_after),
                "plan": {"phase": final_phase},
                "selected_step": "save-checkpoint",
                "result": None,
                "after": copy.deepcopy(last_after),
            }
            if time.monotonic() >= run_deadline:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message=(
                        "native-auto-run gameplay timeout expired before "
                        "final checkpoint"
                    ),
                )
                raise AgentError(
                    "native-auto-run gameplay timeout expired before final "
                    "checkpoint"
                )
            try:
                checkpoint, _snapshot = _materialize_checkpoint(
                    service,
                    driver,
                    spec.profile_dir / "save games",
                    session_done=session_done,
                    session_state=session_state,
                    timeout_seconds=min(
                        readiness_timeout,
                        max(0.001, run_deadline - time.monotonic()),
                    ),
                    poll_interval_seconds=poll_seconds,
                    on_checkpoint_submit=mark_checkpoint_submit_started,
                )
            except BaseException as error:
                status = "stopped_on_error"
                checkpoint_failure_stage = str(
                    current_attempt.get("stage", "checkpoint_preflight")
                )
                capture_first_failure(
                    stage=checkpoint_failure_stage,
                    kind=_generic_failure_kind(checkpoint_failure_stage),
                    message=str(error),
                    error=error,
                )
                raise
            if status == "exact_war_move_poststate_verified":
                current_attempt["stage"] = "checkpoint"
                exact_move_checkpoint = check_exact_war_move_checkpoint(
                    checkpoint, _snapshot, exact_move_contract
                )
                if (_snapshot.get("episode_run_id") != readiness.get("episode_run_id")
                        or _snapshot.get("episode_character_id") != readiness.get("episode_character_id")):
                    raise AgentError("exact war move checkpoint changed campaign identity")
                status = "exact_war_move_checkpointed"
            counts["checkpoint"] += 1
            checkpoints.append(
                {
                    "turn_index": len(turns),
                    "phase": final_phase,
                    **checkpoint,
                }
            )
            current_attempt["stage"] = "checkpoint_complete"
            eligible_since_checkpoint = 0
            dirty_gameplay_since_checkpoint = False
            if status == "operator_stop_requested":
                status = "operator_stop_checkpointed"
            if (
                completion_contract == "next_episode"
                and next_episode_transition is not None
                and post_transition_visible_gameplay_turns > 0
                and post_transition_last_gameplay_turn_index is not None
                and _checkpoint_proves_next_episode_ooda(
                    checkpoints[-1],
                    transition=next_episode_transition,
                    last_gameplay_turn_index=(
                        post_transition_last_gameplay_turn_index
                    ),
                )
            ):
                post_transition_checkpoint = copy.deepcopy(checkpoints[-1])
                status = "next_episode_checkpointed"
            if time.monotonic() >= run_deadline:
                status = "timeout"
                capture_first_failure(
                    stage="bound",
                    kind="wall_clock_bound_exhausted",
                    message=(
                        "native-auto-run gameplay timeout expired during "
                        "final checkpoint"
                    ),
                )
                raise AgentError(
                    "native-auto-run gameplay timeout expired during final "
                    "checkpoint"
                )
    except KeyboardInterrupt as error:
        status = "operator_stop"
        capture_first_failure(
            stage=(
                str(current_attempt.get("stage"))
                if isinstance(current_attempt, dict)
                else "session"
            ),
            kind="operator_stop",
            message="operator requested stop",
            error=error,
        )
        primary_error = "KeyboardInterrupt: operator requested stop"
    except BaseException as error:
        if isinstance(error, NativeReadinessTimeoutError):
            readiness_timeout_diagnostics = copy.deepcopy(
                error.readiness_diagnostics
            )
        if isinstance(current_attempt, dict):
            if isinstance(
                error, (BridgeUnavailableError, UnsupportedStepError)
            ):
                error_plan = getattr(error, "plan", None)
                error_selected_step = getattr(error, "selected_step", None)
                if isinstance(error_plan, dict):
                    current_attempt["plan"] = copy.deepcopy(error_plan)
                if (
                    isinstance(error_selected_step, str)
                    and error_selected_step
                ):
                    current_attempt["selected_step"] = error_selected_step
            if isinstance(error, StepPostconditionError) and isinstance(
                error.step_result, dict
            ):
                current_attempt["result"] = copy.deepcopy(error.step_result)
        session_exited = session_done.is_set()
        failure_stage = (
            "session"
            if session_exited
            else (
                str(current_attempt.get("stage"))
                if isinstance(current_attempt, dict)
                else "startup"
            )
        )
        if status in {"starting", "running"}:
            status = (
                "session_exit" if session_done.is_set() else "stopped_on_error"
            )
        capture_first_failure(
            stage=failure_stage,
            kind=(
                "session_exit"
                if session_exited
                else _generic_failure_kind(failure_stage)
            ),
            message=str(error),
            error=error,
        )
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
            # stop_tracked has its own finite process/Job/watchdog bounds.  Do
            # not close the named pipe until that cleanup report is complete.
            session_thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                capture_first_failure(
                    stage="cleanup",
                    kind="driver_close_failed",
                    message=str(error),
                    error=error,
                )
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )

    session_report = session_state.get("report")
    session_error = session_state.get("error")
    cleanup = _cleanup_report(
        session_report,
        session_error=session_error,
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True:
        cleanup_error = str(
            session_error
            or cleanup.get("reason")
            or "managed native-session cleanup was not proven"
        )
        if first_failure is None:
            capture_first_failure(
                stage="cleanup",
                kind="cleanup_failed",
                message=cleanup_error,
            )
        primary_error = (
            cleanup_error
            if primary_error is None
            else f"{primary_error}; cleanup: {cleanup_error}"
        )

    qualification_gates = {
        "start_alive": bool(
            isinstance(readiness, dict)
            and readiness.get("played_character_alive") is True
        ),
        "fixed_seed_verified": fixed_seed is not None,
        "started_at_seed_date": bool(
            isinstance(fixed_seed, dict)
            and isinstance(readiness, dict)
            and fixed_seed.get("saved_date_raw") == readiness.get("date_raw")
        ),
        "same_episode_binding": same_episode_binding,
        "visible_gameplay": visible_gameplay_turns > 0,
        "date_advanced": date_advanced,
        "death_terminal_executed": bool(
            isinstance(terminal_proof, dict)
            and terminal_proof.get("executed_by_this_run") is True
        ),
        "settlement_matches_episode": bool(
            isinstance(terminal_proof, dict)
            and terminal_proof.get("settlement_matches_episode") is True
        ),
        "no_heir_gameplay": bool(
            isinstance(terminal_proof, dict)
            and terminal_proof.get("no_heir_gameplay") is True
        ),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    if completion_contract == "next_episode":
        qualification_gates.update(
            {
                "next_episode_started": bool(
                    isinstance(next_episode_transition, dict)
                    and next_episode_transition.get("status") == "verified"
                ),
                "new_episode_run_id": bool(
                    isinstance(next_episode_transition, dict)
                    and next_episode_transition.get("new_run_identity") is True
                ),
                "episode_seed_reloaded": bool(
                    isinstance(next_episode_transition, dict)
                    and next_episode_transition.get("seed_reloaded") is True
                ),
                "post_transition_visible_gameplay": (
                    post_transition_visible_gameplay_turns > 0
                ),
                "post_transition_checkpoint": (
                    post_transition_checkpoint is not None
                ),
            }
        )
    if completion_contract == "one_generation":
        qualified = bool(
            primary_error is None
            and status == "episode_complete"
            and all(qualification_gates.values())
        )
    elif completion_contract == "next_episode":
        qualified = bool(
            primary_error is None
            and status == "next_episode_checkpointed"
            and all(qualification_gates.values())
        )
    else:
        existing_opening_focus_readback = bool(
            opening_focus_gate is not None
            and opening_focus_gate.get("stage") == "complete"
            and isinstance(opening_focus_gate.get("existing_focus"), str)
            and opening_focus_gate.get("existing_focus")
            and status == "turn_limit"
            and len(turns) == 1
            and turns[0].get("ok") is True
            and turns[0].get("class") == "query"
            and turns[0].get("selected_step")
            == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
            and isinstance(turns[0].get("before"), dict)
            and turns[0]["before"].get("paused") is True
            and turns[0]["before"].get("date_raw") == opening_date_raw
            and isinstance(turns[0].get("after"), dict)
            and turns[0]["after"].get("paused") is True
            and turns[0]["after"].get("date_raw") == opening_date_raw
            and visible_gameplay_turns == 0
        )
        qualified = bool(
            primary_error is None
            and status in {"turn_limit", "episode_complete", "exact_war_move_checkpointed"}
            and (exact_move_contract is None or (
                status == "exact_war_move_checkpointed"
                and exact_move_poststate is not None
                and exact_move_checkpoint is not None
            ))
            and (
                visible_gameplay_turns > 0
                or existing_opening_focus_readback
            )
            and (
                opening_focus_gate is None
                or opening_focus_gate["stage"] == "complete"
            )
            and (
                status != "episode_complete" or terminal_proof is not None
            )
            and cleanup.get("ok") is True
        )
        if private_active_scheme_sway_target is not None:
            common_sway_proof = bool(
                primary_error is None
                and isinstance(private_active_scheme_sway_observation, dict)
                and private_active_scheme_sway_observation.get("same_frame") is True
                and cleanup.get("ok") is True
                and not turns
                and not date_advanced
            )
            if allow_private_active_scheme_sway_formal_trial is True:
                qualified = bool(
                    common_sway_proof
                    and status == "private_active_scheme_sway_applied"
                    and isinstance(private_active_scheme_sway_formal, dict)
                    and private_active_scheme_sway_formal.get(
                        "postcondition_verified") is True
                    and private_active_scheme_sway_formal.get(
                        "checkpoint_saved") is True
                )
            else:
                qualified = bool(common_sway_proof
                                 and status == "private_active_scheme_sway_observed")
        if private_child_matrilineal_pending_read_target is not None:
            qualified = bool(
                primary_error is None
                and status == "private_child_matrilineal_pending_observed"
                and isinstance(private_child_matrilineal_pending_observation, dict)
                and private_child_matrilineal_pending_observation.get("same_frame") is True
                and (private_child_matrilineal_first_heir_companion is not True
                     or (isinstance(private_first_heir_companion_observation, dict)
                         and private_first_heir_companion_observation.get("same_frame") is True))
                and cleanup.get("ok") is True and not turns and not date_advanced
            )
        if private_child_matrilineal_pending_recovery_only is True:
            # This opt-in is one typed result read, not a bounded campaign turn.
            # A still-pending proposal is a valid read only when its updated
            # ledger has already been paired with a same-date checkpoint.
            turn = turns[0] if len(turns) == 1 else None
            result = turn.get("result") if isinstance(turn, dict) else None
            before = turn.get("before") if isinstance(turn, dict) else None
            after = turn.get("after") if isinstance(turn, dict) else None
            checkpoint = checkpoints[0] if len(checkpoints) == 1 else None
            qualified = bool(
                primary_error is None and status == "turn_limit"
                and isinstance(turn, dict)
                and turn.get("ok") is True
                and turn.get("status") == "executed"
                and turn.get("class") == "query"
                and turn.get("selected_step") == PRIVATE_CHILD_MATRILINEAL_RESULT_STEP
                and isinstance(result, dict)
                and result.get("status") == "pending"
                and result.get("material_result") is False
                and result.get("heir_character_id") == private_child_matrilineal_target[0]
                and result.get("candidate_character_id") == private_child_matrilineal_target[1]
                and isinstance(before, dict) and isinstance(after, dict)
                and before.get("paused") is True and after.get("paused") is True
                and before.get("date_raw") == after.get("date_raw") == opening_date_raw
                and before.get("episode_run_id") == after.get("episode_run_id")
                and before.get("episode_character_id") == after.get("episode_character_id")
                and isinstance(checkpoint, dict)
                and checkpoint.get("phase") == "player_child_matrilineal_result_pending"
                and checkpoint.get("ledger_status") == "pending"
                and checkpoint.get("status") == "saved"
                and checkpoint.get("turn_index") == turn.get("index") == 1
                and checkpoint.get("date_raw") == opening_date_raw
                and checkpoint.get("episode_run_id") == before.get("episode_run_id")
                and checkpoint.get("episode_character_id") == before.get("episode_character_id")
                and "child_matrilineal_result_checkpoint_saved" in turn.get("evidence", [])
                and visible_gameplay_turns == 0 and not date_advanced
                and cleanup.get("ok") is True
            )
        if allow_private_guy_default_formal_trial is True:
            # A paired action needs a following formal read. A recovery-only
            # run may qualify as a bounded read, without claiming marriage.
            default_turns = [
                turn for turn in turns
                if turn.get("selected_step") in {
                    PRIVATE_CHILD_DEFAULT_SUBMIT_STEP,
                    PRIVATE_CHILD_DEFAULT_RESULT_STEP,
                    PRIVATE_CHILD_DEFAULT_ALLIANCE_STEP}]
            submit_turns = [
                turn for turn in default_turns
                if turn.get("selected_step") == PRIVATE_CHILD_DEFAULT_SUBMIT_STEP]
            following_reads = [
                turn for turn in default_turns
                if turn.get("selected_step") in {
                    PRIVATE_CHILD_DEFAULT_RESULT_STEP,
                    PRIVATE_CHILD_DEFAULT_ALLIANCE_STEP}]
            paired = all(
                any(checkpoint.get("turn_index") == turn.get("index")
                    and checkpoint.get("status") == "saved"
                    for checkpoint in checkpoints)
                for turn in default_turns
            )
            qualified = bool(
                primary_error is None and status == "turn_limit"
                and default_turns and len(submit_turns) <= 1
                and (not submit_turns or
                     any(turn.get("index") > submit_turns[0].get("index")
                         for turn in following_reads))
                and all(turn.get("ok") is True
                        and turn.get("status") == "executed"
                        for turn in default_turns)
                and paired and cleanup.get("ok") is True
                and (private_guy_default_first_heir_companion is not True
                     or (isinstance(private_first_heir_companion_observation, dict)
                         and private_first_heir_companion_observation.get("same_frame") is True))
            )
        if private_realm_law_paused_query is True:
            qualified = bool(
                primary_error is None
                and status == "private_realm_law_paused_observed"
                and isinstance(private_realm_law_paused_observation, dict)
                and private_realm_law_paused_observation.get("same_frame") is True
                and cleanup.get("ok") is True
                and not turns
                and not date_advanced
            )
        if private_activity_planner_diag_query is True:
            qualified = bool(
                primary_error is None
                and status == "private_activity_planner_diag_observed"
                and isinstance(private_activity_planner_diag_observation, dict)
                and private_activity_planner_diag_observation.get("same_frame") is True
                and cleanup.get("ok") is True
                and not turns
                and not date_advanced
            )
        if (private_activity_feast_guest_opinion_character_id is not None
                and not combined_target_opinion):
            qualified = bool(
                primary_error is None
                and status == "private_activity_feast_guest_opinion_read"
                and isinstance(private_activity_feast_guest_opinion_observation, dict)
                and private_activity_feast_guest_opinion_observation.get("same_frame") is True
                and private_activity_feast_guest_opinion_observation.get("read_only") is True
                and private_activity_feast_guest_opinion_observation.get("opinion_status") == "observed"
                and cleanup.get("ok") is True
                and not turns and not date_advanced
            )
        if (private_activity_feast_planner_open is True
                and private_activity_cost_slot12_raw_read is not True):
            qualified = bool(
                primary_error is None
                and status == "private_activity_feast_planner_open_observed"
                and isinstance(private_activity_feast_planner_open_observation, dict)
                and private_activity_feast_planner_open_observation.get("same_frame") is True
                and private_activity_feast_planner_open_observation.get("gui_open") is True
                and cleanup.get("ok") is True
                and not turns and not date_advanced
            )
        if (private_activity_feast_stage1_option_read is True
                and private_activity_feast_stage1_confirm is not True):
            qualified = bool(
                primary_error is None
                and status == "private_activity_feast_stage1_option_observed"
                and isinstance(private_activity_feast_planner_open_observation, dict)
                and private_activity_feast_planner_open_observation.get("gui_open") is True
                and isinstance(private_activity_feast_stage1_option_observation, dict)
                and private_activity_feast_stage1_option_observation.get("same_frame") is True
                and private_activity_feast_stage1_option_observation.get("read_only") is True
                and cleanup.get("ok") is True
                and not turns and not date_advanced
            )
        if private_activity_feast_stage1_confirm is True:
            qualified = bool(
                primary_error is None
                and status == (
                    "private_activity_feast_stage5_start_assessed"
                    if private_activity_feast_stage5_start_read is True
                    else "private_activity_feast_guest_opinion_read"
                    if combined_target_opinion
                    else "private_activity_feast_guest_rule_read"
                    if private_activity_feast_guest_rule_key is not None
                    else "private_activity_feast_guest_route_proof_read"
                    if private_activity_feast_guest_route_proof_read is True
                    else "private_activity_feast_guest_target_read"
                    if private_activity_feast_guest_target_character_id is not None
                    else "private_activity_feast_guest_candidate_read"
                    if private_activity_feast_guest_candidate_read is True
                    else "private_activity_feast_stage5_full_cost_observed"
                    if private_activity_feast_stage5_full_cost_read is True
                    else "private_activity_feast_stage2_destination_selected"
                    if private_activity_feast_stage2_destination_province_id is not None
                    else
                    "private_activity_feast_stage2_location_observed"
                    if private_activity_feast_stage2_location_candidate_province_ids is not None
                    else ("private_activity_feast_stage2_gate_observed"
                          if private_activity_feast_stage2_gate_read is True
                          else "private_activity_feast_stage1_confirm_verified")
                )
                and isinstance(private_activity_feast_stage1_confirm_observation, dict)
                and private_activity_feast_stage1_confirm_observation.get("submitted") is True
                and private_activity_feast_stage1_confirm_observation.get("same_frame") is True
                and isinstance(private_activity_feast_stage2_option_observation, dict)
                and private_activity_feast_stage2_option_observation.get("same_frame") is True
                and private_activity_feast_stage2_option_observation.get("stage_two_verified") is True
                and (private_activity_feast_stage2_gate_read is not True
                     or (isinstance(private_activity_feast_stage2_gate_observation, dict)
                         and private_activity_feast_stage2_gate_observation.get("same_frame") is True
                         and private_activity_feast_stage2_gate_observation.get("gate_observed") is True))
                and (private_activity_feast_stage2_location_candidate_province_ids is None
                     or (isinstance(private_activity_feast_stage2_location_observation, dict)
                         and private_activity_feast_stage2_location_observation.get("same_frame") is True
                         and private_activity_feast_stage2_location_observation.get("location_observed") is True))
                and (private_activity_feast_stage2_destination_province_id is None
                     or (isinstance(private_activity_feast_stage2_destination_observation, dict)
                         and private_activity_feast_stage2_destination_observation.get("postcondition_verified") is True
                         and private_activity_feast_stage2_destination_observation.get("same_frame") is True))
                and (private_activity_feast_stage5_full_cost_read is not True
                     or (isinstance(private_activity_feast_stage5_full_cost_observation, dict)
                         and private_activity_feast_stage5_full_cost_observation.get("same_frame") is True
                         and private_activity_feast_stage5_full_cost_observation.get("read_only") is True))
                and (private_activity_feast_stage5_start_read is not True
                     or (isinstance(private_activity_feast_stage5_start_observation, dict)
                         and private_activity_feast_stage5_start_observation.get("same_frame") is True
                         and private_activity_feast_stage5_start_observation.get("decision") == "hold"))
                and (private_activity_feast_guest_candidate_read is not True
                     or (isinstance(private_activity_feast_guest_candidate_observation, dict)
                         and private_activity_feast_guest_candidate_observation.get("same_frame") is True
                         and private_activity_feast_guest_candidate_observation.get("read_only") is True))
                and (private_activity_feast_guest_route_proof_read is not True
                     or (isinstance(private_activity_feast_guest_route_proof_observation, dict)
                         and private_activity_feast_guest_route_proof_observation.get("same_frame") is True
                         and private_activity_feast_guest_route_proof_observation.get("read_only") is True
                         and private_activity_feast_guest_route_proof_observation.get("decision") == "hold"))
                and (private_activity_feast_guest_target_character_id is None
                     or (isinstance(private_activity_feast_guest_target_observation, dict)
                         and private_activity_feast_guest_target_observation.get("same_frame") is True
                         and private_activity_feast_guest_target_observation.get("read_only") is True
                         and private_activity_feast_guest_target_observation.get("decision") == "hold"
                         and private_activity_feast_guest_target_observation.get("formal_action_ready") is False))
                and (private_activity_feast_guest_rule_key is None
                     or (isinstance(private_activity_feast_guest_rule_observation, dict)
                         and private_activity_feast_guest_rule_observation.get("same_frame") is True
                         and private_activity_feast_guest_rule_observation.get("read_only") is True
                         and private_activity_feast_guest_rule_observation.get("decision") == "hold"))
                and (private_activity_feast_guest_target_character_id is None
                     or private_activity_feast_guest_rule_candidate_id
                         != private_activity_feast_guest_target_character_id
                     or (isinstance(private_activity_feast_guest_target_recheck_observation, dict)
                         and private_activity_feast_guest_target_recheck_observation.get("same_frame") is True
                         and _private_activity_feast_guest_target_same_source(
                             private_activity_feast_guest_target_recheck_observation.get("target_read"),
                             private_activity_feast_guest_target_observation.get("target_read"))))
                and (not combined_target_opinion
                     or (isinstance(private_activity_feast_guest_opinion_observation, dict)
                         and private_activity_feast_guest_opinion_observation.get("same_frame") is True
                         and private_activity_feast_guest_opinion_observation.get("read_only") is True
                         and private_activity_feast_guest_opinion_observation.get("opinion_status") == "observed"
                         and private_activity_feast_guest_opinion_observation.get("formal_action_ready") is False))
                and cleanup.get("ok") is True
                and not turns and not date_advanced
            )
        if private_activity_cost_slot12_raw_read is True:
            qualified = bool(
                primary_error is None
                and status == "private_activity_cost_slot12_raw_observed"
                and isinstance(private_activity_cost_slot12_raw_observation, dict)
                and private_activity_cost_slot12_raw_observation.get("same_frame") is True
                and private_activity_cost_slot12_raw_observation.get("read_only") is True
                and (private_activity_feast_planner_open is not True
                     or (isinstance(private_activity_feast_planner_open_observation, dict)
                         and private_activity_feast_planner_open_observation.get("gui_open") is True))
                and cleanup.get("ok") is True
                and not turns and not date_advanced
            )
        if allow_private_activity_feast_stage5_start_formal_trial is True:
            formal = private_activity_feast_stage5_start_formal
            qualified = bool(
                primary_error is None and cleanup.get("ok") is True
                and not date_advanced and isinstance(formal, dict)
                and (
                    (formal.get("status") == "held" and not turns
                     and isinstance(private_activity_feast_stage5_start_observation, dict)
                     and private_activity_feast_stage5_start_observation.get("same_frame") is True
                     and formal["result"].get("decision") == "hold")
                    or (formal["result"].get("postcondition_verified") is True
                        and formal.get("checkpoint_saved") is True
                        and len(turns) == 1)
                )
            )
    candidate_intercept_qualified = bool(
        before_submit is not None
        and opening_focus_gate is None
        and status == "candidate_terminal_intercepted"
        and candidate_interception is not None
        and after_intercept is None
        and checkpoints
        and primary_error is None
        and cleanup.get("ok") is True
    )
    candidate_resolved = bool(
        before_submit is not None
        and opening_focus_gate is None
        and after_intercept is not None
        and status == "candidate_terminal_resolved"
        and candidate_interception is not None
        and isinstance(candidate_resolution, dict)
        and candidate_resolution.get("ok") is True
        and checkpoints
        and primary_error is None
        and cleanup.get("ok") is True
    )
    candidate_qualified = candidate_intercept_qualified or candidate_resolved
    if candidate_qualified:
        qualified = True
        first_blocker = None
    elif qualified:
        first_blocker = None
    elif (
        status == "operator_stop_checkpointed"
        and primary_error is None
        and cleanup.get("ok") is True
    ):
        first_blocker = None
    elif first_failure is not None:
        first_blocker = copy.deepcopy(first_failure)
        first_blocker["run_status"] = status
        first_blocker["cleanup"] = copy.deepcopy(cleanup)
    else:
        first_blocker = _first_blocker_report(
            status=status,
            error=primary_error,
            completion_contract=completion_contract,
            readiness=readiness,
            turns=turns,
            checkpoints=checkpoints,
            fixed_seed=fixed_seed,
            cleanup=cleanup,
        )
    outcome = (
        "operator_stopped"
        if status == "operator_stop_checkpointed"
        and primary_error is None
        and cleanup.get("ok") is True
        else "qualified"
        if qualified
        else (
            (
                "bounded_incomplete"
                if completion_contract in strict_completion_contracts
                else "not_qualified"
            )
            if primary_error is None and cleanup.get("ok") is True
            else "failed"
        )
    )
    attempted_turns = len(turns)
    if isinstance(first_failure, dict):
        failed_turn_index = first_failure.get("turn_index")
        if isinstance(failed_turn_index, int) and not isinstance(
            failed_turn_index, bool
        ):
            attempted_turns = max(attempted_turns, failed_turn_index)
    return {
        "format_version": 1,
        "kind": "ck3_native_auto_run",
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "status": status,
        "outcome": (
            "candidate_resolved"
            if candidate_resolved
            else "candidate_intercepted"
            if candidate_intercept_qualified
            else "private_action_applied"
            if (private_active_scheme_sway_target is not None
                and allow_private_active_scheme_sway_formal_trial is True
                and qualified)
            else ("private_action_applied"
                  if private_activity_feast_stage5_start_formal["action_attempted"]
                  else "private_action_restored")
            if (allow_private_activity_feast_stage5_start_formal_trial is True
                and qualified
                and private_activity_feast_stage5_start_formal["result"].get("postcondition_verified") is True)
            else "read_only_observed"
            if allow_private_activity_feast_stage5_start_formal_trial is True and qualified
            else "gui_open_observed"
            if (private_activity_feast_planner_open is True
                and private_activity_cost_slot12_raw_read is not True
                and private_activity_feast_stage1_confirm is not True
                and qualified)
            else "planning_stage_advanced"
            if private_activity_feast_stage1_confirm is True and qualified
            else "read_only_observed"
            if private_activity_feast_stage1_option_read is True and qualified
            else "read_only_observed"
            if private_activity_cost_slot12_raw_read is True and qualified
            else "read_only_observed"
            if (private_active_scheme_sway_target is not None
                and allow_private_active_scheme_sway_formal_trial is not True
                and qualified)
            or private_child_matrilineal_pending_read_target is not None and qualified
            or private_realm_law_paused_query is True and qualified
            or private_activity_planner_diag_query is True and qualified
            or private_activity_feast_guest_opinion_character_id is not None and qualified
            else outcome
        ),
        "ok": qualified,
        "completion_contract": completion_contract,
        "exact_war_move_stop": {
            "contract": copy.deepcopy(exact_move_contract),
            "pre_submit_seen": exact_move_pre_submit_seen,
            "independent_poststate": copy.deepcopy(exact_move_poststate),
            "checkpoint_poststate": copy.deepcopy(exact_move_checkpoint),
        } if exact_move_contract is not None else None,
        "succession_lifecycle": copy.deepcopy(
            succession_lifecycle_binding
        ),
        "cold_start_checkpoint": cold_start_checkpoint,
        "initial_lifestyle_focus_gate": copy.deepcopy(opening_focus_gate),
        **(
            {"private_active_scheme_sway_observation": copy.deepcopy(
                private_active_scheme_sway_observation)}
            if private_active_scheme_sway_target is not None else {}
        ),
        **(
            {"private_active_scheme_sway_formal": copy.deepcopy(
                private_active_scheme_sway_formal)}
            if allow_private_active_scheme_sway_formal_trial is True else {}
        ),
        **(
            {"private_active_scheme_sway_following_turn": copy.deepcopy(
                private_active_scheme_sway_following_turn)}
            if private_active_scheme_sway_following_turn is not None else {}
        ),
        **(
            {"private_child_matrilineal_pending_observation": copy.deepcopy(
                private_child_matrilineal_pending_observation)}
            if private_child_matrilineal_pending_read_target is not None else {}
        ),
        **(
            {"private_first_heir_companion_observation": copy.deepcopy(
                private_first_heir_companion_observation)}
            if (private_child_matrilineal_first_heir_companion is True
                or private_guy_default_first_heir_companion is True) else {}
        ),
        **(
            {"private_realm_law_paused_observation": copy.deepcopy(
                private_realm_law_paused_observation)}
            if private_realm_law_paused_query is True else {}
        ),
        **(
            {"private_activity_planner_diag_observation": copy.deepcopy(
                private_activity_planner_diag_observation)}
            if private_activity_planner_diag_query is True else {}
        ),
        **(
            {"private_activity_feast_planner_open_observation": copy.deepcopy(
                private_activity_feast_planner_open_observation)}
            if (private_activity_feast_planner_open is True
                or private_activity_feast_stage1_option_read is True
                or private_activity_feast_stage1_confirm is True) else {}
        ),
        **(
            {"private_activity_feast_stage1_option_observation": copy.deepcopy(
                private_activity_feast_stage1_option_observation)}
            if (private_activity_feast_stage1_option_read is True
                or private_activity_feast_stage1_confirm is True) else {}
        ),
        **(
            {"private_activity_feast_stage1_confirm_observation": copy.deepcopy(
                private_activity_feast_stage1_confirm_observation)}
            if private_activity_feast_stage1_confirm is True else {}
        ),
        **(
            {"private_activity_feast_stage2_option_observation": copy.deepcopy(
                private_activity_feast_stage2_option_observation)}
            if private_activity_feast_stage1_confirm is True else {}
        ),
        **(
            {"private_activity_feast_stage2_gate_observation": copy.deepcopy(
                private_activity_feast_stage2_gate_observation)}
            if private_activity_feast_stage2_gate_read is True else {}
        ),
        **(
            {"private_activity_feast_stage2_location_observation": copy.deepcopy(
                private_activity_feast_stage2_location_observation)}
            if private_activity_feast_stage2_location_candidate_province_ids is not None else {}
        ),
        **(
            {"private_activity_feast_stage2_destination_observation": copy.deepcopy(
                private_activity_feast_stage2_destination_observation)}
            if private_activity_feast_stage2_destination_province_id is not None else {}
        ),
        **(
            {"private_activity_feast_stage5_full_cost_observation": copy.deepcopy(
                private_activity_feast_stage5_full_cost_observation)}
            if private_activity_feast_stage5_full_cost_read is True else {}
        ),
        **(
            {"private_activity_feast_stage5_start_observation": copy.deepcopy(
                private_activity_feast_stage5_start_observation)}
            if private_activity_feast_stage5_start_read is True else {}
        ),
        **(
            {"private_activity_feast_stage5_start_formal": copy.deepcopy(
                private_activity_feast_stage5_start_formal)}
            if allow_private_activity_feast_stage5_start_formal_trial is True else {}
        ),
        **(
            {"private_activity_feast_guest_candidate_observation": copy.deepcopy(
                private_activity_feast_guest_candidate_observation)}
            if private_activity_feast_guest_candidate_read is True else {}
        ),
        **(
            {"private_activity_feast_guest_route_proof_observation": copy.deepcopy(
                private_activity_feast_guest_route_proof_observation)}
            if private_activity_feast_guest_route_proof_read is True else {}
        ),
        **(
            {"private_activity_feast_guest_target_observation": copy.deepcopy(
                private_activity_feast_guest_target_observation)}
            if private_activity_feast_guest_target_character_id is not None else {}
        ),
        **(
            {"private_activity_feast_guest_target_recheck_observation": copy.deepcopy(
                private_activity_feast_guest_target_recheck_observation)}
            if private_activity_feast_guest_target_recheck_observation is not None else {}
        ),
        **(
            {"private_activity_feast_guest_opinion_observation": copy.deepcopy(
                private_activity_feast_guest_opinion_observation)}
            if private_activity_feast_guest_opinion_character_id is not None else {}
        ),
        **(
            {"private_activity_feast_guest_rule_observation": copy.deepcopy(
                private_activity_feast_guest_rule_observation)}
            if private_activity_feast_guest_rule_key is not None else {}
        ),
        **(
            {"private_activity_feast_stage5_start_following_turn": copy.deepcopy(
                private_activity_feast_stage5_start_following_turn)}
            if private_activity_feast_stage5_start_following_turn is not None else {}
        ),
        **(
            {"private_activity_cost_slot12_raw_observation": copy.deepcopy(
                private_activity_cost_slot12_raw_observation)}
            if private_activity_cost_slot12_raw_read is True else {}
        ),
        **(
            {
                "private_prisoner_collection_observation": copy.deepcopy(
                    private_prisoner_collection_observation
                )
            }
            if allow_private_prisoner_collection_observation is True
            else {}
        ),
        "fixed_seed": fixed_seed,
        "bounds": {
            "requested_turns": turn_count,
            "max_wall_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "checkpoint_every_eligible_advances": checkpoint_cadence,
            "route_contact_timeline_speed": route_contact_speed,
            "allow_route_contact_high_speed_ab": (
                allow_route_contact_high_speed_ab is True
            ),
            "allow_stationary_objective_hold_sentinel_canary": (
                allow_stationary_objective_hold_sentinel_canary is True
            ),
        },
        "identity": {
            **_identity(config, readiness, spec),
            "succession_lifecycle": copy.deepcopy(
                succession_lifecycle_binding
            ),
        },
        "readiness": _public_binding(readiness) if readiness is not None else None,
        "readiness_diagnostics": readiness_timeout_diagnostics,
        "auto_run": {
            "attempted_turns": attempted_turns,
            "successful_turns": sum(
                1 for row in turns if row.get("ok") is True
            ),
            "counts": counts,
            "visible_gameplay_turns": visible_gameplay_turns,
            "eligible_advances_since_checkpoint": eligible_since_checkpoint,
            "dirty_gameplay_since_checkpoint": dirty_gameplay_since_checkpoint,
            "checkpoint_deferred_for_player_decision": bool(
                modal_decision_pending
                and dirty_gameplay_since_checkpoint
            ),
            "turns": turns,
        },
        "checkpoints": checkpoints,
        "terminal": terminal_proof,
        "candidate_interception": candidate_interception,
        "candidate_resolution": candidate_resolution,
        "natural_succession_transitions": natural_succession_transitions,
        "next_episode": (
            {
                "transition": next_episode_transition,
                "visible_gameplay_turns": (
                    post_transition_visible_gameplay_turns
                ),
                "last_gameplay_turn_index": (
                    post_transition_last_gameplay_turn_index
                ),
                "checkpoint": post_transition_checkpoint,
            }
            if completion_contract == "next_episode"
            else None
        ),
        "qualification_gates": qualification_gates,
        "first_blocker": first_blocker,
        "session": _compact_session_report(session_report),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _wait_for_readiness(
    driver: NativeHeadlessGameplayDriver,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    timeout_seconds: float,
    stable_seconds: float,
    poll_interval_seconds: float,
    cold_start_checkpoint: bool,
    allow_terminal: bool,
    require_post_ready_pump: bool = False,
    expected_character_id: int | None = None,
) -> dict[str, object]:
    """Wait for a stable native frame, optionally pinned to one character.

    Callers that will issue UI or gameplay input against a known save must
    provide ``expected_character_id``.  A map-ready frame can precede the
    played-character and episode projections during direct load.
    ``require_post_ready_pump`` binds the first request after a new process
    launch to a later application-main pump of that same stable frame.
    """
    if expected_character_id is not None and (
        isinstance(expected_character_id, bool)
        or not isinstance(expected_character_id, int)
        or expected_character_id <= 0
    ):
        raise AgentError(
            "expected readiness character id must be a positive integer"
        )
    deadline = time.monotonic() + timeout_seconds
    stable_key: tuple[object, ...] | None = None
    stable_since: float | None = None
    post_ready_pump_required = cold_start_checkpoint or require_post_ready_pump
    ready_pump_epoch: int | None = None
    last_reason = "native DLL has not connected"
    last_observation: dict[str, object] | None = None
    last_readiness_diagnostics: dict[str, object] | None = None
    while True:
        if session_done.is_set():
            raise AgentError(_premature_session_exit(session_state))
        now = time.monotonic()
        if now >= deadline:
            raise NativeReadinessTimeoutError(
                "native readiness timed out: "
                f"{last_reason}; last={last_observation!r}",
                readiness_diagnostics=last_readiness_diagnostics,
                last_observation=last_observation,
            )
        try:
            capabilities = driver.capabilities()
            last_readiness_diagnostics = _compact_readiness_diagnostics(
                capabilities
            )
            diagnostics = capabilities.get("diagnostics")
            _raise_fatal_diagnostics(diagnostics)
            snapshot = _runner_semantic_snapshot(driver)
            # The internal semantic read may bind a cold checkpoint identity;
            # capabilities must be read again so the gate observes that
            # committed binding without copying transcript evidence.
            capabilities = driver.capabilities()
            last_readiness_diagnostics = _compact_readiness_diagnostics(
                capabilities
            )
            ready, reason, observation = _readiness_observation(
                capabilities,
                snapshot,
                cold_start_checkpoint=cold_start_checkpoint,
                allow_terminal=allow_terminal,
                expected_character_id=expected_character_id,
            )
            last_reason = reason
            last_observation = observation
            if ready:
                current_pump_epoch = _main_thread_query_pump_epoch(
                    capabilities
                )
                key = (
                    observation.get("bridge_pid"),
                    observation.get("connection_generation"),
                    observation.get("snapshot_id"),
                    observation.get("revision"),
                    observation.get("native_revision"),
                    observation.get("date_raw"),
                    observation.get("episode_run_id"),
                    observation.get("played_character_id"),
                    observation.get("episode_character_id"),
                )
                if key != stable_key:
                    stable_key = key
                    stable_since = now
                    ready_pump_epoch = (
                        current_pump_epoch
                        if post_ready_pump_required
                        else None
                    )
                post_ready_pump_advanced = bool(
                    not post_ready_pump_required
                    or (
                        current_pump_epoch is not None
                        and ready_pump_epoch is not None
                        and current_pump_epoch > ready_pump_epoch
                    )
                )
                if post_ready_pump_required and not post_ready_pump_advanced:
                    lifecycle = (
                        "cold checkpoint" if cold_start_checkpoint
                        else "fresh-process"
                    )
                    last_reason = (
                        "application-main pump has not advanced after "
                        f"{lifecycle} readiness: "
                        f"baseline={ready_pump_epoch!r}, "
                        f"current={current_pump_epoch!r}"
                    )
                if (
                    post_ready_pump_advanced
                    and stable_since is not None
                    and now - stable_since >= stable_seconds
                ):
                    return observation
            else:
                stable_key = None
                stable_since = None
                ready_pump_epoch = None
        except (BridgeUnavailableError, UnsupportedStepError) as error:
            last_reason = str(error)
            stable_key = None
            stable_since = None
            ready_pump_epoch = None
        time.sleep(min(poll_interval_seconds, max(0.0, deadline - now)))


def _main_thread_query_pump_epoch(
    capabilities: dict[str, object],
) -> int | None:
    diagnostics = capabilities.get("diagnostics")
    heartbeat = (
        diagnostics.get("last_heartbeat")
        if isinstance(diagnostics, dict)
        else None
    )
    mailbox = (
        heartbeat.get("main_thread_query_mailbox_v1")
        if isinstance(heartbeat, dict)
        else None
    )
    pump_epoch = mailbox.get("pump_epochs") if isinstance(mailbox, dict) else None
    return (
        pump_epoch
        if isinstance(pump_epoch, int)
        and not isinstance(pump_epoch, bool)
        and pump_epoch >= 0
        else None
    )


def _compact_readiness_diagnostics(
    capabilities: object,
) -> dict[str, object]:
    """Retain bounded bridge evidence when semantic readiness never arrives.

    A timeout can occur before a semantic snapshot exists, so the normal
    ``_compact_binding`` path has nothing to serialize.  Keep only stable
    transport/heartbeat fields here; full hello capability lists and native
    snapshots are intentionally excluded from the failure report.
    """
    if not isinstance(capabilities, dict):
        return {
            "mode": None,
            "backend_id": None,
            "transport_ready": None,
            "snapshot": None,
            "diagnostics": None,
        }
    diagnostics = capabilities.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return {
            "mode": capabilities.get("mode"),
            "backend_id": capabilities.get("backend_id"),
            "transport_ready": capabilities.get("transport_ready"),
            "snapshot": capabilities.get("snapshot"),
            "diagnostics": None,
        }
    hello = diagnostics.get("hello")
    heartbeat = diagnostics.get("last_heartbeat")
    mailbox = (
        heartbeat.get("main_thread_query_mailbox_v1")
        if isinstance(heartbeat, dict)
        else None
    )
    hello_summary = (
        {
            "ck3_build_match": hello.get("ck3_build_match"),
            "game_adapter_id": hello.get("game_adapter_id"),
            "game_adapter_status": hello.get("game_adapter_status"),
            "executable_sha256": hello.get("executable_sha256"),
        }
        if isinstance(hello, dict)
        else None
    )
    heartbeat_summary = (
        {
            "sequence": heartbeat.get("sequence"),
            "pid": heartbeat.get("pid"),
            "main_thread_query_mailbox_v1": (
                {
                    key: mailbox.get(key)
                    for key in (
                        "installed",
                        "stop",
                        "failure",
                        "pump_epochs",
                        "consecutive_verified",
                        "ready",
                        "executor_submission_enabled",
                        "date_raw",
                        "paused",
                        "executed_requests",
                    )
                }
                if isinstance(mailbox, dict)
                else None
            ),
        }
        if isinstance(heartbeat, dict)
        else None
    )
    return {
        "mode": capabilities.get("mode"),
        "backend_id": capabilities.get("backend_id"),
        "transport_ready": capabilities.get("transport_ready"),
        "snapshot": capabilities.get("snapshot"),
        "diagnostics": {
            "connected": diagnostics.get("connected"),
            "connection_generation": diagnostics.get("connection_generation"),
            "bridge_pid": diagnostics.get("bridge_pid"),
            "semantic_state_available": diagnostics.get(
                "semantic_state_available"
            ),
            "rejected_state_snapshot_count": diagnostics.get(
                "rejected_state_snapshot_count"
            ),
            "snapshot_publish_diagnostic_count": diagnostics.get(
                "snapshot_publish_diagnostic_count"
            ),
            "transport_fatal_error": diagnostics.get("transport_fatal_error"),
            "last_error": diagnostics.get("last_error"),
            "hello": hello_summary,
            "last_heartbeat": heartbeat_summary,
        },
    }


def _readiness_observation(
    capabilities: dict[str, object],
    snapshot: dict[str, object],
    *,
    cold_start_checkpoint: bool,
    allow_terminal: bool,
    expected_character_id: int | None = None,
) -> tuple[bool, str, dict[str, object]]:
    observation = _compact_binding(capabilities, snapshot)
    diagnostics = capabilities.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    heartbeat = (
        diagnostics.get("last_heartbeat")
        if isinstance(diagnostics, dict)
        else None
    )
    mailbox = (
        heartbeat.get("main_thread_query_mailbox_v1")
        if isinstance(heartbeat, dict)
        else None
    )
    control = capabilities.get("native_session_control")
    played = snapshot.get("played_character")
    terminal = bool(
        snapshot.get("one_life_terminal") is True
        or isinstance(snapshot.get("one_life_terminal_reason"), str)
    )
    snapshot_diagnostics = snapshot.get("diagnostics")
    same_transport_binding = bool(
        isinstance(diagnostics, dict)
        and isinstance(snapshot_diagnostics, dict)
        and diagnostics.get("bridge_pid")
        == snapshot_diagnostics.get("bridge_pid")
        and diagnostics.get("connection_generation")
        == snapshot_diagnostics.get("connection_generation")
    )
    checks: list[tuple[bool, str]] = [
        (capabilities.get("mode") == PURE_NATIVE_MODE, "mode is not native-headless"),
        (capabilities.get("backend_id") == PURE_NATIVE_MODE, "backend is not native-headless"),
        (capabilities.get("visual_fallback") is False, "visual fallback is not disabled"),
        (capabilities.get("transport_ready") is True, "native transport is not ready"),
        (isinstance(diagnostics, dict) and diagnostics.get("connected") is True, "bridge is disconnected"),
        (isinstance(diagnostics, dict) and diagnostics.get("semantic_state_available") is True, "semantic state is unavailable"),
        (capabilities.get("snapshot") is True, "snapshot capability is unavailable"),
        (same_transport_binding, "capability and snapshot transports differ"),
        (isinstance(hello, dict), "native hello is unavailable"),
        (isinstance(hello, dict) and hello.get("ck3_build_match") is True, "CK3 exact-build adapter is not ready"),
        (isinstance(hello, dict) and hello.get("game_adapter_status") == "ready", "game adapter status is not ready"),
        (isinstance(heartbeat, dict), "heartbeat is unavailable"),
        (isinstance(heartbeat, dict) and heartbeat.get("startup_failure_containment_enabled") is False, "startup containment is not disabled"),
        (isinstance(heartbeat, dict) and heartbeat.get("startup_particle2_stage_recorder_enabled") is False, "startup stage recorder is not disabled"),
        (isinstance(mailbox, dict) and mailbox.get("installed") is True, "main-thread mailbox is not installed"),
        (isinstance(mailbox, dict) and mailbox.get("stop") is False, "main-thread mailbox is stopping"),
        (isinstance(mailbox, dict) and mailbox.get("failure") == 0, "main-thread mailbox reports failure"),
        (isinstance(mailbox, dict) and mailbox.get("ready") is True, "main-thread mailbox is not ready"),
        (isinstance(mailbox, dict) and mailbox.get("executor_submission_enabled") is True, "main-thread mailbox executor is disabled"),
        (snapshot.get("map_ready") is True, "map is not ready"),
        (snapshot.get("paused") is True, "map is not paused"),
        (snapshot.get("episode_identity_pending") is False, "episode identity is pending"),
        (
            isinstance(snapshot.get("episode_character_id"), int)
            and not isinstance(snapshot.get("episode_character_id"), bool),
            "episode character is unavailable",
        ),
        (
            isinstance(snapshot.get("episode_run_id"), str)
            and bool(snapshot.get("episode_run_id")),
            "episode run is unavailable",
        ),
        (isinstance(control, dict), "native session control is unavailable"),
        (
            isinstance(control, dict)
            and control.get("episode_binding_state")
            in {
                "active_new",
                "active_resumed",
                "active_natural_successor",
            },
            "episode identity is not active",
        ),
        (isinstance(mailbox, dict) and mailbox.get("date_raw") == snapshot.get("date_raw"), "mailbox date differs from paused snapshot"),
        (isinstance(mailbox, dict) and mailbox.get("paused") is True, "mailbox did not observe paused state"),
    ]
    if terminal and allow_terminal:
        checks.extend(
            [
                (
                    isinstance(snapshot.get("episode_character_id"), int)
                    and not isinstance(snapshot.get("episode_character_id"), bool),
                    "terminal episode character is unavailable",
                ),
                (
                    isinstance(snapshot.get("episode_run_id"), str)
                    and bool(snapshot.get("episode_run_id")),
                    "terminal episode run is unavailable",
                ),
            ]
        )
    else:
        checks.extend(
            [
                (isinstance(played, dict), "played character is unavailable"),
                (
                    isinstance(played, dict) and played.get("alive") is True,
                    "played character is not alive",
                ),
                (
                    snapshot.get("episode_character_id")
                    == (
                        played.get("character_id")
                        if isinstance(played, dict)
                        else None
                    ),
                    "played character differs from episode character",
                ),
                (
                    isinstance(
                        played.get("character_id")
                        if isinstance(played, dict)
                        else None,
                        int,
                    )
                    and not isinstance(
                        played.get("character_id")
                        if isinstance(played, dict)
                        else None,
                        bool,
                    ),
                    "played character id is unavailable",
                ),
            ]
        )
    if expected_character_id is not None:
        checks.extend(
            [
                (
                    snapshot.get("episode_character_id")
                    == expected_character_id,
                    "episode character does not match expected character",
                ),
                (
                    isinstance(played, dict)
                    and played.get("character_id") == expected_character_id,
                    "played character does not match expected character",
                ),
            ]
        )
    if cold_start_checkpoint:
        checks.extend(
            [
                (isinstance(control, dict) and control.get("driver_state_restored") is True, "cold driver state was not restored"),
                (isinstance(control, dict) and control.get("driver_state_restore_kind") == "cold_checkpoint", "cold restore kind is not checkpoint"),
                (isinstance(control, dict) and control.get("episode_binding_state") == "active_resumed", "cold episode was not resumed"),
                (isinstance(control, dict) and control.get("cold_candidate_rejection") is None, "cold checkpoint candidate was rejected"),
            ]
        )
    for passed, reason in checks:
        if not passed:
            return False, reason, observation
    return True, "ready", observation


def _runner_semantic_snapshot(
    driver: NativeHeadlessGameplayDriver,
) -> dict[str, object]:
    """Use the native runner's lean frame while preserving driver fallbacks."""
    reader = getattr(
        driver, "take_internal_semantic_snapshot", None
    )
    if callable(reader):
        return reader()
    return driver.take_snapshot()


def _raise_fatal_diagnostics(diagnostics: object) -> None:
    if not isinstance(diagnostics, dict):
        return
    fatal = diagnostics.get("transport_fatal_error")
    if isinstance(fatal, str) and fatal:
        raise AgentError(f"native bridge transport failed: {fatal}")
    hello = diagnostics.get("hello")
    if isinstance(hello, dict) and (
        hello.get("ck3_build_match") is False
        or hello.get("game_adapter_status") == "unsupported_build"
    ):
        raise AgentError(
            "native bridge rejected this CK3 executable: "
            f"sha256={hello.get('executable_sha256')!r}"
        )


def _verify_one_generation_binding(
    binding: dict[str, object],
    initial_episode: dict[str, object] | None,
) -> None:
    if not isinstance(initial_episode, dict):
        raise AgentError("one-generation initial episode binding is unavailable")
    expected_character_id = initial_episode.get("episode_character_id")
    expected_run_id = initial_episode.get("episode_run_id")
    if (
        isinstance(expected_character_id, bool)
        or not isinstance(expected_character_id, int)
        or not isinstance(expected_run_id, str)
        or not expected_run_id
    ):
        raise AgentError("one-generation initial episode binding is malformed")
    if binding.get("episode_character_id") != expected_character_id:
        raise AgentError(
            "one-generation episode CharacterID changed before settlement: "
            f"{binding.get('episode_character_id')!r} != {expected_character_id!r}"
        )
    if binding.get("episode_run_id") != expected_run_id:
        raise AgentError(
            "one-generation episode run changed before settlement: "
            f"{binding.get('episode_run_id')!r} != {expected_run_id!r}"
        )


def _verify_next_episode_binding(
    binding: dict[str, object],
    transition: dict[str, object],
) -> None:
    """Keep every post-relaunch turn on the newly bound seed episode."""
    expected_character_id = transition.get("episode_character_id")
    expected_run_id = transition.get("episode_run_id")
    if (
        isinstance(expected_character_id, bool)
        or not isinstance(expected_character_id, int)
        or not isinstance(expected_run_id, str)
        or not expected_run_id
    ):
        raise AgentError("next-episode transition identity is malformed")
    if (
        binding.get("episode_character_id") != expected_character_id
        or binding.get("episode_run_id") != expected_run_id
        or binding.get("played_character_id") != expected_character_id
        or binding.get("played_character_alive") is not True
        or binding.get("one_life_terminal") is True
        or binding.get("one_life_terminal_reason") is not None
        or binding.get("map_ready") is not True
        or binding.get("paused") is not True
        or binding.get("episode_binding_state") != "active_new"
        or binding.get("driver_state_restore_kind")
        != "new_episode_seed"
    ):
        raise AgentError(
            "next-episode binding changed before its gameplay checkpoint"
        )


def _verify_next_episode_transition(
    result: object,
    *,
    snapshot: dict[str, object],
    binding: dict[str, object],
    initial_episode: dict[str, object] | None,
) -> dict[str, object]:
    """Require a fresh run identity loaded from the immutable episode seed."""
    if not isinstance(initial_episode, dict):
        raise AgentError("next-episode initial identity is unavailable")
    source_character_id = initial_episode.get("episode_character_id")
    source_run_id = initial_episode.get("episode_run_id")
    if (
        isinstance(source_character_id, bool)
        or not isinstance(source_character_id, int)
        or not isinstance(source_run_id, str)
        or not source_run_id
        or not isinstance(result, dict)
    ):
        raise AgentError("next-episode source identity or result is malformed")
    episode_seed = result.get("episode_seed")
    lifecycle = result.get("lifecycle")
    lifecycle_seed = (
        lifecycle.get("episode_seed")
        if isinstance(lifecycle, dict)
        else None
    )
    cross_run_plan = result.get("cross_run_plan_used")
    new_character_id = result.get("episode_character_id")
    new_run_id = result.get("episode_run_id")
    seed_size = (
        episode_seed.get("size") if isinstance(episode_seed, dict) else None
    )
    seed_sha256 = (
        episode_seed.get("sha256")
        if isinstance(episode_seed, dict)
        else None
    )
    seed_date_raw = (
        episode_seed.get("date_raw")
        if isinstance(episode_seed, dict)
        else None
    )
    seed_character_id = (
        episode_seed.get("character_id")
        if isinstance(episode_seed, dict)
        else None
    )
    previous_generation = (
        lifecycle.get("previous_connection_generation")
        if isinstance(lifecycle, dict)
        else None
    )
    connection_generation = (
        lifecycle.get("connection_generation")
        if isinstance(lifecycle, dict)
        else None
    )
    previous_pid = (
        lifecycle.get("previous_pid")
        if isinstance(lifecycle, dict)
        else None
    )
    current_pid = (
        lifecycle.get("pid") if isinstance(lifecycle, dict) else None
    )
    played = snapshot.get("played_character")
    digest_valid = bool(
        isinstance(seed_sha256, str)
        and len(seed_sha256) == 64
        and all(character in "0123456789abcdef" for character in seed_sha256)
    )
    if (
        result.get("step") != "start-next-episode"
        or result.get("accepted") is not True
        or result.get("status") != "started"
        or result.get("lifecycle_intent") != "new_episode"
        or result.get("source_run_id") != source_run_id
        or not isinstance(new_run_id, str)
        or not new_run_id
        or new_run_id == source_run_id
        or isinstance(new_character_id, bool)
        or not isinstance(new_character_id, int)
        or result.get("same_character_id") is not True
        or not isinstance(episode_seed, dict)
        or episode_seed.get("name") != "xar_episode_seed.ck3"
        or episode_seed.get("immutable") is not True
        or isinstance(seed_size, bool)
        or not isinstance(seed_size, int)
        or seed_size <= 0
        or not digest_valid
        or isinstance(seed_date_raw, bool)
        or not isinstance(seed_date_raw, int)
        or isinstance(seed_character_id, bool)
        or not isinstance(seed_character_id, int)
        or seed_character_id != new_character_id
        or not isinstance(cross_run_plan, dict)
        or not isinstance(lifecycle, dict)
        or lifecycle.get("status") != "relaunched"
        or lifecycle.get("lifecycle_intent") != "new_episode"
        or lifecycle.get("continue_last_save") is not False
        or lifecycle.get("load_save_name") != "xar_episode_seed"
        or not isinstance(lifecycle_seed, dict)
        or lifecycle_seed.get("name") != episode_seed.get("name")
        or lifecycle_seed.get("size") != seed_size
        or lifecycle_seed.get("sha256") != seed_sha256
        or lifecycle_seed.get("date_raw") != seed_date_raw
        or lifecycle_seed.get("character_id") != seed_character_id
        or isinstance(previous_generation, bool)
        or not isinstance(previous_generation, int)
        or isinstance(connection_generation, bool)
        or not isinstance(connection_generation, int)
        or previous_generation < 1
        or connection_generation < 1
        or isinstance(previous_pid, bool)
        or not isinstance(previous_pid, int)
        or isinstance(current_pid, bool)
        or not isinstance(current_pid, int)
        or current_pid == previous_pid
        or binding.get("bridge_pid") != current_pid
        or binding.get("connection_generation") != connection_generation
        or snapshot.get("episode_character_id") != new_character_id
        or snapshot.get("episode_run_id") != new_run_id
        or snapshot.get("date_raw") != seed_date_raw
        or not isinstance(played, dict)
        or played.get("character_id") != new_character_id
        or played.get("alive") is not True
        or snapshot.get("one_life_terminal") is True
        or snapshot.get("one_life_terminal_reason") is not None
    ):
        raise AgentError(
            "start-next-episode did not prove a fresh immutable-seed run"
        )
    proof = {
        "status": "verified",
        "source_character_id": source_character_id,
        "source_run_id": source_run_id,
        "episode_character_id": new_character_id,
        "episode_run_id": new_run_id,
        "new_run_identity": True,
        "seed_reloaded": True,
        "episode_seed": copy.deepcopy(episode_seed),
        "cross_run_plan_used": copy.deepcopy(cross_run_plan),
        "lifecycle": copy.deepcopy(lifecycle),
        "initial_binding": copy.deepcopy(initial_episode),
        "new_binding": _public_binding(binding),
    }
    _verify_next_episode_binding(binding, proof)
    return proof


def _checkpoint_proves_next_episode_ooda(
    checkpoint: dict[str, object],
    *,
    transition: dict[str, object],
    last_gameplay_turn_index: int,
) -> bool:
    turn_index = checkpoint.get("turn_index")
    return bool(
        checkpoint.get("status") == "saved"
        and checkpoint.get("episode_character_id")
        == transition.get("episode_character_id")
        and checkpoint.get("episode_run_id")
        == transition.get("episode_run_id")
        and isinstance(turn_index, int)
        and not isinstance(turn_index, bool)
        and turn_index >= last_gameplay_turn_index
    )


def _verify_natural_succession_transition(
    result: object,
    *,
    snapshot: dict[str, object],
    binding: dict[str, object],
    before: dict[str, object],
    succession_lifecycle: dict[str, object],
) -> dict[str, object]:
    """Prove a same-process new episode on CK3's played successor."""

    if not isinstance(result, dict):
        raise AgentError("natural successor continuation returned no result")
    predecessor_id = before.get("episode_character_id")
    predecessor_run_id = before.get("episode_run_id")
    successor_id = before.get("played_character_id")
    successor_run_id = result.get("episode_run_id")
    reconciliation = result.get("reconciliation")
    successor_binding = (
        reconciliation.get("successor_binding")
        if isinstance(reconciliation, dict)
        else None
    )
    played = snapshot.get("played_character")
    same_frame_keys = (
        "bridge_pid",
        "connection_generation",
        "snapshot_id",
        "revision",
        "native_revision",
        "date_raw",
    )
    lifecycle_result_matches = (
        result.get("succession_lifecycle") == succession_lifecycle
        or (
            succession_lifecycle == legacy_rogue_one_life_binding_v1()
            and result.get("succession_lifecycle") is None
        )
    )
    if (
        isinstance(predecessor_id, bool)
        or not isinstance(predecessor_id, int)
        or not isinstance(predecessor_run_id, str)
        or not predecessor_run_id
        or isinstance(successor_id, bool)
        or not isinstance(successor_id, int)
        or successor_id == predecessor_id
        or before.get("played_character_alive") is not True
        or before.get("one_life_terminal") is not True
        or before.get("one_life_terminal_reason")
        != "played_character_changed"
        or result.get("step") != CONTINUE_AS_RECONCILED_SUCCESSOR_STEP
        or result.get("accepted") is not True
        or result.get("status") != "continued"
        or result.get("source") != "native-played-character-transition"
        or result.get("lifecycle_intent") != "natural_succession"
        or not lifecycle_result_matches
        or result.get("predecessor_character_id") != predecessor_id
        or result.get("successor_character_id") != successor_id
        or result.get("source_episode_run_id") != predecessor_run_id
        or not isinstance(successor_run_id, str)
        or not successor_run_id
        or successor_run_id == predecessor_run_id
        or result.get("continue_as_heir_after_death") is not True
        or result.get("heir_gameplay_actions") != 0
        or result.get("ck3_command_submitted") is not False
        or result.get("process_restarted") is not False
        or any(binding.get(key) != before.get(key) for key in same_frame_keys)
        or snapshot.get("episode_character_id") != successor_id
        or snapshot.get("episode_run_id") != successor_run_id
        or not isinstance(played, dict)
        or played.get("character_id") != successor_id
        or played.get("alive") is not True
        or snapshot.get("one_life_terminal") is True
        or snapshot.get("one_life_terminal_reason") is not None
        or binding.get("episode_binding_state")
        != "active_natural_successor"
        or binding.get("driver_state_restore_kind") != "natural_succession"
        or not isinstance(reconciliation, dict)
        or reconciliation.get("status") != "available"
        or reconciliation.get("verdict") != "matched"
        or reconciliation.get("successor_match") is not True
        or reconciliation.get("title_distribution_match") is not True
        or reconciliation.get("predecessor_character_id") != predecessor_id
        or reconciliation.get("actual_successor_character_id") != successor_id
        or not isinstance(successor_binding, dict)
        or any(
            successor_binding.get(key) != before.get(key)
            for key in ("snapshot_id", "revision", "native_revision", "date_raw")
        )
    ):
        raise AgentError(
            "natural successor continuation lacks a matched same-process "
            "episode transition"
        )
    return {
        "status": "verified",
        "predecessor_character_id": predecessor_id,
        "successor_character_id": successor_id,
        "source_episode_run_id": predecessor_run_id,
        "episode_run_id": successor_run_id,
        "date_raw": binding.get("date_raw"),
        "same_campaign_frame": True,
        "ck3_command_submitted": False,
        "process_restarted": False,
        "succession_lifecycle": copy.deepcopy(succession_lifecycle),
        "reconciliation": copy.deepcopy(reconciliation),
        "predecessor_binding": _public_binding(before),
        "successor_episode_binding": _public_binding(binding),
    }


def _verify_one_generation_terminal(
    result: object,
    *,
    snapshot: dict[str, object],
    binding: dict[str, object],
    initial_episode: dict[str, object] | None,
    succession_lifecycle: dict[str, object],
) -> dict[str, object]:
    """Require a scored death settlement for the immutable episode character."""
    if succession_lifecycle.get("lifecycle") != ROGUE_ONE_LIFE:
        raise AgentError(
            "death-terminal verification requires rogue_one_life"
        )
    _verify_one_generation_binding(binding, initial_episode)
    assert isinstance(initial_episode, dict)
    expected_character_id = initial_episode["episode_character_id"]
    expected_run_id = initial_episode["episode_run_id"]
    if not isinstance(result, dict):
        raise AgentError("death-terminal returned no structured result")
    terminal_reason = result.get("terminal_reason")
    snapshot_reason = snapshot.get("one_life_terminal_reason")
    allowed_reasons = {
        "played_character_dead",
        "played_character_changed",
        "played_character_missing",
    }
    if (
        result.get("step") != "death-terminal"
        or result.get("terminal") is not True
        or terminal_reason not in allowed_reasons
        or snapshot.get("one_life_terminal") is not True
        or snapshot_reason != terminal_reason
        or result.get("episode_character_id") != expected_character_id
        or snapshot.get("episode_character_id") != expected_character_id
        or snapshot.get("episode_run_id") != expected_run_id
        or result.get("settlement_status") != "complete"
        or result.get("settlement_unavailable") is True
        or result.get("continue_as_heir_after_death") is not False
        or result.get("heir_gameplay_actions") != 0
    ):
        raise AgentError(
            "death-terminal did not satisfy the immutable no-heir settlement contract"
        )
    try:
        settlement = normalize_one_life_settlement(
            result.get("one_life_settlement")
        )
        snapshot_settlement = normalize_one_life_settlement(
            snapshot.get("one_life_settlement")
        )
        score = normalize_fixed_score(result.get("score"), "score")
    except (TypeError, ValueError) as error:
        raise AgentError(f"death-terminal settlement is malformed: {error}") from error
    if (
        not settlement_ready_for_episode(settlement, expected_character_id)
        or not settlement_ready_for_episode(
            snapshot_settlement, expected_character_id
        )
        or settlement != snapshot_settlement
        or not isinstance(settlement, dict)
        or settlement.get("final_score") != score
    ):
        raise AgentError(
            "death-terminal settlement score/source does not match the episode"
        )
    persistence = result.get("record_persistence")
    persistence_status = (
        persistence.get("status") if isinstance(persistence, dict) else None
    )
    if persistence_status not in {
        "persisted",
        "not_required_zero_score",
        "not_required_no_new_record",
    }:
        raise AgentError(
            "death-terminal record persistence was not verified or explicitly unnecessary"
        )
    if settlement.get("record_written") is True:
        if not (
            isinstance(persistence, dict)
            and persistence.get("required") is True
            and persistence_status == "persisted"
        ):
            raise AgentError(
                "death-terminal new record lacks stable persistence proof"
            )
    cross_run = result.get("cross_run_strategy")
    recorded_episode = (
        cross_run.get("recorded_episode")
        if isinstance(cross_run, dict)
        else None
    )
    successful_steps = (
        recorded_episode.get("successful_steps")
        if isinstance(recorded_episode, dict)
        else None
    )
    if (
        not isinstance(recorded_episode, dict)
        or recorded_episode.get("run_id") != expected_run_id
        or recorded_episode.get("score") != score
        or recorded_episode.get("continue_as_heir_after_death") is not False
        or recorded_episode.get("heir_gameplay_actions") != 0
        or not isinstance(successful_steps, list)
        or "death-terminal" not in successful_steps
    ):
        raise AgentError(
            "death-terminal did not persist the matching one-life episode record"
        )
    return {
        "status": "verified",
        "executed_by_this_run": True,
        "settlement_matches_episode": True,
        "no_heir_gameplay": True,
        "terminal_reason": terminal_reason,
        "terminal_kind": result.get("terminal_kind"),
        "episode_character_id": expected_character_id,
        "episode_run_id": expected_run_id,
        "date_raw": snapshot.get("date_raw"),
        "score": score,
        "one_life_settlement": settlement,
        "record_persistence": persistence,
        "recorded_episode": recorded_episode,
        "succession_lifecycle": copy.deepcopy(succession_lifecycle),
        "final_binding": _public_binding(binding),
    }


def _compact_binding(
    capabilities: dict[str, object], snapshot: dict[str, object]
) -> dict[str, object]:
    diagnostics = capabilities.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
    heartbeat = (
        diagnostics.get("last_heartbeat")
        if isinstance(diagnostics, dict)
        else None
    )
    mailbox = (
        heartbeat.get("main_thread_query_mailbox_v1")
        if isinstance(heartbeat, dict)
        else None
    )
    control = capabilities.get("native_session_control")
    played = snapshot.get("played_character")
    return {
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, dict) else None,
        "connection_generation": diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None,
        "heartbeat_sequence": heartbeat.get("sequence") if isinstance(heartbeat, dict) else None,
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "phase": snapshot.get("phase"),
        "map_ready": snapshot.get("map_ready"),
        "paused": snapshot.get("paused"),
        "played_character_id": played.get("character_id") if isinstance(played, dict) else None,
        "played_character_alive": played.get("alive") if isinstance(played, dict) else None,
        "episode_character_id": snapshot.get("episode_character_id"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "episode_identity_pending": snapshot.get("episode_identity_pending"),
        "one_life_terminal": snapshot.get("one_life_terminal"),
        "one_life_terminal_reason": snapshot.get(
            "one_life_terminal_reason"
        ),
        "one_life_settlement_status": snapshot.get(
            "one_life_settlement_status"
        ),
        "active_context": _active_context_summary(snapshot),
        "driver_state_restored": control.get("driver_state_restored") if isinstance(control, dict) else None,
        "driver_state_restore_kind": control.get("driver_state_restore_kind") if isinstance(control, dict) else None,
        "episode_binding_state": control.get("episode_binding_state") if isinstance(control, dict) else None,
        "cold_candidate_rejection": control.get("cold_candidate_rejection") if isinstance(control, dict) else None,
        "executable_sha256": hello.get("executable_sha256") if isinstance(hello, dict) else None,
        "game_adapter_id": hello.get("game_adapter_id") if isinstance(hello, dict) else None,
        "mailbox": {
            key: mailbox.get(key) if isinstance(mailbox, dict) else None
            for key in (
                "installed",
                "stop",
                "failure",
                "ready",
                "executor_submission_enabled",
                "date_raw",
                "paused",
                "executed_requests",
            )
        },
        "_semantic": {
            "active_event": snapshot.get("active_event"),
            "pending_character_interaction": snapshot.get(
                "pending_character_interaction"
            ),
            "active_wars": snapshot.get("active_wars"),
            "player_armies": snapshot.get("player_armies"),
            "played_character": snapshot.get("played_character"),
            "one_life_terminal": snapshot.get("one_life_terminal"),
            "one_life_terminal_reason": snapshot.get("one_life_terminal_reason"),
        },
    }


def _active_context_summary(snapshot: dict[str, object]) -> dict[str, object]:
    event = snapshot.get("active_event", snapshot.get("current_event"))
    pending = snapshot.get("pending_character_interaction")
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    return {
        "active_event": (
            {
                key: event.get(key)
                for key in (
                    "instance_id",
                    "definition_id",
                    "option_count",
                    "presentation_ready",
                    "semantic_decision_ready",
                )
                if key in event
            }
            if isinstance(event, dict)
            else None
        ),
        "pending_character_interaction": (
            {
                key: pending.get(key)
                for key in (
                    "instance_id",
                    "sender_character_id",
                    "auto_accept_notification",
                    "source",
                    "kind",
                    "deadline_date_raw",
                    "response_ready",
                )
                if key in pending
            }
            if isinstance(pending, dict)
            else None
        ),
        "war_ids": [
            row.get("war_id")
            for row in wars
            if isinstance(row, dict) and row.get("war_id") is not None
        ]
        if isinstance(wars, list)
        else [],
        "army_ids": [
            row.get("army_id")
            for row in armies
            if isinstance(row, dict) and row.get("army_id") is not None
        ]
        if isinstance(armies, list)
        else [],
        "terminal": snapshot.get("one_life_terminal"),
        "terminal_reason": snapshot.get("one_life_terminal_reason"),
        "settlement_status": snapshot.get("one_life_settlement_status"),
    }


def _generic_failure_kind(stage: str) -> str:
    return {
        "startup": "startup_failed",
        "readiness": "readiness_failed",
        "session": "session_exit",
        "opaque_auto_turn": "opaque_auto_turn_failed",
        "planning_or_action": "action_failed",
        "postcondition_observation": "postcondition_observation_failed",
        "postcondition": "postcondition_failed",
        "checkpoint": "checkpoint_failed",
        "checkpoint_preflight": "checkpoint_preflight_failed",
        "cleanup": "cleanup_failed",
        "bound": "wall_clock_bound_exhausted",
    }.get(stage, "action_or_postcondition_failed")


def _first_blocker_report(
    *,
    status: str,
    error: str | None,
    completion_contract: str,
    readiness: dict[str, object] | None,
    turns: list[dict[str, object]],
    checkpoints: list[dict[str, object]],
    fixed_seed: dict[str, object] | None,
    cleanup: dict[str, object],
) -> dict[str, object]:
    latest = turns[-1] if turns else None
    latest_plan = latest.get("plan") if isinstance(latest, dict) else None
    latest_before = latest.get("before") if isinstance(latest, dict) else None
    latest_after = latest.get("after") if isinstance(latest, dict) else None
    cleanup_failed_after_completion = bool(
        status in {"episode_complete", "next_episode_checkpointed"}
        and cleanup.get("ok") is not True
    )
    if status == "blocked":
        stage, kind = "planning", "planner_blocked"
    elif status == "turn_limit":
        stage, kind = "bound", "run_bound_exhausted"
    elif status == "turn_limit_terminal_pending":
        stage, kind = "postcondition", "terminal_finalization_pending"
    elif status == "turn_limit_player_decision_pending":
        stage, kind = "bound", "player_decision_checkpoint_deferred"
    elif status == "operator_stop_checkpoint_deferred":
        stage, kind = "postcondition", "pending_state_checkpoint_deferred"
    elif status == "terminal_preexisting":
        stage, kind = "readiness", "preexisting_terminal"
    elif status == "terminal_non_death_step":
        stage, kind = "planning", "non_death_terminal_step"
    elif status == "next_episode_pending":
        stage, kind = "lifecycle", "next_episode_not_started"
    elif status == "timeout":
        stage, kind = "bound", "wall_clock_bound_exhausted"
    elif status == "session_exit":
        stage, kind = "session", "session_exit"
    elif status == "starting":
        stage, kind = "startup", "startup_failed"
    elif cleanup_failed_after_completion:
        stage, kind = "cleanup", "cleanup_failed"
    elif isinstance(error, str) and "episode " in error and "changed" in error:
        stage, kind = "postcondition", "identity_violation"
    elif isinstance(error, str) and (
        "settlement" in error or "death-terminal" in error
    ):
        stage, kind = "postcondition", "settlement_invalid"
    elif status == "operator_stop":
        stage, kind = "session", "operator_stop"
    else:
        stage, kind = "action", "action_or_postcondition_failed"
    message = error
    if message is None:
        message = {
            "turn_limit": "run bound ended before the player death settlement",
            "turn_limit_terminal_pending": (
                "run bound ended on a terminal frame before death settlement"
            ),
            "turn_limit_player_decision_pending": (
                "run bound ended on a modal player decision; checkpoint was "
                "deferred and the previous durable anchor was retained"
            ),
            "operator_stop_checkpoint_deferred": (
                "operator stopped on a pending player decision or terminal "
                "state; current progress was not checkpointed"
            ),
            "terminal_non_death_step": (
                "a non-death terminal planner step ended the loop"
            ),
            "next_episode_pending": (
                "the source episode settled but the next episode was not "
                "started and checkpointed"
            ),
        }.get(status, f"run ended without qualification: {status}")
    error_type = None
    if isinstance(error, str) and ":" in error:
        error_type = error.split(":", 1)[0]
    last_checkpoint = checkpoints[-1] if checkpoints else fixed_seed
    return {
        "observed_at": utc_now(),
        "turn_index": latest.get("index") if isinstance(latest, dict) else 0,
        "stage": stage,
        "kind": kind,
        "status": status,
        "completion_contract": completion_contract,
        "message": message,
        "error_type": error_type,
        "error": error,
        "initial_episode": (
            {
                key: readiness.get(key)
                for key in (
                    "episode_character_id",
                    "episode_run_id",
                    "date_raw",
                    "played_character_alive",
                )
            }
            if isinstance(readiness, dict)
            else None
        ),
        "before": latest_before,
        "plan": latest_plan,
        "selected_step": (
            latest.get("selected_step") if isinstance(latest, dict) else None
        ),
        "result": (
            latest.get("result") if isinstance(latest, dict) else None
        ),
        "after": latest_after,
        "active_context": (
            latest_after.get("active_context")
            if isinstance(latest_after, dict)
            else (
                latest_before.get("active_context")
                if isinstance(latest_before, dict)
                else None
            )
        ),
        "last_durable_checkpoint": last_checkpoint,
        "recoverable_from_checkpoint": last_checkpoint is not None,
        "cleanup": cleanup,
    }


def _semantic_delta(
    before: dict[str, object],
    after_snapshot: dict[str, object],
    after: dict[str, object],
) -> list[str]:
    evidence: list[str] = []
    before_date = before.get("date_raw")
    after_date = after.get("date_raw")
    if isinstance(before_date, int) and isinstance(after_date, int):
        if after_date > before_date:
            evidence.append("date_advanced")
        elif after_date < before_date:
            evidence.append("date_rewound")
    before_semantic = before.get("_semantic")
    if not isinstance(before_semantic, dict):
        before_semantic = {}
    comparisons = (
        ("active_event", "event_changed"),
        (
            "pending_character_interaction",
            "pending_interaction_changed",
        ),
        ("active_wars", "war_changed"),
        ("player_armies", "army_changed"),
        ("played_character", "played_character_changed"),
        ("one_life_terminal", "terminal_changed"),
        ("one_life_terminal_reason", "terminal_reason_changed"),
    )
    for field, label in comparisons:
        if _semantic_digest(before_semantic.get(field)) != _semantic_digest(
            after_snapshot.get(field)
        ):
            evidence.append(label)
    return evidence


def _pending_interaction_lifecycle_verified(
    step: str,
    result: object,
    *,
    before: dict[str, object],
    after_snapshot: dict[str, object],
    evidence: list[str],
    plan: object = None,
) -> bool:
    """Require the typed reply result and the same old full-ID transition."""

    expected_status = _PENDING_INTERACTION_REPLY_STATUSES.get(step)
    if expected_status is None or not isinstance(result, dict):
        return False
    before_semantic = before.get("_semantic")
    before_pending = (
        before_semantic.get("pending_character_interaction")
        if isinstance(before_semantic, dict)
        else None
    )
    before_wars = (
        before_semantic.get("active_wars")
        if isinstance(before_semantic, dict)
        else None
    )
    interaction_result = result.get("interaction_result")
    remaining_present = "remaining_pending_character_interaction" in result
    remaining = result.get("remaining_pending_character_interaction")
    after_pending = after_snapshot.get("pending_character_interaction")
    old_instance_id = (
        before_pending.get("instance_id")
        if isinstance(before_pending, dict)
        else None
    )
    old_sender_id = (
        before_pending.get("sender_character_id")
        if isinstance(before_pending, dict)
        else None
    )
    remaining_instance_id = (
        remaining.get("instance_id") if isinstance(remaining, dict) else None
    )
    after_instance_id = (
        after_pending.get("instance_id")
        if isinstance(after_pending, dict)
        else None
    )
    ordinary_lifecycle_verified = bool(
        "pending_interaction_changed" in evidence
        and _valid_pending_interaction_id(old_instance_id)
        and isinstance(interaction_result, dict)
        and interaction_result.get("status") == expected_status
        and interaction_result.get("instance_id") == old_instance_id
        and interaction_result.get("sender_character_id") == old_sender_id
        and remaining_present
        and (remaining is None or isinstance(remaining, dict))
        and remaining_instance_id != old_instance_id
        and after_instance_id != old_instance_id
        and _semantic_digest(remaining) == _semantic_digest(after_pending)
        and result.get("paused") is True
        and after_snapshot.get("paused") is True
    )
    if not ordinary_lifecycle_verified:
        return False

    decision = plan.get("decision") if isinstance(plan, dict) else None
    if (
        isinstance(decision, dict)
        and decision.get("rule_id") == "grant-vassal-reject-only-v1"
    ):
        if not (
            step == "reject-pending-character-interaction"
            and decision.get("selected_action") == "reject"
        ):
            return False
        before_signature = war_termination_active_war_signature(before_wars)
        after_signature = war_termination_active_war_signature(
            after_snapshot.get("active_wars")
        )
        if (
            not isinstance(before_signature, list)
            or not isinstance(after_signature, list)
            or before_signature != after_signature
        ):
            return False
        evidence.append("grant_vassal_active_war_signature_preserved")
        return True

    call_ally_assessment = (
        decision.get("call_ally_busy_reject")
        if isinstance(decision, dict)
        else None
    )
    if (
        isinstance(decision, dict)
        and decision.get("rule_id") == "call-ally-busy-reject-v1"
    ):
        evidence_row = (
            call_ally_assessment.get("evidence")
            if isinstance(call_ally_assessment, dict)
            else None
        )
        expected_before_signature = (
            evidence_row.get("active_war_signature_before_reply")
            if isinstance(evidence_row, dict)
            else None
        )
        before_signature = war_termination_active_war_signature(before_wars)
        after_signature = war_termination_active_war_signature(
            after_snapshot.get("active_wars")
        )
        if not isinstance(call_ally_assessment, dict) or not (
            step == "reject-pending-character-interaction"
            and decision.get("selected_action") == "reject"
            and call_ally_assessment.get("status") == "ready"
        ):
            return False
        if not (
            isinstance(expected_before_signature, list)
            and expected_before_signature
            and before_signature == expected_before_signature
            and isinstance(after_signature, list)
        ):
            return False
        before_war_ids = {
            row.get("war_id")
            for row in before_signature
            if isinstance(row, dict)
        }
        after_war_ids = {
            row.get("war_id")
            for row in after_signature
            if isinstance(row, dict)
        }
        no_new_active_war = bool(
            before_war_ids
            and len(after_signature) <= len(before_signature)
            and after_war_ids.issubset(before_war_ids)
        )
        if no_new_active_war:
            evidence.append("call_ally_active_war_signature_not_increased")
        return no_new_active_war

    assessment = (
        decision.get("raiktor_inbound_white_peace")
        if isinstance(decision, dict)
        else None
    )
    if not (
        isinstance(decision, dict)
        and decision.get("rule_id") == "raiktor-inbound-white-peace-v1"
        and decision.get("selected_action") == "accept"
    ):
        return True
    war_id = assessment.get("war_id") if isinstance(assessment, dict) else None
    if (
        isinstance(war_id, bool)
        or not isinstance(war_id, int)
        or war_id <= 0
        or not isinstance(before_wars, list)
    ):
        return False
    after_wars = after_snapshot.get("active_wars")
    return bool(
        assessment.get("status") == "ready"
        and "war_changed" in evidence
        and any(
            isinstance(war, dict) and war.get("war_id") == war_id
            for war in before_wars
        )
        and isinstance(after_wars, list)
        and not any(
            isinstance(war, dict) and war.get("war_id") == war_id
            for war in after_wars
        )
    )


def _white_peace_lifecycle_verified(
    step: str,
    result: object,
    *,
    before: dict[str, object],
    after_snapshot: dict[str, object],
    evidence: list[str],
) -> bool:
    """Bind typed applied/pending status to old/full WarID presence."""
    war_id = parse_offer_white_peace_step(step)
    if war_id is None or not isinstance(result, dict):
        return False
    action = result.get("war_termination_result")
    base_fields = {
        "status",
        "war_id",
        "outcome",
        "submitted_date_raw",
        "observed_date_raw",
        "episode_run_id",
        "starting_snapshot_id",
        "observed_snapshot_id",
        "command_acknowledged",
        "war_id_absent_after_ack",
        "recipient_decision_status_raw",
        "recipient_would_accept_now",
        "casus_belli",
        "claimant_character_id",
        "target_title_ids",
        "remaining_active_war",
    }
    de_jure_fields = {
        "player_side",
        "player_relative_war_score",
        "war_duration_days",
        "recipient_ai_acceptance_raw",
    }
    if not isinstance(action, dict):
        return False
    action_fields = set(action)
    casus_belli = action.get("casus_belli")
    de_jure_variant = bool(
        isinstance(casus_belli, dict)
        and casus_belli.get("canonical_key") == _DE_JURE_NO_SAFE_ROUTE_CB
    )
    if action_fields != (
        base_fields | de_jure_fields if de_jure_variant else base_fields
    ):
        return False
    before_semantic = before.get("_semantic")
    before_wars = (
        before_semantic.get("active_wars")
        if isinstance(before_semantic, dict)
        else None
    )
    after_wars = after_snapshot.get("active_wars")
    before_war = next(
        (
            war
            for war in (
                before_wars if isinstance(before_wars, list) else []
            )
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )
    before_present = any(
        isinstance(war, dict) and war.get("war_id") == war_id
        for war in (before_wars if isinstance(before_wars, list) else [])
    )
    after_present = any(
        isinstance(war, dict) and war.get("war_id") == war_id
        for war in (after_wars if isinstance(after_wars, list) else [])
    )
    after_war = next(
        (
            war
            for war in (after_wars if isinstance(after_wars, list) else [])
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )
    status = action.get("status")
    before_played = (
        before_semantic.get("played_character")
        if isinstance(before_semantic, dict)
        else None
    )
    decision_status_raw = action.get("recipient_decision_status_raw")
    target_title_ids = action.get("target_title_ids")
    declared_target_title_ids = (
        before_war.get("targeted_title_ids")
        if isinstance(before_war, dict)
        else None
    )
    common = bool(
        before_present
        and action.get("war_id") == war_id
        and action.get("outcome") == "white_peace"
        and action.get("command_acknowledged") is True
        and action.get("episode_run_id") == before.get("episode_run_id")
        and action.get("starting_snapshot_id") == before.get("snapshot_id")
        and action.get("observed_snapshot_id")
        == after_snapshot.get("snapshot_id")
        and action.get("submitted_date_raw") == before.get("date_raw")
        and action.get("observed_date_raw")
        == after_snapshot.get("date_raw")
        and action.get("episode_run_id")
        == after_snapshot.get("episode_run_id")
        and action.get("recipient_would_accept_now") is True
        and isinstance(decision_status_raw, int)
        and not isinstance(decision_status_raw, bool)
        and decision_status_raw in {0, 1}
        and isinstance(casus_belli, dict)
        and set(casus_belli) == {"database_index", "canonical_key"}
        and isinstance(casus_belli.get("database_index"), int)
        and not isinstance(casus_belli.get("database_index"), bool)
        and casus_belli.get("database_index") >= 0
        and isinstance(target_title_ids, list)
        and bool(target_title_ids)
        and all(
            isinstance(title_id, int)
            and not isinstance(title_id, bool)
            and title_id > 0
            for title_id in target_title_ids
        )
        and target_title_ids == declared_target_title_ids
    )
    if not common:
        return False
    claim_variant = bool(
        casus_belli.get("canonical_key") == "claim_cb"
        and isinstance(before_played, dict)
        and isinstance(before_played.get("character_id"), int)
        and not isinstance(before_played.get("character_id"), bool)
        and action.get("claimant_character_id")
        == before_played.get("character_id")
    )
    de_jure_variant = bool(
        de_jure_variant
        and casus_belli.get("database_index")
        == _DE_JURE_NO_SAFE_ROUTE_CB_DATABASE_INDEX
        and action.get("claimant_character_id") is None
        and len(target_title_ids) == 1
        and isinstance(before_war, dict)
        and before_war.get("player_side") == "attacker"
        and before_war.get("player_is_primary_war_leader") is True
        and action.get("player_side") == "attacker"
        and action.get("player_relative_war_score")
        == before_war.get("player_relative_war_score")
        and isinstance(action.get("player_relative_war_score"), int)
        and not isinstance(action.get("player_relative_war_score"), bool)
        and 0 < action.get("player_relative_war_score") < 100
        and isinstance(action.get("war_duration_days"), int)
        and not isinstance(action.get("war_duration_days"), bool)
        and action.get("war_duration_days") >= _DE_JURE_NO_SAFE_ROUTE_MIN_DAYS
        and isinstance(action.get("recipient_ai_acceptance_raw"), int)
        and not isinstance(action.get("recipient_ai_acceptance_raw"), bool)
        and action.get("recipient_ai_acceptance_raw") > 0
    )
    if not claim_variant and not de_jure_variant:
        return False
    if status == "applied":
        return bool(
            not after_present
            and action.get("war_id_absent_after_ack") is True
            and action.get("remaining_active_war") is None
            and "war_changed" in evidence
        )
    if status == "submitted_pending":
        remaining = action.get("remaining_active_war")
        return bool(
            after_present
            and action.get("war_id_absent_after_ack") is False
            and isinstance(remaining, dict)
            and remaining.get("war_id") == war_id
            and _semantic_digest(remaining) == _semantic_digest(after_war)
        )
    return False


def _emergency_surrender_lifecycle_verified(
    step: str,
    result: object,
    *,
    before: dict[str, object],
    after_snapshot: dict[str, object],
    evidence: list[str],
) -> bool:
    """Require a typed ACK plus independent old-WarID presence/absence."""
    war_id = parse_surrender_war_step(step)
    action = (
        result.get("war_termination_result")
        if isinstance(result, dict)
        else None
    )
    before_semantic = before.get("_semantic")
    before_wars = (
        before_semantic.get("active_wars")
        if isinstance(before_semantic, dict)
        else None
    )
    after_wars = after_snapshot.get("active_wars")
    before_war = next(
        (
            war
            for war in (before_wars if isinstance(before_wars, list) else [])
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )
    after_war = next(
        (
            war
            for war in (after_wars if isinstance(after_wars, list) else [])
            if isinstance(war, dict) and war.get("war_id") == war_id
        ),
        None,
    )
    cb = action.get("casus_belli") if isinstance(action, dict) else None
    if not (
        isinstance(action, dict)
        and isinstance(before_war, dict)
        and action.get("war_id") == war_id
        and action.get("outcome") == "attacker_defeat"
        and action.get("command_acknowledged") is True
        and action.get("episode_run_id")
        == before.get("episode_run_id")
        == after_snapshot.get("episode_run_id")
        and action.get("starting_snapshot_id") == before.get("snapshot_id")
        and action.get("submitted_date_raw") == before.get("date_raw")
        and action.get("observed_date_raw") == before.get("date_raw")
        and action.get("recipient_would_accept_now") is True
        and action.get("recipient_auto_accept") is True
        and isinstance(cb, dict)
        and action.get("player_side") == "attacker"
        and before_war.get("player_side") == "attacker"
        and before_war.get("player_is_primary_war_leader") is True
        and action.get("player_relative_war_score")
        == before_war.get("player_relative_war_score")
    ):
        return False
    variant = action.get("surrender_variant")
    de_jure_variant = bool(
        (variant is None or variant == "de_jure_no_safe_route")
        and cb.get("canonical_key") == _DE_JURE_NO_SAFE_ROUTE_CB
        and isinstance(action.get("war_duration_days"), int)
        and action.get("war_duration_days")
        >= _DE_JURE_NO_SAFE_ROUTE_MIN_DAYS
    )
    score = action.get("player_relative_war_score")
    raiktor_variant = bool(
        variant == "raiktor_terminal_control"
        and cb.get("canonical_key") == _RAIKTOR_TERMINAL_CONTROL_CB
        and isinstance(score, int)
        and not isinstance(score, bool)
        and score == _RAIKTOR_TERMINAL_CONTROL_SCORE
        and action.get("absolute_war_scores_observable") is True
        and action.get("attacker_war_score") == score
        and action.get("defender_war_score") == -score
    )
    duration = action.get("war_duration_days")
    raiktor_long_war_variant = bool(
        variant == "raiktor_long_war_utility"
        and cb.get("canonical_key") == _RAIKTOR_TERMINAL_CONTROL_CB
        and isinstance(score, int)
        and not isinstance(score, bool)
        and score <= _RAIKTOR_LONG_WAR_SURRENDER_MAX_SCORE
        and isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration >= _RAIKTOR_LONG_WAR_SURRENDER_MIN_DAYS
        and action.get("absolute_war_scores_observable") is True
        and action.get("attacker_war_score") == score
        and action.get("defender_war_score") == -score
    )
    if not (
        de_jure_variant or raiktor_variant or raiktor_long_war_variant
    ):
        return False
    if action.get("status") == "applied":
        return bool(
            action.get("observed_snapshot_id")
            == after_snapshot.get("snapshot_id")
            and action.get("observed_date_raw")
            == after_snapshot.get("date_raw")
            and after_war is None
            and action.get("war_id_absent_after_ack") is True
            and action.get("remaining_active_war") is None
            and "war_changed" in evidence
        )
    remaining = action.get("remaining_active_war")
    if not (
        action.get("status") == "submitted_pending"
        and action.get("war_id_absent_after_ack") is False
        and isinstance(remaining, dict)
        and action.get("observed_snapshot_id") == before.get("snapshot_id")
        and _semantic_digest(remaining) == _semantic_digest(before_war)
    ):
        return False
    if isinstance(after_war, dict):
        return _semantic_digest(remaining) == _semantic_digest(after_war)
    # The executor can return its same-frame pending receipt immediately
    # before the next independent paused snapshot publishes the war removal.
    if "war_changed" not in evidence:
        return False
    evidence.append("war_termination_applied_after_pending_ack")
    return True


def _same_native_frame(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return all(
        before.get(key) == after.get(key)
        for key in (
            "bridge_pid",
            "connection_generation",
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "episode_run_id",
        )
    )


def _compact_root_query_retry(retry: object) -> dict[str, object] | None:
    if not isinstance(retry, dict):
        return None
    return {
        key: copy.deepcopy(value)
        for key, value in retry.items()
        if key not in ("starting_snapshot", "fresh_snapshot")
    }


def _retried_root_query_binding(
    driver: NativeHeadlessGameplayDriver,
    *,
    before: dict[str, object],
    retry: object,
    selected_step: str | None,
    status: object,
) -> dict[str, object] | None:
    """Anchor a successful read to its second paused frame, never skip the guard."""
    if not (
        selected_step == QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
        and status == "executed"
        and isinstance(retry, dict)
    ):
        return None
    starting = retry.get("starting_snapshot")
    fresh = retry.get("fresh_snapshot")
    if not isinstance(starting, dict) or not isinstance(fresh, dict):
        return None
    capabilities = driver.capabilities()
    starting_binding = _compact_binding(capabilities, starting)
    fresh_binding = _compact_binding(capabilities, fresh)
    if not (
        retry.get("old_snapshot_id") == starting_binding.get("snapshot_id")
        and retry.get("old_revision") == starting_binding.get("revision")
        and retry.get("old_native_revision") == starting_binding.get("native_revision")
        and retry.get("fresh_snapshot_id") == fresh_binding.get("snapshot_id")
        and retry.get("fresh_revision") == fresh_binding.get("revision")
        and retry.get("fresh_native_revision") == fresh_binding.get("native_revision")
        and isinstance(retry.get("rejection"), str)
        and "campaign-root snapshot changed or is not ready" in retry["rejection"]
        and all(
            before.get(key) == starting_binding.get(key)
            == fresh_binding.get(key)
            for key in (
                "bridge_pid", "connection_generation", "date_raw",
                "episode_run_id", "episode_character_id",
                "played_character_id",
            )
        )
        and isinstance(before.get("revision"), int)
        and before["revision"] <= starting_binding.get("revision", -1)
        and isinstance(fresh_binding.get("revision"), int)
        and fresh_binding["revision"] > starting_binding.get("revision", -1)
        and starting_binding.get("paused") is True
        and fresh_binding.get("paused") is True
        and starting_binding.get("map_ready") is True
        and fresh_binding.get("map_ready") is True
        and _semantic_delta(before, starting, starting_binding) == []
        and _semantic_delta(starting_binding, fresh, fresh_binding) == []
    ):
        return None
    return fresh_binding


def _observe_private_activity_planner_diag_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Read planner metadata on a paused frame; cost and can_start stay unknown."""
    readback = driver.query_activity_planner_diag_private_v1(
        expected_revision=before["revision"],
    )
    after = service.snapshot()
    after_actor = after.get("played_character")
    same_frame = bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and before.get("paused") is True
        and after.get("paused") is True
        and before.get("map_ready") is True
        and after.get("map_ready") is True
        and isinstance(after_actor, dict)
        and before.get("played_character_id") == after_actor.get("character_id")
        and before.get("played_character_alive") == after_actor.get("alive")
        and readback.get("queried_snapshot_id") == before.get("snapshot_id")
        and readback.get("queried_revision") == before.get("revision")
        and readback.get("queried_native_revision") == before.get("native_revision")
    )
    if not same_frame:
        raise AgentError("private activity planner read crossed its paused source frame")
    return {
        "status": "observed", "turn_index": turn_index, "same_frame": True,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "readback": copy.deepcopy(readback),
    }


_PRIVATE_ACTIVITY_FEAST_OPEN_STEP = "open-activity-feast-planner-v1-private"
_PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP = "query-activity-stage1-option-v1-private"
_PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP = "confirm-activity-feast-stage1-v1-private"
_PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP = "query-activity-feast-stage2-option-v1-private"
_PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP = "query-activity-feast-stage2-gate-v1-private"
_PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP = "query-activity-feast-stage2-location-v1-private"
_PRIVATE_ACTIVITY_STAGE2_DESTINATION_SELECT_STEP = "select-activity-feast-stage2-destination-v1-private"
_PRIVATE_ACTIVITY_COST_SLOT12_RAW_STEP = "query-activity-cost-slot12-raw-v1-private"


def _open_private_activity_feast_planner_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Open the feast planning GUI once; no activity is started or date advanced."""
    revision = before.get("native_revision")
    actor_id = before.get("played_character_id")
    if (before.get("paused") is not True
            or before.get("map_ready") is not True
            or before.get("played_character_alive") is not True
            or type(revision) is not int or revision <= 0
            or type(actor_id) is not int or actor_id <= 0
            or type(before.get("date_raw")) is not int):
        raise AgentError("private feast planner open requires a living paused actor")
    request_id = "activity-feast-open-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id,
        "step": _PRIVATE_ACTIVITY_FEAST_OPEN_STEP,
        "expected_revision": revision,
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(driver.command_timeout_seconds),
    )
    after = service.snapshot()
    after_actor = after.get("played_character")
    same_frame = bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and after.get("paused") is True
        and after.get("map_ready") is True
        and isinstance(after_actor, dict)
        and after_actor.get("character_id") == actor_id
        and after_actor.get("alive") is True
    )
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_feast_planner_open")
              if isinstance(envelope, dict) else None)
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "open_status", "native_dispatch_invoked",
            "selected_feast_verified", "widget_attached",
            "widget_visible", "planning_stage", "configured_cost_state",
            "final_can_start_state", "raw_pointer_fields_persisted",
        }
        and native.get("schema") == "activity-feast-planner-open-private-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == before["date_raw"]
        and native.get("actor_character_id") == actor_id
        and native.get("open_status") in {"opened", "already_open"}
        and type(native.get("native_dispatch_invoked")) is bool
        and native.get("selected_feast_verified") is True
        and native.get("widget_attached") is True
        and native.get("widget_visible") is True
        and type(native.get("planning_stage")) is int
        and native["planning_stage"] in {1, 2}
        and native.get("configured_cost_state") == "unknown"
        and native.get("final_can_start_state") == "unknown"
        and native.get("raw_pointer_fields_persisted") is False
        and (native.get("native_dispatch_invoked") is
             (native.get("open_status") == "opened"))
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "same_frame", "activity_feast_planner_open",
            "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_FEAST_OPEN_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is False
        and envelope.get("advertised") is False
        and envelope.get("same_frame") is True
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "gui_open_observed" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "gui_open": accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "native_receipt": copy.deepcopy(frame),
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast planner open RED: "
            + str(native.get("open_status", "missing_native_receipt")
                  if isinstance(native, dict) else frame.get("error", "missing_result")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_FEAST_OPEN_STEP,
                "status": "red",
                "accepted": False,
                "postcondition_verified": False,
                "activity_feast_planner_open": copy.deepcopy(native),
                "same_frame": same_frame,
                "native_receipt": copy.deepcopy(frame),
            },
            selected_step=_PRIVATE_ACTIVITY_FEAST_OPEN_STEP,
        )
    return observation


def _read_private_activity_feast_stage1_option_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    open_observation: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Read the selected feast option after the verified GUI open, without Confirm."""
    revision = before["native_revision"]
    actor_id = before["played_character_id"]
    opened = open_observation["native_receipt"]["result"][
        "activity_feast_planner_open"
    ]
    pre_read = service.snapshot()

    def same_paused_frame(snapshot: dict[str, object]) -> bool:
        actor = snapshot.get("played_character")
        return bool(
            all(before.get(key) == snapshot.get(key) for key in (
                "snapshot_id", "revision", "native_revision", "date_raw",
                "episode_run_id", "episode_character_id",
            ))
            and snapshot.get("paused") is True
            and snapshot.get("map_ready") is True
            and isinstance(actor, dict)
            and actor.get("character_id") == actor_id
            and actor.get("alive") is True
        )

    if (open_observation.get("gui_open") is not True
            or opened.get("planning_stage") != 1
            or not same_paused_frame(pre_read)):
        raise StepPostconditionError(
            "private feast stage-1 option read requires the opened paused frame",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP,
                "status": "red", "accepted": False,
                "postcondition_verified": False,
                "open_observation": copy.deepcopy(open_observation),
                "pre_read_frame": _public_binding(pre_read),
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP,
        )
    request_id = "activity-stage1-option-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id,
        "step": _PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP,
        "expected_revision": revision,
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(driver.command_timeout_seconds),
    )
    after = service.snapshot()
    same_frame = same_paused_frame(after)
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_stage1_option")
              if isinstance(envelope, dict) else None)
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "planning_stage", "selected_option_key",
            "selected_option_shown", "selected_option_valid",
            "can_progress_stage1", "generic_feast_confirm_ready",
            "read_only", "raw_pointer_fields_persisted",
        }
        and native.get("schema") == "activity-stage1-option-private-read-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == before["date_raw"]
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and type(native.get("planning_stage")) is int
        and native["planning_stage"] == 1
        and native.get("selected_option_key") == "feast_type_generic"
        and type(native.get("selected_option_shown")) is bool
        and type(native.get("selected_option_valid")) is bool
        and type(native.get("can_progress_stage1")) is bool
        and type(native.get("generic_feast_confirm_ready")) is bool
        and native["generic_feast_confirm_ready"] is (
            native["selected_option_shown"]
            and native["selected_option_valid"]
            and native["can_progress_stage1"]
        )
        and native.get("read_only") is True
        and native.get("raw_pointer_fields_persisted") is False
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage1_option", "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is True
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "observed" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "read_only": accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "selected_option": copy.deepcopy(native),
        "native_receipt": copy.deepcopy(frame),
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast stage-1 option read RED: "
            + str(frame.get("error", "invalid_native_readback")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP,
                "status": "red", "accepted": False,
                "postcondition_verified": False,
                "same_frame": same_frame,
                "activity_stage1_option": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE1_OPTION_READ_STEP,
        )
    return observation


def _private_activity_same_paused_frame(
    before: dict[str, object], after: dict[str, object],
) -> bool:
    actor = after.get("played_character")
    return bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and after.get("paused") is True
        and after.get("map_ready") is True
        and isinstance(actor, dict)
        and actor.get("character_id") == before.get("played_character_id")
        and actor.get("alive") is True
    )


def _confirm_private_activity_feast_stage1_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    option_observation: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Confirm only the observed feast stage-1 option; retain ambiguous receipts."""
    selected = option_observation.get("selected_option")
    pre_submit = service.snapshot()
    if (not isinstance(selected, dict)
            or option_observation.get("same_frame") is not True
            or selected.get("generic_feast_confirm_ready") is not True
            or selected.get("selected_option_key") != "feast_type_generic"
            or not _private_activity_same_paused_frame(before, pre_submit)):
        raise StepPostconditionError(
            "private feast stage-1 Confirm lacks a current legal option",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
                "status": "red", "accepted": False,
                "submitted": False, "pending": False,
                "postcondition_verified": False,
                "stage1_option": copy.deepcopy(selected),
                "pre_submit_frame": _public_binding(pre_submit),
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
        )
    revision = before["native_revision"]
    date_raw = before["date_raw"]
    actor_id = before["played_character_id"]
    request_id = "activity-stage1-confirm-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id,
        "step": _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
        "expected_revision": revision,
        "expected_date_raw": date_raw,
        "expected_actor_character_id": actor_id,
        "expected_activity_key": "activity_feast",
        "expected_option_key": "feast_type_generic",
    }
    try:
        driver.endpoint.send(request)
        frame = driver.state.wait_for_command_result(
            request_id, float(driver.command_timeout_seconds),
        )
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-1 Confirm result unresolved",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
                "status": "red", "accepted": False,
                "submitted": None, "pending": True,
                "postcondition_verified": False,
                "request_id": request_id,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
        ) from exc
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_stage1_confirm")
              if isinstance(envelope, dict) else None)
    try:
        after = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-1 Confirm post-frame unresolved",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
                "status": "red", "accepted": False,
                "submitted": (native.get("submitted")
                              if isinstance(native, dict) else None),
                "pending": True, "postcondition_verified": False,
                "native_receipt": copy.deepcopy(frame),
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
        ) from exc
    same_frame = _private_activity_same_paused_frame(before, after)
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "expected_option_key", "selected_option_key",
            "precondition_status", "selected_option_shown",
            "selected_option_valid", "can_progress_stage1",
            "generic_feast_confirm_ready", "status", "submitted",
            "stage_two_visible", "selected_option_retained",
            "planning_stage_after", "gold_before_raw", "gold_after_raw",
            "snapshot_unchanged", "activity_start_state",
            "next_turn_verified", "raw_pointer_fields_persisted", "advertised",
        }
        and native.get("schema") == "activity-stage1-confirm-private-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == date_raw
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and native.get("expected_option_key") == "feast_type_generic"
        and native.get("selected_option_key") == "feast_type_generic"
        and native.get("precondition_status") == "observed"
        and native.get("selected_option_shown") is True
        and native.get("selected_option_valid") is True
        and native.get("can_progress_stage1") is True
        and native.get("generic_feast_confirm_ready") is True
        and native.get("status") == "stage_two_verified"
        and native.get("submitted") is True
        and native.get("stage_two_visible") is True
        and native.get("selected_option_retained") is True
        and type(native.get("planning_stage_after")) is int
        and native["planning_stage_after"] == 2
        and type(native.get("gold_before_raw")) is int
        and type(native.get("gold_after_raw")) is int
        and native["gold_before_raw"] == native["gold_after_raw"]
        and native.get("snapshot_unchanged") is True
        and native.get("activity_start_state") == "not_started_immediate"
        and native.get("next_turn_verified") is False
        and native.get("raw_pointer_fields_persisted") is False
        and native.get("advertised") is False
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage1_confirm", "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is False
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "stage_two_verified" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "submitted": (native.get("submitted")
                      if isinstance(native, dict) else None),
        "pending": not accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "native_receipt": copy.deepcopy(frame),
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast stage-1 Confirm RED: "
            + str(native.get("status", frame.get("error", "invalid_receipt"))
                  if isinstance(native, dict) and isinstance(frame, dict)
                  else frame.get("error", "missing_result")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
                "status": "red", "accepted": False,
                "submitted": observation["submitted"],
                "pending": (observation["submitted"] is not False),
                "postcondition_verified": False,
                "same_frame": same_frame,
                "activity_stage1_confirm": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
        )
    return observation


def _read_private_activity_feast_stage2_option_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    confirm_observation: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Independently re-read the selected option after bounded stage-1 Confirm."""
    revision = before["native_revision"]
    date_raw = before["date_raw"]
    actor_id = before["played_character_id"]
    request_id = "activity-stage2-option-" + uuid.uuid4().hex
    confirm_receipt = copy.deepcopy(confirm_observation.get("native_receipt"))
    if (confirm_observation.get("submitted") is not True
            or confirm_observation.get("same_frame") is not True):
        raise StepPostconditionError(
            "private feast stage-2 read lacks verified Confirm",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": confirm_observation.get("submitted"),
                "pending": True, "postcondition_verified": False,
                "confirm_native_receipt": confirm_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
        )
    try:
        driver.endpoint.send({
            "type": "execute_step", "protocol_version": 1,
            "request_id": request_id,
            "step": _PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
            "expected_revision": revision,
            "expected_date_raw": date_raw,
            "expected_actor_character_id": actor_id,
            "expected_activity_key": "activity_feast",
            "expected_option_key": "feast_type_generic",
        })
        frame = driver.state.wait_for_command_result(
            request_id, float(driver.command_timeout_seconds),
        )
        after = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-2 option read unresolved after Confirm",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "postcondition_verified": False,
                "confirm_native_receipt": confirm_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
        ) from exc
    same_frame = _private_activity_same_paused_frame(before, after)
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_stage2_option")
              if isinstance(envelope, dict) else None)
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "planning_stage", "selected_option_key",
            "generic_feast_selected", "read_only",
            "raw_pointer_fields_persisted", "advertised",
        }
        and native.get("schema") == "activity-stage2-option-private-read-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == date_raw
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and type(native.get("planning_stage")) is int
        and native["planning_stage"] == 2
        and native.get("selected_option_key") == "feast_type_generic"
        and native.get("generic_feast_selected") is True
        and native.get("read_only") is True
        and native.get("raw_pointer_fields_persisted") is False
        and native.get("advertised") is False
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage2_option", "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is True
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "stage_two_observed" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "stage_two_verified": accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "selected_option": copy.deepcopy(native),
        "native_receipt": copy.deepcopy(frame),
        "confirm_native_receipt": confirm_receipt,
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast stage-2 option read RED: "
            + str(frame.get("error", "invalid_native_readback")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "postcondition_verified": False,
                "same_frame": same_frame,
                "activity_stage2_option": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
                "confirm_native_receipt": confirm_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
        )
    return observation


def _read_private_activity_feast_stage2_gate_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    confirm_observation: dict[str, object],
    option_observation: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Read the exact native stage-2 gate without progressing the planner."""
    revision = before["native_revision"]
    date_raw = before["date_raw"]
    actor_id = before["played_character_id"]
    confirm_receipt = copy.deepcopy(confirm_observation.get("native_receipt"))
    option_receipt = copy.deepcopy(option_observation.get("native_receipt"))
    if (confirm_observation.get("submitted") is not True
            or confirm_observation.get("same_frame") is not True
            or option_observation.get("stage_two_verified") is not True
            or option_observation.get("same_frame") is not True):
        raise StepPostconditionError(
            "private feast stage-2 gate lacks verified Confirm and option read",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": confirm_observation.get("submitted"),
                "pending": True, "postcondition_verified": False,
                "confirm_native_receipt": confirm_receipt,
                "stage2_option_native_receipt": option_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
        )
    request_id = "activity-stage2-gate-" + uuid.uuid4().hex
    try:
        driver.endpoint.send({
            "type": "execute_step", "protocol_version": 1,
            "request_id": request_id,
            "step": _PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
            "expected_revision": revision,
            "expected_date_raw": date_raw,
            "expected_actor_character_id": actor_id,
            "expected_activity_key": "activity_feast",
            "expected_option_key": "feast_type_generic",
        })
        frame = driver.state.wait_for_command_result(
            request_id, float(driver.command_timeout_seconds),
        )
        after = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-2 gate read unresolved after Confirm",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "postcondition_verified": False,
                "confirm_native_receipt": confirm_receipt,
                "stage2_option_native_receipt": option_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
        ) from exc
    same_frame = _private_activity_same_paused_frame(before, after)
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_stage2_gate")
              if isinstance(envelope, dict) else None)
    rows = native.get("failing_rows") if isinstance(native, dict) else None
    row_count = (native.get("configuration_row_count")
                 if isinstance(native, dict) else None)
    rows_valid = bool(
        type(row_count) is int and 0 <= row_count <= 128
        and isinstance(rows, list) and len(rows) <= row_count
        and all(
            isinstance(row, dict) and set(row) == {"index", "raw_dword"}
            and type(row.get("index")) is int and 0 <= row["index"] < row_count
            and type(row.get("raw_dword")) is int
            and 0 <= row["raw_dword"] <= 0xFFFFFFFF
            for row in rows
        )
        and len({row["index"] for row in rows}) == len(rows)
    )
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "planning_stage", "selected_option_key",
            "configuration_row_count", "failing_rows",
            "can_progress_stage2", "generic_feast_stage2_advance_ready",
            "read_only", "raw_pointer_fields_persisted", "advertised",
        }
        and native.get("schema") == "activity-stage2-gate-private-read-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == date_raw
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and type(native.get("planning_stage")) is int
        and native["planning_stage"] == 2
        and native.get("selected_option_key") == "feast_type_generic"
        and rows_valid
        and type(native.get("can_progress_stage2")) is bool
        and type(native.get("generic_feast_stage2_advance_ready")) is bool
        and native["can_progress_stage2"] is native["generic_feast_stage2_advance_ready"]
        and native.get("read_only") is True
        and native.get("raw_pointer_fields_persisted") is False
        and native.get("advertised") is False
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage2_gate", "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is True
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "stage_two_gate_observed" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "gate_observed": accepted,
        "advance_ready": native["generic_feast_stage2_advance_ready"]
        if accepted else None,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "gate": copy.deepcopy(native),
        "native_receipt": copy.deepcopy(frame),
        "confirm_native_receipt": confirm_receipt,
        "stage2_option_native_receipt": option_receipt,
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast stage-2 gate read RED: "
            + str(frame.get("error", "invalid_native_readback")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "postcondition_verified": False,
                "same_frame": same_frame,
                "activity_stage2_gate": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
                "confirm_native_receipt": confirm_receipt,
                "stage2_option_native_receipt": option_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
        )
    return observation


def _read_private_activity_feast_stage2_location_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    confirm_observation: dict[str, object],
    option_observation: dict[str, object],
    candidate_province_ids: tuple[int, ...],
    turn_index: int,
) -> dict[str, object]:
    """Read original stage-2 destination eligibility on the Confirm frame."""
    revision = before["native_revision"]
    date_raw = before["date_raw"]
    actor_id = before["played_character_id"]
    confirm_receipt = copy.deepcopy(confirm_observation.get("native_receipt"))
    option_receipt = copy.deepcopy(option_observation.get("native_receipt"))
    if (confirm_observation.get("submitted") is not True
            or confirm_observation.get("same_frame") is not True
            or option_observation.get("stage_two_verified") is not True
            or option_observation.get("same_frame") is not True):
        raise StepPostconditionError(
            "private feast stage-2 location lacks verified Confirm and option read",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": confirm_observation.get("submitted"),
                "pending": True, "postcondition_verified": False,
                "confirm_native_receipt": confirm_receipt,
                "stage2_option_native_receipt": option_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
        )
    request_id = "activity-stage2-location-" + uuid.uuid4().hex
    try:
        driver.endpoint.send({
            "type": "execute_step", "protocol_version": 1,
            "request_id": request_id,
            "step": _PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
            "expected_revision": revision,
            "expected_date_raw": date_raw,
            "expected_actor_character_id": actor_id,
            "expected_activity_key": "activity_feast",
            "expected_option_key": "feast_type_generic",
            "candidate_province_ids": list(candidate_province_ids),
        })
        frame = driver.state.wait_for_command_result(
            request_id, float(driver.command_timeout_seconds),
        )
        after = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-2 location read unresolved after Confirm",
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "postcondition_verified": False,
                "candidate_province_ids": list(candidate_province_ids),
                "confirm_native_receipt": confirm_receipt,
                "stage2_option_native_receipt": option_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
        ) from exc
    same_frame = _private_activity_same_paused_frame(before, after)
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_stage2_location")
              if isinstance(envelope, dict) else None)
    rows = native.get("configuration_rows") if isinstance(native, dict) else None
    candidates = native.get("candidates") if isinstance(native, dict) else None
    active_index = native.get("active_row_index") if isinstance(native, dict) else None
    rows_valid = bool(
        isinstance(rows, list) and len(rows) <= 128
        and all(
            isinstance(row, dict)
            and set(row) == {"index", "phase_kind", "province_id", "is_active"}
            and type(row.get("index")) is int and row["index"] == index
            and (row.get("phase_kind") is None
                 or (type(row.get("phase_kind")) is int
                     and 0 <= row["phase_kind"] <= 0x7FFFFFFF))
            and type(row.get("province_id")) is int
            and 0 <= row["province_id"] <= 0xFFFFFFFF
            and type(row.get("is_active")) is bool
            for index, row in enumerate(rows)
        )
        and (active_index is None
             or (type(active_index) is int and 0 <= active_index < len(rows)))
        and [row["index"] for row in rows if row["is_active"] is True]
        == ([] if active_index is None else [active_index])
    )
    candidates_valid = bool(
        isinstance(candidates, list)
        and len(candidates) == len(candidate_province_ids)
        and all(
            isinstance(candidate, dict)
            and set(candidate) == {"province_id", "can_select"}
            and type(candidate.get("province_id")) is int
            and candidate["province_id"] == province_id
            and type(candidate.get("can_select")) is bool
            for candidate, province_id in zip(candidates, candidate_province_ids)
        )
    )
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "planning_stage", "selected_option_key",
            "configuration_rows", "active_row_index",
            "activity_single_location_flag", "previous_planning_stage",
            "candidates", "can_progress_stage2", "read_only",
            "raw_pointer_fields_persisted", "advertised",
        }
        and native.get("schema") == "activity-stage2-location-private-read-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == date_raw
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and type(native.get("planning_stage")) is int
        and native["planning_stage"] == 2
        and native.get("selected_option_key") == "feast_type_generic"
        and rows_valid and candidates_valid
        and type(native.get("activity_single_location_flag")) is bool
        and type(native.get("previous_planning_stage")) is int
        and 0 <= native["previous_planning_stage"] <= 5
        and type(native.get("can_progress_stage2")) is bool
        and native.get("read_only") is True
        and native.get("raw_pointer_fields_persisted") is False
        and native.get("advertised") is False
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage2_location", "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is True
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "stage_two_location_observed" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "location_observed": accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "location": copy.deepcopy(native),
        "native_receipt": copy.deepcopy(frame),
        "confirm_native_receipt": confirm_receipt,
        "stage2_option_native_receipt": option_receipt,
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast stage-2 location read RED: "
            + str(frame.get("error", "invalid_native_readback")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
                "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "postcondition_verified": False,
                "same_frame": same_frame,
                "activity_stage2_location": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
                "confirm_native_receipt": confirm_receipt,
                "stage2_option_native_receipt": option_receipt,
            },
            selected_step=_PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
        )
    return observation


def _select_private_activity_feast_stage2_destination_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    location_observation: dict[str, object],
    province_id: int,
    turn_index: int,
) -> dict[str, object]:
    """Select one native-legal feast destination and retain ambiguous receipts."""
    step = _PRIVATE_ACTIVITY_STAGE2_DESTINATION_SELECT_STEP
    location = location_observation.get("location")
    candidates = location.get("candidates") if isinstance(location, dict) else None
    rows = location.get("configuration_rows") if isinstance(location, dict) else None
    pre_submit = service.snapshot()
    if (location_observation.get("location_observed") is not True
            or location_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre_submit)
            or not isinstance(location, dict)
            or location.get("planning_stage") != 2
            or location.get("activity_key") != "activity_feast"
            or location.get("selected_option_key") != "feast_type_generic"
            or location.get("activity_single_location_flag") is not True
            or location.get("previous_planning_stage") != 1
            or location.get("active_row_index") != 0
            or not isinstance(rows, list) or len(rows) != 2
            or any(row.get("province_id") != 0 for row in rows)
            or location.get("can_progress_stage2") is not False
            or not isinstance(candidates, list)
            or not any(candidate.get("province_id") == province_id
                       and candidate.get("can_select") is True
                       for candidate in candidates)):
        raise StepPostconditionError(
            "private feast stage-2 destination lacks a current native-legal candidate",
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": False, "pending": False,
                "postcondition_verified": False,
                "province_id": province_id,
                "stage2_location_native_receipt": copy.deepcopy(
                    location_observation.get("native_receipt")),
            },
            selected_step=step,
        )
    revision = before["native_revision"]
    date_raw = before["date_raw"]
    actor_id = before["played_character_id"]
    request_id = "activity-stage2-select-" + uuid.uuid4().hex
    request = {
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": revision,
        "expected_date_raw": date_raw,
        "expected_actor_character_id": actor_id,
        "expected_activity_key": "activity_feast",
        "expected_option_key": "feast_type_generic",
        "province_id": province_id,
    }
    try:
        driver.endpoint.send(request)
        frame = driver.state.wait_for_command_result(
            request_id, float(driver.command_timeout_seconds),
        )
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-2 destination result unresolved",
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": None, "pending": True,
                "postcondition_verified": False,
                "province_id": province_id, "request_id": request_id,
                "stage2_location_native_receipt": copy.deepcopy(
                    location_observation.get("native_receipt")),
            },
            selected_step=step,
        ) from exc
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_stage2_destination_select")
              if isinstance(envelope, dict) else None)
    try:
        after = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast stage-2 destination post-frame unresolved",
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": native.get("submitted") if isinstance(native, dict) else None,
                "pending": True, "postcondition_verified": False,
                "province_id": province_id, "request_id": request_id,
                "activity_stage2_destination_select": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
            },
            selected_step=step,
        ) from exc
    same_frame = _private_activity_same_paused_frame(before, after)
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "selected_option_key", "selected_province_id",
            "status", "submitted", "needs_recovery", "stage_five_visible",
            "rows_filled", "selected_option_retained", "gold_unchanged",
            "frame_unchanged", "no_activity_started", "planning_stage_before",
            "planning_stage_after", "configuration_province_ids_before",
            "configuration_province_ids_after", "player_gold_before_raw",
            "player_gold_after_raw", "read_only", "advertised",
        }
        and native.get("schema") == "activity-stage2-destination-private-action-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == date_raw
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and native.get("selected_option_key") == "feast_type_generic"
        and native.get("selected_province_id") == province_id
        and native.get("status") == "verified_stage_five"
        and native.get("submitted") is True
        and native.get("needs_recovery") is False
        and native.get("stage_five_visible") is True
        and native.get("rows_filled") is True
        and native.get("selected_option_retained") is True
        and native.get("gold_unchanged") is True
        and native.get("frame_unchanged") is True
        and native.get("no_activity_started") is True
        and native.get("planning_stage_before") == 2
        and native.get("planning_stage_after") == 5
        and native.get("configuration_province_ids_before") == [0, 0]
        and native.get("configuration_province_ids_after") == [province_id, province_id]
        and type(native.get("player_gold_before_raw")) is int
        and type(native.get("player_gold_after_raw")) is int
        and native["player_gold_before_raw"] == native["player_gold_after_raw"]
        and native.get("read_only") is False
        and native.get("advertised") is False
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_stage2_destination_select", "backend_id",
        }
        and envelope.get("step") == step
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is False
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "verified_stage_five" if accepted else "red",
        "turn_index": turn_index,
        "same_frame": same_frame,
        "province_id": province_id,
        "submitted": native.get("submitted") if isinstance(native, dict) else None,
        "pending": not accepted,
        "postcondition_verified": accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "activity_stage2_destination_select": copy.deepcopy(native),
        "native_receipt": copy.deepcopy(frame),
        "stage2_location_native_receipt": copy.deepcopy(
            location_observation.get("native_receipt")),
    }
    if not accepted:
        raise StepPostconditionError(
            "private feast stage-2 destination RED: "
            + str(native.get("status", frame.get("error", "invalid_receipt"))
                  if isinstance(native, dict) and isinstance(frame, dict)
                  else frame.get("error", "missing_result")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": observation["submitted"],
                "pending": (observation["submitted"] is not False
                            or (isinstance(native, dict)
                                and native.get("needs_recovery") is True)),
                "postcondition_verified": False,
                "same_frame": same_frame,
                "province_id": province_id,
                "activity_stage2_destination_select": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
                "stage2_location_native_receipt": copy.deepcopy(
                    location_observation.get("native_receipt")),
            },
            selected_step=step,
        )
    return observation


def _read_private_activity_feast_stage5_full_cost_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    destination_observation: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Read four native costs and final CanStart after verified destination select."""
    step = _PRIVATE_ACTIVITY_STAGE5_FULL_COST_READ_STEP
    destination_receipt = copy.deepcopy(
        destination_observation.get("native_receipt"))
    pre = service.snapshot()
    if (destination_observation.get("postcondition_verified") is not True
            or destination_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre)):
        raise StepPostconditionError(
            "private stage-5 cost read lacks verified same-frame destination",
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "destination_postcondition_verified": (
                    destination_observation.get("postcondition_verified")),
                "postcondition_verified": False,
                "destination_native_receipt": destination_receipt,
            },
            selected_step=step,
        )
    try:
        result = query_activity_stage5_feast_full_cost_private_v1(
            driver, expected_revision=pre["revision"],
            timeout_seconds=float(driver.command_timeout_seconds),
        )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private stage-5 full-cost read unresolved after destination selection",
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "destination_postcondition_verified": True,
                "postcondition_verified": False,
                "native_error": type(exc).__name__ + ": " + str(exc),
                "destination_native_receipt": destination_receipt,
            },
            selected_step=step,
        ) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and result["queried_snapshot_id"] == pre["snapshot_id"]
        and result["post_snapshot_id"] == post["snapshot_id"]
        and result["queried_native_revision"] == pre["native_revision"]
    )
    observation = {
        "status": "stage_five_full_cost_observed" if same_frame else "red",
        "turn_index": turn_index, "same_frame": same_frame,
        "read_only": True, "destination_postcondition_verified": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "full_cost": copy.deepcopy(result),
        "destination_native_receipt": destination_receipt,
    }
    if not same_frame:
        raise StepPostconditionError(
            "private stage-5 full-cost read crossed the destination frame",
            step_result={
                "step": step, "status": "red", "accepted": False,
                "submitted": True, "pending": True,
                "destination_postcondition_verified": True,
                "postcondition_verified": False,
                "full_cost": copy.deepcopy(result),
                "destination_native_receipt": destination_receipt,
            },
            selected_step=step,
        )
    return observation


def _read_private_activity_feast_guest_opinion_once(
    driver: NativeHeadlessGameplayDriver,
    *, service: GameplayBridgeService, before: dict[str, object],
    guest_character_id: int, turn_index: int,
) -> dict[str, object]:
    """Read one host relationship value without opening or changing a feast."""
    step = _PRIVATE_ACTIVITY_GUEST_OPINION_STEP
    pre = service.snapshot()
    if not _private_activity_same_paused_frame(before, pre):
        raise StepPostconditionError(
            "private feast guest opinion read crossed paused frame before query",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False}, selected_step=step)
    try:
        read = query_activity_feast_guest_opinion_private_v1(
            driver, expected_revision=pre["revision"],
            guest_character_id=guest_character_id,
            timeout_seconds=float(driver.command_timeout_seconds),
        )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast guest opinion read unresolved",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "native_error": type(exc).__name__ + ": " + str(exc)},
            selected_step=step) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and read["queried_snapshot_id"] == pre["snapshot_id"]
        and read["post_snapshot_id"] == post["snapshot_id"]
    )
    if not same_frame or read["status"] != "observed":
        raise StepPostconditionError(
            "private feast guest opinion unavailable or crossed paused frame",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "opinion_status": read["status"], "opinion_read": read},
            selected_step=step)
    return {
        "status": "guest_opinion_read", "turn_index": turn_index,
        "same_frame": True, "read_only": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "opinion_read": read,
        "opinion_status": "observed",
        "guest_character_id": guest_character_id,
        "guest_opinion_of_actor": read["guest_opinion_of_actor"],
        "decision": "hold", "formal_action_ready": False,
        "rule_membership": None, "final_invite_legal": None,
        "feast_start_ready": None,
    }


def _read_private_activity_feast_guest_candidate_once(
    driver: NativeHeadlessGameplayDriver,
    *, service: GameplayBridgeService, before: dict[str, object],
    cost_observation: dict[str, object], turn_index: int,
) -> dict[str, object]:
    """Read the native pre-invitation filter without proposing an invite."""
    step = _PRIVATE_ACTIVITY_GUEST_CANDIDATE_STEP
    pre = service.snapshot()
    if (cost_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre)):
        raise StepPostconditionError(
            "private feast guest read lacks same-frame Stage-5 cost source",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False}, selected_step=step)
    try:
        read = query_activity_feast_guest_candidate_private_v1(
            driver, expected_revision=pre["revision"],
            timeout_seconds=float(driver.command_timeout_seconds),
        )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast guest candidate read unresolved",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "native_error": type(exc).__name__ + ": " + str(exc)},
            selected_step=step) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and read["queried_snapshot_id"] == pre["snapshot_id"]
        and read["post_snapshot_id"] == post["snapshot_id"]
    )
    if not same_frame:
        raise StepPostconditionError(
            "private feast guest candidate read crossed paused frame",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False, "candidate_read": read},
            selected_step=step)
    if read["status"] not in {"observed", "no_qualified_candidate"}:
        raise StepPostconditionError(
            "private feast guest candidate source unavailable: " + read["status"],
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "candidate_status": read["status"],
                         "candidate_read": read},
            selected_step=step)
    return {
        "status": "guest_candidate_read", "turn_index": turn_index,
        "same_frame": True, "read_only": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "candidate_read": read,
        "candidate_status": read["status"],
        "native_filtered_pre_invitation": read["native_filtered_pre_invitation"],
        "final_invite_legal": None, "feast_start_ready": None,
    }


def _read_private_activity_feast_guest_route_proof_once(
    driver: NativeHeadlessGameplayDriver,
    *, service: GameplayBridgeService, before: dict[str, object],
    cost_observation: dict[str, object], turn_index: int,
) -> dict[str, object]:
    """Bind the native selected-guest and candidate proof to one Stage-5 frame."""
    step = _PRIVATE_ACTIVITY_GUEST_ROUTE_PROOF_STEP
    pre = service.snapshot()
    if (cost_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre)):
        raise StepPostconditionError(
            "private feast guest route proof lacks same-frame Stage-5 cost source",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False}, selected_step=step)
    try:
        read = query_activity_feast_guest_route_proof_private_v1(
            driver, expected_revision=pre["revision"],
            timeout_seconds=float(driver.command_timeout_seconds),
        )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast guest route proof unresolved",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "native_error": type(exc).__name__ + ": " + str(exc)},
            selected_step=step) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and read["queried_snapshot_id"] == pre["snapshot_id"]
        and read["post_snapshot_id"] == post["snapshot_id"]
    )
    if not same_frame or read["status"] != "observed":
        raise StepPostconditionError(
            "private feast guest route proof unavailable or crossed paused frame",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "proof_status": read["status"], "proof_read": read},
            selected_step=step)
    return {
        "status": "guest_route_proof_read", "turn_index": turn_index,
        "same_frame": True, "read_only": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "proof_read": read,
        "decision": "hold", "formal_action_ready": False,
        "native_guest_route_qualified": False,
    }


def _private_activity_feast_guest_target_same_source(
    first: object, repeated: object,
) -> bool:
    """Compare target content across queries, retaining refreshed diagnostics."""
    if not isinstance(first, dict) or not isinstance(repeated, dict):
        return False
    # Each normal paused return increments this observer-local count even when
    # every source and target value is unchanged. Native per-query checks stay.
    return (
        {key: value for key, value in first.items() if key != "normal_refresh_sequence"}
        == {key: value for key, value in repeated.items() if key != "normal_refresh_sequence"}
    )


def _read_private_activity_feast_guest_target_once(
    driver: NativeHeadlessGameplayDriver,
    *, service: GameplayBridgeService, before: dict[str, object],
    cost_observation: dict[str, object], target_character_id: int,
    turn_index: int,
) -> dict[str, object]:
    """Read one full CharacterID from native filtered Stage-5 groups."""
    step = _PRIVATE_ACTIVITY_GUEST_TARGET_STEP
    pre = service.snapshot()
    if (cost_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre)):
        raise StepPostconditionError(
            "private feast target lacks same-frame Stage-5 cost source",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False}, selected_step=step)
    try:
        read = query_activity_feast_guest_target_private_v1(
            driver, expected_revision=pre["revision"],
            target_character_id=target_character_id,
            timeout_seconds=float(driver.command_timeout_seconds),
        )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast target unresolved",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "native_error": type(exc).__name__ + ": " + str(exc)},
            selected_step=step) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and read["queried_snapshot_id"] == pre["snapshot_id"]
        and read["post_snapshot_id"] == post["snapshot_id"]
    )
    if not same_frame or read["status"] != "observed":
        raise StepPostconditionError(
            "private feast target unavailable or crossed paused frame",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "target_status": read["target_status"],
                         "target_read": read}, selected_step=step)
    return {
        "status": "guest_target_read", "turn_index": turn_index,
        "same_frame": True, "read_only": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "target_read": read, "target_character_id": target_character_id,
        "decision": "hold", "formal_action_ready": False,
        "native_guest_route_qualified": False,
    }


def _read_private_activity_feast_guest_rule_once(
    driver: NativeHeadlessGameplayDriver,
    *, service: GameplayBridgeService, before: dict[str, object],
    cost_observation: dict[str, object], authored_rule_key: str,
    candidate_character_id: int | None = None,
    candidate_observation: dict[str, object] | None = None,
    target_observation: dict[str, object] | None = None,
    turn_index: int,
) -> dict[str, object]:
    """Observe one category, optionally binding passive provenance to a guest."""
    step = (_PRIVATE_ACTIVITY_GUEST_RULE_PROVENANCE_STEP
            if candidate_character_id is not None
            else _PRIVATE_ACTIVITY_GUEST_RULE_QUERY_STEP)
    pre = service.snapshot()
    if (cost_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre)):
        raise StepPostconditionError(
            "private feast guest rule read lacks same-frame Stage-5 cost source",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False}, selected_step=step)
    if candidate_character_id is not None:
        target_read = (target_observation.get("target_read")
                       if isinstance(target_observation, dict) else None)
        target_bound = bool(
            isinstance(target_observation, dict)
            and target_observation.get("same_frame") is True
            and isinstance(target_read, dict)
            and target_read.get("status") == "observed"
            and target_read.get("target_character_id") == candidate_character_id
            and type(target_read.get("native_filtered_member")) is bool
        )
        candidate_read = (candidate_observation.get("candidate_read")
                          if isinstance(candidate_observation, dict) else None)
        candidate = (candidate_read.get("candidate")
                     if isinstance(candidate_read, dict) else None)
        legacy_bound = bool(
            isinstance(candidate_observation, dict)
            and candidate_observation.get("same_frame") is True
            and isinstance(candidate, dict)
            and candidate_read.get("status") == "observed"
            and candidate.get("character_id") == candidate_character_id
        )
        if not target_bound and not legacy_bound:
            raise StepPostconditionError(
                "private feast rule provenance lacks same-frame filtered candidate",
                step_result={"step": step, "status": "red", "accepted": False,
                             "postcondition_verified": False}, selected_step=step)
    try:
        if candidate_character_id is None:
            read = query_activity_feast_guest_rule_private_v1(
                driver, authored_rule_key=authored_rule_key,
                expected_revision=pre["revision"],
                timeout_seconds=float(driver.command_timeout_seconds),
            )
        else:
            read = query_activity_feast_guest_rule_provenance_private_v1(
                driver, authored_rule_key=authored_rule_key,
                candidate_character_id=candidate_character_id,
                expected_revision=pre["revision"],
                timeout_seconds=float(driver.command_timeout_seconds),
            )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private feast guest rule read unresolved",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "native_error": type(exc).__name__ + ": " + str(exc)},
            selected_step=step) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and read["queried_snapshot_id"] == pre["snapshot_id"]
        and read["post_snapshot_id"] == post["snapshot_id"]
    )
    if not same_frame:
        raise StepPostconditionError(
            "private feast guest rule read crossed paused frame",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False, "rule_read": read},
            selected_step=step)
    observed_statuses = ({"observed"} if candidate_character_id is not None
                         else {"observed_active", "observed_inactive"})
    if read["status"] not in observed_statuses:
        raise StepPostconditionError(
            "private feast guest rule source unavailable: " + str(read["status"]),
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "rule_status": read["status"], "rule_read": read},
            selected_step=step)
    return {
        "status": "guest_rule_read", "turn_index": turn_index,
        "same_frame": True, "read_only": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "rule_read": read,
        "decision": "hold", "formal_action_ready": False,
        "reason": (
            "candidate_in_active_category_final_invite_unproven"
            if candidate_character_id is not None and read["candidate_membership"] is True
            else "candidate_not_in_named_category"
            if candidate_character_id is not None
            else "category_already_active" if read["status"] == "observed_active"
            else "category_membership_and_value_unobserved"
        ),
        "candidate_category_membership": (
            read["candidate_membership"] if candidate_character_id is not None else None
        ),
        "candidate_value": None,
        "final_invite_legal": None, "feast_start_ready": None,
    }


def _read_private_activity_feast_stage5_start_once(
    driver: NativeHeadlessGameplayDriver,
    *, service: GameplayBridgeService, before: dict[str, object],
    cost_observation: dict[str, object], turn_index: int,
) -> dict[str, object]:
    """Assess native Start inputs with a same-frame peaceful budget."""
    step = _PRIVATE_ACTIVITY_STAGE5_START_INPUT_STEP
    pre = service.snapshot()
    if (cost_observation.get("same_frame") is not True
            or not _private_activity_same_paused_frame(before, pre)):
        raise StepPostconditionError(
            "private Stage-5 Start read lacks a same-frame cost source",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False}, selected_step=step)
    try:
        inputs = query_activity_feast_stage5_start_inputs_private_v1(
            driver, expected_revision=pre["revision"],
            timeout_seconds=float(driver.command_timeout_seconds),
        )
        post = service.snapshot()
    except Exception as exc:
        raise StepPostconditionError(
            "private Stage-5 Start inputs unresolved",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False,
                         "native_error": type(exc).__name__ + ": " + str(exc)},
            selected_step=step) from exc
    same_frame = bool(
        _private_activity_same_paused_frame(before, post)
        and all(pre.get(key) == post.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and inputs["queried_snapshot_id"] == pre["snapshot_id"]
        and inputs["post_snapshot_id"] == post["snapshot_id"]
    )
    if not same_frame:
        raise StepPostconditionError(
            "private Stage-5 Start inputs crossed paused frame",
            step_result={"step": step, "status": "red", "accepted": False,
                         "postcondition_verified": False, "inputs": inputs},
            selected_step=step)
    budget_observation = observe_feast_start_budget_v1(
        post, inputs, state_dir=driver.state_dir)
    policy = assess_feast_start_private_v1(
        inputs, guest=None,
        budget=(budget_observation.get("budget")
                if budget_observation["status"] == "observed" else None),
    )
    return {
        "status": "stage_five_start_assessed", "turn_index": turn_index,
        "same_frame": True, "read_only": True,
        "source_frame": _public_binding(pre),
        "post_frame": _public_binding(post),
        "inputs": inputs,
        "budget_observation": budget_observation,
        "policy_assessment": policy,
        "decision": "hold", "formal_action_ready": False,
        "decision_status": policy.get("status"),
        "decision_reason": ("formal_start_action_disabled_pending_pairing"
                            if policy.get("decision") == "start"
                            else policy.get("reason")),
        "postcondition_verified": False,
    }


def _read_private_activity_cost_slot12_raw_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    open_observation: dict[str, object] | None,
    turn_index: int,
) -> dict[str, object]:
    """Read only normal slot-12 raw aggregates; no resource semantics."""
    revision = before.get("native_revision")
    actor_id = before.get("played_character_id")

    def same_paused_frame(snapshot: dict[str, object]) -> bool:
        actor = snapshot.get("played_character")
        return bool(
            all(before.get(key) == snapshot.get(key) for key in (
                "snapshot_id", "revision", "native_revision", "date_raw",
                "episode_run_id", "episode_character_id",
            ))
            and snapshot.get("paused") is True
            and snapshot.get("map_ready") is True
            and isinstance(actor, dict)
            and actor.get("character_id") == actor_id
            and actor.get("alive") is True
        )

    if (type(revision) is not int or revision <= 0
            or type(actor_id) is not int or actor_id <= 0
            or before.get("paused") is not True
            or before.get("map_ready") is not True
            or before.get("played_character_alive") is not True
            or not same_paused_frame(service.snapshot())
            or (open_observation is not None
                and (open_observation.get("gui_open") is not True
                     or open_observation.get("same_frame") is not True))):
        raise AgentError("private activity raw cost read requires one paused feast frame")
    request_id = "activity-cost-slot12-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": _PRIVATE_ACTIVITY_COST_SLOT12_RAW_STEP,
        "expected_revision": revision,
    })
    frame = driver.state.wait_for_command_result(
        request_id, float(driver.command_timeout_seconds),
    )
    after = service.snapshot()
    same_frame = same_paused_frame(after)
    envelope = frame.get("result") if isinstance(frame, dict) else None
    native = (envelope.get("activity_cost_slot12_raw")
              if isinstance(envelope, dict) else None)
    raw = native.get("raw_aggregate_i64") if isinstance(native, dict) else None
    native_shape = bool(
        isinstance(native, dict)
        and set(native) == {
            "schema", "snapshot_revision", "date_raw", "actor_character_id",
            "activity_key", "planning_stage", "capture_sequence", "source",
            "resource_mapping", "configured_cost", "raw_aggregate_i64",
        }
        and native.get("schema") == "activity-cost-slot12-raw-private-v1"
        and native.get("snapshot_revision") == revision
        and native.get("date_raw") == before.get("date_raw")
        and native.get("actor_character_id") == actor_id
        and native.get("activity_key") == "activity_feast"
        and type(native.get("planning_stage")) is int
        and 0 <= native["planning_stage"] <= 5
        and type(native.get("capture_sequence")) is int
        and native["capture_sequence"] > 0
        and native.get("source") == "normal_slot12_return_0x10AE1AF"
        and native.get("resource_mapping") is None
        and native.get("configured_cost") is None
        and isinstance(raw, list) and len(raw) == 10
        and all(type(value) is int and -(1 << 63) <= value < (1 << 63)
                for value in raw)
    )
    accepted = bool(
        isinstance(frame, dict)
        and frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(envelope, dict)
        and set(envelope) == {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "activity_cost_slot12_raw", "backend_id",
        }
        and envelope.get("step") == _PRIVATE_ACTIVITY_COST_SLOT12_RAW_STEP
        and envelope.get("accepted") is True
        and envelope.get("status") == "available"
        and envelope.get("private_build") is True
        and envelope.get("read_only") is True
        and envelope.get("advertised") is False
        and envelope.get("backend_id") == "native-headless"
        and native_shape and same_frame
    )
    observation = {
        "status": "observed" if accepted else "red",
        "turn_index": turn_index, "same_frame": same_frame,
        "read_only": accepted,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "raw_capture": copy.deepcopy(native),
        "native_receipt": copy.deepcopy(frame),
    }
    if not accepted:
        raise StepPostconditionError(
            "private activity raw cost read RED: "
            + str(frame.get("error", "invalid_native_readback")
                  if isinstance(frame, dict) else "missing_command_result"),
            step_result={
                "step": _PRIVATE_ACTIVITY_COST_SLOT12_RAW_STEP,
                "status": "red", "accepted": False,
                "postcondition_verified": False, "same_frame": same_frame,
                "activity_cost_slot12_raw": copy.deepcopy(native),
                "native_receipt": copy.deepcopy(frame),
            },
            selected_step=_PRIVATE_ACTIVITY_COST_SLOT12_RAW_STEP,
        )
    return observation


def _observe_private_realm_law_paused_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Read current-player final law terms without changing date or law."""
    readback = driver.query_realm_law_final_terms_private_v1(
        expected_revision=before["revision"],
    )
    after = service.snapshot()
    after_actor = after.get("played_character")
    same_frame = bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and before.get("paused") is True
        and after.get("paused") is True
        and before.get("map_ready") is True
        and after.get("map_ready") is True
        and isinstance(after_actor, dict)
        and before.get("played_character_id") == after_actor.get("character_id")
        and before.get("played_character_alive") == after_actor.get("alive")
        and readback.get("queried_snapshot_id") == before.get("snapshot_id")
        and readback.get("queried_revision") == before.get("revision")
        and readback.get("queried_native_revision") == before.get("native_revision")
    )
    if not same_frame:
        raise AgentError("private realm-law read crossed its paused source frame")
    return {
        "status": "observed", "turn_index": turn_index, "same_frame": True,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "readback": copy.deepcopy(readback),
    }


def _observe_private_child_matrilineal_pending_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    pair: tuple[int, int],
    turn_index: int,
) -> dict[str, object]:
    """Cold-read one saved proposal without entering the action planner."""
    ledger = read_child_matrilineal_ledger(driver.state_dir)
    pending = ledger.get("pending")
    if (not isinstance(pending, dict) or ledger.get("resolved") is not None
            or pending.get("played_character_id") != before.get("played_character_id")
            or pending.get("episode_run_id") != before.get("episode_run_id")
            or (pending.get("heir_character_id"),
                pending.get("candidate_character_id")) != pair
            or before.get("paused") is not True
            or before.get("map_ready") is not True):
        raise AgentError("private child pending read lacks its paired paused proposal")
    result = driver.query_player_child_matrilineal_result_private_v1(
        pending=dict(pending), cold=True,
    )
    after = service.snapshot()
    after_actor = after.get("played_character")
    same_frame = bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and after.get("paused") is True and after.get("map_ready") is True
        and isinstance(after_actor, dict)
        and after_actor.get("character_id") == before.get("played_character_id")
        and after_actor.get("alive") == before.get("played_character_alive")
        and result.get("post_native_revision") == before.get("native_revision")
        and result.get("heir_character_id") == pair[0]
        and result.get("candidate_character_id") == pair[1]
    )
    if not same_frame:
        raise AgentError("private child pending read crossed its paused source frame")
    return {
        "status": "observed", "turn_index": turn_index, "same_frame": True,
        "heir_character_id": pair[0], "candidate_character_id": pair[1],
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "readback": copy.deepcopy(result),
    }


def _observe_private_active_scheme_sway_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    service: GameplayBridgeService,
    before: dict[str, object],
    target_character_id: int,
    turn_index: int,
) -> dict[str, object]:
    """Read one native final sway precondition, then verify the paused frame."""
    readback = driver.query_active_scheme_sway_target_private_v1(
        expected_revision=before["revision"],
        target_character_id=target_character_id,
    )
    after = service.snapshot()
    after_actor = after.get("played_character")
    same_frame = bool(
        all(before.get(key) == after.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id",
        ))
        and before.get("paused") is True
        and after.get("paused") is True
        and before.get("map_ready") is True
        and after.get("map_ready") is True
        and isinstance(after_actor, dict)
        and before.get("played_character_id") == after_actor.get("character_id")
        and before.get("played_character_alive") == after_actor.get("alive")
        and readback.get("queried_snapshot_id") == before.get("snapshot_id")
        and readback.get("queried_revision") == before.get("revision")
        and readback.get("queried_native_revision") == before.get("native_revision")
    )
    if not same_frame:
        raise AgentError("private sway read crossed its paused source frame")
    return {
        "status": "observed",
        "turn_index": turn_index,
        "target_character_id": target_character_id,
        "same_frame": True,
        "source_frame": _public_binding(before),
        "post_frame": _public_binding(after),
        "readback": copy.deepcopy(readback),
    }


def _observe_private_prisoner_collection_once(
    driver: NativeHeadlessGameplayDriver,
    *,
    before: dict[str, object],
    turn_index: int,
) -> dict[str, object]:
    """Read one paused frame without adding a prisoner action to the planner."""
    source_frame = _public_binding(before)
    try:
        readback = driver.query_player_prisoner_collection_private_v1(
            expected_revision=before["revision"]
        )
    except Exception as error:
        return {
            "status": "query_failed",
            "turn_index": turn_index,
            "source_frame": source_frame,
            "error_type": type(error).__name__,
            "error": str(error),
        }
    observation = {
        "status": readback.get("status"),
        "turn_index": turn_index,
        "source_frame": source_frame,
        "readback": copy.deepcopy(readback),
    }
    collection = readback.get("player_prisoner_collection")
    if not (
        isinstance(collection, dict)
        and collection.get("status") == "available"
        and collection.get("schema_version") in (4, 5)
        and isinstance(collection.get("prisoners"), list)
    ):
        return observation
    rows = collection["prisoners"]
    original_ids = [row.get("prisoner_character_id") for row in rows]
    followups = []
    # One native evaluator per mailbox. Three rows cover the observed Robert
    # scene without making a paused turn unbounded for larger collections.
    for ordinal in range(1, min(len(rows), 3)):
        try:
            additional = driver.query_player_prisoner_collection_private_v1(
                expected_revision=before["revision"], ransom_ordinal=ordinal,
            )
            other = additional.get("player_prisoner_collection")
            other_rows = other.get("prisoners") if isinstance(other, dict) else None
            if not (
                additional.get("status") == "available"
                and additional.get("queried_snapshot_id") == before.get("snapshot_id")
                and additional.get("queried_revision") == before.get("revision")
                and additional.get("queried_native_revision") == before.get("native_revision")
                and isinstance(other, dict)
                and other.get("date_raw") == before.get("date_raw")
                and other.get("played_character_id") == before.get("played_character_id")
                and isinstance(other_rows, list)
                and [row.get("prisoner_character_id") for row in other_rows] == original_ids
            ):
                raise BridgeUnavailableError("ransom quote collection or paused frame changed")
            followups.append({
                "status": "observed", "source_ordinal": ordinal,
                "prisoner_character_id": original_ids[ordinal],
                "readback": copy.deepcopy(additional),
            })
        except Exception as error:
            followups.append({
                "status": "query_failed", "source_ordinal": ordinal,
                "prisoner_character_id": original_ids[ordinal],
                "error_type": type(error).__name__, "error": str(error),
            })
            break
    observation["ransom_quote_followups"] = followups
    first_quote = rows[0].get("ransom_quote_preview") if rows else None
    observation["ransom_quote_coverage"] = (
        "complete" if len(rows) <= 3
        and (not rows or isinstance(first_quote, dict)
             and first_quote.get("unavailable_reason") != "not_evaluated")
        and all(row["status"] == "observed" for row in followups)
        else "partial"
    )
    return observation


def _turn_record(
    index: int,
    started_at: str,
    *,
    turn_class: str,
    outcome: dict[str, object],
    before: dict[str, object],
    after: dict[str, object],
    evidence: list[str],
    camera_follow: object = None,
) -> dict[str, object]:
    plan = outcome.get("plan")
    result = outcome.get("result")
    return {
        "index": index,
        "started_at": started_at,
        "finished_at": utc_now(),
        "class": turn_class,
        "ok": outcome.get("status") in {"executed", "terminal", "intercepted"},
        "status": outcome.get("status"),
        "pre_submission_revision_replans": outcome.get(
            "pre_submission_revision_replans", 0
        ),
        "read_only_query_retry": _compact_root_query_retry(
            outcome.get("read_only_query_retry")
        ),
        "selected_step": outcome.get("selected_step") or (
            plan.get("selected_step") if isinstance(plan, dict) else None
        ),
        "plan": _compact_plan(plan),
        "result": _compact_step_result(result),
        "before": _public_binding(before),
        "after": _public_binding(after),
        "camera_follow": copy.deepcopy(camera_follow),
        "evidence": evidence or [
            "same_frame_query" if turn_class == "query" else "no_semantic_delta"
        ],
    }


def _compact_plan(plan: object) -> dict[str, object] | None:
    if not isinstance(plan, dict):
        return None
    keys = (
        "phase",
        "selected_step",
        "reason",
        "decision",
        "war_id",
        "army_id",
        "postwar_disband_history_index",
        "target_province_id",
        "event_instance_id",
        "event_decision",
        "event_material_postcondition",
        "required_step",
        "required_capability",
        "required_capabilities",
        "declaration",
        "war_entry_assessment",
        "war_entry_expected_utility",
        "active_event",
        "pending_character_interaction",
        "cross_run_plan_used",
        "timeline_speed",
        "timeline_policy",
        "sentinel_mode",
        "sentinel_scope",
        "absolute_target_date_raw",
        "watch_army_ids",
        "route_subject_army_id",
        "route_target_province_id",
        "subject_army_id",
        "objective_province_id",
        "exact_war_terminal_watch",
        "council_assignment",
        "council_decision",
        "lifestyle_decision",
        "opening_first_focus_comparison",
        "lifestyle_opportunity_status",
        "lifestyle_war_observation",
        "lifestyle_deferred_war_red",
        "lifestyle_action",
        "lifestyle_pending_action",
        "lifestyle_receipt_consumed",
        "construction_private_query",
        "construction_wartime_observation",
        "construction_pending_action",
        "construction_receipt_consumed",
        "family_marriage_choice",
        "family_marriage_pending",
        "family_marriage_result_consumed",
        "family_marriage_alliance_status",
        "family_marriage_status",
        "family_marriage_outbound_pending_state",
        "family_marriage_private_diagnostic",
        "family_marriage_current_relationship",
        "family_marriage_cold_recovery",
        "child_matrilineal_legality",
        "child_matrilineal_value",
        "child_matrilineal_pending",
        "child_matrilineal_resolved",
        "child_matrilineal_cold_recovery",
        "child_matrilineal_observation",
        "child_matrilineal_deferred_war_red",
        "child_default_observation",
        "child_default_displaced_plan",
        "child_default_pending",
        "child_default_resolved",
        "child_default_cold_recovery",
        "child_default_material_recheck",
        "lifestyle_query_status",
        "lifestyle_native_error",
        "exact_active_war_set_watch",
        "maximum_omitted_state_detection_lag_days",
        "omitted_native_watch_fields",
        "terminal_journal_cursors",
        "battle_terminal_cruise_assessments",
    )
    compact = {key: plan.get(key) for key in keys if key in plan}
    opening_life = _compact_opening_lifestyle_observation(
        plan.get("initial_lifestyle_focus_existing")
    )
    if opening_life is not None:
        compact["opening_lifestyle_observation"] = opening_life
    martial = _compact_opening_martial_observation(
        plan.get("opening_lifestyle_martial_observation")
    )
    if martial is not None:
        compact["opening_lifestyle_martial_observation"] = martial
    war_exit = _compact_war_exit_decision(plan.get("war_exit_decision"))
    if war_exit is not None:
        compact["war_exit_decision"] = war_exit
    m5_joint = _compact_m5_joint_collection(plan)
    if m5_joint is not None:
        compact["m5_joint_observation"] = m5_joint
    m5_wartime = _compact_m5_wartime_observation(
        plan.get("m5_joint_wartime_observation")
    )
    if m5_wartime is not None:
        compact["m5_joint_wartime_observation"] = m5_wartime
    return compact


def _compact_opening_martial_observation(value: object) -> dict[str, object] | None:
    """Keep typed final legality and target XP without claiming an action."""
    if not isinstance(value, dict):
        return None
    result = {key: value.get(key) for key in (
        "status", "issue", "error_type", "target_key",
        "target_lifestyle_key",
    ) if key in value}
    result["read_only"] = True
    result["action_admitted"] = False
    if isinstance(value.get("native_legal"), bool):
        result["native_legal"] = value["native_legal"]
    source = value.get("source_frame")
    if isinstance(source, dict):
        result["source_frame"] = {key: source.get(key) for key in (
            "snapshot_id", "native_revision", "date_raw",
            "played_character_id", "episode_run_id",
        )}
    progress = value.get("target_lifestyle_progress")
    if isinstance(progress, dict) and progress.get("presence") in {
        "present", "unavailable",
    }:
        fields = ("presence", "source", "reason", "xp_total_raw",
                  "xp_within_level_raw", "xp_per_level",
                  "unspent_perk_points", "used_perk_points")
        result["target_lifestyle_progress"] = {
            key: progress.get(key) for key in fields if key in progress
        }
    return result


def _compact_opening_lifestyle_observation(value: object) -> dict[str, object] | None:
    """Retain bounded LIFE XP, points and observed perk legality in reports."""
    if not isinstance(value, dict) or value.get("status") != "verified_existing":
        return None
    source = value.get("source_frame")
    focus = value.get("current_focus")
    progress = value.get("current_lifestyle_progress")
    perk = value.get("perk_opportunity")
    if not all(isinstance(item, dict) for item in (source, focus, progress)):
        return None
    result: dict[str, object] = {
        "status": "verified_existing",
        "readback_source": value.get("readback_source"),
        "source_frame": {key: source.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "player_character_id",
        )},
        "current_focus": {key: focus.get(key) for key in (
            "presence", "key", "lifestyle_key",
        )},
        "current_lifestyle_progress": {key: progress.get(key) for key in (
            "presence", "lifestyle_key", "xp_total_raw",
            "xp_within_level_raw", "xp_per_level", "unspent_perk_points",
            "used_perk_points",
        )},
    }
    if isinstance(perk, dict):
        result["perk_opportunity"] = {key: perk.get(key) for key in (
            "status", "query_status", "native_error", "error_type",
            "formal_precondition_status", "candidate_scope",
            "legal_candidate_count_in_scope",
            "policy_target_final_legal", "policy_target_owned",
        )}
    else:
        result["perk_opportunity"] = {
            "status": "unknown", "query_status": "not_observed",
            "candidate_scope": None, "legal_candidate_count_in_scope": None,
            "policy_target_final_legal": None,
            "policy_target_owned": None,
        }
    traits = value.get("actor_traits")
    if isinstance(traits, dict) and traits.get("status") in {
        "available", "unavailable",
    }:
        result["actor_traits"] = {"status": traits["status"]}
        observed = traits.get("observed_keys")
        if traits["status"] == "available" and isinstance(observed, list):
            result["actor_traits"]["observed_keys"] = observed[:32]
    return result


def _compact_m5_wartime_observation(value: object) -> dict[str, object] | None:
    """Retain the bounded wartime comparison beside the selected war step."""
    if not isinstance(value, dict):
        return None
    result = {
        key: value.get(key)
        for key in ("schema", "scope", "status", "read_only", "formal_action_ready",
                    "reason") if key in value
    }
    frame = value.get("frame")
    if isinstance(frame, dict):
        result["frame"] = {
            key: frame.get(key)
            for key in ("snapshot_id", "revision", "native_revision", "date_raw",
                        "episode_run_id", "played_character_id") if key in frame
        }
    war_ids = value.get("war_ids")
    if isinstance(war_ids, list):
        result["war_ids"] = copy.deepcopy(war_ids[:8])
        result["war_count"] = len(war_ids)
        result["war_ids_truncated"] = len(war_ids) > 8
    candidate = value.get("candidate")
    if isinstance(candidate, dict):
        result["candidate"] = {
            key: copy.deepcopy(candidate[key])
            for key in ("barony_title_id", "province_id", "building_type_id",
                        "slot_index", "building_key", "stock_gold_cost_raw",
                        "gold_before_raw",
                        "authored_monthly_income_hundredths") if key in candidate
        }
    elif "candidate" in value:
        result["candidate"] = None
    missing = value.get("missing")
    if isinstance(missing, list):
        result["missing"] = copy.deepcopy(missing[:16])
        result["missing_count"] = len(missing)
        result["missing_truncated"] = len(missing) > 16
    return result


def _compact_m5_joint_collection(plan: dict[str, object]) -> dict[str, object] | None:
    """Retain the actual M5 comparison without its native source inventory."""
    collection = plan.get("m5_joint_query_only")
    if not isinstance(collection, dict):
        return None
    dispatch = collection.get("dispatch")
    if not isinstance(dispatch, dict):
        return None
    analysis = dispatch.get("analysis")
    evaluated = analysis.get("evaluated") if isinstance(analysis, dict) else None
    evaluated_rows = evaluated if isinstance(evaluated, list) else []
    row_keys = (
        "candidate_id", "domain", "reason", "source_policy",
        "gold_cost_raw", "minimum_gold_reserve_raw", "war_slot_claim",
        "army_ids", "ally_character_ids", "character_ids", "commitment_keys",
    )
    evidence_keys = (
        "authored_monthly_income_hundredths", "opinion_delta", "value",
        "predicted_outcome_if_accepted", "realm_alliance_attempt_if_accepted",
        "alliance_established", "unpriced",
    )
    selected_rows = []
    for row in evaluated_rows[:8]:
        if not isinstance(row, dict):
            continue
        compact_row = {
            key: copy.deepcopy(row[key][:8] if isinstance(row[key], list)
                               else row[key])
            for key in row_keys if key in row
        }
        compact_row["resource_claims_truncated"] = any(
            isinstance(row.get(key), list) and len(row[key]) > 8
            for key in ("army_ids", "ally_character_ids", "character_ids",
                        "commitment_keys")
        )
        evidence = row.get("evidence")
        if isinstance(evidence, dict):
            compact_row["value_evidence"] = {
                key: copy.deepcopy(evidence[key][:8]
                                   if isinstance(evidence[key], list)
                                   else evidence[key])
                for key in evidence_keys if key in evidence
            }
        selected_rows.append(compact_row)
    reservation = dispatch.get("reservation")
    reservation_keys = (
        "candidate_id", "domain", "source_policy",
        "observed_opportunity_cost", "commitments_after", "status",
    )
    frame = collection.get("frame")
    frame_keys = (
        "played_character_id", "native_revision", "date_raw",
        "snapshot_id", "revision", "episode_run_id",
    )
    candidate_ids = collection.get("collected_candidate_ids")
    domains = collection.get("collected_domains")
    commitments = (reservation.get("commitments_after")
                   if isinstance(reservation, dict) else None)
    compact_reservation = None
    if isinstance(reservation, dict):
        compact_reservation = {
            key: copy.deepcopy(reservation[key])
            for key in reservation_keys if key in reservation
            and key != "commitments_after"
        }
        if isinstance(commitments, dict):
            compact_reservation["commitments_after"] = {
                key: copy.deepcopy(commitments[key][:8]
                                   if isinstance(commitments[key], list)
                                   else commitments[key])
                for key in ("gold_raw", "pending_war_slots", "army_ids",
                            "ally_character_ids", "character_ids",
                            "commitment_keys") if key in commitments
            }
            compact_reservation["resource_claims_truncated"] = any(
                isinstance(commitments.get(key), list)
                and len(commitments[key]) > 8
                for key in ("army_ids", "ally_character_ids", "character_ids",
                            "commitment_keys")
            )
    return {
        "schema": "xar.ck3.m5-joint-formal-report.v1",
        "frame": ({key: frame.get(key) for key in frame_keys}
                  if isinstance(frame, dict) else None),
        "status": collection.get("status"),
        "producer_family_status": collection.get("producer_family_status"),
        "collected_candidate_ids": (
            copy.deepcopy(candidate_ids[:8]) if isinstance(candidate_ids, list)
            else None),
        "collected_candidate_count": (
            len(candidate_ids) if isinstance(candidate_ids, list) else None),
        "collected_domains": (
            copy.deepcopy(domains[:8]) if isinstance(domains, list) else None),
        "dispatch_status": dispatch.get("status"),
        "evaluated": selected_rows,
        "evaluated_count": len(evaluated_rows) if isinstance(evaluated, list) else None,
        "evaluated_truncated": len(evaluated_rows) > 8,
        "selection_basis": (
            copy.deepcopy(analysis.get("selection_basis"))
            if isinstance(analysis, dict) else None),
        "income_preference_applied": (
            analysis.get("income_preference_applied")
            if isinstance(analysis, dict) else None),
        "selected_candidate_id": dispatch.get("selected_candidate_id"),
        "reservation": compact_reservation,
        "selected_step": plan.get("selected_step"),
        "formal_action_ready": plan.get("m5_joint_formal_action_ready"),
    }


def _compact_war_exit_decision(value: object) -> dict[str, object] | None:
    """Keep only the same-frame ranking and action certificate in success logs."""
    if not isinstance(value, dict):
        return None
    utility = value.get("utility_comparison")
    if not isinstance(utility, dict):
        return None
    options = utility.get("options")
    comparison = utility.get("comparison")
    if not isinstance(options, dict) or not isinstance(comparison, dict):
        return None
    if any(
        not isinstance(options.get(name), dict)
        for name in ("continue", "white_peace", "surrender")
    ):
        return None
    frame = value.get("frame")
    if not isinstance(frame, dict):
        return None
    decision_keys = (
        "policy", "war_id", "recommended_outcome",
        "recommendation_certificate_sha256", "outcome_gate_authorization_sha256",
        "outcome_gate_authorized_literal", "same_frame_power_double_read",
        "action_submitted", "independent_postcondition_verified",
        "cold_restore_verified", "gen034_closed",
    )
    frame_keys = (
        "snapshot_id", "snapshot_revision", "native_revision", "date_raw",
        "connection_generation", "episode_run_id", "attacker_character_id",
        "defender_character_id", "claimant_character_id", "process_id", "war_id",
    )
    option_keys = (
        "eligible", "utility_raw", "hard_budget_breaches",
        "execution_blockers", "measured_power_relation",
        "tail_risk_penalty_raw", "uncertainty_penalty_raw",
    )
    comparison_keys = (
        "status", "eligible_options", "winning_margin_raw",
        "minimum_switch_margin_raw",
    )
    result = {
        key: copy.deepcopy(value[key]) for key in decision_keys if key in value
    }
    result["frame"] = {
        key: copy.deepcopy(frame[key]) for key in frame_keys if key in frame
    }
    result["utility_comparison"] = {
        "schema_version": utility.get("schema_version"),
        "utility_unit": utility.get("utility_unit"),
        "options": {
            name: {
                key: copy.deepcopy(options[name][key])
                for key in option_keys if key in options[name]
            }
            for name in ("continue", "white_peace", "surrender")
        },
        "comparison": {
            key: copy.deepcopy(comparison[key])
            for key in comparison_keys if key in comparison
        },
    }
    return result


def _compact_step_result(result: object) -> dict[str, object] | None:
    if not isinstance(result, dict):
        return None
    keys = (
        "step",
        "status",
        "accepted",
        "source",
        "progress_status",
        "starting_date_raw",
        "target_date_raw",
        "ending_date_raw",
        "elapsed_days",
        "requested_horizon_days",
        "timeline_speed",
        "timeline_policy",
        "sentinel_mode",
        "sentinel_scope",
        "watch_army_ids",
        "stop_kind",
        "terminal_reached",
        "one_life_terminal",
        "one_life_terminal_reason",
        "trigger_reasons",
        "sentinel_generation",
        "completed_daily_ticks",
        "intermediate_pause_count",
        "overshoot_days",
        "zero_intermediate_pause",
        "armed_tactical_daily_sentinel",
        "tactical_daily_sentinel",
        "player_decision_boundary",
        "player_decision_boundary_cancel",
        "external_pause_count",
        "player_decision_boundary_pause_count",
        "external_rich_query_count",
        "managed_failure_cleanup",
        "war_objective_hold_request",
        "war_objective_hold_admission",
        "war_objective_hold_post_stop",
        "exact_war_terminal_watch",
        "exact_active_war_set_watch",
        "maximum_omitted_state_detection_lag_days",
        "war_progress_before",
        "war_progress_after",
        "actions",
        "paused",
        "active_event",
        "pending_character_interaction",
        "final_screen",
        "snapshot_id",
        "revision",
        "native_revision",
        "bridge_pid",
        "connection_generation",
        "played_character_id",
        "played_character_alive",
        "action_request_id",
        "target_key",
        "pre_public_revision",
        "post_public_revision",
        "post_snapshot_id",
        "post_target_perk_owned",
        "post_life2_current_state",
        "postcondition_verified",
        "material_result",
        "prisoner_no_longer_held",
        "observed_player_gold_gain_raw",
        "quoted_gold_raw",
        "post_native_revision",
        "post_date_raw",
        "completion_status",
        "construction_progress_observation",
        "query_sequence",
        "read_only",
        "same_frame",
        "activity_feast_planner_open",
        "native_receipt",
        "heir_character_id",
        "candidate_character_id",
        "recipient_character_id",
        "outbound_pending_state",
        "outbound_pending_id",
        "outbound_pending_age_days",
        "outbound_pending_ai_reply_cutoff_days",
        "relationship_status",
        "played_has_recipient_alliance",
        "recipient_has_played_alliance",
        "alliance_status",
        "snapshot_revision",
        "queried_snapshot_id",
        "queried_revision",
        "queried_native_revision",
        "war_termination_query_mismatch",
        "battle_terminal_transition",
        "terminal",
        "terminal_kind",
        "terminal_reason",
        "episode_character_id",
        "episode_run_id",
        "settlement_status",
        "settlement_unavailable",
        "score",
        "continue_as_heir_after_death",
        "heir_gameplay_actions",
        "one_life_settlement",
        "record_persistence",
        "cross_run_strategy",
        "checkpoint",
        "event_selection",
        "event_material_postcondition",
        "epidemic_recovery_near_pair",
        "council_assign_councillor_ack",
        "council_assign_councillor_receipt",
        "war_action",
        "merge_postcondition",
    )
    compact = {key: result.get(key) for key in keys if key in result}
    if "interaction_result" in result:
        interaction = result.get("interaction_result")
        compact["interaction_result"] = (
            {
                key: interaction.get(key)
                for key in (
                    "status",
                    "instance_id",
                    "sender_character_id",
                )
                if key in interaction
            }
            if isinstance(interaction, dict)
            else None
        )
    if "remaining_pending_character_interaction" in result:
        remaining = result.get("remaining_pending_character_interaction")
        compact["remaining_pending_character_interaction"] = (
            {
                key: remaining.get(key)
                for key in (
                    "instance_id",
                    "sender_character_id",
                    "auto_accept_notification",
                    "source",
                )
                if key in remaining
            }
            if isinstance(remaining, dict)
            else None
        )
    if "war_termination_result" in result:
        action = result.get("war_termination_result")
        compact["war_termination_result"] = (
            {
                key: action.get(key)
                for key in (
                    "status",
                    "war_id",
                    "outcome",
                    "submitted_date_raw",
                    "observed_date_raw",
                    "episode_run_id",
                    "starting_snapshot_id",
                    "observed_snapshot_id",
                    "command_acknowledged",
                    "war_id_absent_after_ack",
                    "recipient_decision_status_raw",
                    "recipient_would_accept_now",
                    "casus_belli",
                    "claimant_character_id",
                    "target_title_ids",
                    "remaining_active_war",
                )
                if key in action
            }
            if isinstance(action, dict)
            else None
        )
    return compact


def _compact_failure_step_result(result: object) -> dict[str, object] | None:
    """Retain the one failed action's bounded postcondition evidence."""
    compact = _compact_step_result(result)
    if compact is None or not isinstance(result, dict):
        return compact
    for key in (
        "ending_date",
        "requested_horizon_days",
        "timeline_speed",
        "timeline_policy",
        "war_progress_after",
        "actions",
        "native_revision",
    ):
        if key in result:
            compact[key] = copy.deepcopy(result[key])
    for key, value in result.items():
        if isinstance(key, str) and key.startswith("contact_"):
            compact[key] = copy.deepcopy(value)
    if result.get("step") in {
        _PRIVATE_ACTIVITY_STAGE1_CONFIRM_STEP,
        _PRIVATE_ACTIVITY_STAGE2_OPTION_READ_STEP,
        _PRIVATE_ACTIVITY_STAGE2_GATE_READ_STEP,
        _PRIVATE_ACTIVITY_STAGE2_LOCATION_READ_STEP,
        _PRIVATE_ACTIVITY_STAGE2_DESTINATION_SELECT_STEP,
        _PRIVATE_ACTIVITY_STAGE5_FULL_COST_READ_STEP,
        _PRIVATE_ACTIVITY_GUEST_CANDIDATE_STEP,
        _PRIVATE_ACTIVITY_GUEST_TARGET_STEP,
        _PRIVATE_ACTIVITY_GUEST_OPINION_STEP,
        _PRIVATE_ACTIVITY_GUEST_RULE_QUERY_STEP,
        _PRIVATE_ACTIVITY_GUEST_RULE_PROVENANCE_STEP,
    }:
        for key in (
            "submitted", "pending", "same_frame", "activity_stage1_confirm",
            "activity_stage2_option", "activity_stage2_gate",
            "activity_stage2_location", "candidate_province_ids", "native_receipt",
            "activity_stage2_destination_select", "province_id",
            "stage2_location_native_receipt", "postcondition_verified",
            "confirm_native_receipt", "stage2_option_native_receipt",
            "destination_postcondition_verified", "destination_native_receipt",
            "full_cost", "native_error", "candidate_status", "candidate_read",
            "rule_status", "rule_read", "opinion_status", "opinion_read",
            "target_status", "target_read",
        ):
            if key in result:
                compact[key] = copy.deepcopy(result[key])
    return compact


def _public_binding(binding: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in binding.items() if key != "_semantic"}


def _turn_class(
    step: str | None, outcome_status: object, plan: object
) -> str:
    if outcome_status in {"terminal", "blocked"}:
        return "terminal"
    if step is None:
        return "terminal" if isinstance(plan, dict) else "gameplay"
    if step.startswith("query-") or step == PRIVATE_PRISONER_RANSOM_RECEIPT_STEP:
        return "query"
    if step == "save-checkpoint":
        return "checkpoint"
    if step in _RECOVERY_STEPS:
        return "recovery"
    if step in _TERMINAL_STEPS:
        return "terminal"
    return "gameplay"


def _eligible_advance(
    step: str,
    outcome: dict[str, object],
    evidence: list[str],
) -> bool:
    result = outcome.get("result")
    return bool(
        (step in _ELIGIBLE_ADVANCE_STEPS or is_life_advance_step(step))
        and evidence
        and isinstance(result, dict)
        and result.get("progress_status") == "postcondition"
    )


def _player_decision_pending(snapshot: object) -> bool:
    return bool(
        isinstance(snapshot, dict)
        and (
            isinstance(snapshot.get("active_event"), dict)
            or isinstance(
                snapshot.get("pending_character_interaction"), dict
            )
        )
    )


def _materialize_checkpoint(
    service: GameplayBridgeService,
    driver: NativeHeadlessGameplayDriver,
    save_dir: Path,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    timeout_seconds: float,
    poll_interval_seconds: float,
    on_checkpoint_submit: Callable[[], None] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    binding = _wait_for_readiness(
        driver,
        session_done=session_done,
        session_state=session_state,
        timeout_seconds=timeout_seconds,
        stable_seconds=0.0,
        poll_interval_seconds=poll_interval_seconds,
        cold_start_checkpoint=False,
        allow_terminal=False,
    )
    if on_checkpoint_submit is not None:
        on_checkpoint_submit()
    result = service.save_checkpoint(
        expected_revision=int(binding["revision"])
    )
    materialized_snapshot = service.snapshot()
    checkpoint = _verify_checkpoint_result(
        result,
        snapshot=materialized_snapshot,
        expected_save_dir=save_dir,
    )
    return checkpoint, materialized_snapshot


def _verify_checkpoint_result(
    result: object,
    *,
    snapshot: dict[str, object],
    expected_save_dir: Path,
) -> dict[str, object]:
    checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
    materialization = (
        result.get("materialization") if isinstance(result, dict) else None
    )
    if not isinstance(checkpoint, dict):
        raise AgentError("save-checkpoint lacks materialization metadata")
    path_value = checkpoint.get("path")
    size = checkpoint.get("size")
    digest = checkpoint.get("sha256")
    date_raw = checkpoint.get("date_raw")
    history_index = checkpoint.get("history_index")
    mtime_ns = (
        materialization.get("mtime_ns")
        if isinstance(materialization, dict)
        else None
    )
    expected_path = (expected_save_dir / "xar_checkpoint.ck3").resolve()
    if (
        not isinstance(result, dict)
        or result.get("step") != "save-checkpoint"
        or result.get("accepted") is not True
        or not isinstance(materialization, dict)
        or materialization.get("available") is not True
        or Path(str(materialization.get("save_dir", ""))).resolve()
        != expected_save_dir.resolve()
        or isinstance(mtime_ns, bool)
        or not isinstance(mtime_ns, int)
        or mtime_ns <= 0
        or checkpoint.get("status") != "saved"
        or checkpoint.get("name") != "xar_checkpoint.ck3"
        or checkpoint.get("strategy") != "native-autosave-command-v1"
        or not isinstance(path_value, str)
        or Path(path_value).resolve() != expected_path
        or isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or date_raw != snapshot.get("date_raw")
        or isinstance(history_index, bool)
        or not isinstance(history_index, int)
        or history_index < 1
        or checkpoint.get("episode_character_id")
        != snapshot.get("episode_character_id")
        or checkpoint.get("episode_run_id") != snapshot.get("episode_run_id")
        or checkpoint.get("succession_lifecycle")
        != snapshot.get("succession_lifecycle")
    ):
        raise AgentError("save-checkpoint materialization metadata is incomplete")
    try:
        actual_stat = expected_path.stat()
        actual_size = actual_stat.st_size
    except OSError as error:
        raise AgentError(
            f"materialized checkpoint is unavailable: {error}"
        ) from error
    actual_digest = _sha256_file(expected_path)
    if (
        actual_size != size
        or actual_stat.st_mtime_ns != mtime_ns
        or actual_digest != digest
    ):
        raise AgentError("materialized checkpoint differs from metadata")
    history = snapshot.get("native_command_history")
    anchor = (
        history[history_index - 1]
        if isinstance(history, list) and history_index <= len(history)
        else None
    )
    anchor_result = anchor.get("result") if isinstance(anchor, dict) else None
    anchor_checkpoint = (
        anchor_result.get("checkpoint")
        if isinstance(anchor_result, dict)
        else None
    )
    if (
        not isinstance(anchor, dict)
        or not isinstance(history, list)
        or history_index != len(history)
        or anchor.get("index") != history_index
        or anchor.get("command") != "save-checkpoint"
        or anchor.get("ok") is not True
        or not isinstance(anchor_checkpoint, dict)
        or anchor_checkpoint.get("size") != size
        or anchor_checkpoint.get("sha256") != digest
        or anchor_checkpoint.get("date_raw") != date_raw
        or anchor_checkpoint.get("succession_lifecycle")
        != checkpoint.get("succession_lifecycle")
    ):
        raise AgentError("checkpoint history anchor does not match saved bytes")
    return {
        "status": "saved",
        "path": str(expected_path),
        "size": size,
        "sha256": digest,
        "date_raw": date_raw,
        "history_index": history_index,
        "mtime_ns": mtime_ns,
        "episode_character_id": checkpoint.get("episode_character_id"),
        "episode_run_id": checkpoint.get("episode_run_id"),
        "succession_lifecycle": copy.deepcopy(
            checkpoint.get("succession_lifecycle")
        ),
    }


def _verify_pending_war_termination_checkpoint(
    checkpoint: object,
    *,
    snapshot: object,
    submitted_step: str,
) -> dict[str, object]:
    """Prove the submitted termination row immediately precedes its save."""

    history = (
        snapshot.get("native_command_history")
        if isinstance(snapshot, dict)
        else None
    )
    checkpoint_index = (
        checkpoint.get("history_index")
        if isinstance(checkpoint, dict)
        else None
    )
    action = (
        history[checkpoint_index - 2]
        if (
            isinstance(history, list)
            and type(checkpoint_index) is int
            and 2 <= checkpoint_index <= len(history)
        )
        else None
    )
    result = action.get("result") if isinstance(action, dict) else None
    termination = (
        result.get("war_termination_result")
        if isinstance(result, dict)
        else None
    )
    war_id = parse_offer_white_peace_step(submitted_step)
    expected_outcome = "white_peace"
    if war_id is None:
        war_id = parse_surrender_war_step(submitted_step)
        expected_outcome = "attacker_defeat"
    if not (
        isinstance(checkpoint, dict)
        and isinstance(snapshot, dict)
        and type(checkpoint_index) is int
        and isinstance(action, dict)
        and action.get("index") == checkpoint_index - 1
        and action.get("command") == submitted_step
        and action.get("ok") is True
        and isinstance(result, dict)
        and result.get("step") == submitted_step
        and isinstance(termination, dict)
        and type(war_id) is int
        and termination.get("status") == "submitted_pending"
        and termination.get("war_id") == war_id
        and termination.get("outcome") == expected_outcome
        and termination.get("command_acknowledged") is True
        and termination.get("war_id_absent_after_ack") is False
        and termination.get("submitted_date_raw")
        == termination.get("observed_date_raw")
        == checkpoint.get("date_raw")
        == snapshot.get("date_raw")
        and checkpoint.get("episode_run_id")
        == termination.get("episode_run_id")
        == snapshot.get("episode_run_id")
    ):
        raise AgentError(
            "submitted war termination is not immediately fenced by its "
            "paired checkpoint history anchor"
        )
    return {
        "step": submitted_step,
        "war_id": war_id,
        "outcome": expected_outcome,
        "status": "submitted_pending",
        "action_history_index": checkpoint_index - 1,
        "checkpoint_history_index": checkpoint_index,
        "date_raw": checkpoint.get("date_raw"),
        "episode_run_id": checkpoint.get("episode_run_id"),
    }


def _verify_pending_construction_checkpoint(
    checkpoint: object,
    *,
    snapshot: object,
    submitted_result: object,
    ledger: object,
) -> dict[str, object]:
    """Bind one pending native ACK and its durable request to the next save."""

    history = (
        snapshot.get("native_command_history")
        if isinstance(snapshot, dict)
        else None
    )
    checkpoint_index = (
        checkpoint.get("history_index")
        if isinstance(checkpoint, dict)
        else None
    )
    action = (
        history[checkpoint_index - 2]
        if (
            isinstance(history, list)
            and type(checkpoint_index) is int
            and 2 <= checkpoint_index <= len(history)
        )
        else None
    )
    action_result = action.get("result") if isinstance(action, dict) else None
    pending = ledger.get("pending") if isinstance(ledger, dict) else None
    played_character = (
        snapshot.get("played_character") if isinstance(snapshot, dict) else None
    )
    ack = (
        submitted_result.get("native_ack")
        if isinstance(submitted_result, dict)
        else None
    )
    request_id = (
        submitted_result.get("action_request_id")
        if isinstance(submitted_result, dict)
        else None
    )
    if not (
        isinstance(checkpoint, dict)
        and isinstance(snapshot, dict)
        and isinstance(action, dict)
        and action.get("index") == checkpoint_index - 1
        and action.get("command") == PRIVATE_CONSTRUCTION_SUBMIT_STEP
        and action.get("ok") is True
        and isinstance(action_result, dict)
        and isinstance(submitted_result, dict)
        and isinstance(pending, dict)
        and isinstance(ledger, dict)
        and ledger.get("applied") is None
        and isinstance(request_id, str)
        and request_id.startswith("construction-submit-")
        and submitted_result.get("status") == "submitted_verification_pending"
        and isinstance(ack, dict)
        and ack.get("status") == "pending_receipt"
        and ack.get("applied") is False
        and ack.get("production_native_path") is True
        and ack.get("receiver_calls") == 1
        and type(ack.get("receiver_command_sequence")) is int
        and ack["receiver_command_sequence"] > 0
        and action_result == submitted_result == pending
        and submitted_result.get("episode_run_id")
        == checkpoint.get("episode_run_id")
        == snapshot.get("episode_run_id")
        and submitted_result.get("actor_character_id")
        == (
            played_character.get("character_id")
            if isinstance(played_character, dict)
            else None
        )
        and type(submitted_result.get("pre_date_raw")) is int
        and submitted_result["pre_date_raw"]
        == checkpoint.get("date_raw")
        == snapshot.get("date_raw")
        and ack.get("proof_epoch")
        == submitted_result.get("pre_proof_epoch")
    ):
        raise AgentError(
            "pending construction ACK is not immediately fenced by its "
            "paired checkpoint and durable request ID"
        )
    return {
        "step": PRIVATE_CONSTRUCTION_SUBMIT_STEP,
        "action_request_id": request_id,
        "status": "submitted_verification_pending",
        "material_postcondition": "unobserved",
        "action_history_index": checkpoint_index - 1,
        "checkpoint_history_index": checkpoint_index,
        "date_raw": checkpoint.get("date_raw"),
        "episode_run_id": checkpoint.get("episode_run_id"),
    }


def _verify_pending_family_marriage_checkpoint(
    checkpoint: object, *, snapshot: object, submitted_result: object,
    ledger: object, expected_step: str = PRIVATE_FAMILY_MARRIAGE_SUBMIT_STEP,
) -> dict[str, object]:
    """Keep the ACK, durable pending identity and game save on one turn."""
    pending = ledger.get("pending") if isinstance(ledger, dict) else None
    played = snapshot.get("played_character") if isinstance(snapshot, dict) else None
    if not (isinstance(checkpoint, dict) and isinstance(snapshot, dict)
            and isinstance(submitted_result, dict)
            and isinstance(pending, dict)
            and pending == submitted_result
            and pending.get("submission_state") == "receipt_pending"
            and pending.get("status") == "receipt_pending"
            and pending.get("material_result") is False
            and pending.get("episode_run_id") == checkpoint.get("episode_run_id")
            == snapshot.get("episode_run_id")
            and pending.get("source_date_raw") == checkpoint.get("date_raw")
            == snapshot.get("date_raw")
            and (expected_step != PRIVATE_CHILD_MATRILINEAL_SUBMIT_STEP
                 or pending.get("matrilineal_option_selected") is True)
            and (expected_step != PRIVATE_CHILD_DEFAULT_SUBMIT_STEP
                 or pending.get("matrilineal_option_selected") is False)
            and isinstance(played, dict)
            and pending.get("played_character_id") == played.get("character_id")):
        raise AgentError("first-heir marriage ACK lacks a paired pending checkpoint")
    return {"step": expected_step,
            "status": "receipt_pending", "material_postcondition": "unobserved",
            "heir_character_id": pending["heir_character_id"],
            "candidate_character_id": pending["candidate_character_id"],
            **({"recipient_character_id": pending["recipient_character_id"]}
               if type(pending.get("recipient_character_id")) is int
               and pending["recipient_character_id"] > 0 else {}),
            "date_raw": checkpoint["date_raw"],
            "episode_run_id": checkpoint["episode_run_id"],
            **({"matrilineal_option_selected": True}
               if expected_step == PRIVATE_CHILD_MATRILINEAL_SUBMIT_STEP
               and pending.get("matrilineal_option_selected") is True else {}),
            **({"matrilineal_option_selected": False}
               if expected_step == PRIVATE_CHILD_DEFAULT_SUBMIT_STEP
               and pending.get("matrilineal_option_selected") is False else {})}


def _cleanup_report(
    session_report: object,
    *,
    session_error: object,
    driver_closed: bool,
    elapsed_seconds: float,
) -> dict[str, object]:
    shutdown = (
        session_report.get("shutdown")
        if isinstance(session_report, dict)
        else None
    )
    ok = bool(
        session_error is None
        and isinstance(session_report, dict)
        and session_report.get("ok") is True
        and session_report.get("exit_reason") == "stop"
        and isinstance(shutdown, dict)
        and shutdown.get("ok") is True
        and shutdown.get("tree_gone") is True
        and shutdown.get("cleanup_proven") is True
        and driver_closed
    )
    return {
        "elapsed_seconds": elapsed_seconds,
        "session_exit_reason": (
            session_report.get("exit_reason")
            if isinstance(session_report, dict)
            else None
        ),
        "session_report_ok": (
            session_report.get("ok")
            if isinstance(session_report, dict)
            else False
        ),
        "shutdown_ok": shutdown.get("ok") if isinstance(shutdown, dict) else False,
        "tree_gone": shutdown.get("tree_gone") if isinstance(shutdown, dict) else False,
        "cleanup_proven": shutdown.get("cleanup_proven") if isinstance(shutdown, dict) else False,
        "driver_closed": driver_closed,
        "reason": session_error,
        "ok": ok,
    }


def _compact_session_report(report: object) -> dict[str, object] | None:
    if not isinstance(report, dict):
        return None
    return {
        key: report.get(key)
        for key in (
            "kind",
            "mode",
            "pipe",
            "pid",
            "started_at",
            "finished_at",
            "elapsed_seconds",
            "exit_reason",
            "process_exit_code",
            "restart_count",
            "ok",
        )
    }


def _identity(
    config: NativeBridgeLaunchConfig,
    readiness: dict[str, object] | None,
    spec: EnvironmentSpec,
) -> dict[str, object]:
    result: dict[str, object] = {
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "bridge_dll": {
            "path": str(config.dll_path),
            "sha256": _sha256_file(config.dll_path),
        },
        "bridge_injector": {
            "path": str(config.injector_path),
            "sha256": _sha256_file(config.injector_path),
        },
        "ck3_executable_sha256": (
            readiness.get("executable_sha256")
            if isinstance(readiness, dict)
            else None
        ),
        "game_adapter_id": (
            readiness.get("game_adapter_id")
            if isinstance(readiness, dict)
            else None
        ),
    }
    manifest_path = getattr(spec, "manifest_path", None)
    if isinstance(manifest_path, Path) and manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            mod = manifest.get("mod") if isinstance(manifest, dict) else None
            result["production_tree_sha256"] = (
                mod.get("production_tree_sha256")
                if isinstance(mod, dict)
                else None
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            result["production_tree_sha256"] = None
    return result


def _premature_session_exit(session_state: dict[str, object]) -> str:
    error = session_state.get("error")
    report = session_state.get("report")
    if error is not None:
        return f"managed native-session exited with error: {error}"
    if isinstance(report, dict):
        return (
            "managed native-session exited before auto-run stop: "
            f"reason={report.get('exit_reason')!r}, "
            f"code={report.get('process_exit_code')!r}"
        )
    return "managed native-session exited without a report"


def _semantic_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("ascii")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AgentError(f"{name} must be a positive integer")
    return value


def _route_contact_speed(
    value: object, *, allow_high_speed_ab: bool
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > 5
    ):
        raise AgentError(
            "route_contact_timeline_speed must be an integer from 1 through 5"
        )
    if value > 3 and allow_high_speed_ab is not True:
        raise AgentError(
            "route_contact_timeline_speed 4..5 is a targeted A/B arm; "
            "set allow_route_contact_high_speed_ab=True explicitly"
        )
    return value


def _valid_pending_interaction_id(value: object) -> bool:
    try:
        normalize_pending_interaction_id(value)
    except ValueError:
        return False
    return True


def _positive_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) <= 0
    ):
        raise AgentError(f"{name} must be finite and positive")
    return float(value)


def _nonnegative_seconds(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0
    ):
        raise AgentError(f"{name} must be finite and nonnegative")
    return float(value)
