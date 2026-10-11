"""Project existing construction results without selecting or submitting an action.

A receipt query observes the material result of its original action.  Its
``applied`` result is not an acknowledgement of a new construction submission.
All verdicts here describe supplied production results; absent identity or
verification fields remain unknown.  This module has no ledger or driver access.
"""

from collections.abc import Mapping


SUBMIT_STEP = "private-submit-player-construction-v1"
RECEIPT_STEP = "private-query-player-construction-receipt-v1"
TUPLE_KEYS = ("barony_title_id", "province_id", "building_type_id", "slot_index")
SCHEMA = "xar.ck3.construction_selected_intent_continuity_v1"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _boolean(value: object) -> bool | None:
    return value if type(value) is bool else None


def _candidate(value: object) -> dict[str, int | None] | None:
    if not isinstance(value, Mapping):
        return None
    return {key: value.get(key) if type(value.get(key)) is int else None
            for key in TUPLE_KEYS}


def _identity(value: object) -> dict[str, object]:
    row = _mapping(value)
    candidate = _mapping(row.get("candidate"))
    return {
        "action_request_id": _text(row.get("action_request_id")),
        "episode_run_id": _text(row.get("episode_run_id")),
        "actor_character_id": (
            row.get("actor_character_id")
            if type(row.get("actor_character_id")) is int else None
        ),
        "candidate": {
            key: candidate.get(key) if type(candidate.get(key)) is int else None
            for key in TUPLE_KEYS
        },
    }


def _equal(left: object, right: object) -> bool | None:
    if left is None or right is None:
        return None
    return left == right


def _all_matches(values: tuple[bool | None, ...]) -> bool | None:
    if False in values:
        return False
    return True if all(value is True for value in values) else None


def _result_fields(value: object) -> dict[str, object]:
    row = _mapping(value)
    status = _text(row.get("status"))
    postcondition = _boolean(row.get("postcondition_verified"))
    reported_requested = _boolean(row.get("requested_postcondition_verified"))
    reported_material = _boolean(row.get("material_postcondition_verified"))
    requested = None
    material = None
    restoration = None
    outcome = "unknown"
    if status == "applied" and postcondition is True:
        # The first production receipt predates the two explicit flags.
        if reported_requested is not False and reported_material is not False:
            requested = True
            material = True
            outcome = "requested_construction_observed"
    elif status == "observed_mismatched_construction":
        if reported_requested is False and reported_material is True:
            requested = False
            material = True
            outcome = "different_construction_observed"
    elif status == "restored_before_action" and postcondition is True:
        # Here postcondition_verified proves rollback, not a built building.
        requested = False
        material = False
        restoration = True
        outcome = "restored_before_original_action"
    elif status == "not_applied_after_restore":
        if reported_requested is False and reported_material is False:
            requested = False
            material = False
            outcome = "original_action_not_applied_after_restore"
    elif status in {"submitted_verification_pending", "action_state_unknown"}:
        outcome = "independent_material_result_pending"
    return {
        "producer_status": status,
        "producer_postcondition_verified": postcondition,
        "producer_requested_postcondition_verified": reported_requested,
        "producer_material_postcondition_verified": reported_material,
        "requested_construction_verified": requested,
        "material_construction_verified": material,
        "restoration_verified": restoration,
        "observed_material_candidate": _candidate(
            row.get("candidate") if status == "applied" and material is True
            else row.get("observed_material_tuple")
        ),
        "intent_outcome": outcome,
    }


def project_construction_selected_intent_v1(
    selected_step: object,
    pending_action: object,
    typed_result: object,
    *,
    deferred_selected_step: object = None,
) -> dict[str, object]:
    """Associate this selected query's result with its original pending action.

    The deferred step is an explicit caller copy.  It is never reconstructed,
    selected, or authorised for replay.  A missing native ACK is not a gate.
    """
    original = _identity(pending_action)
    observed = _identity(typed_result)
    action_match = _all_matches(tuple(
        _equal(original[key], observed[key])
        for key in ("action_request_id", "episode_run_id")
    ))
    actor_match = _equal(original["actor_character_id"], observed["actor_character_id"])
    original_tuple = original["candidate"]
    observed_tuple = observed["candidate"]
    candidate_match = _all_matches(tuple(
        _equal(original_tuple[key], observed_tuple[key]) for key in TUPLE_KEYS
    ))
    fields = _result_fields(typed_result)
    step = _text(selected_step)
    role = (
        "prior_action_receipt_query" if step == RECEIPT_STEP else
        "submission_result" if step == SUBMIT_STEP else "unknown"
    )
    # Restoration results intentionally lack actor/tuple fields.  Positive
    # requested-construction projection additionally needs their exact match.
    bound = action_match is True and actor_match is not False and candidate_match is not False
    if fields["requested_construction_verified"] is True:
        bound = bound and actor_match is True and candidate_match is True
    if role == "unknown" or not bound:
        fields = {**fields, "requested_construction_verified": None,
                  "material_construction_verified": None,
                  "restoration_verified": None, "intent_outcome": "unknown"}
    return {
        "schema": SCHEMA,
        "source_role": role,
        "selected_step": step,
        "deferred_selected_step": _text(deferred_selected_step),
        "original_action": original,
        "observed_action": observed,
        "action_identity_matches": action_match,
        "actor_identity_matches": actor_match,
        "candidate_identity_matches": candidate_match,
        "selected_query_performed_new_submission": False if step == RECEIPT_STEP else None,
        **fields,
    }


def project_construction_consumed_intent_v1(receipt: object) -> dict[str, object]:
    """Expose the old receipt's intent result on the next ordinary plan.

    This contains no current selected command, replay permission, or transition
    eligibility.  Missing original fields cannot be recovered from a later plan.
    """
    identity = _identity(receipt)
    fields = _result_fields(receipt)
    identity_complete = (
        identity["action_request_id"] is not None and identity["episode_run_id"] is not None
    )
    if fields["requested_construction_verified"] is True:
        identity_complete = identity_complete and identity["actor_character_id"] is not None
        identity_complete = identity_complete and all(
            value is not None for value in identity["candidate"].values()
        )
    if not identity_complete:
        fields = {**fields, "requested_construction_verified": None,
                  "material_construction_verified": None,
                  "restoration_verified": None, "intent_outcome": "unknown"}
    return {
        "schema": SCHEMA,
        "source_role": "previous_construction_receipt",
        "original_action": identity,
        "selected_query_performed_new_submission": None,
        **fields,
    }
