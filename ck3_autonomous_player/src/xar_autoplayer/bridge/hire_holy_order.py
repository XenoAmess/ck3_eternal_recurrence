"""Normal native holy-order hire request and submission-only ACK contract."""
from __future__ import annotations

from collections.abc import Mapping
from .player_holy_order_context_private_transport import normalize_player_holy_order_context_v1
from .version_identity import CK3_12003, require_exact_native_build
from .war_contract import HIRE_HOLY_ORDER_V1_CAPABILITY, HIRE_HOLY_ORDER_V1_STEP

STEP = HIRE_HOLY_ORDER_V1_STEP
CAPABILITY = HIRE_HOLY_ORDER_V1_CAPABILITY
SCHEMA = "ck3_12003_holy_order_hire_action_v1"


def validate_hire_holy_order_request_v1(holy_order_id: object, expected_revision: object) -> None:
    if type(holy_order_id) is not int or not 0 <= holy_order_id < 2**32-1:
        raise ValueError("holy_order_id must be a full uint32 holy-order reference; zero is valid")
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative public revision")


def normalize_hire_holy_order_v1(value: object, *, snapshot: Mapping[str, object],
                              expected_holy_order_id: int) -> dict[str, object]:
    if not isinstance(value, dict) or value.get("step") != STEP:
        raise ValueError("native holy-order hire ACK is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if (build != CK3_12003 or value.get("read_only") is not False
            or type(value.get("command_sequence")) is not int or value["command_sequence"] <= 0
            or type(value.get("snapshot_revision")) is not int
            or value["snapshot_revision"] != snapshot.get("native_revision")
            or type(value.get("date_raw")) is not int or value["date_raw"] != snapshot.get("date_raw")):
        raise ValueError("native holy-order hire ACK differs from its submission frame")
    action = value.get("holy_order_hire")
    if not isinstance(action, Mapping) or action.get("schema") != SCHEMA:
        raise ValueError("native holy-order hire action schema is malformed")
    status = action.get("status")
    accepted = status in {"submitted", "already_hired"}
    expected_status = "submitted_verification_pending" if status == "submitted" else status
    if (status not in {"submitted", "already_hired", "rejected", "unavailable"}
            or type(value.get("accepted")) is not bool or value["accepted"] != accepted
            or value.get("status") != expected_status
            or type(action.get("snapshot_revision")) is not int
            or action["snapshot_revision"] != value["snapshot_revision"]
            or type(action.get("date_raw")) is not int or action["date_raw"] != value["date_raw"]
            or type(action.get("holy_order_id")) is not int or action["holy_order_id"] != expected_holy_order_id
            or type(action.get("native_hire_mode")) is not int or action["native_hire_mode"] != 3):
        raise ValueError("native holy-order hire result identity/status is malformed")
    player = snapshot.get("played_character")
    actor = action.get("actor_character_id")
    if not isinstance(player, Mapping) or (actor is not None and actor != player.get("character_id")):
        raise ValueError("native holy-order hire actor differs from current player")
    if accepted and (type(actor) is not int or actor != player.get("character_id")):
        raise ValueError("accepted holy-order hire lacks the current actor")
    for field in ("holy_order_resolved", "native_command_validation_observable",
                  "command_submitted", "verification_pending"):
        if type(action.get(field)) is not bool:
            raise ValueError(f"native holy-order hire {field} is malformed")
    employer = action.get("prior_employer_character_id")
    if employer is not None and (type(employer) is not int or not 0 <= employer < 2**32-1):
        raise ValueError("native holy-order hire prior employer is malformed")
    observable = action["native_command_validation_observable"]
    valid = action.get("native_command_valid")
    if observable and type(valid) is not bool or not observable and valid is not None:
        raise ValueError("native holy-order command validation observation is malformed")
    reason = action.get("unavailable_reason")
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError("native holy-order hire unavailable reason is malformed")
    if action.get("after_state_observed") is not False:
        raise ValueError("native holy-order hire ACK does not supply an independent after-state")
    context = action.get("prior_context")
    # An unavailable binding can have no capture. Otherwise reuse the existing
    # holy-order observation contract, including independent quote/strength.
    if isinstance(context, dict) and context.get("capture_epoch", 0) > 0:
        normalize_player_holy_order_context_v1(context, snapshot=snapshot)
    elif status != "unavailable":
        raise ValueError("native holy-order hire lacks a current context")
    if status == "submitted":
        if (not action["holy_order_resolved"] or not observable or valid is not True
                or action["command_submitted"] is not True
                or action["verification_pending"] is not True):
            raise ValueError("submitted holy-order hire lacks native validation/queue acceptance")
    elif action["command_submitted"] or action["verification_pending"]:
        raise ValueError("unsubmitted holy-order hire claims a queued mutation")
    if status == "already_hired" and employer != actor:
        raise ValueError("already hired holy-order result lacks current employer observation")
    # Preserve native reasons and current terms. Employer/payment/CUnitID
    # outcome requires fresh independent queries after submission.
    return dict(value)
