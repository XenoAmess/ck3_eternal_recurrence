"""Normal native mercenary hire request and submission-only ACK contract."""
from __future__ import annotations

from collections.abc import Mapping
from .player_mercenary_context import _terms
from .version_identity import CK3_12003, require_exact_native_build
from .war_contract import HIRE_MERCENARY_V1_CAPABILITY, HIRE_MERCENARY_V1_STEP

STEP = HIRE_MERCENARY_V1_STEP
CAPABILITY = HIRE_MERCENARY_V1_CAPABILITY
SCHEMA = "ck3_12003_mercenary_hire_action_v1"


def validate_hire_mercenary_request_v1(company_id: object, expected_revision: object) -> None:
    if type(company_id) is not int or not 0 <= company_id < 2**32-1:
        raise ValueError("company_id must be a full uint32 company reference; zero is valid")
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("expected_revision must be a non-negative public revision")


def normalize_hire_mercenary_v1(value: object, *, snapshot: Mapping[str, object],
                              expected_company_id: int) -> dict[str, object]:
    if not isinstance(value, dict) or value.get("step") != STEP:
        raise ValueError("native mercenary hire ACK is malformed")
    build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if (build != CK3_12003 or value.get("read_only") is not False
            or type(value.get("command_sequence")) is not int or value["command_sequence"] <= 0
            or type(value.get("snapshot_revision")) is not int
            or value["snapshot_revision"] != snapshot.get("native_revision")
            or type(value.get("date_raw")) is not int or value["date_raw"] != snapshot.get("date_raw")):
        raise ValueError("native mercenary hire ACK differs from its submission frame")
    action = value.get("mercenary_hire")
    if not isinstance(action, Mapping) or action.get("schema") != SCHEMA:
        raise ValueError("native mercenary hire action schema is malformed")
    status = action.get("status")
    accepted = status in {"submitted", "already_hired"}
    expected_status = "submitted_verification_pending" if status == "submitted" else status
    if (status not in {"submitted", "already_hired", "rejected", "unavailable"}
            or type(value.get("accepted")) is not bool or value["accepted"] != accepted
            or value.get("status") != expected_status
            or type(action.get("snapshot_revision")) is not int
            or action["snapshot_revision"] != value["snapshot_revision"]
            or type(action.get("date_raw")) is not int or action["date_raw"] != value["date_raw"]
            or type(action.get("company_id")) is not int or action["company_id"] != expected_company_id
            or type(action.get("native_hire_mode")) is not int or action["native_hire_mode"] != 1):
        raise ValueError("native mercenary hire result identity/status is malformed")
    player = snapshot.get("played_character")
    actor = action.get("actor_character_id")
    if not isinstance(player, Mapping) or (actor is not None and actor != player.get("character_id")):
        raise ValueError("native mercenary hire actor differs from current player")
    if accepted and (type(actor) is not int or actor != player.get("character_id")):
        raise ValueError("accepted mercenary hire lacks the current actor")
    for field in ("company_resolved", "native_command_validation_observable",
                  "command_submitted", "verification_pending"):
        if type(action.get(field)) is not bool:
            raise ValueError(f"native mercenary hire {field} is malformed")
    employer = action.get("prior_employer_character_id")
    if employer is not None and (type(employer) is not int or not 0 <= employer < 2**32-1):
        raise ValueError("native mercenary hire prior employer is malformed")
    observable = action["native_command_validation_observable"]
    valid = action.get("native_command_valid")
    if observable and type(valid) is not bool or not observable and valid is not None:
        raise ValueError("native mercenary command validation observation is malformed")
    reason = action.get("unavailable_reason")
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError("native mercenary hire unavailable reason is malformed")
    if action.get("after_state_observed") is not False:
        raise ValueError("native mercenary hire ACK does not supply an independent after-state")
    _terms(action.get("final_terms"))
    # Preserve native debt allowance, literal reasons and queue status. No
    # generic affordability gate or observed hire/payment/army result is added.
    return dict(value)
