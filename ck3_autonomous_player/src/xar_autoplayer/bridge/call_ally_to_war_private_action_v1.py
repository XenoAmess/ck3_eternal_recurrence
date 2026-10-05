"""Submit one caller-selected native-final ally invitation to one active war.

The existing family observation permit and execute-step channel are reused.
An observed native refusal returns the queried terms without submitting.
A native submission receipt never establishes that the ally joined the war.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .timeline_blocker_private_transport import _binding
from .version_identity import CK3_12003


SUBMIT_STEP = "submit-call-ally-to-war-v1-private"
SCHEMA = "xar.ck3.call-ally-to-war-private-action.v1"
KIND = "ck3_12003_call_ally_to_war_private_v1"
PERMISSION = "allow_private_family_obligations_query"
COST_SLOTS = ["gold", "prestige", "piety", "renown", "influence", "herd",
              "treasury", "treasury_or_gold", "merit", "barter_goods"]


def _full_id(value: object) -> bool:
    return type(value) is int and -(1 << 31) <= value < (1 << 31) and value != -1


def _costs(value: object) -> bool:
    return (isinstance(value, list) and len(value) == 10
            and all(type(item) is int and -(1 << 63) <= item < (1 << 63)
                    for item in value))


def _frame(driver: object, expected_revision: int) -> dict[str, object]:
    if getattr(driver, PERMISSION, False) is not True:
        raise UnsupportedStepError("private family observation is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must identify the current public snapshot")
    before = driver.take_snapshot()
    actor = before.get("played_character")
    if (before.get("revision") != expected_revision
            or before.get("paused") is not True or before.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or not _full_id(actor.get("character_id"))
            or type(before.get("native_revision")) is not int or before["native_revision"] <= 0
            or private_native_build_identity(before) != CK3_12003):
        raise BridgeUnavailableError("call ally requires the current paused living player frame")
    return before


def submit_call_ally_to_war_private_v1(
    driver: object, *, expected_revision: int, war_id: int,
    recipient_character_id: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Quote the selected pair; reject or queue one native invitation without retry."""
    if not _full_id(war_id) or not _full_id(recipient_character_id):
        raise ValueError("call ally requires complete signed war and character IDs")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _frame(driver, expected_revision)
    actor_id = before["played_character"]["character_id"]
    if recipient_character_id == actor_id:
        raise ValueError("call ally recipient must differ from the played character")
    observation = driver.query_family_obligations_private_v1(
        expected_revision=expected_revision, ally_character_id=recipient_character_id)
    alliance = observation.get("alliance_obligations")
    if (not isinstance(alliance, Mapping) or alliance.get("status") != "available"
            or alliance.get("first_character_id") != actor_id
            or alliance.get("second_character_id") != recipient_character_id
            or alliance.get("raw_scale") != 100000
            or alliance.get("send_cost_slot_keys") != COST_SLOTS
            or not isinstance(alliance.get("first_wars"), list)
            or observation.get("queried_revision") != before["revision"]
            or observation.get("queried_native_revision") != before["native_revision"]):
        raise BridgeUnavailableError("call ally lacks its current selected-pair observation")
    rows = [row for row in alliance["first_wars"] if isinstance(row, Mapping)
            and row.get("war_id") == war_id
            and row.get("caller_character_id") == actor_id
            and row.get("recipient_character_id") == recipient_character_id]
    if len(rows) != 1:
        raise BridgeUnavailableError("call ally selected war is absent or ambiguous")
    selected = rows[0]
    quote = selected.get("send_cost_raw")
    if (selected.get("native_target_can_be_picked") is not True
            or selected.get("native_target_row_selectable") is not True
            or type(selected.get("native_complete_can_send")) is not bool
            or not _costs(quote)):
        raise BridgeUnavailableError("call ally selected target lacks final native send legality")
    if _binding(_frame(driver, expected_revision)) != _binding(before):
        raise BridgeUnavailableError("call ally paused player frame changed before submit")
    if selected["native_complete_can_send"] is False:
        # This is an observed query refusal, with no native sender request.
        # Keep the owning C88 text and sampled terms exactly as published.
        return {
            "schema": SCHEMA, "schema_version": 1, "kind": KIND,
            **private_native_provenance(before),
            "status": "rejected", "accepted": False, "submitted": False,
            "material_result": False, "verification_pending": False,
            "native_submit_attempted": False, "request_id": None,
            "result_source": "native_family_query", "read_only": True,
            "private_build": True, "advertised": False,
            "reason": "call_ally_native_complete_can_send_false",
            "played_character_id": actor_id,
            "recipient_character_id": recipient_character_id, "war_id": war_id,
            "expected_revision": expected_revision,
            "source_date_raw": before.get("date_raw"),
            "queried_snapshot_id": observation.get("queried_snapshot_id"),
            "queried_revision": observation["queried_revision"],
            "queried_native_revision": observation["queried_native_revision"],
            "source_query_frame": deepcopy(observation.get("frame")),
            "raw_scale": 100000, "send_cost_slot_keys": list(COST_SLOTS),
            "quoted_send_cost_raw": list(quote), "automatic_retry": False,
            "selected_native_terms": deepcopy(dict(selected)),
        }
    request_id = "call-ally-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": SUBMIT_STEP, "expected_revision": before["native_revision"],
        "recipient_character_id": recipient_character_id, "war_id": war_id,
        "expected_send_cost_raw": list(quote),
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, Mapping) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("call ally receipt unresolved; do not automatically resubmit")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("call ally native RED: " + str(frame.get("error") or "unknown"))
    result = frame.get("result")
    if (not isinstance(result, dict) or result.get("step") != SUBMIT_STEP
            or result.get("schema") != SCHEMA or result.get("kind") != KIND
            or result.get("private_build") is not True or result.get("read_only") is not False
            or result.get("advertised") is not False
            or result.get("status") not in {"receipt_pending", "rejected", "unavailable"}
            or result.get("material_result") is not False
            or result.get("pre_native_revision") != before["native_revision"]
            or result.get("snapshot_revision") != before["native_revision"]
            or result.get("date_raw") != before.get("date_raw")
            or result.get("game_version") != CK3_12003.game_version
            or result.get("executable_sha256") != CK3_12003.executable_sha256
            or result.get("played_character_id") != actor_id
            or result.get("recipient_character_id") != recipient_character_id
            or result.get("war_id") != war_id
            or type(result.get("send_cost_sampled")) is not bool
            or (result.get("send_cost_sampled") is True
                and not _costs(result.get("actual_send_cost_raw")))
            or (result.get("send_cost_sampled") is False
                and result.get("actual_send_cost_raw") is not None)
            or type(result.get("selected_target_native_legal")) is not bool
            or type(result.get("copied_context_identity_verified")) is not bool
            or not isinstance(result.get("reason"), str)):
        raise BridgeUnavailableError("call ally receipt differs from the selected invitation")
    submitted = result["status"] == "receipt_pending"
    if (result.get("accepted") is not submitted
            or (submitted and (result["send_cost_sampled"] is not True
                               or result["actual_send_cost_raw"] != quote
                               or result["selected_target_native_legal"] is not True
                               or result["copied_context_identity_verified"] is not True))):
        raise BridgeUnavailableError("call ally receipt cannot establish native submission")
    return {"schema": SCHEMA, "schema_version": 1,
            **private_native_provenance(before), **deepcopy(result),
            "submitted": submitted, "verification_pending": submitted,
            "request_id": request_id, "expected_revision": expected_revision,
            "source_date_raw": before.get("date_raw"),
            "raw_scale": 100000, "send_cost_slot_keys": COST_SLOTS,
            "quoted_send_cost_raw": list(quote), "automatic_retry": False,
            "selected_native_terms": deepcopy(dict(selected))}
