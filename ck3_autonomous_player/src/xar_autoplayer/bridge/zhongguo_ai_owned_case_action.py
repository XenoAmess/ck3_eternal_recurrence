"""MCP-first action cell for one AI-owned ZhongGuo B1 case.

The mod's authorized AI-manager route is deliberately not a player command.
The only gameplay action this helper submits is a bounded ``life-advance``.
Business completion is accepted exclusively from a fresh paused
``query-zhongguo-ai-owned-case-snapshot-v1`` response containing the closed
``mechanism_039 / roster_lock`` operation and its joined receipt.  A timeline
ACK is therefore evidence that time was advanced, never evidence that the AI
manager performed its duty.

No OCR, screen coordinates, event selection, debug decision, or test UI is
used here.  If a player-visible event interrupts the timeline, its identity is
queried through the native current-event provider and returned as a blocker.
The caller may resolve that interruption under a separate policy and invoke
this helper again.
"""

from __future__ import annotations

import copy
from typing import Protocol

from .event_contract import action_step_set
from .zhongguo_ai_owned_case_snapshot_contract import (
    QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY,
    ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1,
    validate_ai_owned_case_request_nonce_v1,
)


RAW_HOURS_PER_DAY = 24
DEFAULT_MAX_ADVANCE_STEPS = 370
DEFAULT_MAX_ELAPSED_DAYS = 370
MAX_BOUNDED_ADVANCE_STEPS = 1_100
MAX_BOUNDED_ELAPSED_DAYS = 1_100
_TIER_KEYS = {
    3: "duchy",
    4: "kingdom",
    5: "empire",
    6: "hegemony",
}


class AiOwnedCaseActionService(Protocol):
    """Narrow service surface used by the action cell."""

    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def query_zhongguo_ai_owned_case_snapshot_v1(
        self,
        owner_character_id: int,
        subject_character_id: int,
        request_nonce: str,
        *,
        expected_revision: int | None = None,
    ) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self,
        event_instance_id: int,
        *,
        expected_revision: int,
    ) -> dict[str, object]: ...


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive signed int32")
    return value


def _positive_bound(value: object, name: str, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer in 1..{maximum}")
    return value


def _nonce(prefix: str, suffix: str) -> str:
    return validate_ai_owned_case_request_nonce_v1(f"{prefix}.{suffix}")


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _typed_value(group: object, key: str) -> object | None:
    if not isinstance(group, dict):
        return None
    field = group.get(key)
    if not isinstance(field, dict) or field.get("status") != "available":
        return None
    if field.get("unavailable_reason") is not None:
        return None
    return field.get("value")


def _snapshot_binding(snapshot: object) -> tuple[dict[str, object] | None, str | None]:
    if not isinstance(snapshot, dict):
        return None, "snapshot_not_an_object"
    revision = _integer(snapshot.get("revision"))
    native_revision = _integer(snapshot.get("native_revision"))
    date_raw = _integer(snapshot.get("date_raw"))
    snapshot_id = snapshot.get("snapshot_id")
    played_character = snapshot.get("played_character")
    played_character_id = (
        _integer(played_character.get("character_id"))
        if isinstance(played_character, dict)
        else None
    )
    if snapshot.get("paused") is not True:
        return None, "snapshot_not_paused"
    if snapshot.get("map_ready") is not True:
        return None, "map_not_ready"
    if revision is None or revision < 0:
        return None, "public_revision_unavailable"
    if native_revision is None or native_revision < 1:
        return None, "native_revision_unavailable"
    if date_raw is None:
        return None, "date_raw_unavailable"
    if not isinstance(snapshot_id, str) or not snapshot_id:
        return None, "snapshot_id_unavailable"
    if played_character_id is None or played_character_id < 1:
        return None, "played_character_unavailable"
    active_event = snapshot.get("active_event")
    event_instance_id = (
        _integer(active_event.get("instance_id"))
        if isinstance(active_event, dict)
        else None
    )
    return {
        "snapshot_id": snapshot_id,
        "revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "paused": True,
        "map_ready": True,
        "played_character_id": played_character_id,
        "active_event_instance_id": event_instance_id,
    }, None


def _provider_observation(
    response: object,
    *,
    owner_character_id: int,
    subject_character_id: int,
) -> dict[str, object]:
    """Classify one already-normalized public provider response."""

    observation: dict[str, object] = {
        "classification": "blocked",
        "reason": "provider_response_not_an_object",
        "case_identity": None,
        "receipt_signature": None,
        "response": copy.deepcopy(response),
    }
    if not isinstance(response, dict):
        return observation

    status = response.get("status")
    if status == "unavailable":
        reason = response.get("unavailable_reason")
        observation["classification"] = (
            "pending" if reason == "case_not_found" else "blocked"
        )
        observation["reason"] = reason
        return observation
    if status != "available" or response.get("unavailable_reason") is not None:
        observation["reason"] = "provider_status_invalid"
        return observation

    binding = response.get("binding")
    if not (
        isinstance(binding, dict)
        and binding.get("owner_character_id") == owner_character_id
        and binding.get("subject_character_id") == subject_character_id
        and binding.get("paused") is True
    ):
        observation["reason"] = "provider_binding_mismatch"
        return observation

    readiness = response.get("readiness")
    if not isinstance(readiness, dict) or readiness.get("ready") is not True:
        observation["reason"] = "provider_not_ready"
        return observation

    eligibility = response.get("owner_eligibility")
    tier_raw = _typed_value(eligibility, "primary_title_tier_raw")
    eligibility_expected = {
        "owner_character_id": owner_character_id,
        "owner_alive": True,
        "owner_is_ai": True,
        "government_key": "celestial_government",
        "subject_immediate_liege_character_id": owner_character_id,
        "subject_is_direct_subject": True,
        "authorized": True,
    }
    for key, expected in eligibility_expected.items():
        if _typed_value(eligibility, key) != expected:
            observation["reason"] = f"owner_eligibility_mismatch:{key}"
            return observation
    if (
        isinstance(tier_raw, bool)
        or not isinstance(tier_raw, int)
        or tier_raw not in _TIER_KEYS
        or _typed_value(eligibility, "primary_title_tier_key")
        != _TIER_KEYS[tier_raw]
    ):
        observation["reason"] = "owner_not_landed_celestial_duke_plus"
        return observation

    route = response.get("route")
    route_expected = {
        "kind": ZHONGGUO_AI_OWNED_CASE_BACKGROUND_ROUTE_V1,
        "visible_event_allowed": False,
        "owner_is_ai": True,
        "manager_eligible": True,
        "direct_subject_eligible": True,
    }
    for key, expected in route_expected.items():
        if _typed_value(route, key) != expected:
            observation["reason"] = f"background_route_mismatch:{key}"
            return observation

    case = response.get("case")
    if (
        _typed_value(case, "owner_character_id") != owner_character_id
        or _typed_value(case, "subject_character_id") != subject_character_id
    ):
        observation["reason"] = "case_identity_mismatch"
        return observation
    cycle_serial = _typed_value(case, "cycle_serial")
    case_serial = _typed_value(case, "case_serial")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 1
        for value in (cycle_serial, case_serial)
    ):
        observation["reason"] = "case_serial_unavailable"
        return observation
    observation["case_identity"] = [cycle_serial, case_serial]

    operation = response.get("operation")
    operation_id = _typed_value(operation, "operation_id")
    receipt = response.get("receipt")
    if operation_id == 0 and isinstance(receipt, dict) and receipt.get(
        "status"
    ) == "not_recorded":
        observation["classification"] = "pending"
        observation["reason"] = "allowlisted_operation_not_recorded"
        return observation

    policy = response.get("policy")
    operation_expected = {
        "operation_id": 39,
        "operation_key": "roster_lock",
        "hook": "roster_lock",
        "pre_state": 1,
        "post_state": 1,
    }
    for key, expected in operation_expected.items():
        if _typed_value(operation, key) != expected:
            observation["reason"] = f"allowlisted_operation_mismatch:{key}"
            return observation
    if (
        _typed_value(policy, "policy_id") != "mechanism_039"
        or _typed_value(policy, "choice") != 1
    ):
        observation["reason"] = "allowlisted_policy_mismatch"
        return observation
    if not isinstance(receipt, dict) or receipt.get("status") != "recorded":
        observation["reason"] = "roster_lock_receipt_not_recorded"
        return observation
    receipt_expected = {
        "key": "roster_lock",
        "owner_character_id": owner_character_id,
        "subject_character_id": subject_character_id,
        "cycle_serial": cycle_serial,
        "case_serial": case_serial,
        "state": 1,
        "choice": 1,
    }
    for key, expected in receipt_expected.items():
        if _typed_value(receipt, key) != expected:
            observation["reason"] = f"roster_lock_receipt_mismatch:{key}"
            return observation

    observation["classification"] = "postcondition"
    observation["reason"] = None
    observation["receipt_signature"] = [
        owner_character_id,
        subject_character_id,
        cycle_serial,
        case_serial,
        39,
        1,
    ]
    return observation


def _event_identity(
    service: AiOwnedCaseActionService,
    binding: dict[str, object],
) -> dict[str, object]:
    event_instance_id = binding.get("active_event_instance_id")
    revision = binding.get("revision")
    if (
        isinstance(event_instance_id, bool)
        or not isinstance(event_instance_id, int)
        or event_instance_id < 1
        or isinstance(revision, bool)
        or not isinstance(revision, int)
        or revision < 0
    ):
        return {
            "status": "unavailable",
            "reason": "active_event_binding_unavailable",
        }
    try:
        response = service.query_current_event_window_context_v1(
            event_instance_id,
            expected_revision=revision,
        )
    except Exception as error:  # the RED report must preserve MCP failure
        return {
            "status": "unavailable",
            "reason": "current_event_query_failed",
            "error_type": type(error).__name__,
            "error": str(error),
        }
    return {
        "status": response.get("status"),
        "event_definition_key": response.get("event_definition_key"),
        "response": copy.deepcopy(response),
    }


def run_zhongguo_ai_owned_case_background_action(
    service: AiOwnedCaseActionService,
    *,
    owner_character_id: int,
    subject_character_id: int,
    request_nonce_prefix: str = "zg361.ai.action",
    max_advance_steps: int = DEFAULT_MAX_ADVANCE_STEPS,
    max_elapsed_days: int = DEFAULT_MAX_ELAPSED_DAYS,
    require_transition: bool = True,
) -> dict[str, object]:
    """Advance a bounded real timeline and prove one hidden AI receipt.

    ``require_transition=True`` is the acceptance-grade mode: a receipt that
    already existed before this call is only a baseline, and GREEN requires a
    strictly newer cycle/case receipt.  Set it to ``False`` only when a caller
    needs an idempotent postcondition check; that result clearly reports that
    no gameplay action was executed.
    """

    owner = _positive_int32(owner_character_id, "owner_character_id")
    subject = _positive_int32(subject_character_id, "subject_character_id")
    if owner == subject:
        raise ValueError("owner_character_id and subject_character_id differ")
    steps_bound = _positive_bound(
        max_advance_steps,
        "max_advance_steps",
        MAX_BOUNDED_ADVANCE_STEPS,
    )
    days_bound = _positive_bound(
        max_elapsed_days,
        "max_elapsed_days",
        MAX_BOUNDED_ELAPSED_DAYS,
    )
    if not isinstance(require_transition, bool):
        raise ValueError("require_transition must be boolean")
    _nonce(request_nonce_prefix, "pre")
    _nonce(request_nonce_prefix, f"d{steps_bound}")

    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_ai_owned_case_background_action",
        "result": "RED",
        "mcp_only": True,
        "ocr_used": False,
        "coordinates_used": False,
        "test_ui_used": False,
        "visible_event_allowed": False,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "require_transition": require_transition,
        "max_advance_steps": steps_bound,
        "max_elapsed_days": days_bound,
        "initial_snapshot": None,
        "timeline_actions": [],
        "provider_observations": [],
        "current_event_observation": None,
        "gameplay_action_executed": False,
        "gameplay_action_complete": False,
        "background_business_complete": False,
        "action_ack_is_business_postcondition": False,
        "postcondition_source": (
            "game.command.query-zhongguo-ai-owned-case-snapshot-v1"
        ),
        "terminal_condition": None,
        "failure_reason": None,
    }

    def finish_red(reason: str, terminal: str) -> dict[str, object]:
        report["failure_reason"] = reason
        report["terminal_condition"] = terminal
        return report

    capabilities = service.capabilities()
    bridge_capabilities = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, dict)
        else None
    )
    if not (
        isinstance(bridge_capabilities, list)
        and QUERY_ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_CAPABILITY
        in bridge_capabilities
    ):
        return finish_red(
            "AI-owned case provider capability is not advertised",
            "provider_capability_unavailable",
        )
    if "life-advance" not in action_step_set(capabilities):
        return finish_red(
            "bounded native life-advance is not advertised",
            "timeline_capability_unavailable",
        )

    initial_snapshot = service.snapshot()
    initial_binding, binding_error = _snapshot_binding(initial_snapshot)
    report["initial_snapshot"] = copy.deepcopy(initial_binding)
    if initial_binding is None:
        return finish_red(
            f"initial paused MCP binding unavailable: {binding_error}",
            "initial_snapshot_unavailable",
        )
    if initial_binding["active_event_instance_id"] is not None:
        report["current_event_observation"] = _event_identity(
            service, initial_binding
        )
        return finish_red(
            "a player-visible event is already active; this helper never "
            "selects it",
            "player_visible_event_pending",
        )
    if initial_binding["played_character_id"] == owner:
        return finish_red(
            "requested owner is the played character, not an AI-owned case",
            "owner_is_played_character",
        )

    try:
        initial_response = service.query_zhongguo_ai_owned_case_snapshot_v1(
            owner,
            subject,
            _nonce(request_nonce_prefix, "pre"),
            expected_revision=int(initial_binding["revision"]),
        )
    except Exception as error:
        return finish_red(
            "initial AI-owned provider query failed: "
            f"{type(error).__name__}: {error}",
            "initial_provider_query_failed",
        )
    initial_observation = _provider_observation(
        initial_response,
        owner_character_id=owner,
        subject_character_id=subject,
    )
    observations = report["provider_observations"]
    assert isinstance(observations, list)
    observations.append({"phase": "pre", **initial_observation})
    if initial_observation["classification"] == "blocked":
        return finish_red(
            f"initial AI-owned provider is not actionable: "
            f"{initial_observation['reason']}",
            "initial_provider_blocked",
        )

    baseline_signature = initial_observation.get("receipt_signature")
    baseline_case_identity = initial_observation.get("case_identity")
    if (
        initial_observation["classification"] == "postcondition"
        and not require_transition
    ):
        report["result"] = "GREEN"
        report["gameplay_action_complete"] = True
        report["background_business_complete"] = True
        report["terminal_condition"] = "postcondition_already_observed"
        return report

    initial_date_raw = int(initial_binding["date_raw"])
    played_character_id = int(initial_binding["played_character_id"])
    current_binding = initial_binding
    last_observation = initial_observation

    for index in range(1, steps_bound + 1):
        before_revision = int(current_binding["revision"])
        try:
            acknowledgement = service.execute_step(
                "life-advance",
                expected_revision=before_revision,
            )
        except Exception as error:
            return finish_red(
                "bounded native timeline submission failed: "
                f"{type(error).__name__}: {error}",
                "timeline_submission_failed",
            )
        report["gameplay_action_executed"] = True

        post_snapshot = service.snapshot()
        post_binding, post_error = _snapshot_binding(post_snapshot)
        action_row = {
            "ordinal": index,
            "step": "life-advance",
            "expected_revision": before_revision,
            "acknowledgement": copy.deepcopy(acknowledgement),
            "post_snapshot": copy.deepcopy(post_binding),
            "post_snapshot_error": post_error,
            "business_postcondition": False,
        }
        actions = report["timeline_actions"]
        assert isinstance(actions, list)
        actions.append(action_row)
        if post_binding is None:
            return finish_red(
                f"life-advance lacks a paused postcondition: {post_error}",
                "timeline_postcondition_unavailable",
            )
        if post_binding["played_character_id"] != played_character_id:
            return finish_red(
                "played character changed during the bounded AI-owned cell",
                "played_character_changed",
            )
        if post_binding["active_event_instance_id"] is not None:
            report["current_event_observation"] = _event_identity(
                service, post_binding
            )
            return finish_red(
                "a player-visible event interrupted the hidden AI-owned path; "
                "no event option was selected",
                "player_visible_event_interrupted",
            )

        post_date_raw = int(post_binding["date_raw"])
        if post_date_raw <= int(current_binding["date_raw"]):
            return finish_red(
                "life-advance ACK was not followed by a later paused date",
                "timeline_did_not_advance",
            )
        elapsed_raw_hours = post_date_raw - initial_date_raw
        action_row["elapsed_raw_hours"] = elapsed_raw_hours
        action_row["elapsed_days"] = elapsed_raw_hours / RAW_HOURS_PER_DAY

        try:
            response = service.query_zhongguo_ai_owned_case_snapshot_v1(
                owner,
                subject,
                _nonce(request_nonce_prefix, f"d{index}"),
                expected_revision=int(post_binding["revision"]),
            )
        except Exception as error:
            return finish_red(
                "post-advance AI-owned provider query failed: "
                f"{type(error).__name__}: {error}",
                "post_provider_query_failed",
            )
        observation = _provider_observation(
            response,
            owner_character_id=owner,
            subject_character_id=subject,
        )
        observations.append({"phase": f"after_{index}", **observation})
        last_observation = observation
        if observation["classification"] == "blocked":
            return finish_red(
                f"post-advance AI-owned provider is not actionable: "
                f"{observation['reason']}",
                "post_provider_blocked",
            )
        if observation["classification"] == "postcondition":
            signature = observation.get("receipt_signature")
            case_identity = observation.get("case_identity")
            transition_ready = baseline_signature is None
            if baseline_signature is not None and signature != baseline_signature:
                transition_ready = bool(
                    isinstance(baseline_case_identity, list)
                    and isinstance(case_identity, list)
                    and tuple(case_identity) > tuple(baseline_case_identity)
                )
                if not transition_ready:
                    return finish_red(
                        "the observed receipt changed without a strictly newer "
                        "cycle/case identity",
                        "receipt_identity_regressed",
                    )
            if transition_ready:
                action_row["business_postcondition"] = True
                report["result"] = "GREEN"
                report["gameplay_action_complete"] = True
                report["background_business_complete"] = True
                report["terminal_condition"] = (
                    "new_allowlisted_roster_lock_receipt"
                )
                report["failure_reason"] = None
                return report

        current_binding = post_binding
        if elapsed_raw_hours >= days_bound * RAW_HOURS_PER_DAY:
            break

    last_reason = last_observation.get("reason")
    if initial_observation["classification"] == "pending" and all(
        row.get("classification") == "pending"
        and row.get("reason") == "case_not_found"
        for row in observations
        if isinstance(row, dict)
    ):
        return finish_red(
            "the bounded real timeline never materialized an AI-owned B1 case; "
            "the seed needs a reachable owner/subject birthday-cycle producer",
            "ai_owned_case_producer_seed_unreachable",
        )
    return finish_red(
        "no strictly newer mechanism_039 roster-lock receipt was observed "
        f"within the bounded timeline (last_provider_reason={last_reason})",
        "ai_owned_case_transition_unobserved",
    )


__all__ = [
    "AiOwnedCaseActionService",
    "DEFAULT_MAX_ADVANCE_STEPS",
    "DEFAULT_MAX_ELAPSED_DAYS",
    "run_zhongguo_ai_owned_case_background_action",
]
