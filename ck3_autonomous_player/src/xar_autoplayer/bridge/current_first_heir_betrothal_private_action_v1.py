"""Private fulfillment of the current heir's actual bilateral betrothal."""

from __future__ import annotations

from .current_first_heir_relationship_private_transport import (
    SCHEMA as RELATION_SCHEMA, _current_pair_actionability,
)
from .driver import BridgeUnavailableError
from .marriage_matchmaking_private_transport import _require_same_paused_frame
from .observed_heir_marriage_private_action_v1 import SCHEMA, _command, _paused
from .nonwar_private_build import (
    private_native_provenance, private_native_readback_matches,
)


SUBMIT_STEP = "submit-current-first-heir-betrothal-fulfillment-v1-private"


def submit_current_first_heir_betrothal_private_v1(
    driver: object, *, relationship: dict[str, object],
    timeout_seconds: float = 360.0,
) -> dict[str, object]:
    """Use the fixed-pair query binding; a send ACK remains nonmaterial."""
    before = _paused(driver)
    actor = before["played_character"]["character_id"]
    revision = before["native_revision"]
    heir = relationship.get("heir_character_id")
    partner = relationship.get("betrothed_character_id")
    if (relationship.get("schema") != RELATION_SCHEMA
            or not private_native_readback_matches(before, relationship)
            or relationship.get("status") != "available"
            or relationship.get("read_only") is not True
            or relationship.get("advertised") is not False
            or relationship.get("native_revision") != revision
            or relationship.get("bilateral_verified") is not True
            or type(relationship.get("root_query_sequence")) is not int
            or relationship["root_query_sequence"] <= 0
            or type(heir) is not int or heir <= 0 or heir == actor
            or type(partner) is not int or partner <= 0 or partner == heir
            or relationship.get("primary_spouse_character_id") is not None
            or relationship.get("spouse_character_ids") != []):
        raise BridgeUnavailableError("betrothal fulfillment lacks current bilateral pair")
    value = _current_pair_actionability(
        relationship.get("betrothal_actionability"),
        actor=actor, heir=heir, partner=partner)
    if (value.get("status") != "available"
            or value.get("ready_to_marry_betrothed") is not True
            or value.get("complete_can_send") is not True
            or value.get("recipient_answer_status_raw") not in (0, 1)
            or value.get("recipient_ai_accept_raw", 0) <= 0
            or value.get("predicted_outcome_if_accepted") != "marriage"):
        raise BridgeUnavailableError("betrothal fulfillment lacks native final legality")
    recipient = value["recipient_character_id"]
    _require_same_paused_frame(driver.take_snapshot(), before, revision, actor)
    result = _command(driver, SUBMIT_STEP, {
        "expected_revision": revision,
        "heir_character_id": heir,
        "candidate_character_id": partner,
        "recipient_character_id": recipient,
    }, timeout_seconds)
    if (result.get("status") != "receipt_pending"
            or result.get("material_result") is not False
            or result.get("fulfill_existing_betrothal") is not True
            or result.get("matrilineal_option_selected") is not value["effective_matrilineal_if_accepted"]
            or result.get("pre_native_revision") != revision
            or result.get("played_character_id") != actor
            or result.get("heir_character_id") != heir
            or result.get("candidate_character_id") != partner
            or result.get("recipient_character_id") != recipient):
        raise BridgeUnavailableError("betrothal fulfillment ACK changed its fixed pair")
    return {"schema": SCHEMA, "schema_version": 1,
            **private_native_provenance(before), "advertised": False, **result}
