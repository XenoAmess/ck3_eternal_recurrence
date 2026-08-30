"""Strict Python composition contract for voluntary active-combat retreat."""

from __future__ import annotations

import copy
import re

from .battle_control_contract import normalize_battle_control_snapshot_v1


PREVIEW_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX = (
    "preview-active-combat-retreat-v1-"
)
ORDER_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX = "order-active-combat-retreat-v1-"
ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE = "python_production_composition"

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{32,128}")
_ORDER_PATTERN = re.compile(
    r"order-active-combat-retreat-v1-(?P<selected>[1-9][0-9]*)"
    r"-revision-(?P<revision>0|[1-9][0-9]*)"
    r"-combat-(?P<combat>-?(?:0|[1-9][0-9]*))"
    r"-side-(?P<side>[01])"
    r"-scope-(?P<scope>full_side|owner_subset)"
    r"-to-(?P<target>[1-9][0-9]*)"
    r"-token-(?P<token>[A-Za-z0-9_-]{32,128})"
)

_SOURCE_BINDING_KEYS = {
    "snapshot_id",
    "revision",
    "native_revision",
    "date_raw",
    "episode_run_id",
    "connection_generation",
}
_TARGET_PREVIEW_KEYS = {
    "status",
    "unavailable_reason",
    "provenance",
    "army_id",
    "origin_province_id",
    "target_province_id",
    "route_province_ids",
    "previewed_date_raw",
    "move_mode",
    "eta_date_raw",
    "movement_days",
    "candidate_token",
    "order_step",
}
_PREVIEW_RESULT_KEYS = {
    "schema_version",
    "contract_stage",
    "step",
    "status",
    "unavailable_reason",
    "action_ready",
    "source_binding",
    "battle_control_snapshot",
    "selected_public_cunit_id",
    "selected_native_carmy_id",
    "selected_owner_character_id",
    "combat_id",
    "combat_province_id",
    "side_index",
    "side_scope",
    "affected_public_cunit_ids_in_stored_order",
    "unaffected_same_side_public_cunit_ids_in_stored_order",
    "target_province_id",
    "target_preview",
    "backend_id",
}
_AFFECTED_OBSERVATION_KEYS = {
    "public_cunit_id",
    "present",
    "retreating",
    "move_target_province_id",
    "target_matches",
    "route_province_ids",
    "route_reaches_target",
}
_POSTCONDITION_KEYS = {
    "status",
    "observation_snapshot_id",
    "observation_revision",
    "observation_native_revision",
    "observation_date_raw",
    "affected_armies_in_stored_order",
    "all_affected_retreating_observed",
    "all_affected_target_observed",
    "all_affected_route_observed",
    "combat_id_post_query_performed",
    "winner_verified",
    "phase_verified",
    "full_postcondition_verified",
}
_ORDER_ACK_KEYS = {
    "schema_version",
    "contract_stage",
    "step",
    "accepted",
    "status",
    "rejection_reason",
    "verification_pending",
    "token_consumed",
    "selected_public_cunit_id",
    "expected_snapshot_revision",
    "expected_combat_id",
    "expected_side_index",
    "expected_scope",
    "target_province_id",
    "affected_public_cunit_ids_in_stored_order",
    "unaffected_same_side_public_cunit_ids_in_stored_order",
    "underlying_move_result",
    "semantic_postcondition",
    "backend_id",
}


def preview_active_combat_retreat_v1_step(
    selected_public_cunit_id: int,
    target_province_id: int,
) -> str:
    """Build the canonical preview literal for one selected CUnit/target."""
    selected = _positive_int32(
        selected_public_cunit_id, "selected_public_cunit_id"
    )
    target = _positive_int32(target_province_id, "target_province_id")
    return (
        f"{PREVIEW_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX}{selected}"
        f"-to-{target}"
    )


def parse_preview_active_combat_retreat_v1_step(
    step: object,
) -> tuple[int, int] | None:
    """Parse only the canonical positive-decimal preview spelling."""
    if not isinstance(step, str) or not step.startswith(
        PREVIEW_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX
    ):
        return None
    payload = step.removeprefix(PREVIEW_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX)
    selected_text, separator, target_text = payload.partition("-to-")
    if not separator:
        return None
    if not (
        _canonical_positive_decimal(selected_text)
        and _canonical_positive_decimal(target_text)
    ):
        return None
    selected = int(selected_text)
    target = int(target_text)
    if selected > 2**31 - 1 or target > 2**31 - 1:
        return None
    return selected, target


def order_active_combat_retreat_v1_step(
    selected_public_cunit_id: int,
    *,
    expected_snapshot_revision: int,
    expected_combat_id: int,
    expected_side_index: int,
    expected_scope: str,
    target_province_id: int,
    candidate_token: str,
) -> str:
    """Build a self-contained, single-use active-retreat order literal."""
    selected = _positive_int32(
        selected_public_cunit_id, "selected_public_cunit_id"
    )
    revision = _non_negative_uint64(
        expected_snapshot_revision, "expected_snapshot_revision"
    )
    combat = _full_component_id(expected_combat_id, "expected_combat_id")
    side = _side_index(expected_side_index, "expected_side_index")
    scope = _scope(expected_scope, "expected_scope")
    target = _positive_int32(target_province_id, "target_province_id")
    token = _token(candidate_token, "candidate_token")
    return (
        f"{ORDER_ACTIVE_COMBAT_RETREAT_V1_STEP_PREFIX}{selected}"
        f"-revision-{revision}-combat-{combat}-side-{side}"
        f"-scope-{scope}-to-{target}-token-{token}"
    )


def parse_order_active_combat_retreat_v1_step(
    step: object,
) -> dict[str, object] | None:
    """Parse only a canonical, bounded active-retreat order literal."""
    if not isinstance(step, str):
        return None
    match = _ORDER_PATTERN.fullmatch(step)
    if match is None:
        return None
    selected = int(match.group("selected"))
    revision = int(match.group("revision"))
    combat = int(match.group("combat"))
    target = int(match.group("target"))
    if (
        selected > 2**31 - 1
        or not -(2**31) <= combat <= 2**31 - 1
        or combat == -1
        or target > 2**31 - 1
        or revision > 2**64 - 1
    ):
        return None
    return {
        "selected_public_cunit_id": selected,
        "expected_snapshot_revision": revision,
        "expected_combat_id": combat,
        "expected_side_index": int(match.group("side")),
        "expected_scope": match.group("scope"),
        "target_province_id": target,
        "candidate_token": match.group("token"),
    }


def normalize_active_combat_retreat_v1_preview(
    value: object,
    *,
    expected_selected_public_cunit_id: int,
    expected_target_province_id: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Validate one same-frame legality plus exact-route preview result."""
    selected = _positive_int32(
        expected_selected_public_cunit_id,
        "expected_selected_public_cunit_id",
    )
    target = _positive_int32(
        expected_target_province_id, "expected_target_province_id"
    )
    revision = _non_negative_uint64(
        expected_snapshot_revision, "expected_snapshot_revision"
    )
    expected_step = preview_active_combat_retreat_v1_step(selected, target)
    if not isinstance(value, dict) or set(value) != _PREVIEW_RESULT_KEYS:
        raise ValueError("active-retreat preview has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("contract_stage")
        != ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE
        or value.get("step") != expected_step
        or value.get("selected_public_cunit_id") != selected
        or value.get("target_province_id") != target
    ):
        raise ValueError("active-retreat preview request binding disagrees")
    source = _normalize_source_binding(value.get("source_binding"))
    if source["revision"] != revision:
        raise ValueError("active-retreat preview revision binding disagrees")
    try:
        battle = normalize_battle_control_snapshot_v1(
            value.get("battle_control_snapshot"),
            expected_subject_public_cunit_id=selected,
            expected_observed_date_raw=int(source["date_raw"]),
            expected_snapshot_revision=int(source["native_revision"]),
        )
    except ValueError as error:
        raise ValueError(
            f"active-retreat preview battle frame is malformed: {error}"
        ) from error
    mirrors = {
        "selected_public_cunit_id": battle["selected_public_cunit_id"],
        "selected_native_carmy_id": battle["selected_native_carmy_id"],
        "selected_owner_character_id": battle["selected_owner_character_id"],
        "combat_id": battle["combat_id"],
        "combat_province_id": battle["combat_province_id"],
        "side_index": battle["side_index"],
        "side_scope": battle["side_scope"],
        "affected_public_cunit_ids_in_stored_order": battle[
            "affected_public_cunit_ids_in_stored_order"
        ],
        "unaffected_same_side_public_cunit_ids_in_stored_order": battle[
            "unaffected_same_side_public_cunit_ids_in_stored_order"
        ],
    }
    if any(value.get(key) != expected for key, expected in mirrors.items()):
        raise ValueError("active-retreat preview mirror disagrees with battle")
    target_preview = _normalize_target_preview(
        value.get("target_preview"),
        selected_public_cunit_id=selected,
        combat_province_id=int(battle["combat_province_id"]),
        target_province_id=target,
        source_date_raw=int(source["date_raw"]),
    )
    status = value.get("status")
    unavailable_reason = value.get("unavailable_reason")
    action_ready = _strict_bool(value.get("action_ready"), "action_ready")
    legal_now = battle["legality"].get("legal_now") is True
    if status == "available":
        if (
            unavailable_reason is not None
            or action_ready is not True
            or not legal_now
            or target_preview["status"] != "available"
        ):
            raise ValueError("active-retreat available preview is inconsistent")
    elif status == "unavailable":
        if (
            not isinstance(unavailable_reason, str)
            or not unavailable_reason
            or action_ready is not False
            or target_preview["status"] != "unavailable"
            or target_preview["unavailable_reason"] != unavailable_reason
        ):
            raise ValueError("active-retreat unavailable preview is inconsistent")
        if unavailable_reason.startswith("retreat_not_legal:"):
            reasons = battle["legality"]["reason_codes_in_native_order"]
            if legal_now or not reasons or unavailable_reason != (
                f"retreat_not_legal:{reasons[0]}"
            ):
                raise ValueError("active-retreat native gate reason disagrees")
    else:
        raise ValueError("active-retreat preview status is unknown")
    backend_id = value.get("backend_id")
    if not isinstance(backend_id, str) or not backend_id:
        raise ValueError("active-retreat preview backend_id is missing")
    return {
        **copy.deepcopy(value),
        "source_binding": source,
        "battle_control_snapshot": battle,
        "target_preview": target_preview,
    }


def normalize_active_combat_retreat_v1_order_ack(
    value: object,
    *,
    expected_selected_public_cunit_id: int,
    expected_snapshot_revision: int,
    expected_combat_id: int,
    expected_side_index: int,
    expected_scope: str,
    expected_target_province_id: int,
    expected_candidate_token: str,
) -> dict[str, object]:
    """Validate an order ACK without upgrading it to retreat completion."""
    request = {
        "selected_public_cunit_id": _positive_int32(
            expected_selected_public_cunit_id,
            "expected_selected_public_cunit_id",
        ),
        "expected_snapshot_revision": _non_negative_uint64(
            expected_snapshot_revision, "expected_snapshot_revision"
        ),
        "expected_combat_id": _full_component_id(
            expected_combat_id, "expected_combat_id"
        ),
        "expected_side_index": _side_index(
            expected_side_index, "expected_side_index"
        ),
        "expected_scope": _scope(expected_scope, "expected_scope"),
        "target_province_id": _positive_int32(
            expected_target_province_id, "expected_target_province_id"
        ),
        "candidate_token": _token(
            expected_candidate_token, "expected_candidate_token"
        ),
    }
    expected_step = order_active_combat_retreat_v1_step(**request)
    if not isinstance(value, dict) or set(value) != _ORDER_ACK_KEYS:
        raise ValueError("active-retreat order ACK has a malformed schema")
    if (
        value.get("schema_version") != 1
        or value.get("contract_stage")
        != ACTIVE_COMBAT_RETREAT_V1_CONTRACT_STAGE
        or value.get("step") != expected_step
        or any(
            value.get(key) != request[key]
            for key in (
                "selected_public_cunit_id",
                "expected_snapshot_revision",
                "expected_combat_id",
                "expected_side_index",
                "expected_scope",
                "target_province_id",
            )
        )
    ):
        raise ValueError("active-retreat order ACK binding disagrees")
    accepted = _strict_bool(value.get("accepted"), "accepted")
    pending = _strict_bool(
        value.get("verification_pending"), "verification_pending"
    )
    consumed = _strict_bool(value.get("token_consumed"), "token_consumed")
    if consumed is not True:
        raise ValueError("active-retreat order token was not consumed")
    rejection_reason = value.get("rejection_reason")
    move_result = value.get("underlying_move_result")
    if accepted:
        if (
            value.get("status") != "accepted_verification_pending"
            or rejection_reason is not None
            or pending is not True
            or not isinstance(move_result, dict)
            or move_result.get("accepted") is not True
            or move_result.get("status") != "submitted"
        ):
            raise ValueError("active-retreat accepted ACK is inconsistent")
    else:
        if (
            value.get("status") != "rejected"
            or not isinstance(rejection_reason, str)
            or not rejection_reason
            or pending is not False
            or move_result is not None
        ):
            raise ValueError("active-retreat rejected ACK is inconsistent")
    affected = _positive_int32_list(
        value.get("affected_public_cunit_ids_in_stored_order"),
        "affected_public_cunit_ids_in_stored_order",
        nonempty=accepted,
    )
    unaffected = _positive_int32_list(
        value.get("unaffected_same_side_public_cunit_ids_in_stored_order"),
        "unaffected_same_side_public_cunit_ids_in_stored_order",
    )
    if set(affected) & set(unaffected):
        raise ValueError("active-retreat order scopes overlap")
    postcondition = _normalize_semantic_postcondition(
        value.get("semantic_postcondition"),
        accepted=accepted,
        affected_public_cunit_ids=affected,
        target_province_id=int(request["target_province_id"]),
    )
    backend_id = value.get("backend_id")
    if not isinstance(backend_id, str) or not backend_id:
        raise ValueError("active-retreat order ACK backend_id is missing")
    return {
        **copy.deepcopy(value),
        "affected_public_cunit_ids_in_stored_order": affected,
        "unaffected_same_side_public_cunit_ids_in_stored_order": unaffected,
        "semantic_postcondition": postcondition,
    }


def _normalize_source_binding(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _SOURCE_BINDING_KEYS:
        raise ValueError("active-retreat source binding has a malformed schema")
    snapshot_id = value.get("snapshot_id")
    episode_run_id = value.get("episode_run_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("active-retreat source snapshot_id is missing")
    if not isinstance(episode_run_id, str) or not episode_run_id:
        raise ValueError("active-retreat source episode_run_id is missing")
    return {
        "snapshot_id": snapshot_id,
        "revision": _non_negative_uint64(value.get("revision"), "revision"),
        "native_revision": _positive_uint64(
            value.get("native_revision"), "native_revision"
        ),
        "date_raw": _signed_int64(value.get("date_raw"), "date_raw"),
        "episode_run_id": episode_run_id,
        "connection_generation": _positive_uint64(
            value.get("connection_generation"), "connection_generation"
        ),
    }


def _normalize_target_preview(
    value: object,
    *,
    selected_public_cunit_id: int,
    combat_province_id: int,
    target_province_id: int,
    source_date_raw: int,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _TARGET_PREVIEW_KEYS:
        raise ValueError("active-retreat target preview has a malformed schema")
    if (
        value.get("provenance")
        != "planner_selected_exact_native_route_preview"
        or value.get("army_id") != selected_public_cunit_id
        or value.get("target_province_id") != target_province_id
    ):
        raise ValueError("active-retreat target preview binding disagrees")
    status = value.get("status")
    reason = value.get("unavailable_reason")
    origin = value.get("origin_province_id")
    route = value.get("route_province_ids")
    previewed_date = value.get("previewed_date_raw")
    move_mode = _optional_signed_int32(value.get("move_mode"), "move_mode")
    eta_date = _optional_signed_int64(value.get("eta_date_raw"), "eta_date_raw")
    movement_days = _optional_non_negative_int32(
        value.get("movement_days"), "movement_days"
    )
    token = value.get("candidate_token")
    order_step = value.get("order_step")
    if status == "available":
        origin_id = _positive_int32(origin, "origin_province_id")
        route_ids = _positive_int32_list(
            route, "route_province_ids", nonempty=True
        )
        candidate = _token(token, "candidate_token")
        parsed_order = parse_order_active_combat_retreat_v1_step(order_step)
        if (
            reason is not None
            or origin_id != combat_province_id
            or target_province_id == combat_province_id
            or route_ids[-1] != target_province_id
            or previewed_date != source_date_raw
            or parsed_order is None
            or parsed_order["selected_public_cunit_id"]
            != selected_public_cunit_id
            or parsed_order["target_province_id"] != target_province_id
            or parsed_order["candidate_token"] != candidate
        ):
            raise ValueError("active-retreat available target preview disagrees")
    elif status == "unavailable":
        if not isinstance(reason, str) or not reason:
            raise ValueError("active-retreat target preview reason is missing")
        origin_id = (
            _positive_int32(origin, "origin_province_id")
            if origin is not None
            else None
        )
        route_ids = _positive_int32_list(route, "route_province_ids")
        if (
            route_ids
            or token is not None
            or order_step is not None
            or previewed_date is not None
            or move_mode is not None
            or eta_date is not None
            or movement_days is not None
        ):
            raise ValueError("active-retreat unavailable target preview leaks proof")
        candidate = None
    else:
        raise ValueError("active-retreat target preview status is unknown")
    return {
        "status": status,
        "unavailable_reason": reason,
        "provenance": "planner_selected_exact_native_route_preview",
        "army_id": selected_public_cunit_id,
        "origin_province_id": origin_id,
        "target_province_id": target_province_id,
        "route_province_ids": route_ids,
        "previewed_date_raw": previewed_date,
        "move_mode": move_mode,
        "eta_date_raw": eta_date,
        "movement_days": movement_days,
        "candidate_token": candidate,
        "order_step": order_step,
    }


def _normalize_semantic_postcondition(
    value: object,
    *,
    accepted: bool,
    affected_public_cunit_ids: list[int],
    target_province_id: int,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _POSTCONDITION_KEYS:
        raise ValueError("active-retreat semantic postcondition is malformed")
    status = value.get("status")
    observations = value.get("affected_armies_in_stored_order")
    if not isinstance(observations, list):
        raise ValueError("active-retreat affected observations must be a list")
    normalized_observations: list[dict[str, object]] = []
    for index, row in enumerate(observations):
        if not isinstance(row, dict) or set(row) != _AFFECTED_OBSERVATION_KEYS:
            raise ValueError(
                f"active-retreat affected observation {index} is malformed"
            )
        public_id = _positive_int32(
            row.get("public_cunit_id"),
            f"affected_armies_in_stored_order[{index}].public_cunit_id",
        )
        present = _strict_bool(row.get("present"), "present")
        retreating = _optional_bool(row.get("retreating"), "retreating")
        move_target = _optional_positive_int32(
            row.get("move_target_province_id"), "move_target_province_id"
        )
        target_matches = _optional_bool(
            row.get("target_matches"), "target_matches"
        )
        route = row.get("route_province_ids")
        route_ids = (
            _positive_int32_list(route, "route_province_ids")
            if route is not None
            else None
        )
        route_reaches = _optional_bool(
            row.get("route_reaches_target"), "route_reaches_target"
        )
        if present:
            expected_target_matches = (
                None
                if target_matches is None and move_target is None
                else move_target == target_province_id
            )
            expected_route_reaches = (
                None
                if route_ids is None
                else bool(route_ids) and route_ids[-1] == target_province_id
            )
            if (
                target_matches != expected_target_matches
                or route_reaches != expected_route_reaches
            ):
                raise ValueError(
                    "active-retreat affected semantic observation disagrees"
                )
        elif any(
            field is not None
            for field in (
                retreating,
                move_target,
                target_matches,
                route_ids,
                route_reaches,
            )
        ):
            raise ValueError("missing affected army carries semantic claims")
        normalized_observations.append(
            {
                "public_cunit_id": public_id,
                "present": present,
                "retreating": retreating,
                "move_target_province_id": move_target,
                "target_matches": target_matches,
                "route_province_ids": route_ids,
                "route_reaches_target": route_reaches,
            }
        )
    if status in {"observation_pending", "not_observed"}:
        expected_observation_ids: list[int] = []
    else:
        expected_observation_ids = affected_public_cunit_ids
    if [row["public_cunit_id"] for row in normalized_observations] != (
        expected_observation_ids
    ):
        raise ValueError("active-retreat affected observation order disagrees")
    all_retreating = _optional_bool(
        value.get("all_affected_retreating_observed"),
        "all_affected_retreating_observed",
    )
    all_target = _optional_bool(
        value.get("all_affected_target_observed"),
        "all_affected_target_observed",
    )
    all_route = _optional_bool(
        value.get("all_affected_route_observed"),
        "all_affected_route_observed",
    )
    if accepted and status == "observed_partial":
        snapshot_id = value.get("observation_snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise ValueError("active-retreat observation snapshot_id is missing")
        revision = _non_negative_uint64(
            value.get("observation_revision"), "observation_revision"
        )
        native_revision = _positive_uint64(
            value.get("observation_native_revision"),
            "observation_native_revision",
        )
        date_raw = _signed_int64(
            value.get("observation_date_raw"), "observation_date_raw"
        )
        expected_all_retreating = bool(normalized_observations) and all(
            row["present"] is True and row["retreating"] is True
            for row in normalized_observations
        )
        expected_all_target = bool(normalized_observations) and all(
            row["present"] is True and row["target_matches"] is True
            for row in normalized_observations
        )
        expected_all_route = bool(normalized_observations) and all(
            row["present"] is True and row["route_reaches_target"] is True
            for row in normalized_observations
        )
        if (
            all_retreating != expected_all_retreating
            or all_target != expected_all_target
            or all_route != expected_all_route
        ):
            raise ValueError("active-retreat aggregate observations disagree")
    elif accepted and status == "observation_pending":
        snapshot_id = value.get("observation_snapshot_id")
        revision = value.get("observation_revision")
        native_revision = value.get("observation_native_revision")
        date_raw = value.get("observation_date_raw")
        if (
            any(
                item is not None
                for item in (
                    snapshot_id,
                    revision,
                    native_revision,
                    date_raw,
                    all_retreating,
                    all_target,
                    all_route,
                )
            )
            or normalized_observations
        ):
            raise ValueError("pending active-retreat carries semantic claims")
    else:
        snapshot_id = value.get("observation_snapshot_id")
        revision = value.get("observation_revision")
        native_revision = value.get("observation_native_revision")
        date_raw = value.get("observation_date_raw")
        if (
            status != "not_observed"
            or any(
                item is not None
                for item in (
                    snapshot_id,
                    revision,
                    native_revision,
                    date_raw,
                    all_retreating,
                    all_target,
                    all_route,
                )
            )
            or normalized_observations
        ):
            raise ValueError("rejected active-retreat carries postcondition claims")
    for false_field in (
        "combat_id_post_query_performed",
        "winner_verified",
        "phase_verified",
        "full_postcondition_verified",
    ):
        if value.get(false_field) is not False:
            raise ValueError(
                f"active-retreat {false_field} must remain explicitly false"
            )
    return {
        **copy.deepcopy(value),
        "observation_snapshot_id": snapshot_id,
        "observation_revision": revision,
        "observation_native_revision": native_revision,
        "observation_date_raw": date_raw,
        "affected_armies_in_stored_order": normalized_observations,
    }


def _positive_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _full_component_id(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
        or value == -1
    ):
        raise ValueError(
            f"{name} must be a signed full component ID other than -1"
        )
    return value


def _optional_positive_int32(value: object, name: str) -> int | None:
    return None if value is None else _positive_int32(value, name)


def _positive_uint64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**64 - 1
    ):
        raise ValueError(f"{name} must be a positive uint64")
    return value


def _non_negative_uint64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**64 - 1
    ):
        raise ValueError(f"{name} must be a non-negative uint64")
    return value


def _signed_int64(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**63) <= value <= 2**63 - 1
    ):
        raise ValueError(f"{name} must be a signed int64")
    return value


def _optional_signed_int64(value: object, name: str) -> int | None:
    return None if value is None else _signed_int64(value, name)


def _optional_signed_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a signed int32 or null")
    return value


def _optional_non_negative_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a non-negative int32 or null")
    return value


def _positive_int32_list(
    value: object, name: str, *, nonempty: bool = False
) -> list[int]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{name} must be a{' nonempty' if nonempty else ''} list")
    result = [
        _positive_int32(item, f"{name}[{index}]")
        for index, item in enumerate(value)
    ]
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicates")
    return result


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a bool")
    return value


def _optional_bool(value: object, name: str) -> bool | None:
    if value is None:
        return None
    return _strict_bool(value, name)


def _side_index(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1}:
        raise ValueError(f"{name} must be 0 or 1")
    return value


def _scope(value: object, name: str) -> str:
    if value not in {"full_side", "owner_subset"}:
        raise ValueError(f"{name} must be full_side or owner_subset")
    assert isinstance(value, str)
    return value


def _token(value: object, name: str) -> str:
    if not isinstance(value, str) or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a canonical opaque token")
    return value


def _canonical_positive_decimal(value: str) -> bool:
    return bool(value and value.isascii() and value.isdigit() and value[0] != "0")
