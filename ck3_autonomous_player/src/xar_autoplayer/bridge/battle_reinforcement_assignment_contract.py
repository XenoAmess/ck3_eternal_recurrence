"""Strict exact-build contract for native AI reinforcement assignment state."""

from __future__ import annotations

from typing import Final


QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CAPABILITY: Final = (
    "game.command.query-battle-reinforcement-assignment-v1-N"
)
QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX: Final = (
    "query-battle-reinforcement-assignment-v1-"
)
BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CONTRACT_STAGE: Final = (
    "production_exact_ai_reinforcement_assignment"
)

_FIELDS: Final = {
    "schema_version",
    "contract_stage",
    "status",
    "unavailable_reason",
    "battle_reinforcement_assignment_ready",
    "snapshot_revision",
    "observed_date_raw",
    "selected_public_cunit_id",
    "selected_native_carmy_id",
    "coordinator_id",
    "unit_stack_stored_index",
    "subunit_stored_index",
    "signal",
    "assignment",
    "route",
    "native_order",
    "contact_projection",
}
_SIGNAL_FIELDS: Final = {
    "asking_for_help",
    "assigned_to_help",
    "asking_changed_last_evaluation",
    "request_power_basis_raw",
    "cross_coordinator_request_valid_raw",
    "cross_coordinator_request_power_raw",
    "first_route_edge_remaining_duration_q100000",
}
_ASSIGNMENT_FIELDS: Final = {
    "assignment_target_province_id",
    "target_provenance",
    "combat_binding_status",
    "active_combat_id",
}
_ROUTE_FIELDS: Final = {
    "current_province_id",
    "move_target_province_id",
    "route_province_ids",
    "route_alignment",
    "arrival_date_raws",
    "assignment_eta_date_raw",
}
_NATIVE_ORDER_FIELDS: Final = {
    "support_search_province_ids_in_stored_order",
    "parent_subunits_in_stored_order",
}
_SUBUNIT_FIELDS: Final = {
    "public_cunit_ids_in_stored_order",
    "asking_for_help",
    "assigned_to_help",
    "assignment_target_province_id",
}
_CONTACT_FIELDS: Final = {
    "status",
    "temporal_semantics",
    "current_target_compatible_combat_ids_in_stored_order",
    "contact_if_now_selected_combat_id",
}
_UNAVAILABLE_REASONS: Final = {
    "unsupported_build",
    "requires_paused",
    "subject_cunit_not_found",
    "subject_not_ai_managed",
    "coordinator_generation_mismatch",
    "subunit_backlink_mismatch",
    "parent_membership_mismatch",
    "route_timeline_unavailable",
    "state_changed",
}
_ROUTE_ALIGNMENTS: Final = {
    "aligned_to_assignment",
    "not_aligned",
    "no_assignment",
    "timeline_unavailable",
}


def _int(value: object, field: str, *, minimum: int, maximum: int) -> int:
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
    return _int(value, field, minimum=1, maximum=2**31 - 1)


def _optional_positive_int32(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _positive_int32(value, field)


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be boolean")
    return value


def _dict(value: object, field: str, fields: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{field} must contain exactly the v1 fields")
    return value


def _ids(
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


def query_battle_reinforcement_assignment_v1_step(
    selected_public_cunit_id: int,
) -> str:
    selected_public_cunit_id = _positive_int32(
        selected_public_cunit_id, "selected_public_cunit_id"
    )
    return (
        f"{QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX}"
        f"{selected_public_cunit_id}"
    )


def parse_query_battle_reinforcement_assignment_v1_step(
    step: object,
) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX
    ):
        return None
    suffix = step.removeprefix(
        QUERY_BATTLE_REINFORCEMENT_ASSIGNMENT_V1_STEP_PREFIX
    )
    if not suffix.isascii() or not suffix.isdecimal() or suffix.startswith("0"):
        return None
    try:
        value = int(suffix)
    except ValueError:
        return None
    return value if 1 <= value <= 2**31 - 1 and str(value) == suffix else None


def normalize_battle_reinforcement_assignment_v1(
    value: object,
    *,
    expected_selected_public_cunit_id: int,
    expected_observed_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Normalize one complete v1 frame and reject invented/stale fields."""

    expected_selected_public_cunit_id = _positive_int32(
        expected_selected_public_cunit_id,
        "expected_selected_public_cunit_id",
    )
    expected_observed_date_raw = _int(
        expected_observed_date_raw,
        "expected_observed_date_raw",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    expected_snapshot_revision = _int(
        expected_snapshot_revision,
        "expected_snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    frame = _dict(
        value,
        "battle_reinforcement_assignment",
        _FIELDS,
    )
    if frame.get("schema_version") != 1:
        raise ValueError(
            "battle_reinforcement_assignment.schema_version must be 1"
        )
    if (
        frame.get("contract_stage")
        != BATTLE_REINFORCEMENT_ASSIGNMENT_V1_CONTRACT_STAGE
    ):
        raise ValueError(
            "battle_reinforcement_assignment.contract_stage is invalid"
        )
    status = frame.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError("battle_reinforcement_assignment.status is invalid")
    ready = _bool(
        frame.get("battle_reinforcement_assignment_ready"),
        "battle_reinforcement_assignment."
        "battle_reinforcement_assignment_ready",
    )
    if ready is not (status == "available"):
        raise ValueError(
            "battle_reinforcement_assignment readiness disagrees with status"
        )
    revision = _int(
        frame.get("snapshot_revision"),
        "battle_reinforcement_assignment.snapshot_revision",
        minimum=1,
        maximum=2**64 - 1,
    )
    observed_date_raw = _int(
        frame.get("observed_date_raw"),
        "battle_reinforcement_assignment.observed_date_raw",
        minimum=-(2**63),
        maximum=2**63 - 1,
    )
    selected_id = _positive_int32(
        frame.get("selected_public_cunit_id"),
        "battle_reinforcement_assignment.selected_public_cunit_id",
    )
    if revision != expected_snapshot_revision:
        raise ValueError("battle reinforcement revision binding changed")
    if observed_date_raw != expected_observed_date_raw:
        raise ValueError("battle reinforcement date binding changed")
    if selected_id != expected_selected_public_cunit_id:
        raise ValueError("battle reinforcement CUnitID binding changed")

    unavailable_reason = frame.get("unavailable_reason")
    nullable_groups = (
        "selected_native_carmy_id",
        "coordinator_id",
        "unit_stack_stored_index",
        "subunit_stored_index",
        "signal",
        "assignment",
        "route",
        "native_order",
        "contact_projection",
    )
    if status == "unavailable":
        if unavailable_reason not in _UNAVAILABLE_REASONS:
            raise ValueError(
                "battle_reinforcement_assignment unavailable_reason is invalid"
            )
        if any(frame.get(field) is not None for field in nullable_groups):
            raise ValueError(
                "unavailable battle reinforcement frame invented native state"
            )
        return dict(frame)
    if unavailable_reason is not None:
        raise ValueError(
            "available battle reinforcement frame has unavailable_reason"
        )

    selected_native_id = _optional_positive_int32(
        frame.get("selected_native_carmy_id"),
        "battle_reinforcement_assignment.selected_native_carmy_id",
    )
    coordinator_id = _positive_int32(
        frame.get("coordinator_id"),
        "battle_reinforcement_assignment.coordinator_id",
    )
    unit_stack_index = _int(
        frame.get("unit_stack_stored_index"),
        "battle_reinforcement_assignment.unit_stack_stored_index",
        minimum=0,
        maximum=2**31 - 1,
    )
    subunit_index = _int(
        frame.get("subunit_stored_index"),
        "battle_reinforcement_assignment.subunit_stored_index",
        minimum=0,
        maximum=2**31 - 1,
    )

    signal = _dict(
        frame.get("signal"),
        "battle_reinforcement_assignment.signal",
        _SIGNAL_FIELDS,
    )
    asking = _bool(
        signal.get("asking_for_help"),
        "battle_reinforcement_assignment.signal.asking_for_help",
    )
    assigned = _bool(
        signal.get("assigned_to_help"),
        "battle_reinforcement_assignment.signal.assigned_to_help",
    )
    _bool(
        signal.get("asking_changed_last_evaluation"),
        "battle_reinforcement_assignment.signal."
        "asking_changed_last_evaluation",
    )
    request_power = signal.get("request_power_basis_raw")
    if request_power is not None:
        request_power = _int(
            request_power,
            "battle_reinforcement_assignment.signal.request_power_basis_raw",
            minimum=-(2**63),
            maximum=2**63 - 1,
        )
    if not asking and request_power is not None:
        raise ValueError("stale request power must be null when not asking")
    cross_valid = _int(
        signal.get("cross_coordinator_request_valid_raw"),
        "battle_reinforcement_assignment.signal."
        "cross_coordinator_request_valid_raw",
        minimum=0,
        maximum=255,
    )
    cross_power = signal.get("cross_coordinator_request_power_raw")
    if cross_power is not None:
        cross_power = _int(
            cross_power,
            "battle_reinforcement_assignment.signal."
            "cross_coordinator_request_power_raw",
            minimum=-(2**63),
            maximum=2**63 - 1,
        )
    if cross_valid == 0 and cross_power is not None:
        raise ValueError("stale cross-coordinator power must be null")
    first_edge = signal.get(
        "first_route_edge_remaining_duration_q100000"
    )
    if first_edge is not None:
        first_edge = _int(
            first_edge,
            "battle_reinforcement_assignment.signal."
            "first_route_edge_remaining_duration_q100000",
            minimum=0,
            maximum=2**63 - 1,
        )

    assignment = _dict(
        frame.get("assignment"),
        "battle_reinforcement_assignment.assignment",
        _ASSIGNMENT_FIELDS,
    )
    target_id = _optional_positive_int32(
        assignment.get("assignment_target_province_id"),
        "battle_reinforcement_assignment.assignment."
        "assignment_target_province_id",
    )
    if assigned is not (target_id is not None):
        raise ValueError("assigned flag and native target disagree")
    expected_provenance = "native_help_override" if target_id else "none"
    if assignment.get("target_provenance") != expected_provenance:
        raise ValueError("assignment target provenance is invalid")
    binding_status = assignment.get("combat_binding_status")
    if binding_status not in {
        "already_in_active_combat",
        "unbound_until_contact",
    }:
        raise ValueError("assignment combat binding status is invalid")
    active_combat_id = _optional_positive_int32(
        assignment.get("active_combat_id"),
        "battle_reinforcement_assignment.assignment.active_combat_id",
    )
    if (binding_status == "already_in_active_combat") is not (
        active_combat_id is not None
    ):
        raise ValueError("active CombatID and binding status disagree")
    if active_combat_id is not None and selected_native_id is None:
        raise ValueError("active CombatID requires a resolved native CArmyID")

    route = _dict(
        frame.get("route"),
        "battle_reinforcement_assignment.route",
        _ROUTE_FIELDS,
    )
    current_province_id = _positive_int32(
        route.get("current_province_id"),
        "battle_reinforcement_assignment.route.current_province_id",
    )
    # This wire field is the direct generation-validated CUnit+0x30 slot.
    # ArmySnapshot.move_target_province_id is a different semantic projection:
    # it is the final row of CUnit+0x38/+0x44.  In particular, an active-combat
    # frame may legitimately expose different values.  Keep the two native
    # assignment gates independent below; never normalize this slot to the
    # route-final semantic target.
    move_target_id = _optional_positive_int32(
        route.get("move_target_province_id"),
        "battle_reinforcement_assignment.route.move_target_province_id",
    )
    route_ids = _ids(
        route.get("route_province_ids"),
        "battle_reinforcement_assignment.route.route_province_ids",
        unique=False,
    )
    route_alignment = route.get("route_alignment")
    if route_alignment not in _ROUTE_ALIGNMENTS:
        raise ValueError("battle reinforcement route alignment is invalid")
    arrivals_value = route.get("arrival_date_raws")
    arrivals: list[int] | None = None
    if arrivals_value is not None:
        if not isinstance(arrivals_value, list):
            raise ValueError("route.arrival_date_raws must be a list or null")
        arrivals = [
            _int(
                date,
                f"battle_reinforcement_assignment.route."
                f"arrival_date_raws[{index}]",
                minimum=-(2**31),
                maximum=2**31 - 1,
            )
            for index, date in enumerate(arrivals_value)
        ]
        if len(arrivals) != len(route_ids) or arrivals != sorted(arrivals):
            raise ValueError("route arrival timeline is not parallel/monotonic")
    eta = route.get("assignment_eta_date_raw")
    if eta is not None:
        eta = _int(
            eta,
            "battle_reinforcement_assignment.route.assignment_eta_date_raw",
            minimum=-(2**31),
            maximum=2**31 - 1,
        )
    native_move_target_aligned = (
        target_id is not None and move_target_id == target_id
    )
    route_final_aligned = target_id is not None and (
        (bool(route_ids) and route_ids[-1] == target_id)
        or (not route_ids and current_province_id == target_id)
    )
    assignment_aligned = (
        native_move_target_aligned and route_final_aligned
    )
    if target_id is None and route_alignment != "no_assignment":
        raise ValueError("route without assignment must be no_assignment")
    if target_id is not None and route_alignment == "no_assignment":
        raise ValueError("route with assignment cannot be no_assignment")
    if route_alignment == "not_aligned" and assignment_aligned:
        raise ValueError("not_aligned route is geometrically aligned")
    if route_alignment in {"aligned_to_assignment", "timeline_unavailable"}:
        if not assignment_aligned:
            raise ValueError(
                "aligned route does not satisfy its independent native-slot "
                "and route-final target gates"
            )
    if route_alignment == "timeline_unavailable" and arrivals is not None:
        raise ValueError("timeline_unavailable route invented arrivals")
    if route_alignment == "aligned_to_assignment":
        if arrivals is None:
            raise ValueError("aligned route requires the strict timeline")
        expected_eta = arrivals[-1] if arrivals else observed_date_raw
        if eta != expected_eta:
            raise ValueError("assignment ETA does not equal final arrival")
    elif eta is not None:
        raise ValueError("non-aligned route invented an assignment ETA")
    if not route_ids and first_edge is not None:
        raise ValueError("empty native route invented a first-edge duration")

    native_order = _dict(
        frame.get("native_order"),
        "battle_reinforcement_assignment.native_order",
        _NATIVE_ORDER_FIELDS,
    )
    support_ids = _ids(
        native_order.get("support_search_province_ids_in_stored_order"),
        "battle_reinforcement_assignment.native_order."
        "support_search_province_ids_in_stored_order",
        unique=False,
    )
    rows_value = native_order.get("parent_subunits_in_stored_order")
    if not isinstance(rows_value, list):
        raise ValueError("parent_subunits_in_stored_order must be a list")
    rows: list[dict[str, object]] = []
    for index, row_value in enumerate(rows_value):
        row = _dict(
            row_value,
            f"parent_subunits_in_stored_order[{index}]",
            _SUBUNIT_FIELDS,
        )
        row_ids = _ids(
            row.get("public_cunit_ids_in_stored_order"),
            f"parent_subunits_in_stored_order[{index}]."
            "public_cunit_ids_in_stored_order",
            unique=True,
        )
        row_asking = _bool(
            row.get("asking_for_help"),
            f"parent_subunits_in_stored_order[{index}].asking_for_help",
        )
        row_assigned = _bool(
            row.get("assigned_to_help"),
            f"parent_subunits_in_stored_order[{index}].assigned_to_help",
        )
        row_target = _optional_positive_int32(
            row.get("assignment_target_province_id"),
            f"parent_subunits_in_stored_order[{index}]."
            "assignment_target_province_id",
        )
        if row_assigned is not (row_target is not None):
            raise ValueError("parent subunit assignment target is stale")
        rows.append(
            {
                **row,
                "public_cunit_ids_in_stored_order": row_ids,
                "asking_for_help": row_asking,
                "assigned_to_help": row_assigned,
                "assignment_target_province_id": row_target,
            }
        )
    if subunit_index >= len(rows):
        raise ValueError("selected subunit stored index is out of bounds")
    selected_row = rows[subunit_index]
    if selected_row["public_cunit_ids_in_stored_order"].count(selected_id) != 1:
        raise ValueError("selected CUnitID is not in the selected subunit")
    if (
        selected_row["asking_for_help"] is not asking
        or selected_row["assigned_to_help"] is not assigned
        or selected_row["assignment_target_province_id"] != target_id
    ):
        raise ValueError("selected subunit row disagrees with top-level state")

    contact = _dict(
        frame.get("contact_projection"),
        "battle_reinforcement_assignment.contact_projection",
        _CONTACT_FIELDS,
    )
    contact_status = contact.get("status")
    if contact_status not in {"available", "unavailable", "not_applicable"}:
        raise ValueError("contact projection status is invalid")
    if (
        contact.get("temporal_semantics")
        != "present_time_only_not_future_binding"
    ):
        raise ValueError("contact projection temporal semantics changed")
    combat_ids = _ids(
        contact.get(
            "current_target_compatible_combat_ids_in_stored_order"
        ),
        "battle_reinforcement_assignment.contact_projection."
        "current_target_compatible_combat_ids_in_stored_order",
        unique=True,
    )
    selected_combat_id = _optional_positive_int32(
        contact.get("contact_if_now_selected_combat_id"),
        "battle_reinforcement_assignment.contact_projection."
        "contact_if_now_selected_combat_id",
    )
    if target_id is None:
        if contact_status != "not_applicable" or combat_ids or selected_combat_id:
            raise ValueError("contact projection without target is invented")
    elif contact_status == "not_applicable":
        raise ValueError("assigned target cannot have not_applicable contact")
    elif contact_status == "unavailable":
        if combat_ids or selected_combat_id is not None:
            raise ValueError("unavailable contact projection invented state")
    elif selected_combat_id != (combat_ids[-1] if combat_ids else None):
        raise ValueError("contact selection must be the final stored candidate")

    return {
        **frame,
        "selected_native_carmy_id": selected_native_id,
        "coordinator_id": coordinator_id,
        "unit_stack_stored_index": unit_stack_index,
        "subunit_stored_index": subunit_index,
        "signal": dict(signal),
        "assignment": dict(assignment),
        "route": {
            **route,
            "route_province_ids": route_ids,
            "arrival_date_raws": arrivals,
            "assignment_eta_date_raw": eta,
        },
        "native_order": {
            **native_order,
            "support_search_province_ids_in_stored_order": support_ids,
            "parent_subunits_in_stored_order": rows,
        },
        "contact_projection": {
            **contact,
            "current_target_compatible_combat_ids_in_stored_order": combat_ids,
            "contact_if_now_selected_combat_id": selected_combat_id,
        },
    }
