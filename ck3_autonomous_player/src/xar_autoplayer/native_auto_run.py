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
from .bridge.pending_character_interaction_context_contract import (
    normalize_pending_interaction_id,
)
from .bridge.council_assign_councillor_action_contract import (
    ASSIGN_COUNCILLOR_V1_STEP,
)
from .lifestyle_formal_consumer import RECEIPT_STEP as PRIVATE_LIFESTYLE_RECEIPT_STEP
from .bridge.service import GameplayBridgeService
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
from .errors import AgentError
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
    allow_private_faction_gift_formal_trial: bool = False,
    private_faction_round_id: str | None = None,
    succession_lifecycle: str = ROGUE_ONE_LIFE,
    ordinary_campaign_no_pact: bool = False,
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
        allow_private_faction_gift_formal_trial is True
        and completion_contract != "bounded"
    ):
        raise AgentError(
            "private faction gift trial only admits a bounded contract"
        )
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
            **ordinary_succession_driver_options,
        )
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
            # GameplayBridgeService.auto_turn() owns planning and execution in
            # one call.  Until it returns a typed step, an exception may have
            # occurred after a planner-selected save already overwrote the
            # canonical checkpoint path.
            current_attempt["stage"] = "opaque_auto_turn"
            pre_submission_revision_replans = 0
            while True:
                try:
                    outcome = (
                        service.auto_turn(before_submit=before_submit)
                        if before_submit is not None
                        else service.auto_turn()
                    )
                    break
                except PreSubmissionRevisionMismatchError as error:
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
            evidence = _semantic_delta(before, after_snapshot, after)
            if (
                isinstance(merge_observation, dict)
                and merge_observation.get("status") == "applied"
            ):
                evidence.append(
                    "army_merge_source_removed_independent_paused_frame"
                )
            if step == PRIVATE_LIFESTYLE_RECEIPT_STEP:
                receipt = outcome.get("result")
                if not (
                    isinstance(receipt, dict)
                    and receipt.get("status") == "applied"
                    and receipt.get("postcondition_verified") is True
                    and receipt.get("post_target_perk_owned") is True
                    and receipt.get("post_snapshot_id")
                    == after_snapshot.get("snapshot_id")
                    and receipt.get("post_public_revision")
                    == after_snapshot.get("revision")
                    and receipt.get("episode_run_id")
                    == after_snapshot.get("episode_run_id")
                ):
                    capture_first_failure(
                        stage="lifestyle_receipt",
                        kind="lifestyle_material_postcondition_failed",
                        message="the private HasPerk receipt lost its independent published frame",
                    )
                    raise AgentError(
                        "private LIFE receipt did not match the next paused game frame"
                    )
                evidence.append("lifestyle_has_perk_independent_later_frame")
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
                )
            )
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
                evidence or not _same_native_frame(before, after)
            ):
                capture_first_failure(
                    stage="postcondition",
                    kind="read_only_query_changed_frame",
                    message="read-only native query changed its paused semantic frame",
                )
                raise AgentError(
                    "read-only native query changed its paused semantic frame"
                )
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

        # A bounded production run must not knowingly discard a visible tail.
        # Queries never dirty this tail, and terminal/unknown frames are never
        # forced through a save operation.
        if status == "operator_stop_requested" and (
            terminal_pending or modal_decision_pending
        ):
            status = "operator_stop_checkpoint_deferred"
        final_checkpoint_needed = (
            status == "operator_stop_requested"
            or (status == "turn_limit" and dirty_gameplay_since_checkpoint)
        )
        if final_checkpoint_needed:
            last_after = turns[-1].get("after") if turns else readiness
            final_phase = (
                "operator_stop_checkpoint"
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
        qualified = bool(
            primary_error is None
            and status in {"turn_limit", "episode_complete"}
            and visible_gameplay_turns > 0
            and (
                status != "episode_complete" or terminal_proof is not None
            )
            and cleanup.get("ok") is True
        )
    candidate_intercept_qualified = bool(
        before_submit is not None
        and status == "candidate_terminal_intercepted"
        and candidate_interception is not None
        and after_intercept is None
        and checkpoints
        and primary_error is None
        and cleanup.get("ok") is True
    )
    candidate_resolved = bool(
        before_submit is not None
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
            else outcome
        ),
        "ok": qualified,
        "completion_contract": completion_contract,
        "succession_lifecycle": copy.deepcopy(
            succession_lifecycle_binding
        ),
        "cold_start_checkpoint": cold_start_checkpoint,
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


def _turn_record(
    index: int,
    started_at: str,
    *,
    turn_class: str,
    outcome: dict[str, object],
    before: dict[str, object],
    after: dict[str, object],
    evidence: list[str],
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
        "lifestyle_action",
        "lifestyle_pending_action",
        "lifestyle_receipt_consumed",
        "lifestyle_query_status",
        "lifestyle_native_error",
        "exact_active_war_set_watch",
        "maximum_omitted_state_detection_lag_days",
        "omitted_native_watch_fields",
        "terminal_journal_cursors",
        "battle_terminal_cruise_assessments",
    )
    compact = {key: plan.get(key) for key in keys if key in plan}
    war_exit = _compact_war_exit_decision(plan.get("war_exit_decision"))
    if war_exit is not None:
        compact["war_exit_decision"] = war_exit
    return compact


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
        "postcondition_verified",
        "query_sequence",
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
    if step.startswith("query-"):
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
